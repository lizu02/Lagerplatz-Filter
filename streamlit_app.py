import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

# ========================================================================
# CONFIG
# ========================================================================
st.set_page_config(
    page_title="🏕️ Lagerplatz-Finder",
    page_icon="🏕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================================================================
# LOAD DATA
# ========================================================================
@st.cache_data
def load_data():
    """Lade Daten mit verschiedenen Pfaden"""
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
                return gdf, path
            except Exception as e:
                st.error(f"Fehler beim Laden: {e}")
                return None, None

    return None, None

# ========================================================================
# CREATE MAP
# ========================================================================
def create_map(gdf_data):
    """Erstelle Folium-Karte"""
    if gdf_data is None or len(gdf_data) == 0:
        return None

    bounds = gdf_data.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles="OpenStreetMap"
    )

    farben = {
        "forest": {"fill": "#2d5016", "outline": "#1a3009"},
        "meadow": {"fill": "#90EE90", "outline": "#228B22"},
        "other": {"fill": "#FFD700", "outline": "#FFA500"},
    }

    for idx, row in gdf_data.iterrows():
        try:
            geom = row.geometry
            if geom.geom_type != "Polygon":
                continue

            coords = list(geom.exterior.coords)
            locations = [[lat, lon] for lon, lat in coords]

            landuse = row.get("landuse", "other")
            farbe_config = farben.get(landuse, farben["other"])

            popup_html = f"""
            <div style="width: 280px; font-family: Arial; font-size: 12px;">
                <h4 style="color: #2d5016; margin-bottom: 8px;">🗺️ Lagerfläche #{row.get('lagerplatz_id', idx)}</h4>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background: #f0f0f0;">
                        <td style="padding: 6px; border: 1px solid #ccc;"><b>Fläche:</b></td>
                        <td style="padding: 6px; border: 1px solid #ccc; text-align: right;">{row.get('flaeche_ha', 0):.2f} ha</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px; border: 1px solid #ccc;"><b>Typ:</b></td>
                        <td style="padding: 6px; border: 1px solid #ccc;">{landuse}</td>
                    </tr>
                    <tr style="background: #f0f0f0;">
                        <td style="padding: 6px; border: 1px solid #ccc;"><b>Bewertung:</b></td>
                        <td style="padding: 6px; border: 1px solid #ccc;">{row.get('bewertung', '-')}</td>
                    </tr>
                </table>
                <hr style="margin: 8px 0;">
                <div style="font-size: 11px;">
                    <p style="margin: 5px 0;"><b>🏗️ Infrastruktur:</b></p>
                    <p style="margin: 3px 0;">🚜 Bauernhof: {row.get('dist_bauernhof_m', -1):.0f}m</p>
                    <p style="margin: 3px 0;">🚌 ÖV: {row.get('dist_oev_m', -1):.0f}m</p>
                </div>
            </div>
            """

            folium.Polygon(
                locations=locations,
                color=farbe_config["outline"],
                fill=True,
                fillColor=farbe_config["fill"],
                fillOpacity=0.7,
                weight=2,
                popup=folium.Popup(popup_html, max_width=350),
            ).add_to(m)
        except:
            continue

    folium.LayerControl().add_to(m)
    return m

# ========================================================================
# MAIN
# ========================================================================

st.markdown(
    '<h1 style="color: #2d5016; text-align: center;">🏕️ Lagerplatz-Finder Baselland</h1>',
    unsafe_allow_html=True,
)

# Daten laden
gdf, path = load_data()

if gdf is None:
    st.error("❌ Datei nicht gefunden!")
    st.info("Erwartete Pfade: output/geeignete_lagerflaechen_BL.geojson")
    import sys
    sys.exit()

st.success(f"✅ {len(gdf)} Lagerplätze geladen von: {path}")

# SIDEBAR FILTER
st.sidebar.markdown("## 🎚️ Filter")

has_dist_cols = "dist_bauernhof_m" in gdf.columns and "dist_oev_m" in gdf.columns

if has_dist_cols:
    dist_bauernhof = st.sidebar.slider(
        "🚜 Bauernhöfe",
        min_value=0,
        max_value=3000,
        value=1000,
        step=100,
    )

    dist_oev = st.sidebar.slider(
        "🚌 ÖV-Haltestellen",
        min_value=0,
        max_value=3000,
        value=1000,
        step=100,
    )

    gdf_filtered = gdf[
        (gdf["dist_bauernhof_m"] <= dist_bauernhof)
        & (gdf["dist_oev_m"] <= dist_oev)
    ]
else:
    st.sidebar.warning("⚠️ Distanz-Spalten nicht vorhanden")
    gdf_filtered = gdf

# STATS
st.sidebar.markdown("---")
col1, col2 = st.sidebar.columns(2)
with col1:
    st.metric("📍 Gefiltert", len(gdf_filtered))
with col2:
    st.metric("📊 Gesamt", len(gdf))

if "flaeche_ha" in gdf_filtered.columns:
    st.sidebar.metric("🗺️ Fläche", f"{gdf_filtered['flaeche_ha'].sum():.0f} ha")

# TABS
tab1, tab2, tab3 = st.tabs(["🗺️ Karte", "📊 Statistiken", "📋 Daten"])

with tab1:
    if len(gdf_filtered) > 0:
        st.markdown(f"### 🗺️ Zeigt {len(gdf_filtered)} Lagerplätze")
        m = create_map(gdf_filtered)
        if m:
            st_folium(m, width=1200, height=600)
    else:
        st.error("❌ Keine Lagerplätze mit diesen Filtern")

with tab2:
    if len(gdf_filtered) > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Lagerplätze", len(gdf_filtered))
        with col2:
            if "flaeche_ha" in gdf_filtered.columns:
                st.metric("Gesamtfläche", f"{gdf_filtered['flaeche_ha'].sum():.0f} ha")
        with col3:
            if "flaeche_ha" in gdf_filtered.columns:
                st.metric("Ø Fläche", f"{gdf_filtered['flaeche_ha'].mean():.2f} ha")

        if "landuse" in gdf_filtered.columns:
            st.markdown("### 🌍 Nach Landnutzung")
            st.write(gdf_filtered["landuse"].value_counts())
    else:
        st.warning("⚠️ Keine Daten")

with tab3:
    if len(gdf_filtered) > 0:
        cols_to_show = [
            col
            for col in gdf_filtered.columns
            if col != "geometry" and col != "index"
        ]
        df_show = gdf_filtered[cols_to_show].copy()
        st.dataframe(df_show, use_container_width=True, height=400)

        csv = df_show.to_csv(index=False)
        st.download_button(
            "📥 Download CSV",
            csv,
            "lagerflaechen.csv",
            "text/csv",
        )
    else:
        st.warning("⚠️ Keine Daten")

st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #999; font-size: 12px;">'
    "🏕️ Lagerplatz-Finder v1.0 | Baselland | Mai 2026"
    "</div>",
    unsafe_allow_html=True,
)
