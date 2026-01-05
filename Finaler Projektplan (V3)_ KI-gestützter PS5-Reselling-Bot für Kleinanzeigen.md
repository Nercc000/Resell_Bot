# Finaler Projektplan (V3): KI-gestützter PS5-Reselling-Bot für Kleinanzeigen

Dieses Dokument stellt den finalen, umfassenden Projektplan für die Entwicklung eines KI-gestützten Bots für das PS5-Reselling auf Kleinanzeigen dar. Der Plan integriert die Nutzung von **Crawler-APIs** für die stabile Datenakquise und den spezialisierten Stealth-Browser **Camoufox** für die hochgradig getarnte Interaktion.

## 1. Zielsetzung und Herangehensweise

Das Hauptziel ist die Schaffung eines **zeitkritischen, intelligenten Systems**, das die besten PS5-Deals identifiziert und automatisiert, aber menschlich simuliert, Kontakt aufnimmt.

Die Herangehensweise basiert auf einem **Hybrid-Ansatz** zur Risikominimierung und Effizienzsteigerung:

| Modul | Funktion | Herangehensweise | Risiko |
| :--- | :--- | :--- | :--- |
| **Datenakquise** | Stündliches Abrufen der neuesten 20 Anzeigen. | **Crawler-API** (z.B. ZenRows, Apify) | Gering (Risiko ausgelagert) |
| **Intelligenz** | Bewertung der Anzeige und Generierung der Antwort. | **Large Language Model (LLM)** | Gering (Fokus auf Prompt-Engineering) |
| **Aktion** | Automatisches Senden der Nachricht. | **Camoufox + Residential Proxies** | Mittel (durch Camoufox minimiert) |

## 2. Modulare Architektur des Bots

Der Bot ist in fünf voneinander unabhängige Module unterteilt:

| Modul | Beschreibung | Technologie-Stack |
| :--- | :--- | :--- |
| **A. Datenakquise** | Sendet Suchanfragen an die Crawler-API und parst die strukturierten Ergebnisse. | Python, `requests`, Crawler-API-Client. |
| **B. KI-Analyse & Deal-Scoring** | Bewertet Titel, Beschreibung und Preis. Berechnet einen **Deal-Score** (1-10) basierend auf dynamischem Preis-Benchmarking. | Python, LLM API (z.B. OpenAI), SQLite/PostgreSQL für Preisdatenbank. |
| **C. Antwortgenerierung** | Erstellt einen personalisierten, menschlich klingenden Antworttext mit einem strategischen Preisvorschlag. | Python, LLM API, Prompt-Engineering. |
| **D. Interaktion & Aktion** | Loggt sich in Kleinanzeigen ein und sendet die generierte Nachricht über eine **Camoufox**-Sitzung. | Python, **Camoufox**, Residential Proxies. |
| **E. Steuerung & Monitoring** | Verwaltet den stündlichen Ausführungsplan, protokolliert alle Aktionen und implementiert Fehlerbehandlung. | Python, **APScheduler** (oder Celery), Logging-Bibliothek. |

## 3. Detaillierte Herangehensweisen und Stealth-Strategien

### 3.1. Datenakquise (Modul A)

*   **Technik:** Nutzung einer **Crawler-API** (z.B. Apify Actor für Kleinanzeigen) zur Umgehung von Anti-Bot-Maßnahmen und zur Sicherstellung von Echtzeit-Daten.
*   **Frequenz:** Aufruf der API **stündlich** mit den Suchparametern für PS5.
*   **Datenverarbeitung:** Konvertierung der API-Antwort (JSON) in ein standardisiertes internes Datenformat.

### 3.2. KI-Analyse und Antwortgenerierung (Modul B & C)

*   **Deal-Scoring:** Das LLM bewertet die Anzeige (Preis, Zustand, Verkäufer-Historie) und liefert einen Score. Nur Anzeigen mit einem Score von **> 8** werden zur Interaktion freigegeben.
*   **Prompt-Engineering:** Die Prompts müssen das LLM anweisen, einen Text zu generieren, der:
    1.  Höflich und persönlich ist.
    2.  Auf spezifische Details der Anzeige eingeht (z.B. "wegen des Zubehörs").
    3.  Einen konkreten, durch den Deal-Score gerechtfertigten Preisvorschlag enthält.

### 3.3. Interaktion und Aktion (Modul D) – Camoufox-Strategie

Die Interaktion erfolgt über den **Camoufox**-Browser, der Playwright-kompatibel ist und maximale Tarnung bietet.

| Strategie | Zweck | Implementierung |
| :--- | :--- | :--- |
| **Stealth-Browser** | Umgehung von TLS- und Browser-Fingerprinting. | Nutzung von **Camoufox** anstelle von Standard-Playwright/Chromium. |
| **Netzwerk-Tarnung** | Echte IP-Adresse und Geo-Lokalisierung. | **Residential Proxies** für die Camoufox-Sitzung. Automatische Anpassung von Zeitzone und Sprache (GeoIP) durch Camoufox. |
| **Verhaltens-Tarnung** | Simulation menschlicher Interaktion. | **Zufällige Wartezeiten** (`random.uniform(2, 5)`). **Tipp-Simulation** mit realistischer Verzögerung (50-150 ms pro Zeichen). **Mausbewegungen** vor dem Klicken. |
| **Session-Management** | Vermeidung ständiger Logins. | Speichern und Laden von **Session-Cookies** für den Camoufox-Browser, um den Anmeldevorgang zu überspringen. |

## 4. Schwierigkeiten und Risikomanagement

Die Integration von Camoufox minimiert das technische Risiko, aber die folgenden Herausforderungen bleiben bestehen:

| Schwierigkeit | Kategorie | Risikomanagement-Strategie |
| :--- | :--- | :--- |
| **Account-Sperrung** | Technisch/Plattform-Risiko | **Camoufox** + **Residential Proxies** + **Gezielte Interaktion** (nur Top-Deals) + **Session-Cookies**. |
| **Kosten der Crawler-API** | Technisch/Finanziell | Auswahl eines kosteneffizienten Anbieters und strikte Limitierung der Abfragen auf einmal pro Stunde. |
| **KI-Halluzinationen** | KI-Risiko | **Prompt-Engineering** und **Validierungsfunktion** für die generierte Antwort. |
| **Rechtliche Grauzone** | Rechtliches Risiko | **Transparenz:** Der Nutzer muss sich des Risikos eines Verstoßes gegen die AGB bewusst sein. Hinweis auf die Notwendigkeit einer Gewerbeanmeldung. |

## 5. Implementierungsphasen (Zusammenfassung)

1.  **Setup & Datenakquise:** Projekt initialisieren, Crawler-API-Zugang einrichten, stündliche Abfrage implementieren.
2.  **KI-Logik:** Preisdatenbank aufsetzen, LLM-Prompts für Analyse und Scoring entwickeln.
3.  **Antwortgenerierung:** LLM-Prompts für die Antwort erstellen, Validierungslogik implementieren.
4.  **Interaktion (Camoufox):** Camoufox, Residential Proxies und Session-Management einrichten, menschliches Verhalten simulieren.
5.  **Finalisierung:** Scheduler (APScheduler) und umfassendes Logging implementieren.

Dieser Plan bietet die technisch fortschrittlichste und robusteste Strategie, um den KI-gestützten PS5-Reselling-Bot erfolgreich zu entwickeln.
