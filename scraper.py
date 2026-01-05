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
                closeButtons.forEach(btn => btn.click());
            }
        """)
    except: pass


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
    
    for l in listings:
        t = l['title'].lower()
        
        # MUSS "ps5" oder "playstation 5" enthalten
        if "ps5" not in t and "playstation 5" not in t and "playstation5" not in t:
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

    print(f"✅ {len(pre_filtered)} von {len(listings)} Listings haben den 'PS5'-Namenstest bestanden.")
    
    if not pre_filtered:
        print("❌ Alle Listings wurden vom Vor-Filter aussortiert.")
        return []
    
    # 2. KI-FILTER
    print(f"\n🤖 Analysiere {len(pre_filtered)} Titel mit KI...")
    
    client = Groq(api_key=GROQ_API_KEY)
    
    # Bereite Titel-Liste für den Prompt vor
    titles_text = "\n".join([
        f"{i+1}. {l['title']} | {l['price']} | {', '.join(l['tags'])}"
        for i, l in enumerate(pre_filtered)
    ])
    
    prompt = f"""Du bist ein strenger Einkaufs-Modet.
Aufgabe: Identifiziere Anzeigen, die eine ECHTE PlayStation 5 KONSOLE verkaufen.

FILTERE STRENG RAUS (NEIN):
- ALLES was PS4 oder PS3 ist (auch wenn "5 Spiele" dabei sind!)
- "PlayStation Portal" oder "Remote Player"
- NUR Controller, Headset, Spiele, OVP, Zubehör
- Defekte Konsolen
- Miete / Verleih

BEHALTE NUR (JA):
- Funktionierende PS5 Konsolen (Disc oder Digital)
- Auch Bundles (Konsole + Controller + Spiele) sind OK, solange die KONSOLE dabei ist.

ACHTUNG FALLE: 
- "PS4 mit 5 Spielen" -> NEIN (ist eine PS4)
- "PS5 Verpackung" -> NEIN (nur Karton)
- "Controller für PS5" -> NEIN

ANZEIGEN:
{titles_text}

