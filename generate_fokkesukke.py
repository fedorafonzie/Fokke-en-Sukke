import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re

print("Script gestart: Ophalen van de Fokke & Sukke strip via nrc.nl.")

# De URL van de nrc.nl rubriek pagina
COMIC_PAGE_URL = "https://www.nrc.nl/rubriek/fokke-sukke/"
image_url = None

try:
    # --- Stap 1: Haal de pagina op en extraheer de image URL ---
    print(f"Pagina ophalen: {COMIC_PAGE_URL}")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}
    response = requests.get(COMIC_PAGE_URL, headers=headers)
    response.raise_for_status()

    # Gebruik BeautifulSoup om de HTML te parsen
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Zoek naar de <a> tag die de link naar de specifieke strip bevat
    link_tag = soup.find('a', href=re.compile(r'/fokke-sukke-'))
    
    if not link_tag:
        raise ValueError("Kon geen <a> tag vinden met '/fokke-sukke-' in de href. Structuur mogelijk gewijzigd.")

    # Zoek *binnen* deze link naar de <img> tag.
    # We hoeven niet per se de wrapper te vinden, de img-tag is uniek genoeg.
    img_tag = link_tag.find('img')
    
    # --- AANGEPASTE LOGICA: Geef 'src' prioriteit ---
    if img_tag and img_tag.has_attr('src'):
        # PRIORITEIT: Pak direct de 'src' URL, die bevat de 1280x versie
        image_url = img_tag['src']
        print(f"SUCCES (via 'src'): Afbeelding URL gevonden: {image_url}")

    elif img_tag and img_tag.has_attr('srcset'):
        # FALLBACK: Als 'src' er niet is, parse 'srcset'
        print("INFO: 'src' niet gevonden, fallback naar 'srcset'.")
        srcset = img_tag['srcset']
        srcset_list = srcset.split(',')
        last_url_entry = srcset_list[-1].strip()
        image_url = last_url_entry.split(' ')[0]
        print(f"SUCCES (via 'srcset'): Afbeelding URL gevonden: {image_url}")
        
    else:
        raise ValueError("Kon de <img> tag of diens 'src'/'srcset' attribute niet vinden binnen de link-wrapper.")
    # --- EINDE AANGEPASTE LOGICA ---


except (requests.exceptions.RequestException, ValueError) as e:
    print(f"FOUT: Kon de afbeelding niet ophalen. Foutdetails: {e}")
    exit(1)

# --- Stap 2: Bouw de RSS-feed ---

fg = FeedGenerator()
fg.id(COMIC_PAGE_URL)
fg.title('Fokke & Sukke')
fg.link(href=COMIC_PAGE_URL, rel='alternate')
fg.description('De dagelijkse Fokke & Sukke strip van nrc.nl.')
fg.language('nl')

nu = datetime.now(timezone.utc)
datum_titel = nu.strftime("%Y-%m-%d")

fe = fg.add_entry()
fe.id(image_url)
fe.title(f'Fokke & Sukke - {datum_titel}')
fe.link(href=COMIC_PAGE_URL)
fe.pubDate(nu)
fe.description(f'<img src="{image_url}" alt="Fokke & Sukke strip voor {datum_titel}" />')

# --- Stap 3: Schrijf het XML-bestand weg ---

try:
    fg.rss_file('fokke_sukke.xml', pretty=True)
    print("SUCCES: 'fokke_sukke.xml' is aangemaakt met de strip van vandaag.")
except Exception as e:
    print(f"FOUT: Kon het bestand niet wegschrijven. Foutmelding: {e}")
    exit(1)