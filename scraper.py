"""
Kleinanzeigen PS5 Scraper mit KI-Filter
Benutzt Groq/Llama um irrelevante Anzeigen vor dem Beschreibungs-Scraping auszufiltern.
"""

import json
import os
import random
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os
import uuid
from groq import Groq
from camoufox.sync_api import Camoufox
from supabase import create_client, Client

# .env laden
load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase verbunden")
    except Exception as e:
        print(f"⚠️ Supabase Init Fehler: {e}")



def random_delay(min_sec: float = 1.0, max_sec: float = 3.0):
    """Zufällige Wartezeit für menschlicheres Verhalten."""
    time.sleep(random.uniform(min_sec, max_sec))

def parse_price(price_str):
    if not price_str: return 0.0
    # Entferne 'VB', '€' und Leerzeichen
    clean = price_str.lower().replace('vb', '').replace('€', '').strip()
    # Entferne Tausender-Punkte (1.200 -> 1200)
    clean = clean.replace('.', '')
    # Ersetze Komma durch Punkt (12,50 -> 12.50)
    clean = clean.replace(',', '.')
    try:
        return float(clean)
    except:
        return 0.0


def handle_cookie_consent(page):
    """Spezielle Funktion nur für den Cookie-Banner (Polling)."""
    print("   🍪 Prüfe auf Cookie-Banner...", flush=True)
    try:
        # Versuche 5x im Abstand von 1s den Banner zu finden
        for i in range(5):
            # 1. Shadow DOM Usercentrics (Hartnäckig)
            found = page.evaluate("""
                () => {
                    const host = document.querySelector('#usercentrics-root');
                    if (host && host.shadowRoot) {
                        const btn = host.shadowRoot.querySelector('button[data-testid="uc-accept-all-button"]');
                        if (btn) {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)
            if found:
                print("   ✅ Cookie-Banner (Shadow DOM) akzeptiert.", flush=True)
                return

            # 2. Klassische Banner & Text-Suche (Priorität!)
            try:
                # Suche explizit nach dem Text aus dem Screenshot
                green_btn = page.locator("button:has-text('Alle akzeptieren'), button:has-text('Zustimmen')").first
                if green_btn.count() > 0 and green_btn.is_visible():
                    green_btn.click()
                    print("   ✅ Cookie-Banner ('Alle akzeptieren') geklickt.", flush=True)
                    return

                # Fallback auf IDs
                gdpr_btn = page.locator("#gdpr-banner-accept, [data-testid='gdpr-banner-accept'], #uc-btn-accept-banner").first
                if gdpr_btn.count() > 0 and gdpr_btn.is_visible():
                    gdpr_btn.click()
                    print("   ✅ Cookie-Banner (ID) akzeptiert.", flush=True)
                    return
            except: pass
            
            time.sleep(1.0)
            
    except Exception as e:
        print(f"   ⚠️ Cookie Config Fehler: {e}", flush=True)

def dismiss_overlays(page):
    """Schließt Modal-Backdrops und andere Overlays via JavaScript."""
    # Erst Cookies klären
    handle_cookie_consent(page)
    
    # Dann Rest
    try:
        page.evaluate("""
            () => {
                 // Login Overlay (nerviges zweites Modal)
                const loginOverlay = document.querySelector('.login-overlay--content .overlay-close');
                if (loginOverlay) loginOverlay.click();

                // Allgemeine Modals
                const closeButtons = document.querySelectorAll('.modal-close, .close-button, [aria-label="Schließen"], .overlay-close');
                if (loginOverlay) login.click();

                // Allgemeine Modals
                const closeButtons = document.querySelectorAll('.modal-close, .close-button, [aria-label="Schließen"], .overlay-close');
                closeButtons.forEach(btn => btn.click());
            }
        """)
    except: pass

def scrape_listings(base_url: str, num_pages: int = 1, use_ai_filter: bool = True) -> list[dict]:
    """Scrapt Listings von Kleinanzeigen."""
    listings = []
    
    print(f"🌎 Starte Browser (Camoufox)...")
    
    with Camoufox(headless=True) as browser:
        page = browser.new_page()
        
        # Anti-Detection Headers
        page.set_extra_http_headers({
            "Accept-Language": "de-DE,de;q=0.9",
        })

        for i in range(num_pages):
            page_num = i + 1
            if page_num == 1:
                url = base_url
            else:
                # Kleinanzeigen Pagination Logic
                if "/seite:" in base_url:
                    # Falls URL schon Pagination hat, ersetzen (etwas hacky, für jetzt OK)
                     url = base_url 
                else:
                    # Standard Format: /s-suchbegriff/preis:100:300/k0
                    # Ziel: /s-suchbegriff/seite:2/preis:100:300/k0
                    # Wir suchen das Segement, das NICHT 'preis:' oder 'k0' ist, aber mit 's-' anfängt (optional) oder einfach das erste Segment nach Domain?
                    # Besser: Wir splitten und suchen den Suchbegriff.
                    
                    parts = base_url.split('/')
                    # parts[0-2] ist https://domain
                    # parts[3] ist meist 's-suchbegriff' oder 's-...'
                    
                    # Finde index wo 's-' steht (Such-Segment)
                    insert_idx = -1
                    for idx, p in enumerate(parts):
                        if p.startswith('s-') and 'preis:' not in p and 'seite:' not in p:
                            insert_idx = idx
                            break
                    
                    if insert_idx != -1:
                        # Einfügen von 'seite:N' NACH dem Suchbegriff
                        parts.insert(insert_idx + 1, f"seite:{page_num}")
                        url = "/".join(parts)
                    else:
                        # Fallback: Einfach anhängen, aber vor 'k0' wenn möglich?
                        # Alte Logic fallback
                        url = base_url.replace('/k0', f'/seite:{page_num}/k0') if '/k0' in base_url else base_url + f"/seite:{page_num}" 

            print(f"\n📄 Lade Seite {page_num}: {url}")
            
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                random_delay(2, 4)
                
                # Cookie Banner & Overlays
                if i == 0:
                    dismiss_overlays(page)
                
                # Scrollen
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                random_delay(1, 2)
                
                # Parsing
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(page.content(), "html.parser")
                
                # Find ad list
                ad_list = soup.find('ul', id='srchrslt-adtable')
                if not ad_list:
                    print("   ⚠️ Keine Anzeigen-Liste gefunden.")
                    # DEBUG: Save screenshot and HTML for analysis
                    try:
                        page.screenshot(path="debug_no_adlist.png")
                        with open("debug_no_adlist.html", "w", encoding="utf-8") as f:
                            f.write(page.content())
                        print("   📸 Debug-Screenshot gespeichert: debug_no_adlist.png")
                        
                        # Check for common issues
                        html_lower = page.content().lower()
                        if "captcha" in html_lower or "challenge" in html_lower:
                            print("   🚨 CAPTCHA/Challenge erkannt!")
                        if "blocked" in html_lower or "gesperrt" in html_lower:
                            print("   🚨 IP möglicherweise GEBLOCKT!")
                        if "too many requests" in html_lower:
                            print("   🚨 Rate Limit erkannt!")
                    except Exception as debug_err:
                        print(f"   Debug save error: {debug_err}")
                    break
                    
                items = ad_list.find_all('li', class_='ad-listitem')
                print(f"   Artikel auf Seite: {len(items)}")
                
                for item in items:
                    if 'is-topad' in item.get('class', []): continue # Skip Top Ads (oft Werbung)
                    
                    article = item.find('article')
                    if not article: continue
                    
                    try:
                        id_ = article.get('data-adid')
                        link_elem = article.find('a', class_='ellipsis')
                        
                        if not link_elem: continue
                        
                        title = link_elem.get_text().strip()
                        link = "https://www.kleinanzeigen.de" + link_elem.get('href')
                        
                        # Preis
                        price_elem = article.find('p', class_='aditem-main--middle--price-shipping--price')
                        price = price_elem.get_text().strip() if price_elem else ""
                        
                        # Ort / Zeit
                        details = article.find('div', class_='aditem-main--top--left')
                        location = ""
                        date_str = ""
                        if details:
                            txt = details.get_text(separator='|').strip()
                            parts = [p.strip() for p in txt.split('|') if p.strip()]
                            if len(parts) >= 2:
                                location = parts[0]
                                date_str = parts[1]
                        
                        # Tags
                        tags_elem = article.find('div', class_='aditem-main--bottom')
                        tags = []
                        if tags_elem:
                            tags = [t.get_text().strip() for t in tags_elem.find_all('span', class_='text-module-end')]
                        
                        listing = {
                            "id": id_,
                            "title": title,
                            "price": price,
                            "link": link,
                            "location": location,
                            "date": date_str,
                            "tags": tags,
                            "scraped_at": datetime.now().isoformat(),
                            "isGesuch": "Gesuch" in title or "suche" in title.lower() # Grober check
                        }
                        listings.append(listing)
                        
                    except Exception as e:
                        print(f"   Parsing Fehler für Item: {e}")
                        continue
                        
            except Exception as e:
                print(f"   Fehler beim Laden von Seite {page_num}: {e}")
                
    print(f"\n✅ Scraping beendet. {len(listings)} Anzeigen gefunden.")
    return listings

def categorize_listings(listings: list[dict]) -> list[dict]:
    """
    Kategorisiert Listings in 'normal', 'abholung', 'defekt'.
    """
    print(f"\n🏷️ Kategorisiere {len(listings)} Listings...")
    
    for l in listings:
        text_full = (l['title'] + " " + l.get('description', '')).lower()
        
        # 1. Defekt Check
        if any(x in text_full for x in ['defekt', 'kaputt', 'bastler', 'broken', 'schaden']):
            l['category'] = 'defekt'
            continue
            
        # 2. Abholung Check (wenn 'versand' explizit verneint oder 'nur abholung')
        # Einfache Heuristik: 'nur abholung' oder 'kein versand'
        if 'nur abholung' in text_full or 'kein versand' in text_full:
            l['category'] = 'abholung'
            continue
            
        # Default
        l['category'] = 'normal'
        
    return listings

    print(f"🌎 Starte Browser (Camoufox)...")
    
    with Camoufox(headless=True) as browser:
        page = browser.new_page()
        
        # Anti-Detection Headers
        page.set_extra_http_headers({
            "Accept-Language": "de-DE,de;q=0.9",
        })

        for i in range(num_pages):
            page_num = i + 1
            if page_num == 1:
                url = base_url
            else:
                # Kleinanzeigen Pagination Logic
                if "/seite:" in base_url:
                     url = base_url 
                else:
                    parts = base_url.split('/')
                    insert_idx = -1
                    for idx, p in enumerate(parts):
                        if p.startswith('s-'):
                            insert_idx = idx
                            break
                    
                    if insert_idx != -1:
                        new_s_part = parts[insert_idx].replace('s-', f's-seite:{page_num}-')
                        parts[insert_idx] = new_s_part
                        url = "/".join(parts)
                    else:
                        url = base_url + f"seite:{page_num}/" 

            print(f"\n📄 Lade Seite {page_num}: {url}")
            
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                random_delay(2, 4)
                
                # Cookie Banner & Overlays
                if i == 0:
                    dismiss_overlays(page)
                
                # Scrollen
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                random_delay(1, 2)
                
                # Parsing
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(page.content(), "html.parser")
                
                # Find ad list
                ad_list = soup.find('ul', id='srchrslt-adtable')
                if not ad_list:
                    print("   ⚠️ Keine Anzeigen-Liste gefunden.")
                    break
                    
                items = ad_list.find_all('li', class_='ad-listitem')
                print(f"   Artikel auf Seite: {len(items)}")
                
                for item in items:
                    if 'is-topad' in item.get('class', []): continue # Skip Top Ads (oft Werbung)
                    
                    article = item.find('article')
                    if not article: continue
                    
                    try:
                        id_ = article.get('data-adid')
                        link_elem = article.find('a', class_='ellipsis')
                        
                        if not link_elem: continue
                        
                        title = link_elem.get_text().strip()
                        link = "https://www.kleinanzeigen.de" + link_elem.get('href')
                        
                        # Preis
                        price_elem = article.find('p', class_='aditem-main--middle--price-shipping--price')
                        price = price_elem.get_text().strip() if price_elem else ""
                        
                        # Ort / Zeit
                        details = article.find('div', class_='aditem-main--top--left')
                        location = ""
                        date_str = ""
                        if details:
                            txt = details.get_text(separator='|').strip()
                            parts = [p.strip() for p in txt.split('|') if p.strip()]
                            if len(parts) >= 2:
                                location = parts[0]
                                date_str = parts[1]
                        
                        # Tags
                        tags_elem = article.find('div', class_='aditem-main--bottom')
                        tags = []
                        if tags_elem:
                            tags = [t.get_text().strip() for t in tags_elem.find_all('span', class_='text-module-end')]
                        
                        listing = {
                            "id": id_,
                            "title": title,
                            "price": price,
                            "link": link,
                            "location": location,
                            "date": date_str,
                            "tags": tags,
                            "scraped_at": datetime.now().isoformat(),
                            "isGesuch": "Gesuch" in title or "suche" in title.lower() # Grober check
                        }
                        listings.append(listing)
                        
                    except Exception as e:
                        print(f"   Parsing Fehler für Item: {e}")
                        continue
                        
            except Exception as e:
                print(f"   Fehler beim Laden von Seite {page_num}: {e}")
                
    print(f"\n✅ Scraping beendet. {len(listings)} Anzeigen gefunden.")
    return listings

def categorize_listings(listings: list[dict]) -> list[dict]:
    """
    Kategorisiert Listings in 'normal', 'abholung', 'defekt'.
    """
    print(f"\n🏷️ Kategorisiere {len(listings)} Listings...")
    
    for l in listings:
        text_full = (l['title'] + " " + l.get('description', '')).lower()
        
        # 1. Defekt Check
        if any(x in text_full for x in ['defekt', 'kaputt', 'bastler', 'broken', 'schaden']):
            l['category'] = 'defekt'
            continue
            
        # 2. Abholung Check (wenn 'versand' explizit verneint oder 'nur abholung')
        # Einfache Heuristik: 'nur abholung' oder 'kein versand'
        if 'nur abholung' in text_full or 'kein versand' in text_full:
            l['category'] = 'abholung'
            continue
            
        # Default
        l['category'] = 'normal'
        
    return listings

def filter_titles_with_ai(listings: list[dict]) -> list[dict]:
    """
    Benutzt Groq/Llama um Titel zu analysieren.
    Enthält jetzt auch einen strengen Vor-Filter für offensichtliche Falsch-Treffer.
    """
    if not listings:
        return []

    # 1. HARTER VOR-FILTER (spart API Tokens und filtert offensichtlichen Müll)
    pre_filtered = []
    print(f"\n🔍 Starte Vor-Filterung von {len(listings)} Anzeigen...")
    
    search_term = os.getenv("SEARCH_TERM", "ps5").lower()
    search_term_clean = search_term.replace(" ", "").lower()
    term_parts = search_term.split()

    for l in listings:
        t = l['title'].lower()
        
        # MUSS Suchbegriff enthalten (Token-basiert oder Variationen)
        # Check if ALL parts are in title
        all_parts_found = all(part in t for part in term_parts)
        
        # PS5-Handling fallback
        synonyms = [search_term, search_term_clean]
        if 'ps5' in search_term:
            synonyms.append("playstation 5")
            synonyms.append("playstation5")
            
        matches_strict = any(s in t for s in synonyms)
        
        if not (all_parts_found or matches_strict):
            continue
            
        # Darf NICHT "Suche/Gesuch" sein
        if "suche" in t or "gesuch" in t or "kaufe" in t or "ankauf" in t:
            continue
            
        # Darf NICHT "Portal" sein (PlayStation Portal)
        if "portal" in t and ("remote" in t or "player" in t):
            continue
            
        # Darf NICHT "Ständer" oder "Halterung" sein
        if "ständer" in t or "halterung" in t or "wandhalterung" in t:
            continue
        
        # Controller Filter (einfach)
        if "controller" in t and "konsole" not in t and "bundle" not in t:
             if "scuf" in t or "aim" in t or "edge" in t:
                 continue
            
        pre_filtered.append(l)

    print(f"✅ {len(pre_filtered)} von {len(listings)} Listings haben den '{search_term}'-Namenstest bestanden.")
    
    if not pre_filtered:
        print("❌ Alle Listings wurden vom Vor-Filter aussortiert.")
        return []
    

    # 2. KI-FILTER
    print(f"\n🤖 Analysiere {len(listings)} Titel mit KI...")
    
    # Trenne bereits markierte (durch Vor-Filter) von den zu prüfenden
    # WICHTIG: Auch 'rejected_price' darf NICHT mehr geprüft werden!
    to_check = [l for l in listings if 'rejected' not in l.get('filter_status', '')]
    
    if not to_check:
        print("❌ Alle Listings bereits durch Vor-Filter abgelehnt.")
        return listings

    client = Groq(api_key=GROQ_API_KEY)
    
    # Bereite Titel-Liste für den Prompt vor
    titles_text = "\n".join([
        f"{i+1}. {l['title']} | {price_clean(l['price'])}"
        for i, l in enumerate(to_check)
    ])
    
    # Dynamic Prompt Construction
    
    product_name = search_term.upper()
    
    if "ps5" in search_term or "playstation 5" in search_term:
        # Specific PS5 Rules
        prompt = f"""Du bist ein strenger Einkaufs-Modet.
Aufgabe: Identifiziere Anzeigen, die eine ECHTE PlayStation 5 KONSOLE verkaufen.

FILTERE STRENG RAUS (NEIN):
- ALLES was PS4 oder PS3 ist
- "PlayStation Portal" oder "Remote Player"
- NUR Controller, Headset, Spiele, OVP, Zubehör
- Defekte Konsolen
- Miete / Verleih

BEHALTE NUR (JA):
- Funktionierende PS5 Konsolen (Disc oder Digital)
- Auch Bundles (Konsole + Controller + Spiele) sind OK.

ANZEIGEN:
{titles_text}

Antworte NUR mit einem JSON-Array der Nummern der ECHTEN KONSOLEN, z.B. [1, 3, 5]."""

    else:
        # Generic Rules for other items (Xbox, iPhone, etc.)
        prompt = f"""Du bist ein strenger Einkaufs-Modet.
Aufgabe: Identifiziere Anzeigen, die ein ECHTES '{product_name}' verkaufen.

FILTERE STRENG RAUS (NEIN):
- Veraltete Versionen / Andere Modelle (die nicht {product_name} sind)
- NUR Zubehör, Kabel, Kartons (OVP), Spiele ohne Konsole/Gerät
- Defekte Geräte
- Miete / Verleih
- "Suche" Anzeigen

BEHALTE NUR (JA):
- Funktionierende '{product_name}' Geräte
- Auch Bundles, wenn das Hauptgerät enthalten ist.

ANZEIGEN:
{titles_text}

Antworte NUR mit einem JSON-Array der Nummern der ECHTEN TREFFER, z.B. [1, 3, 5]."""

    print("\n📤 Sende an Groq/Llama 3.3 70B...")
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=500
        )
        
        result_text = response.choices[0].message.content.strip()
        
        import re
        all_matches = re.findall(r'\[[\d,\s]*\]', result_text)
        
        relevant_indices = []
        for match in reversed(all_matches):
            try:
                parsed = json.loads(match)
                if parsed:
                    relevant_indices = parsed
                    break
            except: pass
        
        print(f"Ki Antwort: {result_text}")
        print(f"📊 KI wählt aus: {relevant_indices}")
        
        # Markiere Status
        for i, l in enumerate(to_check):
            idx = i + 1
            if idx in relevant_indices:
                # Wurde von KI akzeptiert
                if not l.get('filter_status'): # Nur wenn nicht schon rejected
                    l['filter_status'] = 'passed_ai_title'
                    l['filter_reason'] = 'AI Title Check Passed'
            else:
                # Von KI abgelehnt
                l['filter_status'] = 'rejected_ai_title'
                l['filter_reason'] = 'AI did not select this title'
        
        return listings # Return original list (modified in place)
        
    except Exception as e:
        print(f"⚠️ KI-Filter Fehler: {e}")
        # Fallback: Alles als 'manual_check_needed' markieren oder so?
        return manual_filter(listings)


def manual_filter(listings: list[dict]) -> list[dict]:
    """Fallback-Filter bzw Vor-Filter ohne KI."""
    
    skip_keywords = [
        'suche', 'gesuch', 'controller', 'dualsense', 'headset', 
        'spiel', 'game', 'laufwerk', 'ps4', 'playstation 4',
        'defekt', 'kaputt', 'bastler', 'scuf', 'edge controller',
        'miete', 'verleih'
    ]
    
    search_term = os.getenv("SEARCH_TERM", "ps5").lower()
    search_term_clean = search_term.replace(" ", "").lower() # e.g. "xboxseriesx"
    
    # Split search term into parts for looser matching if needed (simple approach first)
    # e.g. "xbox series x" -> ["xbox", "series", "x"]
    term_parts = search_term.lower().split()

    for l in listings:
        # Skip wenn schon rejected (z.B. durch anderen Filter)
        if l.get('filter_status') and 'rejected' in l['filter_status']:
            continue
            
        title_lower = l['title'].lower()
        tags_lower = ' '.join(l['tags']).lower()
        
        # Skip Gesuche
        if l.get('isGesuch') or 'gesuch' in tags_lower:
            l['filter_status'] = 'rejected_keyword'
            l['filter_reason'] = 'Gesuch erkannt'
            continue

        # Check ob Suchbegriff im Titel (Basis-Check)
        # Lockerer Check: Mindestens ein wichtiger Teil des Suchbegriffs sollte drin sein
        # Oder der genaue String
        
        # Simple Logic: Check if "ps5" or "playstation 5" matches, customized for configured term
        # Wir prüfen ob der Titel den Search Term enthält
        
        # Falls Search Term "ps5" ist, prüfen wir auch auf "playstation 5"
        term_variations = [search_term, search_term_clean]
        if 'ps5' in search_term:
            term_variations.append("playstation 5")
            term_variations.append("playstation5")
        
        # Check Match
        # Wir prüfen ob ALLE Wörter des Suchbegriffs im Titel vorkommen (Token-basiert)
        # z.B. "Xbox Series X" -> muss "Xbox", "Series" und "X" enthalten (Reihenfolge egal)
        
        # Ausnahme: PS5/Playstation 5 behandeln wir als Synonym
        requires_all = term_parts
        if 'ps5' in search_term:
             # Logic is complex for PS5 synonyms, simplify:
             # Just stick to flexible matching or exact variations
             pass # Use existing var
             
        # Check if ALL parts are in title
        all_parts_found = all(part in title_lower for part in term_parts)
        
        # Alternative: Strict substring match (old way) or cleaned match
        matches_strict = any(t in title_lower for t in term_variations)
        
        if not (all_parts_found or matches_strict):
             l['filter_status'] = 'rejected_name_mismatch'
             l['filter_reason'] = f"Title mismatch '{search_term}'"
             # DEBUG:
             # print(f"   ❌ Rejected: {l['title']} (Reason: {l['filter_reason']})")
             continue
             
        # Skip wenn Keywords im Titel (Negative Keywords)
        matched_kw = next((kw for kw in skip_keywords if kw in title_lower), None)
        if matched_kw:
            # Aber behalte wenn Suchbegriff EINDEUTIG ist und Keyword vielleicht Kontext ist
            if matched_kw in search_term:
                pass 
            else:
                 l['filter_status'] = 'rejected_keyword'
                 l['filter_reason'] = f"Keyword: {matched_kw}"
            continue
            
        # Vor-FilterPassed
        l['filter_status'] = 'passed_prefilter'
    
    passed_count = sum(1 for l in listings if l.get('filter_status') == 'passed_prefilter')
    print(f"✅ {passed_count} von {len(listings)} Listings haben den '{search_term}'-Namenstest bestanden.")
    
    return listings


def price_clean(p):
    if not p: return "0"
    return p.replace("€", "").replace(".", "").replace(",", ".").strip()

def fetch_description(page, url: str) -> dict:
    """Holt die Beschreibung von einer Anzeigen-Detailseite."""
    try:
        # Fast fail für ungültige URLs
        if not url or not url.startswith('http'): 
            return {"description": None}

        page.goto(url, wait_until="domcontentloaded")
        random_delay(1.5, 3)
        
        try:
            page.keyboard.press("Escape")
        except: pass
        
        details = page.evaluate("""
            () => {
                const description = document.querySelector('#viewad-description-text')?.innerText?.trim() || null;
                const sellerName = document.querySelector('#viewad-contact .text-body-regular-strong')?.innerText?.trim() || 'Privat';
                return { description, seller_name: sellerName };
            }
        """)
        
        return details
        
    except Exception as e:
        print(f"⚠️ Fehler beim Laden der Details: {e}")
        return {"description": None}


def filter_with_description(listings: list[dict]) -> list[dict]:
    """
    Zweiter Filter: Prüft mit voller Beschreibung.
    Markiert Listings als rejected_ai_desc oder passed.
    """
    # Nur 'passed' Listings prüfen
    to_check = [l for l in listings if l.get('filter_status') == 'passed_ai_title']
    
    if not to_check:
        return listings
    
    print(f"\n🔍 Zweiter Filter: Prüfe {len(to_check)} Listings mit voller Beschreibung...")
    
    client = Groq(api_key=GROQ_API_KEY)
    
    for listing in to_check:
        title = listing['title']
        desc = listing.get('description', '') or listing.get('snippet', '')
        price = listing['price']
        
        prompt = f"""Ist das ein Verkauf einer PS5-KONSOLE?
TITEL: {title}
PREIS: {price}
BESCHREIBUNG: {desc[:800]}

Antworte NUR mit: JA oder NEIN"""

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=10
            )
            
            answer = response.choices[0].message.content.strip().upper()
            is_console = "JA" in answer
            
            status = "✅" if is_console else "❌"
            print(f"   {status} {title[:40]}... → {answer}")
            
            if is_console:
                listing['filter_status'] = 'passed' # FINAL PASS
                listing['filter_reason'] = 'Confirmed by AI Description'
            else:
                listing['filter_status'] = 'rejected_ai_desc'
                listing['filter_reason'] = f'AI Desc Reject: {answer}'
                
        except Exception as e:
            print(f"   ⚠️ Fehler bei {title[:30]}: {e}")
            # Im Zweifel behalten
            listing['filter_status'] = 'passed'
            listing['filter_reason'] = f'Error fallback: {e}'
            
    return listings


def main():
    # Read config from .env (loaded at top of file)
    search_term = os.getenv("SEARCH_TERM", "ps5")
    min_price_env = os.getenv("MIN_PRICE", "100")
    max_price_env = os.getenv("MAX_PRICE", "350")
    
    # Cast to int for logic
    try:
         max_price_val = int(max_price_env)
    except:
         max_price_val = 350
    
    # Construct URL dynamically
    # Clean search term for URL (replace spaces with -)
    term_clean = search_term.replace(" ", "-").lower()
    if not term_clean.startswith("s-"):
        term_clean = f"s-{term_clean}"
        
    url = f"https://www.kleinanzeigen.de/{term_clean}/k0?minPreis={min_price_env}&maxPreis={max_price_env}"
    
    print(f"🌍 Such-Parameter: '{search_term}' ({min_price_env}-{max_price_env}€)")
    
    # Schritt 1: Scrapen & Initial Filter (Pre-Filter + Title AI)
    # manual_filter läuft implizit VOR der KI in 'scrape_listings' (wenn wir es dort einbauen)
    # Aber hier rufen wir es explizit auf:
    
    raw_listings = scrape_listings(url, num_pages=2, use_ai_filter=False) # False, weil wir eigene Logik machen
    
    if not raw_listings:
        print("⚠️ Keine Listings gefunden.")
        return

    # 1. Manual Filter (Keywords) - Markiert rejected_keyword
    listings = manual_filter(raw_listings)

    # 1.5 Strict Price Filter (Safety Net against Top Ads)
    # Kleinanzeigen shows "Top Ads" that ignore price filters. We must filter them out manually.
    print(f"\n💰 Prüfe Preise (Max {max_price_val}€)...")
    for l in listings:
        if l.get('filter_status') == 'unknown': # Only check if not already rejected
            p_val = parse_price(l.get('price', '0'))
            if p_val > max_price_val:
                l['filter_status'] = 'rejected_price'
                l['filter_reason'] = f'Price too high: {p_val} > {max_price_val}'
                # print(f"   💸 Ignoriere zu teures Listing: {l['title'][:20]}... ({p_val}€)")
    
    # 2. AI Title Filter - Markiert rejected_ai_title / passed_ai_title
    # Nur auf die loslassen, die noch nicht rejected sind
    listings = filter_titles_with_ai(listings)
    
    # 3. Description Fetch & AI Check - Nur für passed_ai_title
    # Wir müssen erst Descriptions holen für die Candidates
    candidates = [l for l in listings if l.get('filter_status') == 'passed_ai_title']
    
    if candidates:
        print(f"\n📖 Hole Beschreibungen für {len(candidates)} Kandidaten...")
        # Wir brauchen Browser Kontext... eigentlich müsste 'fetch_description' im scrape loop sein.
        # Vereinfachung: Wir holen Descriptions erst im 'scrape_listings' loop für ALLE? 
        # Nein, zu teuer. Wir müssen Browser session wiederverwenden.
        # Hack: scrape_listings gibt jetzt browser context nicht zurück.
        # Lösung: scrape_listings sollte Descriptions für 'passed_ai_title' holen.
        # DAZU MÜSSEN WIR SCRAPE_LISTINGS UMBAUEN.
        pass
    
    # Workaround: Wir speichern einfach ALLES ab.
    # Der User will ja sehen, was rejected wurde.
    # Wenn wir descriptions nicht haben, ist filter_reason halt "Title Check".
    
    # Kategorien erkennen (für alle, auch rejected, warum nicht?)
    categorized = categorize_listings(listings)
    
    # Zählen
    passed_count = len([l for l in categorized if l.get('filter_status') == 'passed']) # Wird erst nach Desc Check gesetzt...
    # Da wir Description Check hier nicht einfach machen können (Browser zu), 
    # setzen wir 'passed_ai_title' als vorläufiges 'passed'.
    
    for l in categorized:
        if l.get('filter_status') == 'passed_ai_title':
             l['filter_status'] = 'passed' # Promote to passed (ohne Desc Check für jetzt, oder als 'candidate')

    # Generate Session ID for this run
    session_id = str(uuid.uuid4())
    print(f"\n🆔 Session ID: {session_id}")

    # SAVE ALL to Supabase
    if supabase and categorized:
        print(f"\n💾 Sende {len(categorized)} Listings an Supabase 'listings'...")
        for l in categorized:
            try:
                # Check for None values
                f_status = l.get('filter_status', 'unknown')
                f_reason = l.get('filter_reason', 'No check ran')
                
                data = {
                    "id": l['id'],
                    "title": l['title'],
                    "price": l['price'],
                    "link": l['link'],
                    "location": l.get('location'),
                    "category": l.get('category', 'normal'),
                    "filter_status": f_status,
                    "filter_reason": f_reason,
                    "session_id": session_id,
                    "created_at": datetime.now().isoformat(),
                    "data": l
                }
                supabase.table("listings").upsert(data).execute()
            except Exception as e:
                print(f"   ⚠️ DB Insert Error ({l['id']}): {e}")

    print("\n🚀 Fertig.")

if __name__ == "__main__":
    main()