Antworte NUR mit einem JSON-Array der Nummern der ECHTEN KONSOLEN, z.B. [1, 3, 5].
Keine Erklärung."""

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
        
        # Mapping zurück auf original Objekte
        final_list = []
        for idx in relevant_indices:
            if 0 < idx <= len(pre_filtered):
                final_list.append(pre_filtered[idx-1])
        
        return final_list
        
    except Exception as e:
        print(f"⚠️ KI-Filter Fehler: {e}")
        return manual_filter(listings)


def manual_filter(listings: list[dict]) -> list[dict]:
    """Fallback-Filter ohne KI."""
    filtered = []
    
    skip_keywords = [
        'suche', 'gesuch', 'controller', 'dualsense', 'headset', 
        'spiel', 'game', 'laufwerk', 'ps4', 'playstation 4',
        'defekt', 'kaputt', 'bastler', 'scuf', 'edge controller'
    ]
    
    for l in listings:
        title_lower = l['title'].lower()
        tags_lower = ' '.join(l['tags']).lower()
        
        # Skip Gesuche
        if l.get('isGesuch') or 'gesuch' in tags_lower:
            continue
            
        # Skip wenn Keywords im Titel
        if any(kw in title_lower for kw in skip_keywords):
            # Aber behalte wenn "playstation 5" oder "ps5" auch im Titel
            if 'playstation 5' in title_lower or 'ps5' in title_lower:
                # Prüfe ob es nur Controller/Zubehör ist
                if 'controller' not in title_lower and 'dualsense' not in title_lower:
                    filtered.append(l)
            continue
        
        filtered.append(l)
    
    return filtered


def fetch_description(page, url: str) -> dict:
    """Holt die Beschreibung von einer Anzeigen-Detailseite."""
    try:
        page.goto(url, wait_until="domcontentloaded")
        random_delay(1.5, 3)
        
        try:
            page.keyboard.press("Escape")
            random_delay(0.3, 0.6)
        except Exception:
            pass
        
        details = page.evaluate("""
            () => {
                const description = document.querySelector('#viewad-description-text')?.innerText?.trim() || null;
                const sellerName = document.querySelector('#viewad-contact .text-body-regular-strong')?.innerText?.trim() || 'Privat';
                
                const detailItems = {};
                document.querySelectorAll('.addetails-list--item').forEach(li => {
                    const text = li.innerText.split('\\n').map(s => s.trim()).filter(Boolean);
                    if (text.length >= 2) {
                        detailItems[text[0]] = text[1];
                    }
                });
                
                return {
                    description: description,
                    seller_name: sellerName,
                    details: detailItems
                };
            }
        """)
        
        return details
        
    except Exception as e:
        print(f"⚠️ Fehler beim Laden der Details: {e}")
        return {"description": None, "seller_name": None, "details": {}}


def scrape_listings(base_url: str, num_pages: int = 5, use_ai_filter: bool = True) -> list[dict]:
    """
    Scraped PS5-Listings von mehreren Seiten mit KI-basierter Vorfilterung.
    
    Args:
        base_url: Basis-URL für die Suche (ohne Seiten-Parameter)
        num_pages: Anzahl der Seiten die gescraped werden sollen (default: 5)
        use_ai_filter: Ob der KI-Filter verwendet werden soll
    """
    print(f"🚀 Starte Camoufox Browser...")
    print(f"📄 Scrape {num_pages} Seiten...")
    
    # Pfade für Auth/Device
    base_dir = os.path.dirname(os.path.abspath(__file__))
    auth_file = os.path.join(base_dir, "auth.json")
    device_file = os.path.join(base_dir, "device.json")
    
    all_listings = []
    
    # User Agent laden
    user_agent = None
    if os.path.exists(device_file):
        try:
            with open(device_file, 'r') as f:
                user_agent = json.load(f).get('user_agent')
        except: pass
        
    print("🚀 Initialisiere Camoufox Browser...", flush=True)
    # Headless Config: Standard False (lokal), aber True via Env (Docker/Server)
    headless_mode = os.getenv("HEADLESS", "false").lower() == "true"
    print(f"🖥️ Headless Mode: {headless_mode}", flush=True)

    with Camoufox(headless=headless_mode) as browser:
        
        # 1. IMMER leeren Context erstellen (stabil)
        context = browser.new_context(user_agent=user_agent) if user_agent else browser.new_context()
        
        # 2. Cookies manuell injizieren
        if os.path.exists(auth_file):
            print("   🍪 Lade Cookies für Scraper...", flush=True)
            try:
                with open(auth_file, 'r') as f:
                    data = json.load(f)
                cookies = data.get('cookies', []) if isinstance(data, dict) else data
                if cookies:
                    print(f"   💉 Injiziere {len(cookies)} Cookies...", flush=True)
                    context.add_cookies(cookies)
            except Exception as e:
                print(f"   ⚠️ Cookies defekt ({e}), fahre fort.", flush=True)
        
        page = context.new_page()
        
        # UA speichern falls neu
        if not user_agent:
            try:
                ua = page.evaluate("navigator.userAgent")
                with open(device_file, 'w') as f: json.dump({"user_agent": ua}, f)
            except: pass
        
        for page_num in range(1, num_pages + 1):
            # URL für aktuelle Seite bauen
            if page_num == 1:
                url = base_url
            else:
                # Kleinanzeigen Pagination: /seite:X/ einfügen
                parts = base_url.split("/playstation-5/")
                url = f"{parts[0]}/seite:{page_num}/playstation-5/{parts[1]}" if len(parts) > 1 else f"{base_url}&page={page_num}"
            
            print(f"\n📄 Seite {page_num}/{num_pages}: {url}")
            page.goto(url, wait_until="domcontentloaded")
            random_delay(2, 4)
            
            # Neue Overlay/Banner Logik
            dismiss_overlays(page)
            
            try:
                page.keyboard.press("Escape")
                random_delay(0.5, 1)
            except Exception:
                pass
            
            page.mouse.wheel(0, 500)
            random_delay(1, 2)
            
            # Listings von dieser Seite extrahieren
            raw_listings = page.evaluate("""
                () => {
                    const listings = Array.from(document.querySelectorAll('article.aditem'));
                    return listings.map(ad => {
                        const titleEl = ad.querySelector('h2.text-module-begin .ellipsis') || ad.querySelector('h2 a');
                        const link = ad.querySelector('h2 a')?.getAttribute('href') || null;
                        const priceEl = ad.querySelector('.aditem-main--middle--price-shipping--price');
                        const locationEl = ad.querySelector('.aditem-main--top--left');
                        const dateEl = ad.querySelector('.aditem-main--top--right');
                        
                        // Kurze Beschreibung/Snippet von der Suchergebnis-Seite
                        const snippetEl = ad.querySelector('.aditem-main--middle--description');
                        
                        const tags = Array.from(ad.querySelectorAll('.aditem-main--bottom .simpletag'))
                            .map(s => s.textContent.trim())
                            .filter(t => t.length > 0);
                        
                        const isVersand = tags.some(t => t.toLowerCase().includes('versand'));
                        const isGesuch = tags.some(t => t.toLowerCase().includes('gesuch'));
                        const adId = ad.getAttribute('data-adid');
                        
                        return {
                            id: adId,
                            title: titleEl ? titleEl.textContent.trim() : null,
                            price: priceEl ? priceEl.textContent.trim() : null,
                            link: link ? (link.startsWith('http') ? link : 'https://www.kleinanzeigen.de' + link) : null,
                            location: locationEl ? locationEl.textContent.trim() : null,
                            date: dateEl ? dateEl.textContent.trim() : null,
                            tags: tags,
                            isVersand: isVersand,
                            isGesuch: isGesuch,
                            snippet: snippetEl ? snippetEl.textContent.trim() : null
                        };
                    });
                }
            """)
            
            # Nur gültige Listings hinzufügen
            valid_listings = [l for l in raw_listings if l.get('title') and l.get('link')]
            
            # Duplikate vermeiden (anhand der ID)
            existing_ids = {l['id'] for l in all_listings}
            
            # DB CHECK: Wurde diese ID schonmal gescraped oder angeschrieben?
            db_known_ids = set()
            if supabase:
                try:
                    # Check listings table
                    res = supabase.table("listings").select("id").in_("id", [l['id'] for l in valid_listings]).execute()
                    db_known_ids.update({item['id'] for item in res.data})
                    
                    # Check sent_messages table (listing_id)
                    res2 = supabase.table("sent_messages").select("listing_id").in_("listing_id", [l['id'] for l in valid_listings]).execute()
                    db_known_ids.update({item['listing_id'] for item in res2.data})
                    
                    if len(db_known_ids) > 0:
                        print(f"   🛡️ Ignoriere {len(db_known_ids)} bereits bekannte Anzeigen aus DB.")
                except Exception as e:
                    print(f"   ⚠️ DB Check Warning: {e}")



            new_listings = [
                l for l in valid_listings 
                if l['id'] not in existing_ids 
                and l['id'] not in db_known_ids
                and l['id'] not in db_known_ids
            ]
            
            all_listings.extend(new_listings)
            print(f"   ✅ {len(new_listings)} neue Listings (Gesamt: {len(all_listings)})")
            
            # Kurze Pause zwischen Seiten
            if page_num < num_pages:
                random_delay(1.5, 3)
        
        print(f"\n📋 Insgesamt {len(all_listings)} Listings von {num_pages} Seiten gefunden")
        
        # ... (KI Filter logic follows) ...
        
        # KI-Filter anwenden
        if use_ai_filter:
            filtered_listings = filter_titles_with_ai(all_listings)
        else:
            filtered_listings = manual_filter(all_listings)
        
        if not filtered_listings:
            print("❌ Keine relevanten Anzeigen nach Filterung!")
            return []
        
        # Beschreibungen nur für gefilterte Listings holen
        print(f"\n📖 Hole Beschreibungen von {len(filtered_listings)} relevanten Anzeigen...")
        
        for i, listing in enumerate(filtered_listings):
            print(f"   [{i+1}/{len(filtered_listings)}] {listing['title'][:40]}...")
            
            details = fetch_description(page, listing['link'])
            listing['description'] = details.get('description')
            listing['seller_name'] = details.get('seller_name')
            listing['extra_details'] = details.get('details', {})
            
            if i < len(filtered_listings) - 1:
                random_delay(1, 2)
        
        print("✅ Alle Beschreibungen geladen!")
        
    return filtered_listings


def filter_with_description(listings: list[dict]) -> list[dict]:
    """
    Zweiter Filter: Prüft mit voller Beschreibung ob es wirklich eine PS5-Konsole ist.
    Filtert False Positives vom ersten Durchgang raus.
    """
    if not listings:
        return []
    
    print(f"\n🔍 Zweiter Filter: Prüfe {len(listings)} Listings mit voller Beschreibung...")
    
    client = Groq(api_key=GROQ_API_KEY)
    confirmed = []
    
    for listing in listings:
        title = listing['title']
        desc = listing.get('description', '') or listing.get('snippet', '')
        price = listing['price']
        
        prompt = f"""Ist das ein Verkauf einer PS5-KONSOLE?

