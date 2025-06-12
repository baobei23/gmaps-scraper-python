from botasaurus_server.server import Server
from src.scrape_google_maps import scrape_google_maps
import csv
import urllib.parse

def split_task(data):
    queries = []
    if data.get('use_categories'):
        location = data.get('category_location')
        if not location:
            raise ValueError("Lokasi harus diisi saat menggunakan pencarian kategori.")

        max_categories = data.get('max_categories')
        
        with open('backend/inputs/googlemaps_category.csv', 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            categories = [row[0] for row in reader]
        
        if max_categories:
            categories = categories[:int(max_categories)]
            
        queries = [f'{category} di {location}' for category in categories]
    else:
        queries = data.get('queries', [])

    tasks = []
    for query in queries:
        if not query:
            continue
        encoded_query = urllib.parse.quote_plus(query)
        link = f"https://www.google.com/maps/search/{encoded_query}"
        tasks.append({'query': query, 'link': link})
        
    return tasks

def get_task_name(task):
    return task.get('query')

# Add the scraper to the server
Server.add_scraper(
    scrape_google_maps,
    create_all_task=True,
    split_task=split_task,
    get_task_name=get_task_name,
    remove_duplicates_by='link',
)