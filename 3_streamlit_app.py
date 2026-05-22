import streamlit as st
import geopandas as gpd
import folium
from pathlib import Path
import json
import tempfile
import os
import warnings
from scipy.spatial.distance import cdist
import numpy as np

# Supprimiere alle Warnungen
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Lagerplatz-Finder", layout="wide")

# CSS - Mit fixiertem Header
st.markdown("""
    <style>
    /* Fixierter Header über gesamte Breite */
    .header-fixed {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 999;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px 40px;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
        width: 100%;
        text-align: center;
    }
    
    .header-fixed h1 { color: white; margin: 0 0 8px 0; font-size: 36px; }
    .header-fixed p { color: rgba(255, 255, 255, 0.95); margin: 0; font-size: 14px; }
    
    /* Content nach unten schieben */
    [data-testid="stAppViewContainer"] {
        margin-top: 140px;
    }
    
    .leaflet-control-layers { display: none !important; }
    .leaflet-control-layers-toggle { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

# ========================================================================
# LOAD DATA
# ========================================================================
@st.cache_data
def load_data():
    path = "output/geeignete_lagerflaechen_BL.geojson"
    if Path(path).exists():
        gdf = gpd.read_file(path)
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")
        gdf['geometry'] = gdf.geometry.simplify(tolerance=0.00005)
        return gdf
    return None

@st.cache_data
def load_infrastruktur():
    """Lade Hydranten, Bauernhöfe und ÖV-Haltestellen"""
    infra = {}
    
    # Hydranten
    hydranten_path = "output/hydranten.geojson"
    if Path(hydranten_path).exists():
        gdf_hydrant = gpd.read_file(hydranten_path)
        if gdf_hydrant.crs is None:
            gdf_hydrant = gdf_hydrant.set_crs("EPSG:2056")
        if gdf_hydrant.crs != "EPSG:4326":
            gdf_hydrant = gdf_hydrant.to_crs("EPSG:4326")
        infra['hydranten'] = gdf_hydrant
    else:
        infra['hydranten'] = None
    
    # Bauernhöfe
    bauernhof_path = "output/bauernhoefe.geojson"
    if Path(bauernhof_path).exists():
        gdf_bauernhof = gpd.read_file(bauernhof_path)
        if gdf_bauernhof.crs is None:
            gdf_bauernhof = gdf_bauernhof.set_crs("EPSG:2056")
        if gdf_bauernhof.crs != "EPSG:4326":
            gdf_bauernhof = gdf_bauernhof.to_crs("EPSG:4326")
        infra['bauernhoefe'] = gdf_bauernhof
    else:
        infra['bauernhoefe'] = None
    
    # ÖV-Haltestellen
    oev_path = "output/oev_haltestellen.geojson"
    if Path(oev_path).exists():
        gdf_oev = gpd.read_file(oev_path)
        if gdf_oev.crs is None:
            gdf_oev = gdf_oev.set_crs("EPSG:2056")
        if gdf_oev.crs != "EPSG:4326":
            gdf_oev = gdf_oev.to_crs("EPSG:4326")
        infra['oev'] = gdf_oev
    else:
        infra['oev'] = None
    
    return infra

def apply_buffer_filters(gdf, infra, dist_hydrant, dist_bauernhof, dist_oev):
    """Schneide Lagerflächen mit Buffer-Kreisen um Infrastruktur-Punkte"""
    if len(gdf) == 0:
        return gdf
    
    gdf_result = gdf.copy()
    
    # ========== HYDRANTEN BUFFER ==========
    if infra['hydranten'] is not None and len(infra['hydranten']) > 0 and dist_hydrant > 0:
        # Konvertiere zu LV95 für korrekte Puffer-Berechnung
        gdf_hydrant_lv95 = infra['hydranten'].to_crs("EPSG:2056")
        gdf_result_lv95 = gdf_result.to_crs("EPSG:2056")
        
        # Erstelle Buffer um alle Hydranten
        hydrant_buffer = gdf_hydrant_lv95.geometry.buffer(dist_hydrant).unary_union
        
        # Schneide Flächen mit Buffer
        gdf_result_lv95['geometry'] = gdf_result_lv95.geometry.intersection(hydrant_buffer)
        gdf_result = gdf_result_lv95.to_crs("EPSG:4326")
        gdf_result = gdf_result[~gdf_result.geometry.is_empty]
    
    # ========== BAUERNHÖFE BUFFER ==========
    if infra['bauernhoefe'] is not None and len(infra['bauernhoefe']) > 0 and dist_bauernhof > 0:
        # Konvertiere zu LV95
        gdf_bauernhof_lv95 = infra['bauernhoefe'].to_crs("EPSG:2056")
        gdf_result_lv95 = gdf_result.to_crs("EPSG:2056")
        
        # Erstelle Buffer um Centroide aller Bauernhöfe
        bauernhof_centroids = gdf_bauernhof_lv95.geometry.centroid
        bauernhof_buffer = bauernhof_centroids.buffer(dist_bauernhof).unary_union
        
        # Schneide Flächen mit Buffer
        gdf_result_lv95['geometry'] = gdf_result_lv95.geometry.intersection(bauernhof_buffer)
        gdf_result = gdf_result_lv95.to_crs("EPSG:4326")
        gdf_result = gdf_result[~gdf_result.geometry.is_empty]
    
    # ========== ÖV BUFFER ==========
    if infra['oev'] is not None and len(infra['oev']) > 0 and dist_oev > 0:
        # Konvertiere zu LV95
        gdf_oev_lv95 = infra['oev'].to_crs("EPSG:2056")
        gdf_result_lv95 = gdf_result.to_crs("EPSG:2056")
        
        # Erstelle Buffer um alle ÖV-Haltestellen
        oev_buffer = gdf_oev_lv95.geometry.buffer(dist_oev).unary_union
        
        # Schneide Flächen mit Buffer
        gdf_result_lv95['geometry'] = gdf_result_lv95.geometry.intersection(oev_buffer)
        gdf_result = gdf_result_lv95.to_crs("EPSG:4326")
        gdf_result = gdf_result[~gdf_result.geometry.is_empty]
    
    return gdf_result

# ========================================================================
# CREATE MAP
# ========================================================================
def create_map(gdf_filtered, basemap_type="Höhenlinien", 
               gdf_hydrants_all=None, gdf_bauernhof_all=None, gdf_oev_all=None,
               dist_hydrant=500, dist_bauernhof=1000, dist_oev=1000):
    if len(gdf_filtered) == 0:
        return None
    
    bounds = gdf_filtered.total_bounds
    center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
    
    # Verschiedene Kartentypen
    if basemap_type == "Höhenlinien":
        tiles = "OpenTopoMap"
    elif basemap_type == "Satellit":
        tiles = "Esri.WorldImagery"
    elif basemap_type == "Hell":
        tiles = "CartoDB positron"
    else:
        tiles = "OpenStreetMap"
    
    m = folium.Map(location=center, zoom_start=10, tiles=tiles, prefer_canvas=False)
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]], padding=(50, 50))
    
    geojson = json.loads(gdf_filtered.to_json())
    
    def style_func(feature):
        landuse = feature['properties'].get('landuse', 'other')
        return {
            'fillColor': '#2d5016' if landuse == 'forest' else '#90EE90',
            'color': '#1a3009' if landuse == 'forest' else '#228B22',
            'weight': 1, 'opacity': 0.9, 'fillOpacity': 0.65
        }
    
    folium.GeoJson(geojson, style_function=style_func).add_to(m)
    
    # Buffer-Kreise um die Distanzen zeichnen - UNSICHTBAR (nur für Logik)
    # Hydranten Buffer
    if gdf_hydrants_all is not None and len(gdf_hydrants_all) > 0 and dist_hydrant > 0:
        for idx, row in gdf_hydrants_all.iterrows():
            try:
                geom = row.geometry
                if geom.geom_type == 'Point':
                    # Hydrant Punkt (SICHTBAR)
                    folium.CircleMarker(
                        location=[geom.y, geom.x],
                        radius=4,
                        popup='Hydrant',
                        color='#0284c7',
                        fill=True,
                        fillColor='#0284c7',
                        fillOpacity=0.8,
                        weight=1,
                        tooltip='Hydrant',
                        zIndex=1000
                    ).add_to(m)
            except:
                continue
    
    # Bauernhöfe Centroid (SICHTBAR)
    if gdf_bauernhof_all is not None and len(gdf_bauernhof_all) > 0:
        gdf_bauernhof_centroid = gdf_bauernhof_all.copy()
        gdf_bauernhof_centroid['geometry'] = gdf_bauernhof_centroid.geometry.centroid
        for idx, row in gdf_bauernhof_centroid.iterrows():
            try:
                geom = row.geometry
                if geom.geom_type == 'Point':
                    # Bauernhof Punkt (SICHTBAR)
                    folium.CircleMarker(
                        location=[geom.y, geom.x],
                        radius=3,
                        popup='Bauernhof',
                        color='#d97706',
                        fill=True,
                        fillColor='#d97706',
                        fillOpacity=0.8,
                        weight=1,
                        tooltip='Bauernhof',
                        zIndex=1000
                    ).add_to(m)
            except:
                continue
    
    # ÖV-HALTESTELLEN (SICHTBAR)
    if gdf_oev_all is not None and len(gdf_oev_all) > 0:
        for idx, row in gdf_oev_all.iterrows():
            try:
                geom = row.geometry
                if geom.geom_type == 'Point':
                    # ÖV Punkt (SICHTBAR)
                    folium.RegularPolygonMarker(
                        location=[geom.y, geom.x],
                        fill_color='#ef4444',
                        number_of_sides=3,
                        radius=3,
                        rotation=0,
                        popup=row.get('name', 'ÖV-Haltestelle'),
                        color='#ef4444',
                        fill_opacity=0.8,
                        weight=1,
                        tooltip='ÖV-Haltestelle'
                    ).add_to(m)
            except:
                continue
    
    return m

# ========================================================================
# MAIN APP
# ========================================================================

# Header
st.markdown("""
    <div class="header-fixed">
        <h1>Lagerplatz-Finder</h1>
        <p>Finde ideale Lagerflächen in Baselland</p>
    </div>
    """, unsafe_allow_html=True)

# Load data
gdf = load_data()
if gdf is None:
    st.error("Datei nicht gefunden: output/geeignete_lagerflaechen_BL.geojson")
    st.stop()

infra = load_infrastruktur()

# Sidebar
with st.sidebar:
    st.subheader("Filter")
    
    person_category = st.radio("Personenanzahl", ["< 50 Personen", "50-100 Personen", "> 100 Personen"])
    min_flaeche_ha = {"< 50 Personen": 0.5, "50-100 Personen": 1.0, "> 100 Personen": 2.0}[person_category]
    
    dist_bauernhof = st.slider("Bauernhöfe (m)", 0, 3000, 1000, 100)
    dist_oev = st.slider("ÖV-Haltestellen (m)", 0, 3000, 1000, 100)
    dist_hydrant = st.slider("Hydrant (m)", 0, 3000, 500, 100)
    
    # Kartentyp auswählen
    st.divider()
    basemap_type = st.radio("Kartentyp", ["Höhenlinien", "Satellit", "Hell", "Standard"], horizontal=True)
    
    # Filter - Basis
    gdf_filtered = gdf[
        (gdf["dist_bauernhof_m"] <= dist_bauernhof) &
        (gdf["dist_oev_m"] <= dist_oev) &
        (gdf["flaeche_ha"] >= min_flaeche_ha) &
        (gdf["dist_hydrant_m"] <= dist_hydrant)
    ]
    
    # Wende Buffer-Filterung an
    gdf_filtered = apply_buffer_filters(gdf_filtered, infra, dist_hydrant, dist_bauernhof, dist_oev)
    
    # Stats
    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("Gefiltert", len(gdf_filtered))
    col2.metric("Gesamt", len(gdf))
    col3.metric("Anteil", f"{(len(gdf_filtered) / len(gdf) * 100):.0f}%")

# Main content
if len(gdf_filtered) > 0:
    m = create_map(gdf_filtered, basemap_type, 
                   infra['hydranten'], infra['bauernhoefe'], infra['oev'],
                   dist_hydrant, dist_bauernhof, dist_oev)
    if m:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            m.save(tmp.name)
            tmp_path = tmp.name
        
        with open(tmp_path, 'r', encoding='utf-8') as f:
            st.components.v1.html(f.read(), height=600, scrolling=True)
        
        try:
            os.unlink(tmp_path)
        except:
            pass
    
    # Titel UNTER der Karte
    st.subheader(f"Karte ({len(gdf_filtered)} Lagerflächen)")
    st.info("Grün = Wiese | Dunkelgrün = Wald | 🔵 Blau = Hydranten | 🟠 = Bauernhöfe (Zentrum) | 🔺 = ÖV-Haltestellen")
else:
    st.error("Keine Lagerflächen mit diesen Filtern gefunden")