TITEL: {title}
PREIS: {price}
BESCHREIBUNG: {desc[:500]}

Antworte NUR mit: JA oder NEIN
- JA = Es wird eine PS5-Konsole verkauft (auch wenn defekt)
- NEIN = Es ist KEIN Konsolen-Verkauf (nur Zubehör, nur Controller, Gesuch, etc.)"""

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
                confirmed.append(listing)
                
        except Exception as e:
            print(f"   ⚠️ Fehler bei {title[:30]}: {e}")
            # Im Zweifel behalten
            confirmed.append(listing)
    
    print(f"\n✅ {len(confirmed)} echte PS5-Konsolen bestätigt!")
    return confirmed


def generate_message(listing: dict) -> str:
    """
    Generiert eine einfache Kaufanfrage für ein Listing.
    Fragt nach Verfügbarkeit und Zahlungsmöglichkeiten.
    """
    title = listing['title']
    
    # Einfache, standardisierte Nachricht
    message = f"""Hallo,

ich bin interessiert an deiner PS5. Ist sie noch verfügbar?

Könntest du mir sagen, ob eine Zahlung über PayPal (Käuferschutz) oder das Kleinanzeigen Bezahlsystem möglich wäre?

Danke und Grüße!"""
    
    return message


def detect_category(listing: dict) -> str:
    """
    Detects the category of a listing based on title and description.
    Returns: 'normal', 'abholung', or 'defekt'
    """
    title_lower = listing.get('title', '').lower()
    desc_lower = listing.get('description', '').lower()
    combined = title_lower + ' ' + desc_lower
    
    # Defekt keywords
    defekt_keywords = ['defekt', 'kaputt', 'bastler', 'reparatur', 'nicht funktioniert', 
                       'geht nicht', 'funktioniert nicht', 'defective', 'broken', 'für bastler']
    if any(kw in combined for kw in defekt_keywords):
        return 'defekt'
    
    # Abholung only keywords
    abholung_keywords = ['nur abholung', 'keine versand', 'kein versand', 'selbstabholung', 
                         'nur selbstabholung', 'abholung bevorzugt', 'nur bar', 'nur barzahlung']
    if any(kw in combined for kw in abholung_keywords):
        return 'abholung'
    
    # Check if listing explicitly has no shipping
    if not listing.get('isVersand', True):  # Default to True if not specified
        return 'abholung'
    
    return 'normal'


def categorize_listings(listings: list[dict]) -> list[dict]:
    """
    Adds category to all listings. Does NOT filter them out.
    Categories: 'normal', 'abholung', 'defekt'
    """
    for l in listings:
        l['category'] = detect_category(l)
        
        if l['category'] == 'defekt':
            print(f"   ⚠️ Defekt erkannt: {l['title'][:40]}...")
        elif l['category'] == 'abholung':
            print(f"   🚗 Nur Abholung: {l['title'][:40]}...")
    
    return listings





def main():
    url = "https://www.kleinanzeigen.de/s-preis:150:260/playstation-5/k0"
    
    # Schritt 1: Scrapen von 5 Seiten mit grobem KI-Filter
    listings = scrape_listings(url, num_pages=5, use_ai_filter=True)
    
    if not listings:
        print("\n⚠️ Keine relevanten PS5-Konsolen gefunden!")
        return
    
    # Schritt 2: Zweiter Filter mit voller Beschreibung
    confirmed_listings = filter_with_description(listings)
    
    if not confirmed_listings:
        print("\n⚠️ Nach zweitem Filter keine PS5-Konsolen übrig!")
        return
    
    # Schritt 3: Kategorien erkennen (normal, abholung, defekt)
    print("\n📦 Erkenne Kategorien (Normal/Abholung/Defekt)...")
    categorized = categorize_listings(confirmed_listings)
    
    # Zählen
    normal_count = len([l for l in categorized if l['category'] == 'normal'])
    abholung_count = len([l for l in categorized if l['category'] == 'abholung'])
    defekt_count = len([l for l in categorized if l['category'] == 'defekt'])
    
    print(f"\n📊 Kategorien: {normal_count} Normal | {abholung_count} Abholung | {defekt_count} Defekt")
    
    # Schritt 4: Nachrichten nur für normale Listings generieren
    print("\n" + "="*60)
    print("📧 GENERIERE NACHRICHTEN (nur Normal-Kategorie)")
    print("="*60)
    
    normal_listings = [l for l in categorized if l['category'] == 'normal']
    
    for listing in normal_listings:
        print(f"\n📌 {listing['title']}")
        print(f"   💰 {listing['price']} | 📍 {listing['location']}")
        
        message = generate_message(listing)
        listing['generated_message'] = message
    
    # Zusammenfassung
    print("\n" + "="*60)
    print("📊 ZUSAMMENFASSUNG")
    print("="*60)
    print(f"📦 {len(categorized)} Gesamt | ✅ {normal_count} Normal | 🚗 {abholung_count} Abholung | ⚠️ {defekt_count} Defekt")
    
    # SAVE ALL to Supabase (with category)
    if supabase and categorized:
        print(f"\n💾 Sende {len(categorized)} Listings an Supabase 'listings'...")
        for l in categorized:
            try:
                data = {
                    "id": l['id'],
                    "title": l['title'],
                    "price": l['price'],
                    "link": l['link'],
                    "location": l.get('location'),
                    "category": l['category'],  # NEW: Save category
                    "created_at": datetime.now().isoformat(),
                    "data": l
                }
                supabase.table("listings").upsert(data).execute()
            except Exception as e:
                print(f"   ⚠️ DB Insert Error ({l['id']}): {e}")

    print("\n🚀 Nächster Schritt: Nachrichten über Kleinanzeigen senden")


if __name__ == "__main__":
    main()
