from botasaurus.browser import browser, Driver
import subprocess
import json
import os
from botasaurus.lang import Lang
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
from threading import Lock
import queue
import threading
import time

# Thread pool for handling subprocess calls
thread_pool = ThreadPoolExecutor(max_workers=5)
result_lock = Lock()

def call_node_scraper(link, cookies, query):
    """Call Node.js scraper using subprocess"""
    try:
        script_path = os.path.join(os.path.dirname(__file__), 'scraper_node.js')
        cookies_json = json.dumps(cookies)
        
        # Call Node.js script
        result = subprocess.run([
            'node', script_path, link, cookies_json, query or ''
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"Node.js error for {link}: {result.stderr}")
            return {
                "nama": None,
                "alamat": None,
                "telepon": None,
                "kategori": None,
                "pemilik": None,
                "link": link,
                "query": query,
                "error": result.stderr
            }
        
        # Parse the JSON result
        scraped_data = json.loads(result.stdout.strip())
        print(f"Scraped: {scraped_data.get('nama', 'Unknown')}")
        return scraped_data
        
    except subprocess.TimeoutExpired:
        print(f"Timeout scraping {link}")
        return {
            "nama": None,
            "alamat": None,
            "telepon": None,
            "kategori": None,
            "pemilik": None,
            "link": link,
            "query": query,
            "error": "Timeout"
        }
    except Exception as e:
        print(f"Error scraping {link}: {str(e)}")
        return {
            "nama": None,
            "alamat": None,
            "telepon": None,
            "kategori": None,
            "pemilik": None,
            "link": link,
            "query": query,
            "error": str(e)
        }

class NodeScraperQueue:
    """Custom async queue implementation for Node.js scraper with concurrent processing"""
    def __init__(self):
        self.processed_links = set()  # Track processed links to avoid duplicates
        self.task_queue = queue.Queue()
        self.results = []
        self.metadata = {}
        self.is_scraping = False
        self.scraping_thread = None
        
    def put(self, links, metadata=None):
        """Add links to the queue"""
        if metadata:
            self.metadata.update(metadata)
        
        if isinstance(links, str):
            links = [links]
            
        new_links = []
        for link in links:
            if link not in self.processed_links:
                self.processed_links.add(link)
                new_links.append(link)
                
        if new_links:
            for link in new_links:
                self.task_queue.put(link)
            
            # Start scraping thread if not already running
            if not self.is_scraping:
                self.start_scraping()
    
    def start_scraping(self):
        """Start background scraping thread"""
        if self.is_scraping:
            return
            
        self.is_scraping = True
        self.scraping_thread = threading.Thread(target=self._scrape_worker, daemon=True)
        self.scraping_thread.start()
        print("Background scraping dimulai...")
    
    def _scrape_worker(self):
        """Background worker that processes the queue"""
        cookies = self.metadata.get('cookies', {})
        query = self.metadata.get('query', '')
        
        while self.is_scraping:
            try:
                # Get link from queue with timeout
                link = self.task_queue.get(timeout=2)
                
                # Process the link
                future = thread_pool.submit(call_node_scraper, link, cookies, query)
                
                try:
                    result = future.result(timeout=60)
                    if result:
                        with result_lock:
                            self.results.append(result)
                            print(f"✓ Selesai scraping: {result.get('nama', 'Unknown')} (Total: {len(self.results)})")
                except Exception as e:
                    print(f"Error scraping {link}: {str(e)}")
                
                self.task_queue.task_done()
                
            except queue.Empty:
                # No tasks in queue, continue waiting
                continue
            except Exception as e:
                print(f"Worker error: {str(e)}")
    
    def stop_scraping(self):
        """Stop the background scraping"""
        self.is_scraping = False
        if self.scraping_thread:
            self.scraping_thread.join(timeout=5)
        print("Background scraping dihentikan.")
    
    def get(self):
        """Wait for all tasks to complete and return results"""
        # Wait for all queued tasks to complete
        print("Menunggu semua scraping selesai...")
        self.task_queue.join()
        
        # Stop the scraping thread
        self.stop_scraping()
        
        print(f"Total hasil scraping: {len(self.results)}")
        return self.results

def scrape_place_title():
    """Initialize the Node.js scraper queue"""
    return NodeScraperQueue()

def has_reached_end(driver):
    return driver.select('p.fontBodyMedium > span > span') is not None

def extract_links(driver):
    return driver.get_all_links('[role="feed"] > div > div > a')

@browser(headless=False,
         block_images_and_css=True,
         lang=Lang.Indonesian,
         output=None
         )
def scrape_google_maps(driver: Driver, data):
    url = data['link']
    query = data.get('query')
    driver.google_get(url, accept_google_cookies=True)  # accepts google cookies popup

    scrape_place_obj = scrape_place_title()  # initialize the Node.js scraper queue
    cookies = driver.get_cookies_dict()  # get the cookies from the driver

    while True:
        links = extract_links(driver)  # get the links to places
        scrape_place_obj.put(links, metadata={"cookies": cookies, "query": query})  # add the links to the queue

        print("scrolling")
        driver.scroll_to_bottom('[role="feed"]')  # scroll to the bottom of the feed

        if has_reached_end(driver):  # we have reached the end, let's break buddy
            links = extract_links(driver)  # get the links to places
            scrape_place_obj.put(links, metadata={"cookies": cookies, "query": query})  # add the links to the queue
            break

    results = scrape_place_obj.get()  # get the scraped results from the queue
    return results