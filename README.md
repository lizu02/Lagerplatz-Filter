Lagerplatz-Finder Baselland

Hackathon GeoProg 2 (FHNW) - Mai 2026

Projektziel:
Interaktives Tool zur Findung idealer Lagerplatzflächen in Baselland mit räumlicher Analyse von Infrastrukturen in der Nähe. Die Anwendung filtert Lagerplatzflächen basierend auf räumlichen Kriterien und visualisiert diese interaktiv auf einer Karte.

Installationsanleitung:
conda create -n lagerplatz-finder python=3.10
conda activate lagerplatz-finder
pip install -r requirements.txt

Dateistruktur:
Stelle sicher, dass folgende Dateistruktur vorhanden ist:

output/
├── geeignete_lagerflaechen_BL.geojson
├── hydranten.geojson
├── bauernhoefe.geojson
└── oev_haltestellen.geojson

App starten:
streamlit run 3_streamlit_app.py
Die Anwendung öffnet sich automatisch unter http://localhost:8501

Funktionalität:
Die Anwendung ermöglicht folgende Filter:

Personenanzahl: <50, 50-100, >100 Personen
Bauernhöfe: 0-3000m Distanz
ÖV-Haltestellen: 0-3000m Distanz
Hydranten: 0-3000m Distanz

Nur Lagerplatzflächen innerhalb aller definierten/gefilterten Puffer werden angezeigt.

Kartendarstellung:
Mehrere Grundlagekarten und Darstellungsarten (Höhenlinien, Satellit, Hell, Standard)
Farbcodierung der Flächen: Wiesen (hellgrün), Wald (dunkelgrün)
Symbole für Infrastruktur: Hydranten (blau), Bauernhöfe (orange), ÖV-Haltestellen (rot)
Live-Statistiken mit gefilterten Flächen und Anzahl Gesamtflächen

Bibliotheken:
Streamlit, GeoPandas, Folium, Pandas, NumPy, SciPy, Shapely

Team:
Quirin, Elias, Silvan, Cédric, Livio

Pitch (Powerpoint) präsentiert am: 27.05.2026
