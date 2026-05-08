# ElasticLens - Elasticsearch Cluster-Inspektionssystem

<div align="center">

**Web-basierte automatisierte Interpretationsplattform für Elasticsearch-Cluster-Inspektionsergebnisse**

![alt text](mian_web.png)

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18.2-61dafb.svg)](https://react.dev/)
[![Flask](https://img.shields.io/badge/flask-3.0-black.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Sprachen:** [English](../README.md) | [简体中文](README.zh.md) | [Français](README.fr.md) | [Русский](README.ru.md) | [日本語](README.ja.md)

</div>


---

## 📖 Einführung

ElasticLens ist eine **Visualisierungs- und Analyseplattform** für Inspektionsergebnisse von Elasticsearch-Clustern. Das System wurde entwickelt, um Diagnose-ZIP-Pakete zu verarbeiten, die vom **offiziellen Elasticsearch-Diagnosetool** exportiert wurden, diagnostische Daten automatisch zu analysieren, eine tiefgehende Cluster-Gesundheitsanalyse durchzuführen und mehrdimensionale Inspektionsberichte (HTML / Word / JSON) zu generieren.

Diese Plattform hilft Betriebspersonal, den Cluster-Gesundheitsstatus schnell zu verstehen, potenzielle Probleme zu entdecken und Optimierungsempfehlungen durch intuitive visuelle Darstellungen zu erhalten, ohne komplexe Diagnosedaten manuell analysieren zu müssen.

**Offizielles Elasticsearch-Diagnosetool**: [elastic/support-diagnostics](https://github.com/elastic/support-diagnostics/)

### ✨ Hauptfunktionen

- 🌐 **Web-Plattform** - Vollständige Web-Anwendung basierend auf React + Flask, unterstützt Drag-and-Drop-Upload von Diagnosepaketen
- 📊 **Multi-Format-Berichte** - Automatische Generierung von Inspektionsberichten im HTML- und Word-Format (.docx)
- 🔍 **Intelligente Analyse** - Automatische Analyse von ES-Diagnose-ZIP-Paketen, Extraktion wichtiger Metriken (Cluster-Gesundheit, Knotenressourcen, Index-Details, ILM, Snapshots, Sicherheit usw.)
- 🧠 **Tiefenanalyse** - Regelbasierte Gesundheitsbewertung, Ressourcenanalyse und Alarmgenerierung
- 🎯 **Gesundheitsbewertung** - 0-100 quantitative Bewertung zur intuitiven Anzeige der Cluster-Gesundheitsstufen
- 🔔 **Abgestufte Warnungen** - Drei-Stufen/Zwei-Stufen/Ein-Stufen-Warnmechanismus (severity_level)
- ⚡ **Asynchrone Verarbeitung** - Hintergrund-asynchrone Aufgabenverarbeitung, unterstützt große Dateien (2GB) Upload und langlaufende Analysen
- 📈 **Visualisierung** - Kreisförmiges Gesundheitsbewertungs-Dashboard, Fortschrittsbalken, Karten und andere visuelle Anzeigen
- 📝 **Mehrsprachige Unterstützung** - Vollständige Unterstützung für Vereinfachtes Chinesisch, Traditionelles Chinesisch, Englisch, Japanisch, Französisch, Deutsch, Russisch - sieben Sprachen, mit automatischer Oberflächen- und Berichtsumschaltung

### 🌍 Mehrsprachige Unterstützung

Das System unterstützt umfassend Internationalisierung (i18n) und bietet folgende 7 Sprachen:

- 🇨🇳 **Vereinfachtes Chinesisch (zh-CN)** - Standardsprache
- 🇹🇼 **Traditionelles Chinesisch (zh-TW)** - Vollständige Übersetzung
- 🇺🇸 **Englisch (en-US)** - Vollständige Übersetzung
- 🇯🇵 **Japanisch (ja-JP)** - Vollständige Übersetzung
- 🇫🇷 **Französisch (fr-FR)** - Vollständige Übersetzung
- 🇩🇪 **Deutsch (de-DE)** - Vollständige Übersetzung
- 🇷🇺 **Russisch (ru-RU)** - Vollständige Übersetzung

**Funktionen:**
- ✅ Frontend-Benutzeroberfläche dynamische Sprachumschaltung (Startseite, Aufgabenliste, Berichte, Upload, Verlauf, Einstellungen)
- ✅ Backend-Berichtsgenerierung unterstützt mehrere Sprachen (HTML + Word-Format)
- ✅ Spracheinstellung automatisch gespeichert, wird beim nächsten Besuch automatisch angewendet
- ✅ Ant Design-Komponentenbibliothek passt sich automatisch an mehrere Sprachen an
- ✅ Intelligente Übersetzungsfunktion verarbeitet dynamische Inhalte (z.B. "5 Indizes" → "5インデックス" → "5 indices")
- ✅ Dynamische Nachrichten intelligente Übereinstimmung und automatischer Übersetzungs-Fallback-Mechanismus

**Verwendung:**
Klicken Sie auf die Sprachumschalt-Schaltfläche auf der rechten Seite des Startseite-Titels und wählen Sie die gewünschte Sprache.

---

## 🏗️ Systemarchitektur

```
┌─────────────────┐      REST API      ┌─────────────────┐
│   Frontend       │ ◄───────────────► │   Backend        │
│   (React)        │                    │   (Flask)        │
│                 │                    │                 │
│ - Datei-Upload   │                    │ - Aufgabenverw.  │
│ - Aufgaben-      │                    │ - Asynchrone     │
│   tracking       │                    │   Verarbeitung   │
│ - Berichts-      │                    │ - Berichtsgen.   │
│   anzeige        │                    │ - Dateiverwaltung│
└─────────────────┘                    └────────┬────────
                                                │
                                                ▼
                                    ┌────────────────────┐
                                    │  es_insight Core     │
                                    │                     │
                                    │ - Diagnosedaten     │
                                    │ - Regelengine-Check │
                                    │ - Gesundheits-      │
                                    │   bewertung         │
                                    │ - HTML/Word-Berichte│
                                    └────────┬───────────┘
                                             │
                                             ▼
                                    ┌────────────────────┐
                                    │  SQLite-Datenbank    │
                                    │                     │
                                    │ - Aufgaben-Meta-    │
                                    │   daten             │
                                    │ - Berichts-Meta-    │
                                    │   daten             │
                                    │ - Abfrage & Stat.   │
                                    └────────┬───────────┘
                                             │
                                             ▼
                                    ┌────────────────────┐
                                    │  Dateisystem         │
                                    │                     │
                                    │ - Hochgeladene ZIPs │
                                    │ - JSON-Berichte     │
                                    │ - HTML-Berichte     │
                                    │ - Word-Berichte     │
                                    └────────────────────┘
```

---

## 🚀 Schnellstart

### Anforderungen

- **Python**: 3.9+
- **Node.js**: 18+ (Frontend-Entwicklung/Build)
- **npm**: 9+ (Frontend-Paketverwaltung)
- **Betriebssystem**: Windows 10+/Linux/macOS

### Methode 1: Web-Plattform (Empfohlen)

#### 🐳 Docker-Bereitstellung (Empfohlen für Produktion)

Verwenden Sie Docker Compose für One-Click-Bereitstellung von Frontend- und Backend-Diensten:

```bash
# Im Projekt-Stammverzeichnis ausführen
cd elasticlens

# Alle Dienste starten (Frontend + Backend)
./start.sh

# Oder manuell ausführen
docker compose up -d
```

**Zugriffs-URLs:**
- Frontend-Oberfläche: http://localhost:8080
- Backend-API: http://localhost:5001

**Vorteile:**
- ✅ Keine Installation von Python- und Node.js-Umgebungen erforderlich
- ✅ Verarbeitet automatisch alle Abhängigkeiten
- ✅ Datenpersistenz (Datenbank, hochgeladene Dateien, Berichte)
- ✅ Gesundheitschecks und automatischer Neustart
- ✅ Geeignet für Produktionsumgebungsbereitstellung
- ✅ Unterstützt Intranet-Offline-Bereitstellung

Für detaillierte Bereitstellungsanleitung siehe: [Intranet-Offline-Docker-Bereitstellungsanleitung.md](内网离线Docker部署方案.md)

---

#### Traditionelle Bereitstellung (Lokale Entwicklung)

##### 1. Backend-Abhängigkeiten installieren

```bash
cd backend
pip install -r requirements.txt
```

Backend-Abhängigkeiten umfassen:
- Flask 3.0.0 - Web-Framework
- Flask-CORS 4.0.0 - Cross-Origin-Unterstützung
- python-docx >= 1.0.0 - Word-Berichtsgenerierung
- loguru 0.7.2 - Protokollverwaltung
- weasyprint >= 60.0 - PDF-Rendering (optional)
- SQLite3 - Datenbank (Python integriert, Null-Konfiguration)

#### 2. Frontend-Abhängigkeiten installieren

```bash
cd frontend
npm install
```

Frontend-Abhängigkeiten umfassen:
- React 18.2 + TypeScript
- Ant Design 5.12 - UI-Komponentenbibliothek
- Vite 5.0 - Build-Tool
- Axios 1.6 - HTTP-Client
- Zustand 4.4 - Zustandsverwaltung
- Recharts 2.10 - Diagrammbibliothek

##### 3. Dienste starten

**Backend starten** (im Projekt-Stammverzeichnis):
```bash
cd backend
python app.py
```
Backend-Dienst läuft auf `http://localhost:5000`

**Frontend starten** (im Projekt-Stammverzeichnis):
```bash
cd frontend
npm run dev
```
Frontend-Dienst läuft auf `http://localhost:5173`

#### 4. Web-Plattform verwenden

1. Browser öffnen auf `http://localhost:5173`
2. ES-Diagnose-ZIP-Datei per Drag-and-Drop oder Klick hochladen
3. Auf Abschluss der asynchronen Analyse warten
4. Inspektionsbericht anzeigen (HTML-Anzeige)
5. Auf "Word herunterladen"-Schaltfläche klicken, um Word-Bericht zu exportieren

### Methode 2: Kommandozeilen-Tool (CLI)

#### Installation

```bash
pip install -r requirements.txt
pip install -e .
```

#### Grundlegende Verwendung

```bash
# Diagnosepaket analysieren und Bericht generieren
es-insight data/local-diagnostics-*.zip

# Ausgabeverzeichnis angeben
es-insight data/local-diagnostics-*.zip -o ./reports

# Ausgabeformat angeben
es-insight data/local-diagnostics-*.zip -f html,json

# Benutzerdefinierte Konfiguration verwenden
es-insight data/local-diagnostics-*.zip -c configs/checkpoints_thresholds_complete.yaml
```

#### Python-Skript verwenden

```bash
# Ein-Klick-Verarbeitung des Diagnose-ZIP-Pakets
python process_diagnostic_zip.py

# HTML-Bericht generieren
python generate_html_report.py data/local-diagnostics-*.zip
```

---

## 📁 Projektstruktur

```
Inspektionspunkt-Lesung/
├── backend/                    # Flask-Backend-Dienst
│   ├── app.py                  # Hauptdienstdatei (Datei-Upload, Aufgabenverwaltung, Berichtsgenerierungs-API)
│   ├── version.py              # Versionskonfiguration (v1.0.9)
│   ├── db_server/              # Datenbankdienstmodul
│   │   ├── __init__.py         # Paketinitialisierung
│   │   ├── database.py         # Datenbankinitialisierung und Verbindungsverwaltung
│   │   └── models.py           # Datenmodell-Operationskapselung (TaskModel, ReportModel)
│   ├── es_insight.db           # SQLite-Datenbankdatei (automatisch generiert)
│   ├── migrate_*.py            # Datenmigrationsskripte
│   ├── requirements.txt        # Backend-Abhängigkeiten
│   └── DEPLOYMENT.md           # Bereitstellungsdokumentation
│
├── frontend/                   # React-Frontend-Anwendung
│   ├── src/
│   │   ├── api/                # API-Schnittstellenkapselung (Axios-Instanz, Interceptors)
│   │   ├── components/         # Allgemeine Komponenten (Upload, Task, Report)
│   │   ├── pages/              # Seitenkomponenten (Home, Report, History, Settings)
│   │   ├── store/              # Zustand-Zustandsverwaltung
│   │   ├── hooks/              # Benutzerdefinierte Hooks (usePolling, useDownload)
│   │   ├── types/              # TypeScript-Typdefinitionen
│   │   └── utils/              # Hilfsfunktionen
│   ├── .env.development        # Entwicklungsumgebungsvariablen
│   ├── .env.production         # Produktionsumgebungsvariablen
│   ├── package.json
│   └── vite.config.ts          # Vite-Konfiguration (Proxy, Plugins)
│
├── es_insight/                 # Kernanalyse-Engine
│   ├── parsers/                # Datenparser
│   │   ├── health_parser.py    # Cluster-Gesundheitsparsing
│   │   ├── nodes_parser.py     # Knoteninformationsparsing
│   │   └── indices_parser.py   # Indexinformationsparsing
│   ├── analyzers/              # Analyse-Engines
│   │   ├── health_engine.py    # Gesundheitsbewertung
│   │   └── resource_engine.py  # Ressourcenanalyse
│   ├── rules/                  # Regel-Engine
│   │   └── engine.py           # Schwellenwertprüfung und Alarmgenerierung (50+ Regeln)
│   ├── models/                 # Datenmodelle
│   ├── diagnostic_extractor.py # Diagnose-ZIP-Paket-Extraktor
│   ├── parse_check_result.py   # Prüfergebnisparsing (Gesundheitsbewertungsberechnung)
│   ├── report_generator.py     # Multi-Format-Berichtsgenerator
│   ├── generate_html_report.py # HTML-Berichtsgenerierung
│   └── cli.py                  # Kommandozeilenschnittstelle
│
├── configs/                    # Konfigurationsdateien
│   ├── checkpoints_thresholds_complete.yaml  # Prüfpunkt-Schwellenwertkonfiguration (vollständige Version)
│   ├── default_thresholds.yaml               # Standardschwellenwerte
│   ├── default_report.yaml                   # Berichtskonfiguration
│   └── Testanleitung.md
│
├── data/                       # Testdatenverzeichnis
├── uploads/                    # Hochgeladene ZIP-Dateien (Web-Modus)
├── out/                        # Analyse-Zwischenausgabe
├── reports/                    # Generierte Berichtsdateien
├── doc/                        # Dokumentationsverzeichnis
│   ├── Frontend-Design/        # Frontend-Designdokumente
│   └── Backend-Design/         # Backend-Designdokumente
└── tests/                      # Testfälle
```

---

## 📊 Übersicht der Inspektionspunkte

Das System deckt **11 Hauptkategorien** von Inspektionsindikatoren ab, einschließlich **30+ spezifischer Prüfungen**:

| Kategorie | Gewichtung | Prüfpunkte |
|-----------|------------|------------|
| **Cluster-Gesundheit** | 30% | Cluster-Status, aktiver Shard-Anteil, nicht zugewiesene Shards, initialisierende Shards, relocating Shards |
| **Knotenressourcen** | 25% | Festplattennutzung, JVM-Heap-Nutzung, CPU-Nutzung, Systemlast, Shards pro Knoten |
| **Index-Gesundheit** | 20% | Index-Gesundheitsverteilung, Anzahl großer Indizes, Indizes mit hoher Segmentanzahl, Indizes mit hoher Shard-Anzahl, Indizes mit großer Dokumentanzahl |
| **Shard-Prüfungen** | 5% | Einzelne Shard-Größe, einzelne Shard-Dokumentanzahl, Shard-Verteilungsausgleich |
| **Wiederherstellungsprüfungen** | 5% | Anzahl wiederherstellender Shards, durchschnittlicher Wiederherstellungsfortschritt |
| **ILM-Richtlinie** | 3% | ILM-Statusprüfung |
| **Snapshot-Prüfung** | 3% | Snapshot-Konfiguration und -Status |
| **Sicherheitsprüfung** | 2% | X-Pack-Sicherheitsfunktionsaktivierung |
| **Vorlagen & Mappings** | 2% | Index-Vorlagen, Komponenten-Vorlagen, durchschnittliche Feldanzahl |
| **Protokolle & Fehler** | 2% | GC-Anzahl, GC-Zeitstatistiken |
| **Leistungsinformationen** | - | Gesamte Cluster-Dokumente, gesamte Cluster-Speichergröße (Informationsanzeige, nicht in Bewertung enthalten) |

---

## ⚙️ Konfiguration

### Schwellenwertkonfiguration

Kern-Schwellenwertkonfigurationsdatei befindet sich unter `configs/checkpoints_thresholds_complete.yaml`, Hauptkonfigurationselemente:

```yaml
# Cluster-Gesundheit
cluster:
  status:
    green: none     # GRÜN-Status keine Warnung
    yellow: warning # GELB-Status Warnung
    red: critical   # ROT-Status kritisch
  active_shards_percent:
    warning: 95     # Unter 95% Warnung
    critical: 90    # Unter 90% kritisch

# Knotenressourcen
node:
  disk_usage_percent:
    warning: 70     # Festplatte 70% Aufmerksamkeit
    alert: 80       # Festplatte 80% Wasserzeichen
    critical: 85    # Festplatte 85% Schreibverweigerung
  heap_used_percent:
    warning: 70     # JVM 70% Aufmerksamkeit
    critical: 85    # JVM 85% OOM-Risiko

# Index-Gesundheit
index:
  size_gb:
    warning: 50     # Einzelner Index 50GB Aufmerksamkeit
    critical: 100   # Einzelner Index 100GB kritisch
  docs_count:
    warning: 100000000    # 100M Dokumente Aufmerksamkeit
    critical: 500000000   # 500M Dokumente kritisch
```

### Gesundheitsbewertungsberechnung

```python
Bewertung = 100 - (Kritische Warnungen × 20) - (Warnungen × 5) - (Info-Warnungen × 1)
Bewertungsbereich: 0-100
```

| Bewertungsbereich | Gesundheitsstufe |
|-------------------|------------------|
| 90-100 | 🌟 Ausgezeichnet |
| 75-89 | 👍 Gut |
| 60-74 | ⚠️ Befriedigend |
| 40-59 | 🔴 Schlecht |
| 0-39 | 🚨 Kritisch |

---

## 📄 Berichtsausgabe

### HTML-Bericht

- Lila Farbverlauf-Themendesign
- Kreisförmige Gesundheitsbewertungsvisualisierung
- Responsives Kartenlayout
- Abgestufte Alarminformationsanzeige (Critical/Warning/Info)
- Vollständige Prüfpunkt-Detailtabelle

### Word-Bericht (.docx)

- Professionelles Layout-Format
- Cluster-Basisinformationstabelle
- Gesundheitsbewertung und -bewertung
- Prüfpunkt-Details (Bestanden/Nicht bestanden Status, Werte, Schwellenwerte)
- Abgestufte Alarm-Details-Liste
- Farbcodierung (✅ Grün bestanden, ❌ Rot fehlgeschlagen)

### JSON-Bericht

- Strukturierte Daten
- Enthält vollständige `check_results` Prüfpunkt-Details
- Praktisch für Sekundärentwicklung und Datenanalyse

---

## 🔧 API-Endpunkte

Backend stellt folgende REST-API-Endpunkte bereit:

### Aufgabenverwaltung

| Methode | Endpunkt | Beschreibung |
|---------|----------|--------------|
| POST | `/api/v1/upload` | Diagnose-ZIP-Datei hochladen, asynchrone Aufgabe erstellen |
| GET | `/api/v1/tasks` | Aufgabenliste abrufen (paginiert, gelöschte ausschließen) |
| GET | `/api/v1/tasks/<task_id>` | Einzelne Aufgabendetails abrufen |
| DELETE | `/api/v1/tasks/<task_id>` | Soft-Delete-Aufgabe (kaskadierendes Löschen von Berichten) |

### Berichtsverwaltung

| Methode | Endpunkt | Beschreibung |
|---------|----------|--------------|
| GET | `/api/v1/reports` | Berichtsliste abrufen (unterstützt Filterung und Paginierung) |
| GET | `/api/v1/reports/statistics` | Berichtsstatistiken abrufen |
| GET | `/api/v1/reports/<report_id>` | Berichts-JSON-Daten abrufen |
| GET | `/api/v1/reports/<report_id>/html` | HTML-Berichtsinhaltsstring abrufen |
| GET | `/api/v1/reports/<report_id>/view` | HTML-Bericht direkt anzeigen (iframe) |
| GET | `/api/v1/reports/<report_id>/download?format=word` | Word-Bericht herunterladen |
| GET | `/api/v1/reports/<report_id>/download?format=json` | JSON-Bericht herunterladen |
| GET | `/api/v1/reports/<report_id>/download?format=html` | HTML-Bericht herunterladen |

### System-Endpunkte

| Methode | Endpunkt | Beschreibung |
|---------|----------|--------------|
| GET | `/api/v1/health` | Gesundheitscheck (gibt Versionsinformationen zurück) |

---

## 🧪 Tests

```bash
# Unit-Tests ausführen
pytest tests/

# Spezifischen Test ausführen
pytest tests/unit/test_health_parser.py

# Mit Coverage-Bericht
pytest --cov=es_insight --cov-report=html
```

---

## 📦 Abhängigkeitsliste

### Backend-Kernabhängigkeiten

| Paket | Version | Zweck |
|-------|---------|-------|
| Flask | 3.0.0 | Web-Framework |
| Flask-CORS | 4.0.0 | Cross-Origin-Unterstützung |
| Werkzeug | 3.0.1 | WSGI-Toolkit |
| python-docx | >= 1.0.0 | Word-Berichtsgenerierung |
| click | 8.1.7 | CLI-Framework |
| pyyaml | >= 6.0 | YAML-Konfigurationsparsing |
| loguru | 0.7.2 | Protokollverwaltung |
| orjson | >= 3.6.0 | Hochleistungs-JSON |
| weasyprint | >= 60.0 | PDF-Rendering (optional) |
| SQLite3 | Python integriert | Datenspeicherung |

### Frontend-Kernabhängigkeiten

| Paket | Version | Zweck |
|-------|---------|-------|
| React | 18.2 | UI-Framework |
| TypeScript | 5.2 | Typsystem |
| Ant Design | 5.12 | UI-Komponentenbibliothek |
| Vite | 4.x | Build-Tool |
| Axios | 1.6 | HTTP-Client |
| Zustand | 4.4 | Zustandsverwaltung |
| React Router | 6.21 | Routenverwaltung |
| Recharts | 2.10 | Diagrammbibliothek |
| Day.js | 1.11 | Datumsbehandlung |

---

## 🐛 Fehlerbehebung

### Häufige Probleme

#### 1. Word-Berichtsgenerierung fehlgeschlagen
```bash
# Überprüfen, ob python-docx installiert ist
pip install python-docx>=1.0.0
```

#### 2. Frontend-Start fehlgeschlagen
```bash
# Sicherstellen, dass Node.js >= 18
node -v
npm -v

# Abhängigkeiten neu installieren
cd frontend
rm -rf node_modules
npm install
```

#### 3. Backend-Port belegt
```bash
# Portnummer in backend/app.py ändern
# Standardport: 5000
```

#### 4. Frontend-Port belegt
```bash
# Portnummer in frontend/vite.config.ts ändern
# Standardport: 5173
```

#### 5. Windows-Chinesische-Pfad-Probleme
- python-docx kann Kompatibilitätsprobleme mit Windows-chinesischen Pfaden haben
- Empfohlen, Projekt in englischem Pfad zu platzieren

#### 6. Datenbankdatei beschädigt
```bash
# Datenbankdatei löschen, Dienstneustart erstellt sie automatisch neu
cd backend
rm es_insight.db
python app.py
```
**Hinweis**: Dies verliert alle historischen Daten, bitte mit Vorsicht operieren!

#### 7. Aufgabenstatus wird nicht aktualisiert
- Überprüfen, ob Backend-Dienst normal läuft (zugreifen auf `http://localhost:5000/api/v1/health`)
- Browser-Konsole auf Netzwerkfehler überprüfen
- Bestätigen, dass Frontend-API-Adresse korrekt ist (`.env.development`)

---

## 📚 Dokumentation

Für detaillierte Dokumentation bitte das `doc/`-Verzeichnis überprüfen:

| Dokument | Beschreibung |
|----------|--------------|
| `doc/Frontend-Design/README.md` | Frontend-Dokumentationsnavigation |
| `doc/Frontend-Design/Frontend-Designplan.md` | Frontend-Technologieauswahl und Architekturentwurf |
| `doc/Frontend-Design/Frontend-Implementierungsleitfaden.md` | Frontend-detaillierte Codeimplementierung |
| `doc/Frontend-Design/Backend-Dienstentwurf.md` | Flask-API-Entwurf und -Bereitstellung |
| `doc/Frontend-Design/Frontend-Anforderungen.md` | Detaillierte Anforderungsspezifikationen |
| `configs/Testanleitung.md` | Testfälle und Nutzungsleitfaden |

---

## 📜 Änderungsprotokoll

Siehe [backend/CHANGELOG.md](backend/CHANGELOG.md) und [frontend/CHANGELOG.md](frontend/CHANGELOG.md) für Details

### v1.0.9 (2026-05-06)

- 🐳 **Docker-Bereitstellungsunterstützung hinzugefügt**: Containerisierte Bereitstellungslösung für Frontend und Backend implementiert
  - Backend Dockerfile: Basierend auf Python 3.11-slim, optimierte Image-Größe (~567MB)
  - Frontend Dockerfile: Multi-Stage-Build, verwendet Nginx Alpine (~45MB)
  - docker-compose.yml: Service-Orchestrierung, Gesundheitschecks, Datenpersistenz
  - start.sh / stop.sh: One-Click-Start/Stopp-Skripte, kompatibel mit Docker Compose V1/V2
  - Verbesserte Datenpersistenzlösung: Volume-Mounting für uploads, out, reports, db-Verzeichnisse
  - Intranet-Offline-Bereitstellungsdokumentation hinzugefügt: Vollständiger Verpackungs-, Transfer-, Bereitstellungsprozess
  
- 🔧 **Abhängigkeitsverwaltung optimiert**: Fehlende Python-Abhängigkeitspakete hinzugefügt
  - pandas>=1.3.0, numpy>=1.20.0, pyyaml>=6.0, jinja2>=3.0.0, orjson>=3.6.0 hinzugefügt
  
- 🐛 **Fehlerbehebungen**:
  - Debian Trixie-Paketname-Problem behoben
  - TypeScript-Kompilierungsfehler behoben (nicht verwendete Ant Design-Komponentenimporte entfernt)
  - Docker-Volume-Mount-Konflikte behoben

### v1.0.8 (2026-04-30)

- 🌍 **Mehrsprachige Internationalisierungsunterstützung hinzugefügt**: System unterstützt umfassend Französisch, Deutsch, Russisch
  - Backend-Berichtsgenerierung unterstützt Französisch (fr-FR), Deutsch (de-DE), Russisch (ru-RU)
  - Ungefähr 1065 Übersetzungsschlüssel batchweise hinzugefügt (927 statische Übersetzungen + 138 dynamische Phrasen)
  - Intelligente Übersetzungsfunktion `translate_check_message()` erweitert, unterstützt 46 häufige Phrasen-Zuordnungen
  - Nicht übersetzten Text in HTML-Berichten von 99 auf 34 reduziert (66% Verbesserung)

### v1.0.7 (2026-04-30)

- 🇯🇵 **Japanische Internationalisierungsunterstützung verbessert**: Verbleibende chinesische Übersetzungsprobleme in Berichten gründlich gelöst
  - 33 fehlende statische Übersetzungsschlüssel in `translations.py` ergänzt
  - Doppelte Definitionen in `translations_map` behoben, die fehlende japanische Übersetzungen verursachten
  - Intelligente Übersetzungslogik für dynamischen Wert "unbekannt" implementiert
  
- 📊 **Index-Datenquellenkonfiguration optimiert**: Genauigkeit und Konsistenz von Index-Statistikdaten verbessert
  - Index-Basisinformationsdatenquelle von `indices.json` durch genaueres `indices_stats.json` ersetzt
  - Einheitliche Verwendung von `cat_shards.txt` als autoritative Quelle für Shard-Anzahl- und Größenstatistiken

### v1.0.6 (2026-04-29)

- 🇯🇵 **Japanische Internationalisierungsunterstützung hinzugefügt**: System unterstützt umfassend Japanisch (ja-JP)
  - Backend-Berichtsgenerierung unterstützt japanische Übersetzung (HTML + Word)
  - Ungefähr 370 japanische Übersetzungsschlüssel hinzugefügt, die gesamten Berichtsinhalt abdecken
  - Frontend-UI unterstützt vollständig 4 Sprachen (Vereinfachtes Chinesisch, Traditionelles Chinesisch, Englisch, Japanisch)
  
- 🐛 **Word-Bericht-Sprachumschaltungsfehler behoben**: Heruntergeladene Word-Berichte nach Sprachumschaltung verwenden aktuelle Sprache
  - Verschiedene Sprachen verwenden unabhängige Dateinamen: `{report_id}_{lang}.docx`
  - Problem behoben, bei dem Downloads nach Umschaltung noch alte Sprache verwendeten

### v1.0.5 (2026-04-27)

- 🔔 **Drei-Stufen-Warnklassifizierungssystem hinzugefügt**: severity_level-Validierungsstufe eingeführt
  - 🔴 Stufe-3-Warnung (Muss behandelt werden): severity_level=3, sehr ernste Probleme
  - 🟡 Stufe-2-Warnung (Empfohlen zu behandeln): severity_level=2, allgemeine Probleme
  - 🔵 Stufe-1-Warnung (Optimierungsvorschlag): severity_level=1, nicht ernste Probleme
  - Warnanzahlstatistiken nach Ebene in Gesundheitsbewertungsberichten hinzugefügt
  
- 📊 **Alarminformationsanzeige refaktoriert**: Von "Kritisch/Warnung" Zwei-Stufen zu "Stufe 3/Stufe 2/Stufe 1" Drei-Stufen-Klassifizierung geändert
  - HTML- und Word-Berichtsalarminformationen nach severity_level gruppiert und angezeigt
  - Listenseite zeigt Warnanzahlen nach Ebene (level_1_count, level_2_count, level_3_count)

### v1.0.4 (2026-04-27)

- 📈 **5 erweiterte Analysekomponenten hinzugefügt**: Tiefenanalysefunktionalität in HTML- und Word-Berichten hinzugefügt
  - ⚠️ Thread-Pool-Warteschlangen-Akkumulationswarnung: Thread-Pool-Warteschlangengröße und Ablehnungsanzahl überwachen
  - 🔥 Shard-Verteilungs-Hotspots: Lastindex basierend auf Shard-Anzahl, CPU%, Festplatte% berechnen
  - 💾 JVM-Speicherprofil: JVM-Heap-Nutzung, verwendeter/maximaler Heap-Speicher für jeden Knoten anzeigen
  - ⚙️ Konfigurationsdrift-Erkennung: Wichtige Konfigurationsparameter über Knoten hinweg vergleichen, Inkonsistenzen erkennen
  - ✅ Shard-Zuweisungsstatus: Nicht zugewiesene Shards erkennen und Fehlergründe anzeigen

### v1.0.3 (2026-04-27)

- 🎯 **Gewichtetes Dimensionsbewertungssystem hinzugefügt**: 6 Hauptdimensionskategorien und Gewichtungsmechanismus eingeführt
  - Cluster-Gesundheit (25%), Knotenleistung (25%), Index-Status (20%)
  - Leistungsmetriken (15%), Sicherheitskonfiguration (10%), Betriebsstatus (5%)
  - Drei-Stufen-Schwellenwert-lineare Interpolationsalgorithmus hinzugefügt: Gradbewertung unterstützen, kleine Probleme von ernsten Problemen unterscheiden
  - 4 Konfigurationsdateien hinzugefügt: dimension_weights.yaml, indicator_weights.yaml usw.
  
- 🐛 **Bewertungslogikprobleme behoben**:
  - Dictionary-Typ-Wertbehandlungsfehler behoben
  - Dimensionsgewichtskonfigurationsparseproblem behoben
  - Inkonsistenz zwischen Listenseiten- und Berichtsseitenbewertungen behoben

### v1.0.2 (2026-04-22)

- 💾 **Inspektionsbericht-Persistenzspeicherung implementiert** (SQLite-Datenbank)
  - `backend/db_server/`-Modul erstellt, einschließlich Datenbankverwaltung und Datenmodellen
  - tasks-Tabelle und reports-Tabelle implementiert, unterstützt vollständige Lebenszyklusverwaltung von Aufgaben und Berichten
  - Berichtslistenabfrageschnittstelle hinzugefügt, unterstützt Filterung nach Cluster-Name und Gesundheitsbewertung
  - Berichtsstatistikschnittstelle hinzugefügt, bietet Gesamtberichtsanzahl, durchschnittliche Gesundheitsbewertung und andere statistische Daten
  
- 📄 **Word-Format-Bericht-Download-Funktionalität**
  - Unterstützung zum Exportieren von Inspektionsberichten ins Microsoft Word (.docx)-Format
  - Lazy-Generierungsstrategie übernommen: Beim ersten Request aus JSON-Daten generieren und cachen

---

## 🤝 Mitwirken

Willkommen zum Einreichen von Issues und Pull Requests!

### Codestandards

```bash
# Backend-Code-Formatierung
black es_insight/ backend/

# Frontend-Code-Überprüfung
cd frontend
npm run lint
```

---

## 📄 Lizenz

MIT-Lizenz

---

## 👥 Betreuer

ElasticLens Team

---

## 📞 Kontakt

Bei Fragen oder Vorschlägen bitte kontaktieren über:

- **Issues**: GitHub Issues
- **E-Mail**: support@yogoo.net

---

<div align="center">

**Wenn dieses Projekt Ihnen hilft, geben Sie ihm bitte einen ⭐ Stern!**

Erstellt mit ❤️ vom ElasticLens Team

**Aktuelle Version**: v1.0.9 | **Letzte Aktualisierung**: 2026-05-06

## Berichtsoberflächenanzeige

![alt text](report_1.png)

![alt text](report_2.png)

![alt text](report_3.png)

![alt text](report_4.png)
</div>
