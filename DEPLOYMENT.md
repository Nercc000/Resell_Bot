# 🚀 PS5 Bot – Deployment Guide (Ubuntu Server)

Dieses Guide erklärt Schritt-für-Schritt, wie du den Bot auf deinem Ubuntu Server installierst und startest.

---

## 1. Voraussetzungen auf dem Server
Verbinde dich per SSH mit deinem Server:
```bash
ssh root@45.147.7.54
# (Passwort: 3VE2tsb7y1kt)
```

Installiere Docker & Git (falls noch nicht drauf):
```bash
sudo apt update
sudo apt install -y git docker.io
sudo systemctl enable --now docker
```

---

## 2. Projekt herunterladen
Klone das Repository:
```bash
git clone https://github.com/Nercc000/Resell_Bot.git
cd Resell_Bot
```

---

## 3. Konfiguration (.env)
Erstelle die `.env` Datei auf dem Server:
```bash
nano .env
```
Füge dort deine API-Keys ein (kopiere sie lokal aus deiner `.env`):
```ini
KLEINANZEIGEN_EMAIL=...
KLEINANZEIGEN_PASSWORD=...
SUPABASE_URL=...
SUPABASE_KEY=...
GROQ_API_KEY=...
```
*(Drücke `STRG+O`, `Enter` zum Speichern und `STRG+X` zum Beenden)*

---

## 4. Auth-Daten hochladen (WICHTIG!)
Die Datei `auth.json` (dein Login-Cookie) ist **nicht** im Git. Du musst sie manuell hochladen oder den Inhalt kopieren.

**Option A (Einfach - Copy Paste):**
1. Öffne lokal `auth.json` und kopiere ALLES.
2. Auf dem Server: `nano auth.json`
3. Inhalt einfügen -> Speichern.

**Option B (SCP - von deinem PC aus):**
```bash
scp auth.json root@45.147.7.54:/root/Resell_Bot/auth.json
```

---

## 5. Deployment mit `deploy.sh` (Empfohlen!)

Ich habe dir ein Skript `deploy.sh` erstellt, das ALLES für dich erledigt.
Es prüft automatisch, ob Docker schon da ist (und überspringt die Installation dann).

**WICHTIG:** Dieses Skript führst du auf **DEINEM PC** aus (nicht auf dem Server)!

1.  Mach das Skript ausführbar:
    ```bash
    chmod +x deploy.sh
    ```
2.  Starte den Deploy:
    ```bash
    ./deploy.sh
    ```
3.  Gib das Server-Passwort ein, wenn gefragt (`3VE2tsb7y1kt`).

Das Skript macht Folgendes:
- Verbindet sich zum Server.
- Installiert Docker (nur wenn es FEHLT).
- Aktualisiert den Code.
- Lädt deine `.env` und `auth.json` hoch.
- Startet alles neu (mit HTTPS via Caddy).

Nach ca. 1 Minute ist alles live unter `https://45.147.7.54` ! 🚀

---

## 6. Dashboard (Frontend) nutzen
Du kannst das Dashboard lokal auf deinem PC laufen lassen, aber mit dem Server verbinden. 

Öffne lokal `dashboard/.env.local` (oder erstelle sie) und setze:
```ini
NEXT_PUBLIC_API_URL=http://45.147.7.54:8000
```
Dann lokal `npm run dev`. Das Dashboard steuert jetzt den Bot auf dem Server!
