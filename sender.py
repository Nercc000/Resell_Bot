"""
Kleinanzeigen Nachrichten-Sender
Liest ready_to_send.json und sendet Nachrichten über Camoufox.
"""

import json
import os
import time
import random
from pathlib import Path
from dotenv import load_dotenv
from camoufox.sync_api import Camoufox
from playwright.sync_api import sync_playwright # Fallback
from supabase import create_client, Client
from datetime import datetime

# .env laden
load_dotenv()

EMAIL = os.getenv("KLEINANZEIGEN_EMAIL")
PASSWORD = os.getenv("KLEINANZEIGEN_PASSWORD")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
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
    
    # Dann Rest (Security Modal, Login Overlay, etc.)
    try:
        page.evaluate("""
            () => {
                // 1. Security/Fraud Warning Modal ("Schütze dich vor Betrug")
                // Der X-Button hat meist die Klasse .mfp-close oder ist ein button mit aria-label
                const securityModalClose = document.querySelector('.mfp-close, button[aria-label="Schließen"], .modal-dialog button.close, [class*="modal"] button[class*="close"]');
                if (securityModalClose) securityModalClose.click();
                
                // 2. Login Overlay
                const loginOverlay = document.querySelector('.login-overlay--content .overlay-close');
                if (loginOverlay) loginOverlay.click();

                // 3. Allgemeine Modals/Overlays
                const closeButtons = document.querySelectorAll('.modal-close, .close-button, [aria-label="Schließen"], .overlay-close, .mfp-close');
                closeButtons.forEach(btn => btn.click());
                
                // 4. Backdrop wegklicken (falls vorhanden)
                const backdrop = document.querySelector('.modal-backdrop, .mfp-bg');
                if (backdrop) backdrop.click();
            }
        """)
    except Exception:
        pass


def load_listings(filename: str = "ready_to_send.json") -> list[dict]:
    """Lädt die zu sendenden Listings - bevorzugt aus Supabase, Fallback auf JSON."""
    
    # 1. Versuche Supabase
    if supabase:
        try:
            print("   📡 Lade Listings aus Supabase...", flush=True)
            response = supabase.table("listings").select("*").execute()
            if response.data:
                listings = []
                for row in response.data:
                    # Kombiniere Hauptdaten mit 'data' JSONB Feld
                    listing = {
                        "id": row.get("id"),
                        "title": row.get("title"),
                        "price": row.get("price"),
                        "link": row.get("link"),
                        "location": row.get("location"),
                        "category": row.get("category", "normal"),  # NEW: Load category
                    }
                    # Extra Daten aus JSONB
                    if row.get("data"):
                        listing.update(row["data"])
                    listings.append(listing)
                print(f"   ✅ {len(listings)} Listings aus DB geladen.", flush=True)
                return listings
        except Exception as e:
            print(f"   ⚠️ Supabase Fehler: {e}", flush=True)
            return []
    
    return []


