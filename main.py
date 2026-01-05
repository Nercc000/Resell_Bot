"""
Kleinanzeigen PS5 Bot - Hauptcontroller
Führt Scraper und Sender nacheinander aus.
"""

import subprocess
import sys
import time
from pathlib import Path


def run_script(script_name: str) -> bool:
    """Führt ein Python-Script aus und zeigt die Ausgabe."""
    print(f"\n{'='*60}")
    print(f"🚀 Starte: {script_name}")
    print("="*60 + "\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=Path(__file__).parent,
            check=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler beim Ausführen von {script_name}: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Script nicht gefunden: {script_name}")
        return False


import argparse

def main():
    parser = argparse.ArgumentParser(description="Kleinanzeigen Bot")
    parser = argparse.ArgumentParser(description="Kleinanzeigen Bot")
    parser.add_argument("--mode", type=str, default="full", choices=["full", "scrape", "send", "login"], help="Modus: full, scrape, send, login")
    args = parser.parse_args()
    
    mode = args.mode
    
    print("="*60)
    print("🎮 KLEINANZEIGEN PS5 BOT")
    print(f"Modus: {mode.upper()}")
    print("="*60)
    
    # Schritt 1: Scraper
    if mode in ["full", "scrape"]:
        print("\n📡 SCHRITT 1: SCRAPING")
        success = run_script("scraper.py")
        if not success:
            print("\n❌ Scraping fehlgeschlagen!")
            return
            
    # Pause nur wenn beides läuft
    if mode == "full":


        print("\n⏳ Kurze Pause vor dem Senden (10 Sekunden)...")
        time.sleep(10)
        
    # Schritt 2: Sender
    if mode in ["full", "send"]:
        print("\n📬 SCHRITT 2: NACHRICHTEN SENDEN")
        success = run_script("sender.py")
        if not success:
            print("\n❌ Senden fehlgeschlagen!")
            return
            
    # Schritt 3: Nur Login Test
    if mode == "login":
        print("\n🔐 NUR LOGIN TEST")
        # Wir rufen sender.py mit dem speziellen Flag auf
        # run_script unterstützt keine Args, also nutzen wir direkt subprocess hier oder passen run_script an?
        # Einfacher: subprocess direkt
        try:
             subprocess.run([sys.executable, "sender.py", "--login-only"], cwd=Path(__file__).parent, check=True)
        except Exception as e:
             print(f"❌ Fehler bei Login-Test: {e}")
    
    print("\n" + "="*60)
    print("✅ BOT FERTIG!")
    print("="*60)

if __name__ == "__main__":
    main()
