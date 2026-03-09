import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os

st.set_page_config(page_title="Senzera Performance Dashboard", layout="wide")

# --- FARBEN ---
SENZERA_PINK = '#D81B60'
SENZERA_BLUE = '#1f77b4'
ZENLOOP_GREEN = '#00BFA5'
ZENLOOP_RED = '#FF5252'
ZENLOOP_YELLOW = '#FFC107'

# --- DATEN LADEN FUNKTIONEN ---
def load_google_data():
    if not os.path.exists('Senzera_Dashboard_Data.csv'):
        return pd.DataFrame()
    df = pd.read_csv('Senzera_Dashboard_Data.csv')
    if 'Monat' not in df.columns:
        df['Monat'] = 'März 2026'
    if 'Studio_Display' not in df.columns:
        df['Studio_Display'] = df['Studiokürzel'] + " - " + df['Strasse + HNr']
    return df

def load_zenloop_data():
    # Wir suchen flexibel nach der Datei (Groß-/Kleinschreibung)
    possible_names = ['Zenloop_Antworten.csv', 'Zenloop_Antworten.CVS', 'zenloop_antworten.csv']
    for name in possible_names:
        if os.path.exists(name):
            df = pd.read_csv(name)
            # WICHTIG: Wir vereinheitlichen den Spaltennamen für das Studio
            if 'Property - studio' in df.columns:
                df.rename(columns={'Property - studio': 'studio_id'}, inplace=True)
            return df
    return pd.DataFrame()

# Daten laden
df = load_google_data()
df_nps = load_zenloop_data()

if df.empty:
    st.error("Datei 'Senzera_Dashboard_Data.csv' nicht gefunden. Bitte lade sie hoch.")
    st.stop()

st.title("📊 Senzera Vertriebssteuerung")
st.markdown("**Performance Dashboard: Google-Bewertungen & Zenloop Kundenstimmen**")

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter-Optionen")
rl_options = ["Alle"] + sorted(df['Regionalleitung'].dropna().unique().tolist())
selected_rl = st.sidebar.selectbox("Regionalleitung wählen", options=rl_options)

df_filtered = df if selected_rl == "Alle" else df[df['Regionalleitung'] == selected_rl]

city_options = sorted(df_filtered['Stadt'].unique())
selected_city = st.sidebar.multiselect("Stadt wählen", options=city_options, default=city_options)
df_filtered = df_filtered[df_filtered['Stadt'].isin(selected_city)]

studio_options = sorted(df_filtered['Studio_Display'].unique())
selected_studios = st.sidebar.multiselect("Studio wählen", options=studio_options, default=studio_options)
filtered_df = df_filtered[df_filtered['Studio_Display'].isin(selected_studios)]

# --- HAUPTBEREICH ---
if not filtered_df.empty:
    aktueller_monat = filtered_df['Monat'].unique()[-1]
    df_aktuell = filtered_df[filtered_df['Monat'] == aktueller_monat]
    selected_kuerzel = df_aktuell['Studiokürzel'].unique()

    # Zenloop Filterung
    if not df_nps.empty and 'studio_id' in df_nps.columns:
        df_nps_filtered = df_nps[df_nps['studio_id'].isin(selected_kuerzel)]
    else:
        df_nps_filtered = pd.DataFrame()

    tab_google, tab_zenloop = st.tabs(["🌟 GOOGLE BEWERTUNGEN", "💙 ZENLOOP NPS & FEEDBACK"])

    # --- TAB 1: GOOGLE ---
    with tab_google:
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Ø-Rating Gesamt", f"{df_aktuell['Rating'].mean():.2f} ⭐")
        kpi2.metric("Gesamt-Rezensionen", f"{df_aktuell['TotalReviews'].sum():,}")
        kpi3.metric("Neue Rezensionen", f"+{df_aktuell['NewReviews'].sum()}")
        kpi4.metric("Ø-NPS (Integrierter Wert)", f"{df_aktuell['NPS'].mean():.0f}")

        st.divider()
        critical_df = df_aktuell[df_aktuell['Rating'] < 4.2].sort_values('Rating')
        if not critical_df.empty:
            st.error("🚨 **ALARM: Handlungsbedarf!** (Rating < 4,2)")
            st.dataframe(critical_df[['Studiokürzel', 'Stadt', 'Rating', 'NewReviews']], use_container_width=True)
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("🏆 Top 10 Google Ratings")
            fig = px.bar(df_aktuell.sort_values('Rating', ascending=False).head(10), x='Studiokürzel', y='Rating', color='Rating', color_continuous_scale='RdYlGn', range_y=[3.5, 5])
            st.plotly_chart(fig, use_container_width=True)
        with col_g2:
            st.subheader("📈 Trend")
            trend = filtered_df.groupby('Monat', sort=False)['Rating'].mean().reset_index()
            fig_t = px.line(trend, x='Monat', y='Rating', markers=True)
            st.plotly_chart(fig_t, use_container_width=True)

    # --- TAB 2: ZENLOOP (LIVE BERECHNUNG) ---
    with tab_zenloop:
        if df_nps_filtered.empty:
            st.warning("⚠️ Keine Daten in 'Zenloop_Antworten.csv' für die Auswahl gefunden. Prüfe, ob die Studio-Kürzel übereinstimmen.")
        else:
            total = len(df_nps_filtered)
            prom = len(df_nps_filtered[df_nps_filtered['score_type'] == 'promoter'])
            detr = len(df_nps_filtered[df_nps_filtered['score_type'] == 'detractor'])
            nps_val = ((prom - detr) / total) * 100 if total > 0 else 0
            
            c1, c2, c3 = st.columns(3)
            c1.metric("💙 Aktueller NPS", f"{nps_val:.0f}")
            c2.metric("🟢 Promotoren", f"{prom}")
            c3.metric("🔴 Detraktoren", f"{detr}")
            
            st.divider()
            
            # Kommentar-Sektion
            st.subheader("💬 Kundenstimmen (aus der Zenloop-Datei)")
            df_comm = df_nps_filtered.dropna(subset=['comment'])
            if not df_comm.empty:
                st.dataframe(df_comm[['studio_id', 'score', 'comment']].rename(columns={'studio_id': 'Studio', 'score': 'Punkte', 'comment': 'Kommentar'}), use_container_width=True)
            else:
                st.info("Keine Kommentare vorhanden.")

    # --- BERICHT ---
    st.divider()
    with st.expander("📝 E-Mail Bericht generieren"):
        bericht = f"Update für {team_name} ({aktueller_monat}):\n"
        bericht += f"- Google Rating: {df_aktuell['Rating'].mean():.2f}\n"
        if not df_nps_filtered.empty: bericht += f"- Zenloop NPS: {nps_val:.0f}\n"
        st.text_area("Bericht kopieren:", bericht, height=200)

else:
    st.info("Bitte wähle Studios aus.")