def login_kleinanzeigen(page) -> bool:
    """Loggt sich bei Kleinanzeigen ein."""
    print("🔐 Login bei Kleinanzeigen...", flush=True)
    
    try:
        print("   🌍 Lade Login-Seite...", flush=True)
        page.goto("https://www.kleinanzeigen.de/m-einloggen.html", wait_until="domcontentloaded")
        random_delay(2, 4)
        
        # Overlays schließen
        print("   🧹 Schließe Overlays...", flush=True)
        dismiss_overlays(page)
        random_delay(1, 2)
        
        # Email eingeben
        email_field = page.locator("#login-email")
        if email_field.count() == 0:
            print("   ❌ Email-Feld nicht gefunden!", flush=True)
            page.screenshot(path="debug_login_no_email.png")
            return False
        
        print("   ⌨️ Gebe Email ein...", flush=True)
        email_field.click()
        random_delay(0.5, 1)
        email_field.fill(EMAIL)
        random_delay(0.5, 1)
        
        # Passwort eingeben
        password_field = page.locator("#login-password")
        if password_field.count() == 0:
            print("   ❌ Passwort-Feld nicht gefunden!", flush=True)
            return False
        
        print("   ⌨️ Gebe Passwort ein...", flush=True)
        password_field.click()
        random_delay(0.5, 1)
        password_field.fill(PASSWORD)
        random_delay(0.5, 1)
        
        # Login Button
        login_btn = page.locator("#login-submit")
        print("   🖱️ Klicke Login...", flush=True)
        login_btn.click()
        
        print("   ⏳ Warte auf Login (Seite lädt)...", flush=True)
        # Besserer Wait: Warte auf Navigation oder Fehler
        try:
            # Warte bis URL NICHT mehr 'm-einloggen' enthält
            page.wait_for_url(lambda url: "einloggen" not in url.lower(), timeout=15000)
        except:
            print("   ⚠️ Timeout beim Warten auf URL-Änderung.", flush=True)
        
        random_delay(2, 3)
        
        # Prüfe ob Login erfolgreich (URL Check ist nicht genug!)
        # Wir warten explizit auf ein Element, das nur eingeloggte User sehen
        try:
             # Warte auf verifizierte Selektoren (a#user-logout, a#site-mainnav-my-link, span.user-profile-badge)
             login_selector = "a#user-logout, a#site-mainnav-my-link, span.user-profile-badge"
             page.wait_for_selector(login_selector, timeout=20000)
             print("   ✅ Login bestätigt (Logout/Meins/Avatar gefunden).", flush=True)
             return True
        except:
             print("   ❌ Login fehlgeschlagen! (Kein User-Element nach Login gefunden)", flush=True)
             # Ist vielleicht ein Captcha da?
             if "captcha" in page.content().lower() or "challenge" in page.url.lower():
                  print("   ⚠️ ACHTUNG: CAPTCHA erkannt!", flush=True)
             
             # Screenshot machen
             page.screenshot(path="debug_login_fail.png")
             return False
            
    except Exception as e:
        print(f"   ❌ Login Exception: {e}", flush=True)
        try: page.screenshot(path="debug_login_exception.png")
        except: pass
        return False



def load_message_templates() -> list[str]:
    """Lädt aktive Nachrichten-Vorlagen aus Supabase."""
    if not supabase:
        return []
    try:
        response = supabase.table("message_templates").select("content").eq("is_active", True).execute()
        if response.data:
            templates = [row['content'] for row in response.data]
            print(f"   📋 {len(templates)} Nachrichten-Vorlagen geladen.", flush=True)
            return templates
    except Exception as e:
        print(f"   ⚠️ Fehler beim Laden der Vorlagen: {e}", flush=True)
    return []

# Globale Vorlagen (werden in send_all_messages geladen)
MESSAGE_TEMPLATES = []

