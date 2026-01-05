
import os
import time
import json
import random
from camoufox.sync_api import Camoufox
from dotenv import load_dotenv

# Env laden für Credentials
load_dotenv()
EMAIL = os.getenv("KLEINANZEIGEN_EMAIL")
PASSWORD = os.getenv("KLEINANZEIGEN_PASSWORD")

def random_delay(min_sec=1.0, max_sec=3.0):
    time.sleep(random.uniform(min_sec, max_sec))

def dismiss_overlays(page):
    """Klickt Cookie-Banner und Overlays weg."""
    print("   🍪/🧹 Versuche Overlays zu schließen...", flush=True)
    try:
        # 1. Cookie Banner (Shadow DOM & Normal)
        page.evaluate("""() => {
            const host = document.querySelector('#usercentrics-root');
            if (host && host.shadowRoot) {
                const btn = host.shadowRoot.querySelector('button[data-testid="uc-accept-all-button"]');
                if (btn) btn.click();
            }
        }""")
        
        # Normaler Button (oft "Alle akzeptieren" oder "Zustimmen")
        page.locator("button:has-text('Alle akzeptieren'), button:has-text('Zustimmen')").first.click(timeout=2000)
    except: pass

    try:
        # 2. Andere Modals
        page.evaluate("""() => {
            const close = document.querySelector('.modal-close, .close-button, .overlay-close');
            if (close) close.click();
        }""")
    except: pass


def login(page):
    print("🔐 Starte Login-Vorgang...", flush=True)
    try:
        page.goto("https://www.kleinanzeigen.de/m-einloggen.html", wait_until="domcontentloaded")
        random_delay(2, 3)
        dismiss_overlays(page)
        
        # Email
        print("   ⌨️ Email...", flush=True)
        page.locator("#login-email").fill(EMAIL)
        random_delay(0.5, 1)
        
        # Password
        print("   ⌨️ Password...", flush=True)
        page.locator("#login-password").fill(PASSWORD)
        random_delay(0.5, 1)
        
        # Button
        print("   🖱️ Login Klick...", flush=True)
        page.locator("#login-submit").click()
        
        # Warten auf Erfolg
        print("   ⏳ Warte auf Weiterleitung...", flush=True)
        page.wait_for_url(lambda url: "einloggen" not in url.lower(), timeout=15000)
        
        # Check
        if page.locator(".user-account-avatar, #user-account-id").count() > 0:
            print("   ✅ LOGIN ERFOLGREICH!", flush=True)
            return True
        else:
            print("   ❌ Login scheint fehlgeschlagen (Kein Avatar).", flush=True)
            return False
            
    except Exception as e:
        print(f"   ❌ Login Fehler: {e}", flush=True)
        return False

def inspect_element(page, selector, name):
    print(f"   🔍 Inspiziere '{name}' ({selector})...", flush=True)
    try:
        loc = page.locator(selector).first
        if loc.count() > 0 and loc.is_visible():
            print(f"      ✅ GEFUNDEN! Text: '{loc.inner_text().strip()[:50]}...'", flush=True)
            print(f"      📄 HTML: {loc.evaluate('el => el.outerHTML')[:200]}...", flush=True)
            return True
        else:
            print(f"      ❌ Nicht sichtbar/gefunden.", flush=True)
            return False
    except Exception as e:
         print(f"      ⚠️ Fehler bei Inspektion: {e}")
         return False

