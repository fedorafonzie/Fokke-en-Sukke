import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re  # <-- Deze regel is nieuw

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
    
    # --- AANGEPASTE LOGICA ---
    # We zoeken nu specifieker: vind een <a> tag waarvan de 'href' (link)
    # de tekst '/fokke-sukke-' bevat. Dit is veel specifieker.
    link_tag = soup.find('a', href=re.compile(r'/fokke-sukke-'))
    
    if not link_tag:
        raise ValueError("Kon geen <a> tag vinden met '/fokke-sukke-' in de href. Structuur mogelijk gewijzigd.")

    # Zoek nu *binnen* deze gevonden link naar de image wrapper
    wrapper = link_tag.find('div', class_='nmt-item_image-wrapper')
    
    if not wrapper:
         raise ValueError(f"Kon de <div> met class='nmt-item_image-wrapper' *binnen* de gevonden link niet vinden. Href was: {link_tag.get('href')}")
    # --- EINDE AANGEPASTE LOGICA ---

    # Zoek de <img> tag binnen deze wrapper
    img_tag = wrapper.find('img')
    
    if img_tag and img_tag.has_attr('srcset'):
        # Het 'srcset' attribute bevat meerdere URLs.
        # We pakken de laatste, dit is meestal de hoogste resolutie.
        srcset = img_tag['srcset']
        
        # Split de srcset op komma's
        srcset_list = srcset.split(',')
        
        # Pak het laatste item (bv. 'https://.../image.jpg 1280w')
        # .strip() om eventuele witruimte te verwijderen
        last_url_entry = srcset_list[-1].strip()
        
        # Split op spatie en pak het eerste deel (de URL)
        image_url = last_url_entry.split(' ')[0]
        
        print(f"SUCCES: Afbeelding URL gevonden: {image_url}")
        
    elif img_tag and img_tag.has_attr('src'):
        # Fallback: als 'srcset' er niet is, pak 'src'
        image_url = img_tag['src']
        print(f"SUCCES (via fallback): Afbeelding URL gevonden: {image_url}")
    else:
        raise ValueError("Kon de <img> tag of diens 'srcset'/'src' attribute niet vinden binnen de wrapper.")

except (requests.exceptions.RequestException, ValueError) as e:
    print(f"FOUT: Kon de afbeelding niet ophalen. Foutdetails: {e}")
    exit(1)

# --- Stap 2: Bouw de RSS-feed ---

fg = FeedGenerator()
fg.id(COMIC_PAGE_URL)
fg.title('Fokke & Sukke')
fg.link(href=COMIC_PAGE_URL, rel='alternate')
fg.description('De dagelijkse Fokke & Sukke strip van nrc.nl.')
fg.language('nl') # Taal aangepast naar Nederlands

nu = datetime.now(timezone.utc)
datum_titel = nu.strftime("%Y-%m-%d")

fe = fg.add_entry()
fe.id(image_url) # Gebruik de unieke image URL als ID
fe.title(f'Fokke & Sukke - {datum_titel}')
fe.link(href=COMIC_PAGE_URL) # Link naar de rubriekpagina
fe.pubDate(nu)

# Zet de afbeelding in de description
fe.description(f'<img src="{image_url}" alt="Fokke & Sukke strip voor {datum_titel}" />')

# --- Stap 3: Schrijf het XML-bestand weg ---

try:
    fg.rss_file('fokke_sukke.xml', pretty=True)
    print("SUCCES: 'fokke_sukke.xml' is aangemaakt met de strip van vandaag.")
except Exception as e:
    print(f"FOUT: Kon het bestand niet wegschrijven. Foutmelding: {e}")
    exit(1)