def send_message(page, listing: dict) -> bool:
    """Sendet eine Nachricht an einen Verkäufer. (V2 - Robuste Selektoren)"""
    title = listing['title']
    link = listing['link']
    
    # Template Rotation
    if MESSAGE_TEMPLATES:
        message = random.choice(MESSAGE_TEMPLATES)
    else:
        message = listing.get('generated_message', 'Hallo, ist Versand und PayPal möglich?')
    
    if not message:
        print(f"   ⚠️ Keine Nachricht für: {title}", flush=True)
        return False
    
    print(f"📨 {title[:45]}... (Template: '{message[:30]}...')", flush=True)
    
    try:
        # 1. Zur Anzeige navigieren
        page.goto(link, wait_until="domcontentloaded")
        random_delay(2, 4)
        dismiss_overlays(page)
        
        # 2. CHECK: Ist die Anzeige gelöscht/reserviert?
        # WICHTIG: `:not(.is-hidden)` filtert nur sichtbare Status-Badges!
        status_badge = page.locator("span.pvap-reserved-title:not(.is-hidden)")
        if status_badge.count() > 0:
            badge_text = status_badge.first.inner_text().strip().lower()
            if "gelöscht" in badge_text or "deleted" in badge_text:
                print(f"   ⏩ GELÖSCHT (Badge: '{badge_text}')", flush=True)
                listing['deleted'] = True
                return False
            elif "reserviert" in badge_text:
                print(f"   ℹ️ RESERVIERT - Sende trotzdem...", flush=True)
        
        # 3. "Nachricht schreiben" Button finden und klicken
        msg_button = page.locator("button:has-text('Nachricht schreiben')")
        if msg_button.count() == 0:
            # Fallback auf Link-Variante
            msg_button = page.locator("a:has-text('Nachricht schreiben')")
        
        if msg_button.count() == 0 or not msg_button.first.is_visible():
            print("   ⚠️ Kein 'Nachricht schreiben' Button gefunden.", flush=True)
            page.screenshot(path=f"debug_no_msg_btn_{listing.get('id', 'unknown')}.png")
            return False
        
        msg_button.first.click()
        random_delay(1.5, 2.5)
        
        # 4. Warte auf Modal-Textarea
        textarea = page.locator("#message-textarea-input")
        try:
            textarea.wait_for(state="visible", timeout=5000)
        except:
            print("   ⚠️ Message Modal/Textarea nicht gefunden.", flush=True)
            page.screenshot(path=f"debug_no_textarea_{listing.get('id', 'unknown')}.png")
            return False
        
        # 5. Nachricht eingeben
        textarea.fill(message)
        random_delay(0.5, 1)
        
        # 6. Senden-Button klicken
        send_btn = page.locator("#message-submit-button")
        if send_btn.count() == 0 or not send_btn.is_visible():
            # Fallback
            send_btn = page.locator("button[type='submit']:has-text('Senden')")
        
        if send_btn.count() == 0:
            print("   ⚠️ Kein Senden-Button gefunden.", flush=True)
            return False
        
        send_btn.first.click()
        print("   ⏳ Senden geklickt...", flush=True)
        
        # 7. Verifizieren (optional, aber hilfreich)
        random_delay(2, 3)
        # Kleinanzeigen zeigt oft eine Erfolgsmeldung oder leitet um
        # Wir nehmen an, dass es geklappt hat, wenn kein Fehler kam
        print(f"   ✅ Nachricht gesendet!", flush=True)
        return True

    except Exception as e:
        print(f"   ❌ Fehler: {e}", flush=True)
        return False


