from botasaurus.browser import browser, Driver, AsyncQueueResult
from botasaurus.request import request, Request
from botasaurus.lang import Lang
import json

def extract_title(html):
    try:
        raw_data = json.loads(html.split(";window.APP_INITIALIZATION_STATE=")[1].split(";window.APP_FLAGS")[0])[3][6]
        raw_data.startswith(")]}'")
        cleaned = raw_data[5:]
        parsed_data = json.loads(cleaned)

        nama = parsed_data[6][11]
        alamat = parsed_data[6][39]
        telepon = parsed_data[6][178][0][3]
        kategori = parsed_data[6][13]
        pemilik = parsed_data[6][57][1]

        return(nama, alamat, telepon, kategori, pemilik)
    except (IndexError, KeyError, ValueError, TypeError):
        return None, None, None, None, None

@request(
    parallel=5,
    async_queue=True,
    max_retry=5,
    output=None
)
def scrape_place_title(request: Request, link, metadata):
    cookies = metadata["cookies"]
    query = metadata.get("query")
    html = request.get(link, cookies=cookies, timeout=12).text
    nama, alamat, telepon, kategori, pemilik = extract_title(html)
    print(nama)
    return {
        "nama": nama,
        "alamat": alamat,
        "telepon": telepon,
        "kategori": kategori,
        "pemilik": pemilik,
        "link": link,
        "query": query,
        }

def has_reached_end(driver):
    return driver.select('p.fontBodyMedium > span > span') is not None

def extract_links(driver):
    return driver.get_all_links('[role="feed"] > div > div > a')

@browser(headless=True,
         block_images_and_css=True,
         lang=Lang.Indonesian,
         wait_for_complete_page_load=False,
         output=None
         )
def scrape_google_maps(driver: Driver, data):
    url = data['link']
    query = data.get('query')
    driver.google_get(url, accept_google_cookies=True)  # accepts google cookies popup

    scrape_place_obj: AsyncQueueResult = scrape_place_title()  # initialize the async queue for scraping places
    cookies = driver.get_cookies_dict()  # get the cookies from the driver

    while True:
        links = extract_links(driver)  # get the links to places
        scrape_place_obj.put(links, metadata={"cookies": cookies, "query": query})  # add the links to the async queue for scraping

        print("scrolling")
        driver.scroll_to_bottom('[role="feed"]')  # scroll to the bottom of the feed

        if has_reached_end(driver):  # we have reached the end, let's break buddy
            break

    results = scrape_place_obj.get()  # get the scraped results from the async queue
    return results