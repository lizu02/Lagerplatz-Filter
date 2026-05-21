import streamlit as st
import geopandas as gpd
import folium
from pathlib import Path
import json
import tempfile
import os

st.set_page_config(page_title="Lagerplatz-Finder", layout="wide")

# CSS - Minimal und sauber
st.markdown("""
    <style>
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px 40px;
        margin: -20px -20px 20px -20px;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
    }
    .header h1 { color: white; margin: 0 0 8px 0; font-size: 36px; }
    .header p { color: rgba(255, 255, 255, 0.95); margin: 0; font-size: 14px; }
    
    .leaflet-control-layers { display: none !important; }
    .leaflet-control-layers-toggle { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

# ========================================================================
# LOAD DATA
# ========================================================================
@st.cache_data
def load_data():
    paths = ["output/geeignete_lagerflaechen_BL.geojson", "./output/geeignete_lagerflaechen_BL.geojson"]
    for path in paths:
        if Path(path).exists():
            gdf = gpd.read_file(path)
            if gdf.crs != "EPSG:4326":
                gdf = gdf.to_crs("EPSG:4326")
            gdf['geometry'] = gdf.geometry.simplify(tolerance=0.00005)
            return gdf
    return None

# ========================================================================
# HYDRANT BUFFER
# ========================================================================
def apply_hydrant_buffer(gdf, dist_m):
    gdf_hydrants = gdf[gdf["nahe_hydrant"] == True].copy()
    if len(gdf_hydrants) == 0:
        return gdf
    
    hydrant_points = gdf_hydrants.geometry.centroid
    buffer_degrees = dist_m / 111000
    buffer_union = hydrant_points.buffer(buffer_degrees).unary_union
    
    gdf_clipped = gdf.copy()
    gdf_clipped['geometry'] = gdf.geometry.intersection(buffer_union)
    return gdf_clipped[~gdf_clipped.geometry.is_empty]

# ========================================================================
# CREATE MAP
# ========================================================================
def create_map(gdf_filtered, gdf_hydrants=None):
    if len(gdf_filtered) == 0:
        return None
    
    bounds = gdf_filtered.total_bounds
    center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
    
    m = folium.Map(location=center, zoom_start=10, tiles="OpenStreetMap", prefer_canvas=False)
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
    
    # Hydranten aus gefilterten Daten
    #gdf_hydrants = gdf_filtered[gdf_filtered["nahe_hydrant"] == True].copy()
    #if len(gdf_hydrants) > 0:
    #    for idx, row in gdf_hydrants.iterrows():
    #        try:
    #            geom = row.geometry
    #            if geom.geom_type == 'Point':
    #                folium.RegularPolygonMarker(
    #                    location=[geom.y, geom.x],
    #                    fill_color='#0284c7',
    #                    number_of_sides=4,
    #                    radius=3,
    #                    rotation=45,
    #                    color='#0284c7',
    #                    fill_opacity=0.8,
    #                    weight=1,
    #                    tooltip='Hydrant'
    #                ).add_to(m)
    #        except:
    #            pass
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
    return m

# ========================================================================
# MAIN APP
# ========================================================================

# Header
st.markdown('<div class="header"><h1>🗺️ Lagerplatz-Finder</h1><p>Finde ideale Lagerflächen in Baselland</p></div>', unsafe_allow_html=True)

# Load data
gdf = load_data()
if gdf is None:
    st.error("Datei nicht gefunden: output/geeignete_lagerflaechen_BL.geojson")
    st.stop()

# Sidebar
with st.sidebar:
    st.subheader("Filter")
    
    person_category = st.radio("Personenanzahl", ["< 50 Personen", "50-100 Personen", "> 100 Personen"])
    min_flaeche_ha = {"< 50 Personen": 0.5, "50-100 Personen": 1.0, "> 100 Personen": 2.0}[person_category]
    
    dist_bauernhof = st.slider("Bauernhöfe (m)", 0, 3000, 1000, 100)
    dist_oev = st.slider("ÖV-Haltestellen (m)", 0, 5000, 1000, 100)
    dist_hydrant = st.slider("Hydrant (m)", 0, 3000, 500, 100)
    
    # Filter
    gdf_filtered = gdf[
        (gdf["dist_bauernhof_m"] <= dist_bauernhof) &
        (gdf["dist_oev_m"] <= dist_oev) &
        (gdf["flaeche_ha"] >= min_flaeche_ha)
    ]
    
    # Hydranten-Filter und Buffer SEPARAT
    if "dist_hydrant_m" in gdf_filtered.columns:
        gdf_filtered = gdf_filtered[gdf_filtered["dist_hydrant_m"] <= dist_hydrant]
        gdf_filtered = apply_hydrant_buffer(gdf_filtered, dist_hydrant)
    
    # Stats
    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("Gefiltert", len(gdf_filtered))
    col2.metric("Gesamt", len(gdf))
    col3.metric("Anteil", f"{(len(gdf_filtered) / len(gdf) * 100):.0f}%")

# Main content
if len(gdf_filtered) > 0:
    st.subheader(f"Karte ({len(gdf_filtered)} Lagerflächen)")
    
    m = create_map(gdf_filtered)
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
    
    st.info("🟩 Grün = Wiese | 🟩 Dunkelgrün = Wald | 🔷 Blau = Hydranten")
else:
    st.error("Keine Lagerflächen mit diesen Filtern gefunden")