def send_all_messages(listings: list[dict]) -> dict:
    """Sendet Nachrichten an alle Listings."""
    # Templates laden
    global MESSAGE_TEMPLATES
    MESSAGE_TEMPLATES = load_message_templates()
    
    if not listings:
        print("❌ Keine Listings zum Senden!")
        return {"sent": 0, "failed": 0, "skipped": 0}
    
    # 1. PRÜFE ERST, OB LISTINGS SCHON GESENDET WURDEN (Supabase)
    print(f"\n🔍 Prüfe {len(listings)} Listings auf bereits gesendete Nachrichten...")
    
    skipped = 0
    listings_to_send = []
    
    try:
        # Hole nur ERFOLGREICH gesendete listing_ids (nicht failed!)
        response = supabase.table("sent_messages").select("listing_id").eq("status", "sent").execute()
        sent_ids = {row['listing_id'] for row in response.data} if response.data else set()
        print(f"   📊 {len(sent_ids)} Nachrichten erfolgreich gesendet in DB.")
        
        for listing in listings:
            listing_id = listing.get('id')
            category = listing.get('category', 'normal')
            
            # Skip already sent
            if listing_id in sent_ids:
                print(f"   ⏩ Überspringe '{listing.get('title', 'Unbekannt')[:30]}...' (bereits gesendet)")
                skipped += 1
            # Skip non-normal categories
            elif category in ('abholung', 'defekt'):
                print(f"   ⏩ Überspringe '{listing.get('title', 'Unbekannt')[:30]}...' (Kategorie: {category})")
                skipped += 1
            else:
                listings_to_send.append(listing)
        
        print(f"   → {len(listings_to_send)} neu zu senden, {skipped} übersprungen.\n")
        
    except Exception as e:
        print(f"   ⚠️ DB-Check fehlgeschlagen ({e}), sende alle.")
        listings_to_send = listings
    
    if not listings_to_send:
        print("✅ Alle Nachrichten wurden bereits gesendet!")
        return {"sent": 0, "failed": 0, "skipped": skipped}
    
    print(f"🚀 Starte Camoufox Browser...")
    print(f"📬 {len(listings_to_send)} Nachrichten zu senden\n")
    
    sent = 0
    failed = 0
    
    # Speicherort für Cookies/Login (Absolut)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    auth_file = os.path.join(base_dir, "auth.json")
    
    print(f"🚀 Starte Camoufox Browser...", flush=True)
    print(f"🍪 Auth-File Pfad: {auth_file}", flush=True)
    
    # Konfiguration für Camoufox
    print("🚀 Initialisiere Camoufox Browser...", flush=True)
    
    # Headless Config: Standard False (lokal), aber True via Env (Docker/Server)
    headless_mode = os.getenv("HEADLESS", "false").lower() == "true"
    print(f"🖥️ Headless Mode: {headless_mode}", flush=True)
    
    with Camoufox(headless=headless_mode) as browser:
        print("✅ Browser gestartet.", flush=True)
        
        # Context konfigurieren - WICHTIG: Erst leeren Context, dann Cookies injizieren!
        # (storage_state im Konstruktor verursacht "Doppel-Fenster" bei Problemen)
        device_file = os.path.join(base_dir, "device.json")
        user_agent = None
        
        # Versuche gespeicherten User-Agent zu laden
        if os.path.exists(device_file):
            try:
                with open(device_file, 'r') as f:
                    device_data = json.load(f)
                    user_agent = device_data.get('user_agent')
                    print(f"📱 Nutze gespeicherten User-Agent: {user_agent[:30]}...", flush=True)
            except: pass

        # 1. IMMER leeren Context erstellen (stabil, kein Fenster-Flicker)
        context = browser.new_context(user_agent=user_agent) if user_agent else browser.new_context()
        page = context.new_page()
        
        # 2. Cookies manuell injizieren (sicher, kein Crash bei defekten Cookies)
        if os.path.exists(auth_file):
            print(f"🍪 Auth-Datei gefunden ({os.path.getsize(auth_file)} bytes)...", flush=True)
            try:
                with open(auth_file, 'r') as f:
                    data = json.load(f)
                cookies = data.get('cookies', []) if isinstance(data, dict) else data
                if cookies:
                    print(f"   💉 Injiziere {len(cookies)} Cookies...", flush=True)
                    context.add_cookies(cookies)
                    print("   ✅ Cookies gesetzt!", flush=True)
                else:
                    print("   ⚠️ Keine Cookies im JSON.", flush=True)
            except Exception as e:
                print(f"   ❌ Cookie-Fehler: {e} (Fenster bleibt offen!)", flush=True)
        else:
            print("🆕 Keine Auth-Datei vorhanden.", flush=True)
        
        # Falls wir noch keinen gespeicherten UA haben, jetzt speichern
        if not user_agent:
            current_ua = page.evaluate("navigator.userAgent")
            try:
                with open(device_file, 'w') as f:
                    json.dump({"user_agent": current_ua}, f)
                print(f"📱 Neuer User-Agent gespeichert: {current_ua[:30]}...", flush=True)
            except: pass

        # 0. Cookie Banner & Login Check
        print("🌍 Öffne Kleinanzeigen für Session-Check...", flush=True)
        try:
            page.goto("https://www.kleinanzeigen.de", wait_until="domcontentloaded")
            random_delay(2, 3)
            dismiss_overlays(page)
        except Exception:
            pass
        
        # Check ob eingeloggt - MEHRERE METHODEN
        # 1. Text "angemeldet als" (sichtbar im Header wenn eingeloggt)
        # 2. Logout-Link: a#user-logout
        # 3. Meins-Link: a#site-mainnav-my-link  
        # 4. Avatar: span.user-profile-badge
        is_logged_in = False
        
        # Methode 1: Text "angemeldet als" (funktioniert immer!)
        if "angemeldet als" in page.content().lower():
            print("✅ BEREITS EINGELOGGT! ('angemeldet als' im HTML gefunden)", flush=True)
            is_logged_in = True
        else:
            # Methode 2: Selektoren prüfen
            login_selector = "a#user-logout, a#site-mainnav-my-link, span.user-profile-badge"
            if page.locator(login_selector).first.count() > 0:
                print("✅ Logout/Meins/Avatar gefunden -> Bereits eingeloggt.", flush=True)
                is_logged_in = True
            else:
                print("ℹ️ Nicht eingeloggt.", flush=True)
                is_logged_in = False

        if not is_logged_in:
             print("🚀 Starte Login-Prozess...", flush=True)
             if login_kleinanzeigen(page):
                 print("✅ Login erfolgreich durchgelaufen. Speichere Cookies...", flush=True)
                 
                 # Cookies speichern
                 context.storage_state(path=auth_file)
                 
                 # User Agent auch update/sichern
                 current_ua = page.evaluate("navigator.userAgent")
                 with open(device_file, 'w') as f:
                     json.dump({"user_agent": current_ua}, f)
                     
                 is_logged_in = True
             else:
                 print("❌ Login fehlgeschlagen! Bot kann nicht senden.", flush=True)
                 return {"sent": 0, "failed": len(listings_to_send), "skipped": skipped}
        
        if is_logged_in:
            try: context.storage_state(path=auth_file)
            except: pass

        # Nachrichten senden (nur die gefilterten!)
        for i, listing in enumerate(listings_to_send):
            print(f"\n[{i+1}/{len(listings_to_send)}]", end=" ", flush=True)
            
            success = send_message(page, listing)
            
            if success:
                sent += 1
                listing['sent'] = True
                # Update Supabase: message_sent = true
                if supabase:
                    try:
                        supabase.table("listings").update({"message_sent": True}).eq("id", listing.get("id")).execute()
                    except: pass
            else:
                failed += 1
                listing['sent'] = False
                # Wenn gelöscht, auch in Supabase markieren
                if listing.get('deleted') and supabase:
                    try:
                        supabase.table("listings").update({"deleted": True}).eq("id", listing.get("id")).execute()
                    except: pass
            
            # Pause zwischen Nachrichten (Anti-Bot-Schutz)
            
        return {"sent": sent, "failed": failed, "skipped": skipped, "listings": listings_to_send}


