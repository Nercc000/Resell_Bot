import json
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Keine Supabase Credentials in .env")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def import_sent():
    if not os.path.exists("sent_messages.json"):
        return
    
    with open("sent_messages.json", "r") as f:
        data = json.load(f)
        listings = data.get("listings", []) if isinstance(data, dict) else data
    
    print(f"📦 Importiere {len(listings)} gesendete Nachrichten...")
    
    count = 0
    for l in listings:
        try:
            # 1. Erst Listing anlegen (FK constraint)
            listing_data = {
                "id": l['id'],
                "title": l.get('title', 'Unknown'),
                "price": l.get('price', ''),
                "link": l.get('link', ''),
                "data": l
            }
            try:
                supabase.table("listings").upsert(listing_data).execute()
            except: pass # Evtl schon da
            
            # 2. Nachricht Eintrag
            msg_data = {
                "listing_id": l['id'],
                "status": "sent" if l.get('sent') else "failed",
                "sent_at": "2024-01-01T00:00:00Z", # Dummy, da wir es nicht wissen
                "log": "Legacy Import"
            }
            supabase.table("sent_messages").upsert(msg_data, on_conflict="listing_id").execute()
            count += 1
        except Exception as e:
            print(f"Fehler bei {l.get('id')}: {e}")
            
    print(f"✅ {count} importiert.")

def import_ready():
    if not os.path.exists("ready_to_send.json"):
        return
        
    with open("ready_to_send.json", "r") as f:
        data = json.load(f)
        listings = data.get("listings", [])
        
    print(f"📦 Importiere {len(listings)} Ready-Listings...")
    
    count = 0
    for l in listings:
        try:
            listing_data = {
                "id": l['id'],
                "title": l['title'],
                "price": l['price'],
                "link": l['link'],
                "data": l
            }
            supabase.table("listings").upsert(listing_data).execute()
            count += 1
        except Exception as e:
            print(f"Fehler Import {l['id']}: {e}")

    print(f"✅ {count} importiert.")

if __name__ == "__main__":
    print("Starte Legacy Import...")
    import_sent()
    import_ready()
    print("Fertig.")
