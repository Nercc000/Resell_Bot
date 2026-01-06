# 🎮 Kleinanzeigen PS5 Reselling Bot - Vollständige Dokumentation

## 📋 Projektübersicht

Ein automatisierter Bot zum Finden und Kontaktieren von PS5-Verkäufern auf Kleinanzeigen.de.

**Features:**
- 🔍 Automatisches Scraping von PS5-Angeboten
- 🤖 KI-gestützte Filterung (Groq/Llama)
- 📬 Automatischer Nachrichtenversand
- 📊 Dashboard zur Überwachung
- 🔄 Echtzeit-Updates via WebSocket

---

## 🏗️ Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│               resellerbot.de (Vercel)                           │
│                    Next.js Dashboard                             │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTPS API Calls
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                  │
│            45.147.7.54 (Ubuntu VPS)                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Caddy     │───▶│  FastAPI    │───▶│  Scraper    │         │
│  │ (Reverse    │    │  (API)      │    │  + Sender   │         │
│  │  Proxy/SSL) │    │  Port 8000  │    │  (Python)   │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATENBANK                                   │
│                 Supabase (PostgreSQL)                            │
│           listings, messages, templates                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Komponente | Technologie |
|------------|-------------|
| **Frontend** | Next.js 14, React, TypeScript, TailwindCSS, shadcn/ui |
| **Backend API** | FastAPI (Python), Uvicorn |
| **Scraper** | Playwright, Camoufox (Anti-Detection Browser) |
| **KI-Filter** | Groq API (Llama 3.3 70B) |
| **Datenbank** | Supabase (PostgreSQL) |
| **Hosting Frontend** | Vercel |
| **Hosting Backend** | Ubuntu VPS (Docker + Caddy) |
| **SSL/HTTPS** | Caddy (Auto Let's Encrypt) |

---

## 📁 Projektstruktur

```
resell/
├── dashboard/              # Next.js Frontend
│   ├── app/               # App Router Pages
│   ├── components/        # React Components
│   ├── lib/               # Utilities (Supabase, API)
│   └── api/               # FastAPI Backend (!)
│       └── main.py        # API Endpoints
│
├── scraper.py             # Haupt-Scraper Logik
├── sender.py              # Nachrichtenversand
├── main.py                # Bot Orchestrator
├── cleanup_db.py          # DB Wartung
│
├── Dockerfile             # Backend Container
├── docker-compose.yml     # Container Orchestrierung
├── Caddyfile              # Reverse Proxy Config
├── deploy.sh              # Deployment Script
│
├── auth.json              # Kleinanzeigen Session (GEHEIM!)
├── device.json            # Browser Fingerprint
└── .env                   # Environment Variables (GEHEIM!)
```

---

## 🔐 Environment Variables

### Backend (.env)
```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJxxx...
GROQ_API_KEY=gsk_xxx...
```

### Frontend (Vercel Dashboard)
```env
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx...
NEXT_PUBLIC_API_URL=https://45.147.7.54.nip.io  # ⚠️ Aktuell nip.io!
```

> ⚠️ **WICHTIG:** `NEXT_PUBLIC_API_URL` muss auf den Backend-Server zeigen!
> Normalerweise: `https://api.resellerbot.de`
> Aktuell (wegen SSL Rate Limit): `https://45.147.7.54.nip.io`

---

## 🚀 Deployment Workflow

### 1. Code ändern (lokal)
```bash
# Dateien bearbeiten...
```

### 2. Commit & Push
```bash
git add .
git commit -m "Beschreibung der Änderung"
git push
```

### 3. Backend deployen
```bash
./deploy.sh
```
Das macht automatisch:
- SSH zum Server
- Git Pull
- Secrets kopieren (auth.json, .env)
- Docker Container neu bauen
- Caddy + Backend starten

### 4. Frontend deployen (nur bei Dashboard-Änderungen)
- Vercel deployed automatisch bei Push zu `main`
- Oder: Manuell in Vercel Dashboard "Redeploy" klicken

---

## 🖥️ Server-Zugang

```bash
# SSH Verbindung
ssh root@45.147.7.54
# Passwort: 3VE2tsb7y1kt

# Zum Projekt
cd Resell_Bot

# Logs anzeigen
docker logs ps5-bot-backend --tail 100
docker logs ps5-bot-caddy --tail 50

# Container neustarten
docker compose restart

# Komplett neu bauen
docker compose down && docker compose up -d --build
```

---

## 📊 Dashboard URLs

| Seite | URL |
|-------|-----|
| **Dashboard** | https://resellerbot.de |
| **Login** | https://resellerbot.de/login |
| **Listings** | https://resellerbot.de/listings |
| **Templates** | https://resellerbot.de/templates |
| **Settings** | https://resellerbot.de/settings |
| **Debug Filter** | https://resellerbot.de/debug-filter |

---

## 🔧 Wichtige Befehle

### Bot manuell starten (auf Server)
```bash
docker exec ps5-bot-backend python3 -u main.py --mode full
```

### Nur Scrapen (ohne Senden)
```bash
docker exec ps5-bot-backend python3 -u main.py --mode debug
```

### DB aufräumen (teure Listings löschen)
```bash
docker exec ps5-bot-backend python3 cleanup_db.py
```

### Lokales Dashboard starten
```bash
cd dashboard
npm run dev
# Öffne http://localhost:3000
```

---

## ⚠️ Bekannte Probleme & Lösungen

### SSL Fehler / "Gesicherte Verbindung fehlgeschlagen"
**Ursache:** Let's Encrypt Rate Limit (5 Zertifikate/Woche)
**Lösung:** Wechsel zu `45.147.7.54.nip.io` als API Domain

### Bot findet keine Listings
**Ursache:** Kleinanzeigen Captcha/Bot-Schutz
**Lösung:** Warten und später erneut versuchen

### "Zu teure" Listings erscheinen
**Ursache:** Top-Ads ignorieren Preisfilter
**Lösung:** Python-Filter in `scraper.py` (Max 320€)

---

## 🔄 SSL Domain Wechsel (nach 48h)

Wenn Let's Encrypt Rate Limit abgelaufen ist:

1. **Caddyfile ändern:**
   ```
   api.resellerbot.de {
       reverse_proxy ps5-bot-backend:8000
   }
   ```

2. **deploy.sh Message ändern:**
   ```bash
   echo "🌐 API is reachable via HTTPS: https://api.resellerbot.de"
   ```

3. **Vercel Env Var ändern:**
   ```
   NEXT_PUBLIC_API_URL=https://api.resellerbot.de
   ```

4. **Deployen:**
   ```bash
   git add . && git commit -m "Switch back to main domain" && git push
   ./deploy.sh
   ```

---

## 📝 Entwickler-Notizen

- **Camoufox** wird benutzt um Bot-Detection zu umgehen
- **auth.json** enthält die Kleinanzeigen Session Cookies (NIEMALS committen!)
- **Groq API** hat ein Rate Limit von ~30 req/min
- **Supabase** Free Tier hat 500MB Speicher
- **Vercel** Free Tier hat 100GB Bandwidth/Monat

---

## 📞 Kontakt & Support

Bei Fragen oder Problemen einfach fragen!
