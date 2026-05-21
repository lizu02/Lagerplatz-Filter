import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from pathlib import Path
import warnings
import json

warnings.filterwarnings("ignore")

# ========================================================================
# CONFIG
# ========================================================================
st.set_page_config(
    page_title="Lagerplatz-Finder",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS für modernes Design
st.markdown("""
    <style>
    * {
        box-sizing: border-box;
    }
    
    html, body {
        font-size: 14px;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a8c 100%);
        width: 320px !important;
    }
    
    [data-testid="stSidebarNav"] {
        background: transparent;
    }
    
    .main {
        background: linear-gradient(to bottom, #f8fafc 0%, #e8eef5 100%);
        padding: 20px;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background: transparent;
    }
    
    [data-testid="stSidebar"] .css-1d391kg {
        color: white;
    }
    
    /* Alle Sidebar-Texte weiß machen */
    [data-testid="stSidebar"] {
        color: white !important;
    }
    
    [data-testid="stSidebar"] span {
        color: white !important;
    }
    
    [data-testid="stSidebar"] label {
        color: white !important;
    }
    
    [data-testid="stSidebar"] p {
        color: white !important;
    }
    
    [data-testid="stSidebar"] div {
        color: white !important;
    }
    
    [role="slider"] {
        accent-color: #4db8ff !important;
    }
    
    h1, h2, h3 {
        color: #1e3a5f;
        font-weight: 700;
        line-height: 1.3;
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: white !important;
    }
    
    h2 {
        font-size: 24px;
        margin: 20px 0 16px 0;
    }
    
    p {
        line-height: 1.5;
    }
    
    .sidebar-title {
        color: white;
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 20px;
        padding: 10px 0;
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        color: white;
        border-left: 3px solid #4db8ff;
    }
    
    .filter-label {
        color: white;
        font-weight: 600;
        font-size: 13px;
        margin-top: 16px;
        margin-bottom: 8px;
        display: block;
        letter-spacing: 0.5px;
    }
    
    .value-display {
        background: rgba(255, 255, 255, 0.15);
        color: white;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 12px;
        margin-top: 6px;
        font-weight: 500;
        text-align: center;
    }
    
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.08);
        padding: 16px;
        border-radius: 8px;
        border-left: 3px solid #4db8ff;
        min-height: 80px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    [data-testid="stMetric"] label {
        color: white !important;
        font-size: 11px !important;
        margin-bottom: 8px;
    }
    
    [data-testid="stMetric"] > div:last-child {
        color: white !important;
        font-size: 28px !important;
        font-weight: 700 !important;
        word-break: break-word;
        overflow-wrap: break-word;
    }
    
    /* Input Elemente in Sidebar */
    [data-testid="stSidebar"] input {
        color: white !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stSlider"] {
        color: white !important;
    }
    
    /* Slider Farbe */
    input[type="range"] {
        accent-color: #4db8ff !important;
    }
    
    .main-container {
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 20px 0;
    }
    
    .title-section {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a8c 100%);
        padding: 24px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(30, 58, 95, 0.3);
    }
    
    .title-section h1 {
        color: white;
        margin: 0;
        font-size: 28px;
        line-height: 1.2;
    }
    
    .title-section p {
        color: rgba(255, 255, 255, 0.9);
        margin: 8px 0 0 0;
        font-size: 13px;
    }
    
    .info-bar {
        background: linear-gradient(to right, #e0f2fe, #f0f9ff);
        border-left: 4px solid #0284c7;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 16px 0;
        color: #0c4a6e;
        font-size: 14px;
        font-weight: 500;
    }
    
    [data-testid="stSlider"] {
        margin: 12px 0;
    }
    
    [role="slider"] {
        accent-color: #0284c7;
    }
    
    footer {
        text-align: center;
        padding: 20px;
        color: #94a3b8;
        font-size: 12px;
        border-top: 1px solid #e2e8f0;
        margin-top: 40px;
    }
    
    .map-container {
        background: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 16px 0;
    }
    
    /* Fix für st_folium Rendering */
    iframe {
        border: none;
        border-radius: 8px;
    }
    
    @media (max-width: 1200px) {
        [data-testid="stSidebar"] {
            width: 280px !important;
        }
        
        .title-section {
            padding: 20px;
        }
        
        .title-section h1 {
            font-size: 24px;
        }
        
        .title-section p {
            font-size: 12px;
        }
        
        h2 {
            font-size: 20px;
        }
    }
    
    @media (max-width: 768px) {
        [data-testid="stSidebar"] {
            width: 100% !important;
        }
        
        .title-section h1 {
            font-size: 22px;
        }
        
        h2 {
            font-size: 18px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# ========================================================================
# LOAD & CACHE DATA
# ========================================================================
@st.cache_data
def load_data():
    """Lade Daten mit Geometrie-Simplification"""
    paths = [
        "output/geeignete_lagerflaechen_BL.geojson",
        "./output/geeignete_lagerflaechen_BL.geojson",
        "geeignete_lagerflaechen_BL.geojson",
    ]
    
    for path in paths:
        if Path(path).exists():
            try:
                gdf = gpd.read_file(path)
                
                if gdf.crs != "EPSG:4326":
                    gdf = gdf.to_crs("EPSG:4326")
                
                # Reduziere Simplification für mehr Details
                # Statt 0.0005 (sehr aggressiv) nutze 0.00005 (minimal)
                gdf['geometry'] = gdf.geometry.simplify(tolerance=0.00005)
                
                return gdf, path
            except Exception as e:
                st.error(f"Fehler beim Laden: {e}")
                return None, None
    
    return None, None

# ========================================================================
# CREATE MAP - Vereinfacht für bessere Stabilität
# ========================================================================
def create_map_with_hydrants(gdf_lagerflaechen, gdf_hydrants=None):
    """Erstelle Karte mit Lagerflaechen und Hydranten"""
    if gdf_lagerflaechen is None or len(gdf_lagerflaechen) == 0:
        return None
    
    bounds = gdf_lagerflaechen.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles="OpenStreetMap",
        prefer_canvas=False,  # Wichtig: Canvas deaktivieren für bessere Stabilität
        max_bounds=True
    )
    
    # Fit Bounds
    sw = [bounds[1], bounds[0]]
    ne = [bounds[3], bounds[2]]
    m.fit_bounds([sw, ne], padding=(50, 50))
    
    # Geojson für Lagerflächen
    geojson_data = json.loads(gdf_lagerflaechen.to_json())
    
    def style_function(feature):
        landuse = feature['properties'].get('landuse', 'other')
        if landuse == 'forest':
            return {
                'fillColor': '#2d5016',
                'color': '#1a3009',
                'weight': 1,
                'opacity': 0.9,
                'fillOpacity': 0.65
            }
        else:
            return {
                'fillColor': '#90EE90',
                'color': '#228B22',
                'weight': 1,
                'opacity': 0.9,
                'fillOpacity': 0.65
            }
    
    folium.GeoJson(
        geojson_data,
        style_function=style_function,
        popup=folium.GeoJsonPopup(fields=['lagerplatz_id', 'flaeche_ha', 'landuse', 'bewertung']),
        tooltip=folium.GeoJsonTooltip(fields=['lagerplatz_id', 'landuse'])
    ).add_to(m)
    
    # Hydranten hinzufügen
    if gdf_hydrants is not None and len(gdf_hydrants) > 0:
        for idx, row in gdf_hydrants.iterrows():
            try:
                geom = row.geometry
                if geom.geom_type == 'Point':
                    folium.CircleMarker(
                        location=[geom.y, geom.x],
                        radius=6,
                        popup='Hydrant',
                        color='#0284c7',
                        fill=True,
                        fillColor='#0284c7',
                        fillOpacity=0.8,
                        weight=2,
                        tooltip='Hydrant'
                    ).add_to(m)
            except:
                continue
    
    folium.LayerControl(collapsed=False, position='topright').add_to(m)
    return m

# ========================================================================
# MAIN
# ========================================================================

# Header
st.markdown("""
    <div class="title-section">
        <h1>Lagerplatz-Finder</h1>
        <p>Finde ideale Lagerflächen in Baselland basierend auf Infrastruktur-Nähe</p>
    </div>
    """, unsafe_allow_html=True)

# Lade Daten
with st.spinner("Lade Daten..."):
    gdf, path = load_data()

if gdf is None:
    st.error("Datei nicht gefunden!")
    st.info("Erwartete Pfade: output/geeignete_lagerflaechen_BL.geojson")
    import sys
    sys.exit()

# ========================================================================
# SIDEBAR - FILTER
# ========================================================================
with st.sidebar:
    st.markdown('<div class="sidebar-title">Filter</div>', unsafe_allow_html=True)
    
    has_dist_cols = "dist_bauernhof_m" in gdf.columns and "dist_oev_m" in gdf.columns
    has_hydrant = "dist_hydrant_m" in gdf.columns
    has_flaeche = "flaeche_m2" in gdf.columns
    
    # Personenanzahl-Filter
    st.markdown('<span class="filter-label">Personenanzahl</span>', unsafe_allow_html=True)
    person_category = st.radio(
        "Personenanzahl",
        options=["< 50 Personen", "50-100 Personen", "> 100 Personen"],
        label_visibility="collapsed"
    )
    
    # Feste Flächenwerte pro Kategorie
    if person_category == "< 50 Personen":
        person_label = "< 50 Personen"
        min_flaeche_ha = 0.5  # 5.000 m²
    elif person_category == "50-100 Personen":
        person_label = "50-100 Personen"
        min_flaeche_ha = 1.0  # 10.000 m²
    else:  # > 100 Personen
        person_label = "> 100 Personen"
        min_flaeche_ha = 2.0  # 20.000 m²
    
    min_flaeche_m2 = min_flaeche_ha * 10000
    
    st.markdown(f'<div class="value-display">{person_label}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="value-display" style="background: rgba(76, 175, 80, 0.3); border-left-color: #4CAF50;">Mindestfläche: {min_flaeche_ha:.1f} ha</div>', unsafe_allow_html=True)
    
    if has_dist_cols:
        st.markdown('<span class="filter-label">Bauernhöfe (m)</span>', unsafe_allow_html=True)
        dist_bauernhof = st.slider(
            "Bauernhöfe",
            min_value=0,
            max_value=3000,
            value=1000,
            step=100,
            label_visibility="collapsed"
        )
        st.markdown(f'<div class="value-display">Aktuell: {dist_bauernhof:,} m</div>', unsafe_allow_html=True)
        
        st.markdown('<span class="filter-label">ÖV-Haltestellen (m)</span>', unsafe_allow_html=True)
        dist_oev = st.slider(
            "ÖV-Haltestellen",
            min_value=0,
            max_value=5000,
            value=1000,
            step=100,
            label_visibility="collapsed"
        )
        st.markdown(f'<div class="value-display">Aktuell: {dist_oev:,} m</div>', unsafe_allow_html=True)
        
        if has_hydrant:
            st.markdown('<span class="filter-label">Hydrant (m)</span>', unsafe_allow_html=True)
            dist_hydrant = st.slider(
                "Hydrant",
                min_value=0,
                max_value=3000,
                value=500,
                step=100,
                label_visibility="collapsed"
            )
            st.markdown(f'<div class="value-display">Aktuell: {dist_hydrant:,} m</div>', unsafe_allow_html=True)
        
        # Filter anwenden - KORREKT mit allen Bedingungen
        gdf_filtered = gdf.copy()
        
        # Distanz-Filter
        gdf_filtered = gdf_filtered[
            (gdf_filtered["dist_bauernhof_m"] <= dist_bauernhof)
            & (gdf_filtered["dist_oev_m"] <= dist_oev)
        ]
        
        # Hydrant-Filter
        if has_hydrant:
            gdf_filtered = gdf_filtered[gdf_filtered["dist_hydrant_m"] <= dist_hydrant]
        
        # Flächen-Filter - mit HEKTAR!
        if "flaeche_ha" in gdf_filtered.columns:
            gdf_filtered = gdf_filtered[gdf_filtered["flaeche_ha"] >= min_flaeche_ha]
        
        gdf_hydrants = None
        if has_hydrant and len(gdf_filtered) > 0:
            gdf_with_hydrants = gdf_filtered[gdf_filtered["nahe_hydrant"] == True].copy()
            if len(gdf_with_hydrants) > 0:
                gdf_hydrants = gdf_with_hydrants.copy()
                gdf_hydrants['geometry'] = gdf_hydrants.geometry.centroid
    else:
        st.warning("Distanz-Spalten nicht vorhanden")
        gdf_filtered = gdf.copy()
        if "flaeche_ha" in gdf_filtered.columns:
            gdf_filtered = gdf_filtered[gdf_filtered["flaeche_ha"] >= min_flaeche_ha]
        gdf_hydrants = None
    
    st.markdown("---")
    st.markdown('<div class="filter-label">Ergebnisse</div>', unsafe_allow_html=True)
    
    # Berechne Werte
    gefiltert = len(gdf_filtered)
    gesamt = len(gdf)
    anteil = (gefiltert / gesamt) * 100
    
    # Custom HTML statt st.metric (bessere Kontrolle)
    st.markdown(f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px;">
            <div style="background: rgba(255, 255, 255, 0.08); padding: 16px; border-radius: 8px; border-left: 3px solid #4db8ff; text-align: center;">
                <div style="color: rgba(255, 255, 255, 0.7); font-size: 11px; margin-bottom: 8px;">Gefiltert</div>
                <div style="color: white; font-size: 32px; font-weight: 700;">{gefiltert}</div>
            </div>
            <div style="background: rgba(255, 255, 255, 0.08); padding: 16px; border-radius: 8px; border-left: 3px solid #4db8ff; text-align: center;">
                <div style="color: rgba(255, 255, 255, 0.7); font-size: 11px; margin-bottom: 8px;">Gesamt</div>
                <div style="color: white; font-size: 32px; font-weight: 700;">{gesamt}</div>
            </div>
            <div style="background: rgba(255, 255, 255, 0.08); padding: 16px; border-radius: 8px; border-left: 3px solid #4db8ff; text-align: center;">
                <div style="color: rgba(255, 255, 255, 0.7); font-size: 11px; margin-bottom: 8px;">Anteil</div>
                <div style="color: white; font-size: 32px; font-weight: 700;">{anteil:.0f}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ========================================================================
# MAIN CONTENT
# ========================================================================

st.markdown(f"""
    <div class="info-bar">
        <strong>{len(gdf_filtered):,} Lagerflächen</strong> entsprechen den gewählten Kriterien
    </div>
    """, unsafe_allow_html=True)

if len(gdf_filtered) > 0:
    st.markdown(f'<h2>Karte ({len(gdf_filtered):,} Lagerflächen)</h2>', unsafe_allow_html=True)
    
    with st.spinner("Erstelle Karte..."):
        m = create_map_with_hydrants(gdf_filtered, gdf_hydrants)
        if m:
            # Verwende st_folium mit Workaround
            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            map_data = st_folium(m, width=1400, height=600)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("")
            
            st.markdown("""
                <div style="background: #f0f9ff; padding: 12px 16px; border-radius: 8px; border-left: 4px solid #0284c7;">
                    <p style="margin: 0; font-size: 13px; color: #0c4a6e;"><strong>Legende:</strong></p>
                    <p style="margin: 6px 0; font-size: 12px; color: #0c4a6e;">Grün = Wiese | Dunkelgrün = Wald | Blaue Kreise = Hydrant</p>
                </div>
                """, unsafe_allow_html=True)
else:
    st.error("Keine Lagerflächen mit diesen Filtern gefunden")

st.markdown("""
    <footer>
        <strong>Lagerplatz-Finder</strong> | Baselland | 2026<br>
        Basierend auf OpenStreetMap und geo.admin.ch Daten
    </footer>
    """, unsafe_allow_html=True)