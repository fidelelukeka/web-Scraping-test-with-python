import requests
from bs4 import BeautifulSoup
import asyncio
import aiohttp
import logging
import time

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Définir une limite de tentatives et un délai d'attente
MAX_RETRIES = 3
TIMEOUT = 10  # secondes

# Liste des user-agents pour le spoofing
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux i686; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-G998B Build/R16KP.210331.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.101 Mobile Safari/537.36",
]

async def fetch_page(session, url, retry_count=0):
    """
    Récupère le contenu d'une page web de manière asynchrone avec gestion des erreurs et des retours à la ligne.

    Args:
        session (aiohttp.ClientSession): La session HTTP à utiliser.
        url (str): L'URL de la page à récupérer.
        retry_count (int, optional): Le nombre de tentatives de récupération. Defaults to 0.

    Returns:
        str: Le contenu de la page web, ou None en cas d'échec après plusieurs tentatives.
    """
    user_agent = USER_AGENTS[retry_count % len(USER_AGENTS)]  # Sélectionne un user-agent
    headers = {'User-Agent': user_agent}

    try:
        async with session.get(url, headers=headers, timeout=TIMEOUT) as response:
            response.raise_for_status()  # Lève une exception pour les codes d'erreur HTTP (4xx ou 5xx)
            return await response.text()
    except aiohttp.ClientError as e:
        logging.error(f"Erreur de client HTTP pour {url}: {e}")
        if retry_count < MAX_RETRIES:
            await asyncio.sleep(2 ** retry_count)  # Délai exponentiel
            logging.info(f"Réessai de {url} (tentative {retry_count + 1})")
            return await fetch_page(session, url, retry_count + 1)
        else:
            logging.error(f"Abandon de la récupération de {url} après {MAX_RETRIES} tentatives")
            return None
    except Exception as e:
        logging.error(f"Erreur inattendue lors de la récupération de {url}: {e}")
        return None

def extract_data(html, url):
    """
    Extrait les données pertinentes du HTML de la page.

    Args:
        html (str): Le code HTML de la page web.
        url (str): L'URL de la page (pour le logging).

    Returns:
        dict: Un dictionnaire contenant les données extraites, ou None en cas d'échec.
    """
    try:
        soup = BeautifulSoup(html, 'lxml')  # Utilisez lxml pour une meilleure performance
        # Exemple d'extraction (à adapter à la structure réelle de la page)
        name = soup.find('h1', class_='DUwDvf').text.strip() if soup.find('h1', class_='DUwDvf') else "N/A"
        address = soup.find('div', class_='LrzXr').text.strip() if soup.find('div', class_='LrzXr') else "N/A"
        # phone = soup.find('...')  # À adapter
        # email = soup.find('...')  # À adapter
        # website = soup.find('...') # À adapter

        data = {
            'name': name,
            'address': address,
            # 'phone': phone,
            # 'email': email,
            # 'website': website,
            'url': url,  # Inclure l'URL pour référence
        }
        return data
    except Exception as e:
        logging.error(f"Erreur lors de l'extraction des données de {url}: {e}")
        return None

async def process_url(session, url, results):
    """
    Récupère et traite une URL, en ajoutant les résultats à la liste partagée.

    Args:
        session (aiohttp.ClientSession): La session HTTP.
        url (str): L'URL à traiter.
        results (list): La liste partagée pour stocker les résultats.
    """
    html = await fetch_page(session, url)
    if html:
        data = extract_data(html, url)
        if data:
            results.append(data)

async def main(urls):
    """
    Fonction principale pour lancer le scraping asynchrone.

    Args:
        urls (list): La liste des URLs à scraper.
    """
    results = []  # Liste pour stocker les résultats
    async with aiohttp.ClientSession() as session:
        tasks = [process_url(session, url, results) for url in urls]
        await asyncio.gather(*tasks)  # Exécute toutes les tâches en parallèle
    return results

if __name__ == "__main__":
    # Exemple d'utilisation
    start_time = time.time()
    sample_urls = [
        "https://www.google.com/maps?cid=10841271384594827821",  # Exemple 1
        "https://www.google.com/maps?cid=1519735334139957582",   # Exemple 2
        "https://www.google.com/maps?cid=17223482373573387535", # Exemple 3
        # Ajouter plus d'URLs ici
    ]
    scraped_data = asyncio.run(main(sample_urls))
    end_time = time.time()

    if scraped_data:
        print(f"Données récupérées : {scraped_data}")
        print(f"Temps total d'exécution : {end_time - start_time:.2f} secondes")
    else:
        print("Aucune donnée récupérée.")