def test_login_process() -> bool:
    """Nur Einloggen und Cookies testen/speichern."""
    print("🚀 Starte Login-Test...", flush=True)
    
    # Pfade
    base_dir = os.path.dirname(os.path.abspath(__file__))
    auth_file = os.path.join(base_dir, "auth.json")
    device_file = os.path.join(base_dir, "device.json")
    
    print(f"📁 Auth-File: {auth_file}")
    
    # Camoufox Start
    with Camoufox(headless=False) as browser:
        print("✅ Browser gestartet.", flush=True)
        
        # User-Agent laden
        user_agent = None
        if os.path.exists(device_file):
            try:
                with open(device_file, 'r') as f:
                    user_agent = json.load(f).get('user_agent')
            except: pass
            
        # 1. IMMER leeren Context erstellen (stabil, kein Fenster-Flicker)
        context = browser.new_context(user_agent=user_agent) if user_agent else browser.new_context()
        page = context.new_page()
        
        # 2. Cookies manuell injizieren
        if os.path.exists(auth_file):
            print("   🍪 Lade Cookies...", flush=True)
            try:
                with open(auth_file, 'r') as f:
                    data = json.load(f)
                cookies = data.get('cookies', []) if isinstance(data, dict) else data
                if cookies:
                    print(f"   💉 Injiziere {len(cookies)} Cookies...", flush=True)
                    context.add_cookies(cookies)
            except Exception as e:
                print(f"   ⚠️ Cookies defekt ({e}), fahre fort.", flush=True)
        else:
            print("   🆕 Keine Cookies.", flush=True)
        
        # UA speichern falls neu
        if not user_agent:
            try:
                ua = page.evaluate("navigator.userAgent")
                with open(device_file, 'w') as f: json.dump({"user_agent": ua}, f)
            except: pass

        # Seite öffnen
        print("   🌍 Gehe zu Kleinanzeigen...", flush=True)
        page.goto("https://www.kleinanzeigen.de", wait_until="domcontentloaded")
        random_delay(2, 3)
        
        dismiss_overlays(page)
        
        # Check Login - MEHRERE METHODEN
        is_logged_in = False
        
        # Methode 1: Text "angemeldet als"
        if "angemeldet als" in page.content().lower():
            print("   ✅ BEREITS EINGELOGGT! ('angemeldet als' gefunden)", flush=True)
            is_logged_in = True
        else:
            # Methode 2: Selektoren
            login_selector = "a#user-logout, a#site-mainnav-my-link, span.user-profile-badge"
            if page.locator(login_selector).first.count() > 0:
                print("   ✅ BEREITS EINGELOGGT! (Logout/Meins/Avatar gefunden)", flush=True)
                is_logged_in = True
            else:
                print("   ℹ️ Nicht eingeloggt.", flush=True)
             
        if not is_logged_in:
            print("   🔐 Starte Login...", flush=True)
            if login_kleinanzeigen(page):
                print("   ✅ Login erfolgreich! Speichere Cookies...", flush=True)
                context.storage_state(path=auth_file)
                return True
            else:
                print("   ❌ Login fehlgeschlagen.", flush=True)
                # Screenshot für Debugging
                page.screenshot(path="debug_test_login_fail.png")
                # Kurz warten damit User es sieht
                time.sleep(5)
                return False
        
        print("   💾 Aktualisiere Cookies...", flush=True)
        context.storage_state(path=auth_file)
        
        print("   ⏳ Warte 5s zur Bestätigung...", flush=True)
        time.sleep(5)
        return True



