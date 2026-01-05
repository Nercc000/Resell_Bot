
import os
import re
from dotenv import load_dotenv
from supabase import create_client

# Load vars
load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("❌ Fehler: SUPABASE_URL oder SUPABASE_KEY fehlen in .env")
    exit(1)

supabase = create_client(url, key)

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

def main():
    print("🧹 Starte Datenbank-Bereinigung...")
    
    # 1. Fetch listings
    # Pagination loop might be needed if > 1000, but let's try grabbing a chunk
    response = supabase.table('listings').select('*').execute()
    listings = response.data
    
    print(f"📊 Analysiere {len(listings)} Listings auf Preise...")
    
    ids_to_delete = []
    
    for l in listings:
        p_str = l.get('price', '')
        price = parse_price(p_str)
        
        # LOGIC: Delete if > 320 (Buffer for 300)
        if price > 320:
            print(f"   🗑️ Lösche: {l['title'][:30]}... ({p_str})")
            ids_to_delete.append(l['id'])
            
    if not ids_to_delete:
        print("✅ Keine zu teuren Listings gefunden.")
        return

    print(f"\n🚀 Lösche {len(ids_to_delete)} Einträge...")
    
    # Batch delete
    try:
        supabase.table('listings').delete().in_('id', ids_to_delete).execute()
        print("✅ Erfolgreich gelöscht!")
    except Exception as e:
        print(f"❌ Fehler beim Löschen: {e}")

if __name__ == "__main__":
    main()
