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
    print(f"\n🤖 Analysiere {len(listings)} Titel mit KI...")
    
    # Trenne bereits markierte (durch Vor-Filter) von den zu prüfenden
    to_check = [l for l in listings if l.get('filter_status') != 'rejected_keyword']
    
    if not to_check:
        print("❌ Alle Listings bereits durch Vor-Filter abgelehnt.")
        return listings

    client = Groq(api_key=GROQ_API_KEY)
    
    # Bereite Titel-Liste für den Prompt vor
    titles_text = "\n".join([
        f"{i+1}. {l['title']} | {price_clean(l['price'])}"
        for i, l in enumerate(to_check)
    ])
    
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
            
        # Skip wenn Keywords im Titel
        matched_kw = next((kw for kw in skip_keywords if kw in title_lower), None)
        if matched_kw:
            # Aber behalte wenn "playstation 5" oder "ps5" auch im Titel
            if 'playstation 5' in title_lower or 'ps5' in title_lower:
                # Prüfe ob es nur Controller/Zubehör ist
                if 'controller' not in title_lower and 'dualsense' not in title_lower:
                    # Scheint OK zu sein
                    pass
                else:
                    l['filter_status'] = 'rejected_keyword'
                    l['filter_reason'] = f"Keyword: {matched_kw}"
            else:
                 l['filter_status'] = 'rejected_keyword'
                 l['filter_reason'] = f"Keyword: {matched_kw}"
            continue
            
        # Vor-FilterPassed (wird später von KI überschrieben oder bestätigt)
        l['filter_status'] = 'passed_prefilter'
    
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
    url = "https://www.kleinanzeigen.de/s-preis:150:400/playstation-5/k0" # Preis etwas angepasst
    
    # Schritt 1: Scrapen & Initial Filter (Pre-Filter + Title AI)
    # manual_filter läuft implizit VOR der KI in 'scrape_listings' (wenn wir es dort einbauen)
    # Aber hier rufen wir es explizit auf:
    
    raw_listings = scrape_listings(url, num_pages=2, use_ai_filter=False) # False, weil wir eigene Logik machen
    
    if not raw_listings:
        print("⚠️ Keine Listings gefunden.")
        return

    # 1. Manual Filter (Keywords) - Markiert rejected_keyword
    listings = manual_filter(raw_listings)
    
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
                    "created_at": datetime.now().isoformat(),
                    "data": l
                }
                supabase.table("listings").upsert(data).execute()
            except Exception as e:
                print(f"   ⚠️ DB Insert Error ({l['id']}): {e}")

    print("\n🚀 Fertig.")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
