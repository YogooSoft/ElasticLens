# ElasticLens - Système d'Inspection de Cluster Elasticsearch

<div align="center">

**Plateforme Web d'Interprétation Automatisée des Résultats d'Inspection de Cluster Elasticsearch**

![alt text](mian_web.png)

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18.2-61dafb.svg)](https://react.dev/)
[![Flask](https://img.shields.io/badge/flask-3.0-black.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Langues:** [English](../README.md) | [简体中文](README.zh.md) | [Deutsch](README.de.md) | [Русский](README.ru.md) | [日本語](README.ja.md)

</div>


---

## 📖 Introduction

ElasticLens est une **plateforme de visualisation et d'analyse** des résultats d'inspection de clusters Elasticsearch. Le système est conçu pour traiter les packages ZIP de diagnostic exportés depuis l'**outil de diagnostic officiel Elasticsearch**, analyser automatiquement les données de diagnostic, effectuer une analyse approfondie de la santé du cluster et générer des rapports d'inspection multidimensionnels (HTML / Word / JSON).

Cette plateforme aide le personnel d'exploitation à comprendre rapidement l'état de santé du cluster, découvrir les problèmes potentiels et recevoir des recommandations d'optimisation grâce à des affichages visuels intuitifs, éliminant ainsi le besoin d'analyser manuellement des données de diagnostic complexes.

**Outil de diagnostic officiel Elasticsearch**: [elastic/support-diagnostics](https://github.com/elastic/support-diagnostics/)

### ✨ Fonctionnalités Principales

- 🌐 **Plateforme Web** - Application Web full-stack basée sur React + Flask, supportant le glisser-déposer pour télécharger des packages de diagnostic
- 📊 **Rapports Multi-Formats** - Génération automatique de rapports d'inspection aux formats HTML et Word (.docx)
- 🔍 **Analyse Intelligente** - Analyse automatique des packages ZIP de diagnostic ES, extraction des métriques clés (santé du cluster, ressources des nœuds, détails des index, ILM, snapshots, sécurité, etc.)
- 🧠 **Analyse Approfondie** - Évaluation de la santé basée sur un moteur de règles, analyse des ressources et génération d'alertes
- 🎯 **Score de Santé** - Notation quantitative 0-100 pour afficher intuitivement les niveaux de santé du cluster
- 🔔 **Alertes Gradées** - Mécanisme d'alerte à trois niveaux/deux niveaux/un niveau (severity_level)
- ⚡ **Traitement Asynchrone** - Traitement asynchrone des tâches en arrière-plan, supportant le téléchargement de gros fichiers (2 Go) et les analyses longues
- 📈 **Visualisation** - Tableau de bord circulaire du score de santé, barres de progression, cartes et autres affichages visuels
- 📝 **Support Multilingue** - Support complet du chinois simplifié, chinois traditionnel, anglais, japonais, français, allemand, russe - sept langues, avec basculement automatique de l'interface et des rapports

### 🌍 Support Multilingue

Le système prend entièrement en charge l'internationalisation (i18n), offrant les 7 langues suivantes :

- 🇨🇳 **Chinois Simplifié (zh-CN)** - Langue par défaut
- 🇹🇼 **Chinois Traditionnel (zh-TW)** - Traduction complète
- 🇺🇸 **Anglais (en-US)** - Traduction complète
- 🇯🇵 **Japonais (ja-JP)** - Traduction complète
- 🇫🇷 **Français (fr-FR)** - Traduction complète
- 🇩🇪 **Allemand (de-DE)** - Traduction complète
- 🇷🇺 **Russe (ru-RU)** - Traduction complète

**Fonctionnalités :**
- ✅ Basculement dynamique de la langue de l'interface utilisateur frontend (page d'accueil, liste des tâches, rapports, téléchargement, historique, paramètres)
- ✅ Génération de rapports backend supportant plusieurs langues (format HTML + Word)
- ✅ Préférence de langue sauvegardée automatiquement, appliquée automatiquement lors de la prochaine visite
- ✅ Bibliothèque de composants Ant Design s'adaptant automatiquement aux multilingues
- ✅ Fonction de traduction intelligente gérant le contenu dynamique (par exemple "5 index" → "5インデックス" → "5 indices")
- ✅ Correspondance intelligente des messages dynamiques et mécanisme de repli de traduction automatique

**Utilisation :**
Cliquez sur le bouton de changement de langue à droite du titre de la page d'accueil et sélectionnez la langue souhaitée.

---

## 🏗️ Architecture du Système

```
┌─────────────────┐      API REST      ┌─────────────────┐
│   Frontend       │ ◄───────────────► │   Backend        │
│   (React)        │                    │   (Flask)        │
│                 │                    │                 │
│ - Téléchargement │                    │ - Gestion des    │
│   de Fichiers    │                    │   Tâches         │
│ - Suivi des      │                    │ - Traitement     │
│   Tâches         │                    │   Asynchrone     │
│ - Affichage des  │                    │ - Génération de  │
│   Rapports       │                    │   Rapports       │
│ - Historique     │                    │ - Gestion des    │
│                  │                    │   Fichiers       │
└─────────────────┘                    └────────┬────────
                                                │
                                                ▼
                                    ┌────────────────────┐
                                    │  Noyau es_insight    │
                                    │                     │
                                    │ - Extraction des    │
                                    │   Données de Diag.  │
                                    │ - Vérification du   │
                                    │   Moteur de Règles  │
                                    │ - Calcul du Score   │
                                    │   de Santé          │
                                    │ - Rapports HTML/    │
                                    │   Word              │
                                    └────────┬───────────┘
                                             │
                                             ▼
                                    ┌────────────────────┐
                                    │  Base de Données     │
                                    │  SQLite              │
                                    │                     │
                                    │ - Métadonnées des   │
                                    │   Tâches            │
                                    │ - Métadonnées des   │
                                    │   Rapports          │
                                    │ - Requêtes & Stat.  │
                                    └────────┬───────────┘
                                             │
                                             ▼
                                    ┌────────────────────┐
                                    │  Système de Fichiers │
                                    │                     │
                                    │ - ZIPs Téléchargés  │
                                    │ - Rapports JSON     │
                                    │ - Rapports HTML     │
                                    │ - Rapports Word     │
                                    └────────────────────┘
```

---

## 🚀 Démarrage Rapide

### Prérequis

- **Python**: 3.9+
- **Node.js**: 18+ (développement/build frontend)
- **npm**: 9+ (gestion des packages frontend)
- **Système d'Exploitation**: Windows 10+/Linux/macOS

### Méthode 1 : Plateforme Web (Recommandée)

#### 🐳 Déploiement Docker (Recommandé pour la Production)

Utilisez Docker Compose pour un déploiement en un clic des services frontend et backend :

```bash
# Exécuter dans le répertoire racine du projet
cd elasticlens

# Démarrer tous les services (frontend + backend)
./start.sh

# Ou exécuter manuellement
docker compose up -d
```

**URLs d'Accès :**
- Interface Frontend : http://localhost:8080
- API Backend : http://localhost:5001

**Avantages :**
- ✅ Pas besoin d'installer les environnements Python et Node.js
- ✅ Gère automatiquement toutes les dépendances
- ✅ Persistance des données (base de données, fichiers téléchargés, rapports)
- ✅ Contrôles de santé et redémarrage automatique
- ✅ Adapté au déploiement en environnement de production
- ✅ Supporte le déploiement hors ligne intranet

Pour un guide de déploiement détaillé, veuillez consulter : [Guide de Déploiement Docker Hors Ligne Intranet.md](内网离线Docker部署方案.md)

---

#### Déploiement Traditionnel (Développement Local)

##### 1. Installer les Dépendances Backend

```bash
cd backend
pip install -r requirements.txt
```

Les dépendances backend incluent :
- Flask 3.0.0 - Framework Web
- Flask-CORS 4.0.0 - Support cross-origin
- python-docx >= 1.0.0 - Génération de rapports Word
- loguru 0.7.2 - Gestion des logs
- weasyprint >= 60.0 - Rendu PDF (optionnel)
- SQLite3 - Base de données (intégré à Python, configuration zéro)

#### 2. Installer les Dépendances Frontend

```bash
cd frontend
npm install
```

Les dépendances frontend incluent :
- React 18.2 + TypeScript
- Ant Design 5.12 - Bibliothèque de composants UI
- Vite 5.0 - Outil de build
- Axios 1.6 - Client HTTP
- Zustand 4.4 - Gestion d'état
- Recharts 2.10 - Bibliothèque de graphiques

##### 3. Démarrer les Services

**Démarrer le Backend** (dans le répertoire racine du projet) :
```bash
cd backend
python app.py
```
Le service backend fonctionne sur `http://localhost:5000`

**Démarrer le Frontend** (dans le répertoire racine du projet) :
```bash
cd frontend
npm run dev
```
Le service frontend fonctionne sur `http://localhost:5173`

#### 4. Utiliser la Plateforme Web

1. Ouvrir le navigateur sur `http://localhost:5173`
2. Glisser-déposer ou cliquer pour télécharger le fichier ZIP de diagnostic ES
3. Attendre la fin de l'analyse asynchrone
4. Afficher le rapport d'inspection (affichage HTML)
5. Cliquer sur le bouton "Télécharger Word" pour exporter le rapport au format Word

### Méthode 2 : Outil en Ligne de Commande (CLI)

#### Installation

```bash
pip install -r requirements.txt
pip install -e .
```

#### Utilisation de Base

```bash
# Analyser le package de diagnostic et générer un rapport
es-insight data/local-diagnostics-*.zip

# Spécifier le répertoire de sortie
es-insight data/local-diagnostics-*.zip -o ./reports

# Spécifier le format de sortie
es-insight data/local-diagnostics-*.zip -f html,json

# Utiliser une configuration personnalisée
es-insight data/local-diagnostics-*.zip -c configs/checkpoints_thresholds_complete.yaml
```

#### Utiliser le Script Python

```bash
# Traiter le package ZIP de diagnostic en un clic
python process_diagnostic_zip.py

# Générer un rapport HTML
python generate_html_report.py data/local-diagnostics-*.zip
```

---

## 📁 Structure du Projet

```
Lecture des Points d'Inspection/
├── backend/                    # Service backend Flask
│   ├── app.py                  # Fichier de service principal (téléchargement de fichiers, gestion des tâches, API de génération de rapports)
│   ├── version.py              # Configuration de version (v1.0.9)
│   ├── db_server/              # Module de service de base de données
│   │   ├── __init__.py         # Initialisation du package
│   │   ├── database.py         # Initialisation de la base de données et gestion des connexions
│   │   └── models.py           # Encapsulation des opérations de modèle de données (TaskModel, ReportModel)
│   ├── es_insight.db           # Fichier de base de données SQLite (généré automatiquement)
│   ├── migrate_*.py            # Scripts de migration de données
│   ├── requirements.txt        # Dépendances backend
│   └── DEPLOYMENT.md           # Documentation de déploiement
│
├── frontend/                   # Application frontend React
│   ├── src/
│   │   ├── api/                # Encapsulation des interfaces API (instance Axios, intercepteurs)
│   │   ├── components/         # Composants communs (Upload, Task, Report)
│   │   ├── pages/              # Composants de page (Home, Report, History, Settings)
│   │   ├── store/              # Gestion d'état Zustand
│   │   ├── hooks/              # Hooks personnalisés (usePolling, useDownload)
│   │   ├── types/              # Définitions de type TypeScript
│   │   └── utils/              # Fonctions utilitaires
│   ├── .env.development        # Variables d'environnement de développement
│   ├── .env.production         # Variables d'environnement de production
│   ├── package.json
│   └── vite.config.ts          # Configuration Vite (proxy, plugins)
│
├── es_insight/                 # Moteur d'analyse principal
│   ├── parsers/                # Analyseurs de données
│   │   ├── health_parser.py    # Analyse de la santé du cluster
│   │   ├── nodes_parser.py     # Analyse des informations des nœuds
│   │   └── indices_parser.py   # Analyse des informations des index
│   ├── analyzers/              # Moteurs d'analyse
│   │   ├── health_engine.py    # Évaluation de la santé
│   │   └── resource_engine.py  # Analyse des ressources
│   ├── rules/                  # Moteur de règles
│   │   └── engine.py           # Vérification des seuils et génération d'alertes (50+ règles)
│   ├── models/                 # Modèles de données
│   ├── diagnostic_extractor.py # Extracteur de package ZIP de diagnostic
│   ├── parse_check_result.py   # Analyse des résultats de vérification (calcul du score de santé)
│   ├── report_generator.py     # Générateur de rapports multi-formats
│   ├── generate_html_report.py # Génération de rapport HTML
│   └── cli.py                  # Interface en ligne de commande
│
├── configs/                    # Fichiers de configuration
│   ├── checkpoints_thresholds_complete.yaml  # Configuration des seuils des points de contrôle (version complète)
│   ├── default_thresholds.yaml               # Seuils par défaut
│   ├── default_report.yaml                   # Configuration du rapport
│   └── Guide de Test.md
│
├── data/                       # Répertoire de données de test
├── uploads/                    # Fichiers ZIP téléchargés (mode Web)
├── out/                        # Sortie intermédiaire d'analyse
├── reports/                    # Fichiers de rapport générés
├── doc/                        # Répertoire de documentation
│   ├── Conception Frontend/    # Documents de conception frontend
│   └── Conception Backend/     # Documents de conception backend
└── tests/                      # Cas de test
```

---

## 📊 Aperçu des Points d'Inspection

Le système couvre **11 catégories principales** d'indicateurs d'inspection, comprenant **30+ vérifications spécifiques** :

| Catégorie | Poids | Points de Vérification |
|-----------|-------|------------------------|
| **Santé du Cluster** | 30% | État du cluster, ratio de shards actifs, shards non assignés, shards en initialisation, shards en relocation |
| **Ressources des Nœuds** | 25% | Utilisation du disque, utilisation du tas JVM, utilisation du CPU, charge système, shards par nœud |
| **Santé des Index** | 20% | Distribution de la santé des index, nombre d'index volumineux, index à nombre élevé de segments, index à nombre élevé de shards, index à nombre élevé de documents |
| **Vérifications des Shards** | 5% | Taille d'un shard unique, nombre de documents d'un shard unique, équilibre de la distribution des shards |
| **Vérifications de Récupération** | 5% | Nombre de shards en récupération, progression moyenne de la récupération |
| **Politique ILM** | 3% | Vérification de l'état ILM |
| **Vérification des Snapshots** | 3% | Configuration et état des snapshots |
| **Vérification de Sécurité** | 2% | Activation des fonctionnalités de sécurité X-Pack |
| **Modèles & Mappings** | 2% | Modèles d'index, modèles de composants, nombre moyen de champs |
| **Logs & Erreurs** | 2% | Nombre de GC, statistiques de temps GC |
| **Informations de Performance** | - | Total des documents du cluster, taille totale de stockage du cluster (affichage d'information, non inclus dans le score) |

---

## ⚙️ Configuration

### Configuration des Seuils

Le fichier de configuration des seuils principaux se trouve à `configs/checkpoints_thresholds_complete.yaml`, éléments de configuration principaux :

```yaml
# Santé du Cluster
cluster:
  status:
    green: none     # État VERT pas d'alerte
    yellow: warning # État JAUNE avertissement
    red: critical   # État ROUGE critique
  active_shards_percent:
    warning: 95     # En dessous de 95% avertissement
    critical: 90    # En dessous de 90% critique

# Ressources des Nœuds
node:
  disk_usage_percent:
    warning: 70     # Disque 70% attention
    alert: 80       # Disque 80% seuil
    critical: 85    # Disque 85% rejet d'écriture
  heap_used_percent:
    warning: 70     # JVM 70% attention
    critical: 85    # JVM 85% risque OOM

# Santé des Index
index:
  size_gb:
    warning: 50     # Index unique 50 Go attention
    critical: 100   # Index unique 100 Go critique
  docs_count:
    warning: 100000000    # 100M de documents attention
    critical: 500000000   # 500M de documents critique
```

### Calcul du Score de Santé

```python
Score = 100 - (Alertes Critiques × 20) - (Avertissements × 5) - (Infos × 1)
Plage de Score : 0-100
```

| Plage de Score | Niveau de Santé |
|----------------|-----------------|
| 90-100 | 🌟 Excellent |
| 75-89 | 👍 Bon |
| 60-74 | ⚠️ Moyen |
| 40-59 | 🔴 Faible |
| 0-39 | 🚨 Critique |

---

## 📄 Sortie des Rapports

### Rapport HTML

- Conception de thème dégradé violet
- Visualisation circulaire du score de santé
- Mise en page responsive en cartes
- Affichage gradé des informations d'alerte (Critical/Warning/Info)
- Tableau complet des détails des points de vérification

### Rapport Word (.docx)

- Format de mise en page professionnel
- Tableau des informations de base du cluster
- Évaluation et score de santé
- Détails des points de vérification (statut réussi/échoué, valeurs, seuils)
- Liste détaillée des alertes gradées
- Codage couleur (✅ Vert réussi, ❌ Rouge échoué)

### Rapport JSON

- Données structurées
- Inclut les détails complets des points de vérification `check_results`
- Pratique pour le développement secondaire et l'analyse de données

---

## 🔧 Points d'API

Le backend fournit les points d'API REST suivants :

### Gestion des Tâches

| Méthode | Point d'Accès | Description |
|---------|---------------|-------------|
| POST | `/api/v1/upload` | Télécharger le fichier ZIP de diagnostic, créer une tâche asynchrone |
| GET | `/api/v1/tasks` | Obtenir la liste des tâches (paginée, exclure supprimées) |
| GET | `/api/v1/tasks/<task_id>` | Obtenir les détails d'une tâche unique |
| DELETE | `/api/v1/tasks/<task_id>` | Suppression douce de la tâche (suppression en cascade des rapports) |

### Gestion des Rapports

| Méthode | Point d'Accès | Description |
|---------|---------------|-------------|
| GET | `/api/v1/reports` | Obtenir la liste des rapports (supporte le filtrage et la pagination) |
| GET | `/api/v1/reports/statistics` | Obtenir les statistiques des rapports |
| GET | `/api/v1/reports/<report_id>` | Obtenir les données JSON du rapport |
| GET | `/api/v1/reports/<report_id>/html` | Obtenir la chaîne de contenu du rapport HTML |
| GET | `/api/v1/reports/<report_id>/view` | Afficher directement le rapport HTML (iframe) |
| GET | `/api/v1/reports/<report_id>/download?format=word` | Télécharger le rapport Word |
| GET | `/api/v1/reports/<report_id>/download?format=json` | Télécharger le rapport JSON |
| GET | `/api/v1/reports/<report_id>/download?format=html` | Télécharger le rapport HTML |

### Points d'Accès Système

| Méthode | Point d'Accès | Description |
|---------|---------------|-------------|
| GET | `/api/v1/health` | Contrôle de santé (renvoie les informations de version) |

---

## 🧪 Tests

```bash
# Exécuter les tests unitaires
pytest tests/

# Exécuter un test spécifique
pytest tests/unit/test_health_parser.py

# Avec rapport de couverture
pytest --cov=es_insight --cov-report=html
```

---

## 📦 Liste des Dépendances

### Dépendances Principales Backend

| Package | Version | Usage |
|---------|---------|-------|
| Flask | 3.0.0 | Framework Web |
| Flask-CORS | 4.0.0 | Support cross-origin |
| Werkzeug | 3.0.1 | Boîte à outils WSGI |
| python-docx | >= 1.0.0 | Génération de rapports Word |
| click | 8.1.7 | Framework CLI |
| pyyaml | >= 6.0 | Analyse de configuration YAML |
| loguru | 0.7.2 | Gestion des logs |
| orjson | >= 3.6.0 | JSON haute performance |
| weasyprint | >= 60.0 | Rendu PDF (optionnel) |
| SQLite3 | Intégré Python | Stockage de base de données |

### Dépendances Principales Frontend

| Package | Version | Usage |
|---------|---------|-------|
| React | 18.2 | Framework UI |
| TypeScript | 5.2 | Système de types |
| Ant Design | 5.12 | Bibliothèque de composants UI |
| Vite | 4.x | Outil de build |
| Axios | 1.6 | Client HTTP |
| Zustand | 4.4 | Gestion d'état |
| React Router | 6.21 | Gestion des routes |
| Recharts | 2.10 | Bibliothèque de graphiques |
| Day.js | 1.11 | Gestion des dates |

---

## 🐛 Dépannage

### Problèmes Courants

#### 1. Échec de la Génération de Rapport Word
```bash
# Vérifier si python-docx est installé
pip install python-docx>=1.0.0
```

#### 2. Échec du Démarrage Frontend
```bash
# S'assurer que Node.js >= 18
node -v
npm -v

# Réinstaller les dépendances
cd frontend
rm -rf node_modules
npm install
```

#### 3. Port Backend Occupé
```bash
# Modifier le numéro de port dans backend/app.py
# Port par défaut : 5000
```

#### 4. Port Frontend Occupé
```bash
# Modifier le numéro de port dans frontend/vite.config.ts
# Port par défaut : 5173
```

#### 5. Problèmes de Chemin Chinois Windows
- python-docx peut avoir des problèmes de compatibilité avec les chemins chinois Windows
- Recommandé de placer le projet dans un chemin anglais

#### 6. Fichier de Base de Données Corrompu
```bash
# Supprimer le fichier de base de données, le redémarrage du service le reconstruira automatiquement
cd backend
rm es_insight.db
python app.py
```
**Note** : Cela perdra toutes les données historiques, veuillez opérer avec prudence !

#### 7. État de la Tâche Ne Se Met Pas à Jour
- Vérifier si le service backend fonctionne normalement (accéder à `http://localhost:5000/api/v1/health`)
- Vérifier la console du navigateur pour les erreurs réseau
- Confirmer que l'adresse API frontend est correcte (`.env.development`)

---

## 📚 Documentation

Pour une documentation détaillée, veuillez vérifier le répertoire `doc/` :

| Document | Description |
|----------|-------------|
| `doc/Conception Frontend/README.md` | Navigation de la documentation frontend |
| `doc/Conception Frontend/Plan de Conception Frontend.md` | Sélection technologique et conception architecturale frontend |
| `doc/Conception Frontend/Guide d'Implémentation Frontend.md` | Implémentation de code détaillée frontend |
| `doc/Conception Frontend/Conception du Service Backend.md` | Conception et déploiement de l'API Flask |
| `doc/Conception Frontend/Exigences Frontend.md` | Spécifications d'exigences détaillées |
| `configs/Guide de Test.md` | Cas de test et guide d'utilisation |

---

## 📜 Journal des Modifications

Voir [backend/CHANGELOG.md](backend/CHANGELOG.md) et [frontend/CHANGELOG.md](frontend/CHANGELOG.md) pour les détails

### v1.0.9 (2026-05-06)

- 🐳 **Ajout du Support de Déploiement Docker** : Implémentation de la solution de déploiement conteneurisé pour frontend et backend
  - Dockerfile Backend : Basé sur Python 3.11-slim, taille d'image optimisée (~567 Mo)
  - Dockerfile Frontend : Build multi-étapes, utilisant Nginx Alpine (~45 Mo)
  - docker-compose.yml : Orchestration de services, contrôles de santé, persistance des données
  - start.sh / stop.sh : Scripts de démarrage/arrêt en un clic, compatibles avec Docker Compose V1/V2
  - Solution de persistance des données améliorée : Montage de volume pour les répertoires uploads, out, reports, db
  - Ajout de la documentation de déploiement hors ligne intranet : Processus complet d'emballage, transfert, déploiement
  
- 🔧 **Optimisation de la Gestion des Dépendances** : Ajout des packages de dépendances Python manquants
  - Ajout de pandas>=1.3.0, numpy>=1.20.0, pyyaml>=6.0, jinja2>=3.0.0, orjson>=3.6.0
  
- 🐛 **Corrections de Bugs** :
  - Correction du problème de nom de package Debian Trixie
  - Correction des erreurs de compilation TypeScript (suppression des imports de composants Ant Design inutilisés)
  - Correction des conflits de montage de volume Docker

### v1.0.8 (2026-04-30)

- 🌍 **Ajout du Support d'Internationalisation Multilingue** : Le système prend entièrement en charge le français, l'allemand, le russe
  - Génération de rapports backend supportant le français (fr-FR), l'allemand (de-DE), le russe (ru-RU)
  - Ajout d'environ 1065 clés de traduction par lots (927 traductions statiques + 138 phrases dynamiques)
  - Fonction de traduction intelligente `translate_check_message()` améliorée, supporte 46 mappages de phrases courantes
  - Réduction du texte non traduit dans les rapports HTML de 99 à 34 (amélioration de 66%)

### v1.0.7 (2026-04-30)

- 🇯🇵 **Amélioration du Support d'Internationalisation Japonais** : Résolution complète des problèmes de traduction chinoise restants dans les rapports
  - Complément de 33 clés de traduction statiques manquantes dans `translations.py`
  - Correction des définitions dupliquées dans `translations_map` causant des traductions japonaises manquantes
  - Implémentation de la logique de traduction intelligente pour la valeur dynamique "inconnu"
  
- 📊 **Optimisation de la Configuration de Source de Données d'Index** : Amélioration de la précision et de la cohérence des données statistiques d'index
  - Remplacement de la source de données d'informations de base d'index de `indices.json` par `indices_stats.json` plus précis
  - Utilisation unifiée de `cat_shards.txt` comme source autoritaire pour les statistiques de nombre et de taille de shards

### v1.0.6 (2026-04-29)

- 🇯🇵 **Ajout du Support d'Internationalisation Japonais** : Le système prend entièrement en charge le japonais (ja-JP)
  - Génération de rapports backend supportant la traduction japonaise (HTML + Word)
  - Ajout d'environ 370 clés de traduction japonaises, couvrant tout le contenu des rapports
  - Interface utilisateur frontend supportant entièrement 4 langues (chinois simplifié, chinois traditionnel, anglais, japonais)
  
- 🐛 **Correction du Bug de Changement de Langue des Rapports Word** : Les rapports Word téléchargés après le changement de langue utilisent la langue actuelle
  - Différentes langues utilisent des noms de fichiers indépendants : `{report_id}_{lang}.docx`
  - Résolution du problème où les téléchargements utilisaient encore l'ancienne langue après le changement

### v1.0.5 (2026-04-27)

- 🔔 **Ajout du Système de Classification d'Alertes à Trois Niveaux** : Introduction du niveau de validation severity_level
  - 🔴 Alerte de Niveau 3 (Doit Être Traitée) : severity_level=3, problèmes très graves
  - 🟡 Alerte de Niveau 2 (Recommandé de Traiter) : severity_level=2, problèmes généraux
  - 🔵 Alerte de Niveau 1 (Suggestion d'Optimisation) : severity_level=1, problèmes non graves
  - Ajout de statistiques de nombre d'alertes par niveau dans les rapports de score de santé
  
- 📊 **Refactorisation de l'Affichage des Informations d'Alerte** : Changement de "Critique/Avertissement" deux niveaux à "Niveau 3/Niveau 2/Niveau 1" classification à trois niveaux
  - Informations d'alerte des rapports HTML et Word groupées et affichées par severity_level
  - La page de liste affiche les nombres d'alertes par niveau (level_1_count, level_2_count, level_3_count)

### v1.0.4 (2026-04-27)

- 📈 **Ajout de 5 Composants d'Analyse Avancés** : Ajout de fonctionnalités d'analyse approfondie dans les rapports HTML et Word
  - ⚠️ Alerte d'Accumulation de File d'Attente de Pool de Threads : Surveiller la taille de la file d'attente du pool de threads et le nombre de rejets
  - 🔥 Points Chauds de Distribution des Shards : Calculer l'indice de charge basé sur le nombre de shards, CPU%, disque%
  - 💾 Profil de Mémoire JVM : Afficher l'utilisation du tas JVM, mémoire tas utilisée/maximale pour chaque nœud
  - ⚙️ Détection de Dérive de Configuration : Comparer les paramètres de configuration clés entre les nœuds, détecter les incohérences
  - ✅ État d'Allocation des Shards : Détecter les shards non assignés et afficher les raisons d'échec

### v1.0.3 (2026-04-27)

- 🎯 **Ajout du Système de Notation Dimensionnelle Pondérée** : Introduction de 6 catégories de dimensions principales et mécanisme de pondération
  - Santé du Cluster (25%), Performance des Nœuds (25%), État des Index (20%)
  - Métriques de Performance (15%), Configuration de Sécurité (10%), État Opérationnel (5%)
  - Ajout de l'algorithme d'interpolation linéaire de seuil à trois niveaux : Support de la notation de degré, distinguer les problèmes mineurs des problèmes graves
  - Ajout de 4 fichiers de configuration : dimension_weights.yaml, indicator_weights.yaml, etc.
  
- 🐛 **Correction des Problèmes de Logique de Notation** :
  - Correction de l'erreur de traitement de valeur de type dictionnaire
  - Correction du problème d'analyse de configuration de poids dimensionnel
  - Correction de l'incohérence entre les scores de la page de liste et de la page de rapport

### v1.0.2 (2026-04-22)

- 💾 **Implémentation du Stockage Persistant des Rapports d'Inspection** (Base de Données SQLite)
  - Création du module `backend/db_server/`, incluant la gestion de base de données et les modèles de données
  - Implémentation des tables tasks et reports, supportant la gestion complète du cycle de vie des tâches et des rapports
  - Ajout de l'interface de requête de liste de rapports, supportant le filtrage par nom de cluster et score de santé
  - Ajout de l'interface de statistiques de rapports, fournissant le nombre total de rapports, le score de santé moyen et autres données statistiques
  
- 📄 **Fonctionnalité de Téléchargement de Rapport au Format Word**
  - Support de l'exportation des rapports d'inspection au format Microsoft Word (.docx)
  - Stratégie de génération paresseuse adoptée : Générer et mettre en cache à partir des données JSON lors de la première requête

---

## 🤝 Contribution

Bienvenue pour soumettre des Issues et des Pull Requests !

### Standards de Code

```bash
# Formatage du code backend
black es_insight/ backend/

# Vérification du code frontend
cd frontend
npm run lint
```

---

## 📄 Licence

Licence MIT

---

## 👥 Mainteneurs

Équipe ElasticLens

---

## 📞 Contact

Pour toute question ou suggestion, veuillez contacter via :

- **Issues** : GitHub Issues
- **Email** : support@yogoo.net

---

<div align="center">

**Si ce projet vous aide, veuillez lui donner une ⭐ Étoile !**

Créé avec ❤️ par l'Équipe ElasticLens

**Version Actuelle** : v1.0.9 | **Dernière Mise à Jour** : 2026-05-06

## Affichage de l'Interface des Rapports

![alt text](report_1.png)

![alt text](report_2.png)

![alt text](report_3.png)

![alt text](report_4.png)
</div>