def debug_login_flow():
    print("🛑 START SELECTOR INSPECTION (MIT AUTH & LOGIN)")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    auth_file = os.path.join(base_dir, "auth.json")
    
    print(f"📂 Auth-File: {auth_file}")

    if not EMAIL or not PASSWORD:
        print("❌ FEHLER: Keine Email/Passwort in .env gefunden!")
        return

    print("🚀 Camoufox Init (Manual Cookie Injection)...")
    try:
        with Camoufox(headless=False) as browser:
            print("✅ Browser offen.")
            
            context = browser.new_context(user_agent=None) 
            page = context.new_page()
            
            # Cookies laden versuchen
            if os.path.exists(auth_file):
                 print(f"   🍪 Auth-Datei gefunden ({os.path.getsize(auth_file)} bytes)...", flush=True)
                 try:
                    with open(auth_file, 'r') as f:
                        data = json.load(f)
                    cookies = data.get('cookies', []) if isinstance(data, dict) else data
                    if cookies:
                        print(f"   💉 Injiziere {len(cookies)} Cookies...", flush=True)
                        # Check für wichtige Auth-Cookies
                        auth_cookies = [c for c in cookies if c.get('name') in ['access_token', 'refresh_token', 'CSRF-TOKEN']]
                        print(f"      → Davon wichtige Auth-Cookies: {len(auth_cookies)}", flush=True)
                        context.add_cookies(cookies)
                        print("   ✅ Cookies gesetzt!", flush=True)
                    else:
                        print("   ⚠️ Keine Cookies im JSON gefunden.", flush=True)
                 except Exception as e:
                    print(f"   ❌ Cookie-Fehler: {e}", flush=True)
            else:
                print("   🆕 Keine Auth-Datei vorhanden.", flush=True)

            print("🌍 Öffne Startseite...", flush=True)
            page.goto("https://www.kleinanzeigen.de", wait_until="domcontentloaded")
            random_delay(2, 3)
            
            # 1. INSPEKTION: Cookie Banner
            print("\n🔬 ANALYSE: Cookie Banner")
            # Dump Body start to see if overlay exists
            inspect_element(page, "#usercentrics-root", "Shadow Host")
            inspect_element(page, "button:has-text('Alle akzeptieren')", "Button 'Alle akzeptieren'")
            inspect_element(page, "#gdpr-banner-accept", "GDPR Button ID")
            
            dismiss_overlays(page)
            
            # Check Status - MEHRERE METHODEN (verifiziert!)
            # 1. Text "angemeldet als" (sichtbar im Header wenn eingeloggt)
            # 2. Logout-Link: a#user-logout
            # 3. Meins-Link: a#site-mainnav-my-link
            # 4. Avatar: span.user-profile-badge
            
            is_logged_in = False
            
            # Methode 1: Text "angemeldet als" (funktioniert immer!)
            if "angemeldet als" in page.content().lower():
                print("   ✅ BEREITS EINGELOGGT! ('angemeldet als' im HTML gefunden)", flush=True)
                is_logged_in = True
            else:
                # Methode 2: Selektoren prüfen
                login_selector = "a#user-logout, a#site-mainnav-my-link, span.user-profile-badge"
                if page.locator(login_selector).first.count() > 0:
                    print("   ✅ BEREITS EINGELOGGT! (Logout/Meins/Avatar gefunden)", flush=True)
                    is_logged_in = True
                else:
                    print("   ℹ️ Nicht eingeloggt.", flush=True)
                    is_logged_in = False
            
            if not is_logged_in:
                # Login Seite
                print("\n🔐 Gehe zu Login...", flush=True)
                page.goto("https://www.kleinanzeigen.de/m-einloggen.html", wait_until="domcontentloaded")
                random_delay(2, 3)
                dismiss_overlays(page)
                
                print("\n🔬 Führe Login durch...")
                
                # Email
                print("   ⌨️ Email...", flush=True)
                page.locator("#login-email").fill(EMAIL)
                random_delay(0.5, 1)
                
                # Password
                print("   ⌨️ Password...", flush=True)
                page.locator("#login-password").fill(PASSWORD)
                random_delay(0.5, 1)
                
                # Button
                print("   🖱️ Login Klick...", flush=True)
                page.locator("#login-submit").click()
                
                print("   ⏳ Warte auf Post-Login State...", flush=True)
                
                # WARTE AUF KORREKTEN SELECTOR (verifiziert!)
                try:
                    page.wait_for_selector(login_selector, timeout=15000)
                    print("      ✅ Login-Indikator im Header erschienen!", flush=True)
                    is_logged_in = True
                except:
                    print("      ⚠️ Kein Login-Header innerhalb von 15s erschienen.")
                
                # DEBUG: HTML Dump egal was passiert
                print("   💾 Dume HTML-Source für Analyse...", flush=True)
                with open("debug_source.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                    
                print("   📸 Mache Screenshot...", flush=True)
                page.screenshot(path="debug_state_full.png")
                
                # Check Header Explizit
                try:
                    header_html = page.locator("#site-header, header").first.inner_html()
                    with open("debug_header.html", "w", encoding="utf-8") as f:
                        f.write(header_html)
                except: 
                    print("   ⚠️ Konnte Header nicht isolieren.")

                # Fallback Check
                if not is_logged_in:
                    if "meine-anzeigen" in page.url or "login=success" in page.url:
                        print("      ✅ URL deutet auf Erfolg hin.", flush=True)
                        is_logged_in = True
                
                # cleanup banners
                inspect_element(page, "div:has-text('Willkommen bei Kleinanzeigen')", "Willkommen Modal")
                inspect_element(page, "button:has-text('Alle akzeptieren')", "Post-Login 'Alle akzeptieren'")
                
                dismiss_overlays(page)
                
                # Cookies speichern
                if is_logged_in:
                    print("   💾 LOGIN BESTÄTIGT! Speichere Cookies...", flush=True)
                    current_cookies = context.cookies()
                    with open(auth_file, 'w') as f:
                        json.dump({"cookies": current_cookies, "origins": []}, f, indent=2)
                else:
                    print("   ❌ Login Erkennung fehlgeschlagen (Trotz URL Wechsel?)", flush=True)
                    print("   ℹ️ ANALYSIERE 'debug_source.html' UM DEN FEHLER ZU FINDEN!")

            print("⏳ Warte 10 Sekunden...", flush=True)
            time.sleep(10)
            
            print("🛑 ENDE DEBUG")
            
    except Exception as e:
        print(f"❌ CRASH: {e}")
        print("⏳ Ich lasse das Fenster noch 60s offen zur Diagnose...", flush=True)
        time.sleep(60)

if __name__ == "__main__":
    debug_login_flow()
