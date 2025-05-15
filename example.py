import asyncio
import logging
import time
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
from playwright.async_api import async_playwright
from beautifulsoup4 import BeautifulSoup

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Données globales à servir
scraped_data = []

async def fetch_with_browser(playwright, url, retry_count=0, max_retries=3):
    """
    Utilise Playwright pour charger dynamiquement une page Google Maps et en extraire le titre.

    Args:
        playwright: Instance Playwright.
        url (str): URL à scraper.
        retry_count (int): Nombre de tentatives effectuées.
        max_retries (int): Nombre max de tentatives.

    Returns:
        dict: Un dictionnaire avec l'URL et le titre ou une erreur.
    """
    try:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=30000)
        await page.wait_for_timeout(4000)  # attendre le rendu JS
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string if soup.title else "Titre introuvable"
        await browser.close()
        return {"url": url, "title": title}
    except Exception as e:
        logging.error(f"Erreur lors du chargement de {url} : {e}")
        if retry_count < max_retries:
            await asyncio.sleep(2 ** retry_count)
            logging.info(f"Nouvelle tentative pour {url} (tentative {retry_count + 1})")
            return await fetch_with_browser(playwright, url, retry_count + 1, max_retries)
        return {"url": url, "error": str(e)}

async def main(urls):
    """
    Fonction principale pour gérer les tâches Playwright en parallèle.
    """
    async with async_playwright() as playwright:
        tasks = [fetch_with_browser(playwright, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

class DataHandler(SimpleHTTPRequestHandler):
    """
    Serveur HTTP simple qui renvoie les données scrapées au format JSON.
    """
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"scraped_data": scraped_data}, ensure_ascii=False, indent=2).encode())
        else:
            super().do_GET()

def run_server(data):
    """
    Lance un serveur HTTP sur localhost:8000
    """
    global scraped_data
    scraped_data = data
    port = 8000
    httpd = HTTPServer(('localhost', port), DataHandler)
    print(f"Serveur HTTP disponible sur http://localhost:{port}/")
    httpd.serve_forever()

if __name__ == "__main__":
    # Liste d’exemples d’URL Google Maps (cid)
    sample_urls = [
        "https://www.google.com/maps?cid=10841271384594827821",
        "https://www.google.com/maps?cid=1519735334139957582",
        "https://www.google.com/maps?cid=17223482373573387535",
    ]

    # Lancer le scraping
    start_time = time.time()
    results = asyncio.run(main(sample_urls))
    end_time = time.time()

    if results:
        print(f"Données récupérées en {end_time - start_time:.2f} secondes.")
        for res in results:
            print(res)

        # Lancer un serveur HTTP local pour afficher les résultats
        server_thread = threading.Thread(target=run_server, args=(results,))
        server_thread.daemon = True
        server_thread.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nArrêt du serveur.")
    else:
        print("Aucune donnée récupérée.")