def main():
    print("="*60)
    print("📬 KLEINANZEIGEN NACHRICHTEN-SENDER")
    print("="*60)
    
    import sys
    if "--login-only" in sys.argv:
        print("🔧 MODUS: NUR LOGIN TESTEN")
        test_login_process()
        return

    if not EMAIL or not PASSWORD:
        print("❌ Keine Login-Daten in .env gefunden!")
        return
    
    print(f"📧 Login als: {EMAIL}")
    
    listings = load_listings("ready_to_send.json")
    
    if not listings:
        print("❌ Keine Listings gefunden! Erst scraper.py ausführen.")
        return
    
    print(f"📋 {len(listings)} Listings geladen\n")
    
    result = send_all_messages(listings)
    
    print("\n" + "="*60)
    print("📊 ERGEBNIS")
    print("="*60)
    print(f"✅ Gesendet: {result['sent']}")
    print(f"❌ Fehlgeschlagen: {result['failed']}")
    
    # DB Save
    if supabase:
        print(f"💾 Speichere {len(listings)} Ergebnisse in DB 'sent_messages'...")
        for l in listings:
            try:
                data = {
                    "listing_id": l['id'],
                    "status": "sent" if l.get('sent') else "failed",
                    "sent_at": datetime.now().isoformat(),
                    "log": "Sent via Bot" if l.get('sent') else "Failed to send"
                }
                supabase.table("sent_messages").insert(data).execute()
            except Exception as e:
                print(f"   ⚠️ DB Insert Error ({l['id']}): {e}")




if __name__ == "__main__":
    main()
