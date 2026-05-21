import streamlit as st
import geopandas as gpd
import folium
from pathlib import Path
import warnings
import json
import tempfile
import os

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

# MODERNES COLOR SCHEME: Purple/Violet
st.markdown("""
    <style>
    * { box-sizing: border-box; }
    html, body { font-size: 14px; }
    
    /* ENTFERNE FOLIUM LAYER CONTROL CHECKBOXES */
    .leaflet-control-layers-toggle {
        display: none !important;
    }
    
    .leaflet-control-layers {
        display: none !important;
    }
    
    /* HEADER BOX */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px 40px;
        border-radius: 0;
        margin: -20px -20px 20px -20px;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
        border-bottom: 3px solid #5568d3;
    }
    
    .header-container h1 {
        color: white;
        margin: 0 0 8px 0;
        font-size: 36px;
        font-weight: 700;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    
    .header-container p {
        color: rgba(255, 255, 255, 0.95);
        margin: 0;
        font-size: 14px;
    }
    
    /* SIDEBAR - Modern Hell */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #f0f1f5 100%);
        width: 320px !important;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background: transparent;
    }
    
    /* MAIN */
    .main { 
        background: linear-gradient(to bottom, #ffffff 0%, #f8f9fa 100%);
    }
    
    /* TEXT */
    h1, h2, h3 {
        color: #2d3748;
        font-weight: 700;
        line-height: 1.3;
    }
    
    h2 { font-size: 24px; margin: 20px 0 16px 0; color: #667eea; }
    p { line-height: 1.5; color: #4a5568; }
    
    /* SIDEBAR LABELS */
    .sidebar-title {
        color: #667eea;
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 20px;
        padding: 10px 0;
        border-bottom: 2px solid #667eea;
    }
    
    .filter-label {
        color: #2d3748;
        font-weight: 600;
        font-size: 13px;
        margin-top: 16px;
        margin-bottom: 8px;
        display: block;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    
    .value-display {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        color: #2d3748;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 12px;
        margin-top: 6px;
        font-weight: 600;
        text-align: center;
        border-left: 3px solid #667eea;
    }
    
    /* METRICS */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        padding: 16px;
        border-radius: 8px;
        border-left: 3px solid #667eea;
        min-height: 80px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    [data-testid="stMetric"] label {
        color: #667eea !important;
        font-size: 11px !important;
        margin-bottom: 8px;
        font-weight: 600;
    }
    
    [data-testid="stMetric"] > div:last-child {
        color: #667eea !important;
        font-size: 28px !important;
        font-weight: 700 !important;
    }
    
    /* RADIO & SLIDER */
    [data-testid="stRadio"] label { color: #2d3748 !important; font-weight: 500; }
    input[type="range"] { accent-color: #667eea !important; }
    
    /* INFO BAR */
    .info-bar {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-left: 4px solid #667eea;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 16px 0;
        color: white;
        font-size: 14px;
        font-weight: 500;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
    }
    
    .info-bar strong { color: #fff; font-weight: 700; }
    
    /* LEGEND */
    .legend-box {
        background: linear-gradient(135deg, #f0f4ff 0%, #f5f1ff 100%);
        padding: 12px 16px;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin-top: 16px;
    }
    
    .legend-box p { margin: 0; color: #2d3748; font-size: 12px; }
    .legend-box strong { color: #667eea; font-weight: 700; }
    
    /* MAP */
    .map-container {
        background: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.1);
        margin: 16px 0;
    }
    
    iframe { border: none; border-radius: 8px; }
    
    /* FOOTER */
    footer { text-align: center; padding: 20px; color: #a0aec0; font-size: 12px; border-top: 1px solid #e2e8f0; margin-top: 40px; }
    
    @media (max-width: 1200px) {
        [data-testid="stSidebar"] { width: 280px !important; }
        .title-section h1 { font-size: 24px; }
        h2 { font-size: 20px; }
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
                
                gdf['geometry'] = gdf.geometry.simplify(tolerance=0.00005)
                
                return gdf, path
            except Exception as e:
                st.error(f"Fehler beim Laden: {e}")
                return None, None
    
    return None, None

# ========================================================================
# HYDRANT BUFFER ANALYSIS
# ========================================================================
def apply_hydrant_buffer(gdf_lagerflaechen, dist_hydrant_m):
    """Erstelle Buffer um Hydranten und schneide Lagerflächen darauf"""
    if gdf_lagerflaechen is None or len(gdf_lagerflaechen) == 0:
        return gdf_lagerflaechen
    
    gdf_with_hydrants = gdf_lagerflaechen[gdf_lagerflaechen["nahe_hydrant"] == True].copy()
    
    if len(gdf_with_hydrants) == 0:
        return gdf_lagerflaechen
    
    hydrant_points = gdf_with_hydrants.geometry.centroid
    buffer_degrees = dist_hydrant_m / 111000
    buffer_union = hydrant_points.buffer(buffer_degrees).unary_union
    
    gdf_clipped = gdf_lagerflaechen.copy()
    gdf_clipped['geometry'] = gdf_lagerflaechen.geometry.intersection(buffer_union)
    gdf_clipped = gdf_clipped[~gdf_clipped.geometry.is_empty]
    
    return gdf_clipped

# ========================================================================
# CREATE MAP
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
        prefer_canvas=False,
        max_bounds=True
    )
    
    sw = [bounds[1], bounds[0]]
    ne = [bounds[3], bounds[2]]
    m.fit_bounds([sw, ne], padding=(50, 50))
    
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
    
    # Hydranten hinzufügen als einfache blaue Quadrate
    if gdf_hydrants is not None and len(gdf_hydrants) > 0:
        for idx, row in gdf_hydrants.iterrows():
            try:
                geom = row.geometry
                if geom.geom_type == 'Point':
                    folium.RegularPolygonMarker(
                        location=[geom.y, geom.x],
                        fill_color='#0284c7',
                        number_of_sides=4,
                        radius=3,
                        rotation=45,
                        popup='Hydrant',
                        color='#0284c7',
                        fill_opacity=0.8,
                        weight=1,
                        tooltip='Hydrant'
                    ).add_to(m)
            except:
                continue
    
    folium.LayerControl(collapsed=False, position='topright').add_to(m)
    return m

# ========================================================================
# MAIN
# ========================================================================

# HEADER
st.markdown("""
    <div class="header-container">
        <h1>🗺️ Lagerplatz-Finder</h1>
        <p>Finde ideale Lagerflächen in Baselland basierend auf Infrastruktur-Nähe</p>
    </div>
    """, unsafe_allow_html=True)

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
    
    # Personenanzahl
    st.markdown('<span class="filter-label">Personenanzahl</span>', unsafe_allow_html=True)
    person_category = st.radio(
        "Personenanzahl",
        options=["< 50 Personen", "50-100 Personen", "> 100 Personen"],
        label_visibility="collapsed"
    )
    
    if person_category == "< 50 Personen":
        person_label = "< 50 Personen"
        min_flaeche_ha = 0.5
    elif person_category == "50-100 Personen":
        person_label = "50-100 Personen"
        min_flaeche_ha = 1.0
    else:
        person_label = "> 100 Personen"
        min_flaeche_ha = 2.0
    
    min_flaeche_m2 = min_flaeche_ha * 10000
    
    st.markdown(f'<div class="value-display">{person_label}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="value-display">Mindestfläche: {min_flaeche_ha:.1f} ha</div>', unsafe_allow_html=True)
    
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
        
        gdf_filtered = gdf.copy()
        gdf_filtered = gdf_filtered[
            (gdf_filtered["dist_bauernhof_m"] <= dist_bauernhof)
            & (gdf_filtered["dist_oev_m"] <= dist_oev)
        ]
        
        if has_hydrant:
            gdf_filtered = gdf_filtered[gdf_filtered["dist_hydrant_m"] <= dist_hydrant]
            gdf_filtered = apply_hydrant_buffer(gdf_filtered, dist_hydrant)
        
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
    st.markdown('<div class="sidebar-title">Ergebnisse</div>', unsafe_allow_html=True)
    
    gefiltert = len(gdf_filtered)
    gesamt = len(gdf)
    anteil = (gefiltert / gesamt) * 100
    
    st.markdown(f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px;">
            <div style="background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%); padding: 16px; border-radius: 8px; border-left: 3px solid #667eea; text-align: center;">
                <div style="color: #667eea; font-size: 11px; margin-bottom: 8px; font-weight: 600;">Gefiltert</div>
                <div style="color: #667eea; font-size: 28px; font-weight: 700;">{gefiltert}</div>
            </div>
            <div style="background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%); padding: 16px; border-radius: 8px; border-left: 3px solid #667eea; text-align: center;">
                <div style="color: #667eea; font-size: 11px; margin-bottom: 8px; font-weight: 600;">Gesamt</div>
                <div style="color: #667eea; font-size: 28px; font-weight: 700;">{gesamt}</div>
            </div>
            <div style="background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%); padding: 16px; border-radius: 8px; border-left: 3px solid #667eea; text-align: center;">
                <div style="color: #667eea; font-size: 11px; margin-bottom: 8px; font-weight: 600;">Anteil</div>
                <div style="color: #667eea; font-size: 28px; font-weight: 700;">{anteil:.0f}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ========================================================================
# MAIN CONTENT
# ========================================================================

st.markdown(f"""
    <div class="info-bar">
        <strong>{gefiltert:,} Lagerflächen</strong> entsprechen den gewählten Kriterien
    </div>
    """, unsafe_allow_html=True)

if len(gdf_filtered) > 0:
    st.markdown(f'<h2>Karte ({gefiltert:,} Lagerflächen)</h2>', unsafe_allow_html=True)
    
    with st.spinner("Erstelle Karte..."):
        m = create_map_with_hydrants(gdf_filtered, gdf_hydrants)
        if m:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
                m.save(tmp.name)
                tmp_path = tmp.name
            
            with open(tmp_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            st.components.v1.html(html_content, height=650, scrolling=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            try:
                os.unlink(tmp_path)
            except:
                pass
            
            st.markdown("")
            
            st.markdown("""
                <div class="legend-box">
                    <p><strong>Legende:</strong></p>
                    <p>Grün = Wiese | Dunkelgrün = Wald | Blaue Quadrate = Hydranten</p>
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