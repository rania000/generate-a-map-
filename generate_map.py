import os
import base64
from io import BytesIO
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import folium
from folium import IFrame


# ===============================
# 1. CONFIGURATION
# ===============================

STATIONS_PATH = "dataset/stations.csv" # chemin vers le fichier des stations spatiales
WATER_LEVELS_PATH = "dataset/water_levels.csv" # chemin vers le fichier des niveaux d'eau (doit contenir une colonne "Date (TU)" et des colonnes "station_{code}")

TIME_COL = "Date (TU)"    # nom de la colone time , doit être au format datetime
LAT_COL = "site_coord_y"  # nom de la colonne latitude
LON_COL = "site_coord_x"  # nom de la colonne longitude

PLOT_DAYS = 365 * 3 # nombre de jours à afficher dans les graphiques
OUTPUT_FILE = "stations_map.html" # type de fichier de sortie (html pour une carte interactive)


# ===============================
# 2. CHECK FILES
# ===============================

if not os.path.exists(STATIONS_PATH):
    raise FileNotFoundError(f"{STATIONS_PATH} fichie non trouvable")

if not os.path.exists(WATER_LEVELS_PATH):
    raise FileNotFoundError(f"{WATER_LEVELS_PATH} fichier non trouvable.")


# ===============================
# 3. LOAD DATA
# ===============================

df_s = pd.read_csv(STATIONS_PATH)
df_t = pd.read_csv(WATER_LEVELS_PATH, parse_dates=[TIME_COL])


# ===============================
# 4. CHECK REQUIRED COLUMNS
# ===============================

required_s_cols = ["station_code", LAT_COL, LON_COL]
required_t_cols = [TIME_COL]

missing_s = set(required_s_cols) - set(df_s.columns)
missing_t = set(required_t_cols) - set(df_t.columns)

if missing_s:
    raise ValueError(f"colone manquante dans stations.csv: {missing_s}")

if missing_t:
    raise ValueError(f"colone manquante dans water_levels.csv: {missing_t}")

# ===============================
# 5. FILTRAGE POUR LE PLOT GRAPHIQIUE 
# ===============================
# derniers 3 ans ici 
tmax = df_t[TIME_COL].max()
tmin = tmax- pd.Timedelta(days=PLOT_DAYS)
df_t_recent = df_t[
    (df_t[TIME_COL] >= tmin) &
    (df_t[TIME_COL] <= tmax)
].copy()

# On met Date (TU) en index
df_recent_idx = df_t_recent.set_index(TIME_COL).sort_index()

station_cols = [c for c in df_recent_idx.columns if c.startswith("station_")]

# Resample horaire (grille créée automatiquement)
df_hourly = df_recent_idx[station_cols].resample("1h").mean()

# Stats manquants / dispo
missing_rate = df_hourly.isna().mean()
n_total = len(df_hourly)
n_available = df_hourly.notna().sum()



# ===============================
# 6. PLOT FUNCTION
# ===============================

def make_station_plot_base64(station_code: str) -> str:
    col = f"station_{station_code}"

    if col not in df_t_recent.columns:
        return ""

    s = df_t_recent[[TIME_COL, col]].dropna()

    if len(s) < 2:
        return ""

    fig = plt.figure(figsize=(4.8, 2.2))
    plt.scatter(s[TIME_COL],s[col],s=3, alpha=0.6)
    plt.title(f"{station_code} - {PLOT_DAYS} derniers jours",fontsize=10)
    plt.xticks(rotation=30, fontsize=7)
    plt.yticks(fontsize=7)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)

    img_b64 = base64.b64encode(buf.read()).decode("utf-8") # encode l'image en base64 pour l'inclure dans le popup HTML
    return img_b64


# ===============================
# 7. CREATE MAP
# ===============================

center_lat = df_s[LAT_COL].mean()
center_lon = df_s[LON_COL].mean()

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=8,
    tiles="OpenTopoMap"
)


# ===============================
# 8. ADD STATIONS
# ===============================

for _, row in df_s.iterrows():

    st = str(row["station_code"])
    col = f"station_{st}"
    mr = float(missing_rate.get(col, np.nan))
    ar = 1.0 - mr if np.isfinite(mr) else np.nan
    nav = int(n_available.get(col, 0)) if col in n_available else 0

    lat = row[LAT_COL]
    lon = row[LON_COL]
    label = str(row.get("station_label", st))

    tooltip = folium.Tooltip(
        f"<b>{label}</b><br>"
        f"<b>{st}</b><br>"
        f"Missing : {mr*100:.1f}%<br>"
        f"station_type: {row.get('station_type', 'NA')}<br>"
        f"site_type: {row.get('site_type', 'NA')}",
        sticky=True
    )

    img_b64 = make_station_plot_base64(st)

    popup_html = f"""
    <div style="font-family: Arial; width: 520px;">
      <h4>{label}</h4>
      <div><b>Code:</b> {st}</div>
      <ul>
        <li><b>station_type</b>: {row.get('station_type', 'NA')}</li>
        <li><b>site_type</b>: {row.get('site_type', 'NA')}</li>
        <li><b>Coord</b>: ({lat:.5f}, {lon:.5f})</li>
        <li><b>Données manquantes</b>: {mr*100:.1f}%</li>
      </ul>
      {"<img src='data:image/png;base64," + img_b64 + "' style='width: 500px;'/>"
        if img_b64 else
        "<i>Pas assez de données récentes.</i>"}
    </div>
    """

    iframe = IFrame(html=popup_html, width=540, height=320) 
    popup = folium.Popup(iframe, max_width=600)
    
    folium.Marker(
        location=[lat, lon],
        tooltip=tooltip,
        popup=popup,
        icon=folium.Icon( icon="tint", prefix="fa")
    ).add_to(m)


# ===============================
# 9. SAVE OUTPUT
# ===============================

m.save(OUTPUT_FILE)

print(f"Carte générée : {OUTPUT_FILE}")
