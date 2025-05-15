import asyncio
import aiohttp
import logging
import time
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define retry limit and timeout
MAX_RETRIES = 3
TIMEOUT = 10  # seconds

async def fetch_page(session, url, retry_count=0):
    """
    Asynchronously fetches the content of a web page.

    Args:
        session (aiohttp.ClientSession): The HTTP session to use.
        url (str): The URL of the page to fetch.
        retry_count (int, optional): The number of retrieval attempts. Defaults to 0.

    Returns:
        str: The content of the web page, or None if it fails after several attempts.
    """
    try:
        async with session.get(url, timeout=TIMEOUT) as response:
            response.raise_for_status()  # Raise an exception for HTTP error codes
            return await response.text()
    except aiohttp.ClientError as e:
        logging.error(f"HTTP client error for {url}: {e}")
        if retry_count < MAX_RETRIES:
            await asyncio.sleep(2 ** retry_count)
            logging.info(f"Retrying {url} (attempt {retry_count + 1})")
            return await fetch_page(session, url, retry_count + 1)
        else:
            logging.error(f"Failed to retrieve {url} after {MAX_RETRIES} attempts")
            return None
    except Exception as e:
        logging.error(f"Unexpected error while fetching {url}: {e}")
        return None

async def main(urls):
    """
    Main function to launch asynchronous scraping.

    Args:
        urls (list): The list of URLs to scrape.
    """
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_page(session, url) for url in urls]
        results = await asyncio.gather(*tasks)  # Execute all tasks in parallel
        return results

class DataHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"scraped_data": scraped_data}).encode())
        else:
            super().do_GET()

def run_server(data):
    global scraped_data
    scraped_data = data
    port = 8000
    httpd = HTTPServer(('localhost', port), DataHandler)
    print(f"Serving scraped data on http://localhost:{port}/")
    httpd.serve_forever()

if __name__ == "__main__":
    # Example usage
    start_time = time.time()
    sample_urls = [
        "https://www.google.com/maps?cid=10841271384594827821",
        "https://www.google.com/maps?cid=1519735334139957582",
        "https://www.google.com/maps?cid=17223482373573387535",
    ]
    scraped_data_results = asyncio.run(main(sample_urls))
    end_time = time.time()

    if scraped_data_results:
        print(f"Retrieved data: {scraped_data_results}")
        print(f"Total execution time: {end_time - start_time:.2f} seconds")

        # Run a simple web server in a separate thread
        server_thread = threading.Thread(target=run_server, args=(scraped_data_results,))
        server_thread.daemon = True
        server_thread.start()

        # Keep the main thread alive to allow the server to run
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nServer stopped.")
    else:
        print("No data retrieved.")