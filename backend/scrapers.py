from botasaurus_server.server import Server
from src.scrape_google_maps import scrape_google_maps

# Add the scraper to the server
Server.add_scraper(scrape_google_maps)