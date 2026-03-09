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

# --- DATEN LADEN ---
def load_data():
    # Google Daten
    if os.path.exists('Senzera_Dashboard_Data.csv'):
        df_g = pd.read_csv('Senzera_Dashboard_Data.csv')
    else:
        df_g = pd.DataFrame()
        
    # Zenloop Daten
    df_z = pd.DataFrame()
    for name in ['Zenloop_Antworten.csv', 'Zenloop_Antworten.CVS']:
        if os.path.exists(name):
            df_z = pd.read_csv(name)
            break
            
    return df_g, df_z

df, df_nps = load_data()

if df.empty:
    st.error("Datei 'Senzera_Dashboard_Data.csv' nicht gefunden.")
    st.stop()

# Vorbereitung Google Daten
if 'Monat' not in df.columns: df['Monat'] = 'März 2026'
if 'Studio_Display' not in df.columns:
    df['Studio_Display'] = df['Studiokürzel'] + " - " + df['Strasse + HNr']

st.title("📊 Senzera Vertriebssteuerung")
st.markdown("**Google-Bewertungen & Zenloop NPS Kundenfeedback**")

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

# --- BERECHNUNGEN (VOR DEN TABS) ---
if not filtered_df.empty:
    aktueller_monat = filtered_df['Monat'].unique()[-1]
    df_aktuell = filtered_df[filtered_df['Monat'] == aktueller_monat]
    selected_kuerzel = df_aktuell['Studiokürzel'].unique()

    # Zenloop NPS Berechnung
    df_nps_filtered = pd.DataFrame()
    calc_nps_total = 0
    studio_nps_list = []
    
    if not df_nps.empty and 'Property - studio' in df_nps.columns:
        df_nps_filtered = df_nps[df_nps['Property - studio'].isin(selected_kuerzel)]
        if not df_nps_filtered.empty:
            total_a = len(df_nps_filtered)
            prom = len(df_nps_filtered[df_nps_filtered['score_type'] == 'promoter'])
            detr = len(df_nps_filtered[df_nps_filtered['score_type'] == 'detractor'])
            calc_nps_total = ((prom - detr) / total_a) * 100
            
            # NPS pro Studio für den Bericht
            for s in df_nps_filtered['Property - studio'].unique():
                s_d = df_nps_filtered[df_nps_filtered['Property - studio'] == s]
                s_tot = len(s_d)
                s_nps = ((len(s_d[s_d['score_type'] == 'promoter']) - len(s_d[s_d['score_type'] == 'detractor'])) / s_tot) * 100
                studio_nps_list.append({'Studio': s, 'NPS': s_nps})

    # --- KPI HEADER ---
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Ø-Google Rating", f"{df_aktuell['Rating'].mean():.2f} ⭐")
    kpi2.metric("Neue Rezensionen", f"+{df_aktuell['NewReviews'].sum()}")
    kpi3.metric("Ø-NPS (Zenloop)", f"{calc_nps_total:.0f}" if not df_nps_filtered.empty else "--")
    kpi4.metric("Feedback-Antworten", f"{len(df_nps_filtered)}" if not df_nps_filtered.empty else "0")

    # --- ALARM BEREICH (IMMER SICHTBAR) ---
    critical_df = df_aktuell[df_aktuell['Rating'] < 4.2].sort_values('Rating')
    if not critical_df.empty:
        st.error("🚨 **ALARM: Handlungsbedarf!** Folgende Studios liegen unter 4,2 Sternen:")
        st.dataframe(critical_df[['Studiokürzel', 'Stadt', 'Rating', 'NewReviews']], use_container_width=True)
        with st.expander("💡 Action-Plan anzeigen"):
            st.markdown("1. Google-Karten bestellen. 2. Team sensibilisieren. 3. Gäste aktiv ansprechen.")

    st.divider()

    # --- TABS ---
    tab1, tab2 = st.tabs(["🌟 GOOGLE CHARTS", "💙 ZENLOOP DETAILS"])

    with tab1:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("🏆 Top 10 Google Ratings")
            fig = px.bar(df_aktuell.sort_values('Rating', ascending=False).head(10), x='Studiokürzel', y='Rating', color='Rating', color_continuous_scale='RdYlGn', range_y=[3.5, 5])
            st.plotly_chart(fig, use_container_width=True)
        with col_g2:
            st.subheader("📈 Entwicklung")
            trend = filtered_df.groupby('Monat', sort=False)['Rating'].mean().reset_index()
            fig_t = px.line(trend, x='Monat', y='Rating', markers=True)
            fig_t.update_traces(line_color=SENZERA_PINK)
            st.plotly_chart(fig_t, use_container_width=True)

    with tab2:
        if df_nps_filtered.empty:
            st.warning("Keine Zenloop-Daten gefunden.")
        else:
            c_z1, c_z2 = st.columns(2)
            with c_z1:
                st.subheader("📊 NPS Verteilung")
                pie_df = df_nps_filtered['score_type'].value_counts().reset_index()
                fig_p = px.pie(pie_df, values='count', names='score_type', hole=0.4, color='score_type',
                               color_discrete_map={'promoter': ZENLOOP_GREEN, 'passive': ZENLOOP_YELLOW, 'detractor': ZENLOOP_RED})
                st.plotly_chart(fig_p, use_container_width=True)
            with c_z2:
                st.subheader("💬 Letzte Kommentare")
                df_comm = df_nps_filtered.dropna(subset=['comment']).sort_values('date_received', ascending=False)
                st.dataframe(df_comm[['Property - studio', 'score', 'comment']].head(20), use_container_width=True)

    # --- BERICHT & EXPORT (ZURÜCK AN DER ALTEN STELLE) ---
    st.divider()
    st.subheader("📝 Automatischer Monatsbericht")
    
    team_name = f"Region {selected_rl}" if selected_rl != "Alle" else "Senzera-Team"
    bericht = f"Hallo liebes {team_name},\n\nhier ist das Update für {aktueller_monat}:\n\n"
    bericht += f"📊 Google Rating: {df_aktuell['Rating'].mean():.2f} ⭐\n"
    if not df_nps_filtered.empty:
        bericht += f"💙 Zenloop NPS: {calc_nps_total:.0f}\n"
    
    bericht += "\nEinzelauswertung:\n"
    for _, row in df_aktuell.iterrows():
        nps_val = next((item['NPS'] for item in studio_nps_list if item['Studio'] == row['Studiokürzel']), None)
        nps_str = f" | NPS: {int(nps_val)}" if nps_val is not None else ""
        bericht += f"- {row['Stadt']} ({row['Studiokürzel']}): {row['Rating']} ⭐{nps_str}\n"
        if row['Rating'] < 4.2: bericht += "  -> 🚨 Bitte Google-Karten bestellen!\n"

    st.text_area("E-Mail Vorlage:", bericht, height=300)

    st.subheader("📥 Daten Export")
    csv = filtered_df.drop(columns=['Studio_Display']).to_csv(index=False, sep=';').encode('utf-8-sig')
    st.download_button("Tabelle als CSV laden", data=csv, file_name=f"Senzera_Export_{aktueller_monat}.csv")
    
    with st.expander("Ganze Tabelle ansehen"):
        st.dataframe(filtered_df.drop(columns=['Studio_Display']), use_container_width=True)

else:
    st.info("Bitte wähle Studios aus.")
