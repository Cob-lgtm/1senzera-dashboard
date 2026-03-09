import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
from datetime import datetime

# --- SETTINGS ---
st.set_page_config(page_title="Senzera Executive Cockpit", layout="wide")

# Senzera Style
PINK = '#D81B60'
BLUE = '#1E88E5'
GREEN = '#00BFA5'
RED = '#F44336'

# --- DATA ENGINE ---
@st.cache_data
def load_senzera_data():
    # Google Daten
    df_g = pd.read_csv('Senzera_Dashboard_Data.csv') if os.path.exists('Senzera_Dashboard_Data.csv') else pd.DataFrame()
    # Zenloop Daten
    df_z = pd.read_csv('Zenloop_Antworten.csv') if os.path.exists('Zenloop_Antworten.csv') else pd.DataFrame()
    
    if not df_g.empty:
        if 'Monat' not in df_g.columns: df_g['Monat'] = 'März 2026'
        df_g['Studio_Display'] = df_g['Studiokürzel'] + " - " + df_g['Stadt']
    return df_g, df_z

df_g, df_z = load_senzera_data()

if df_g.empty:
    st.error("❌ Kritischer Fehler: 'Senzera_Dashboard_Data.csv' nicht gefunden!")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.title("Senzera Navigation")
rl_opts = ["Alle"] + sorted(df_g['Regionalleitung'].unique().tolist())
sel_rl = st.sidebar.selectbox("Fokus Regionalleitung", rl_opts)

df_f = df_g if sel_rl == "Alle" else df_g[df_g['Regionalleitung'] == sel_rl]
studio_opts = sorted(df_f['Studio_Display'].unique().tolist())
sel_studios = st.sidebar.multiselect("Studios filtern", studio_opts, default=studio_opts)

# Gefilterte Datenmengen
df_final = df_f[df_f['Studio_Display'].isin(sel_studios)]
active_codes = df_final['Studiokürzel'].unique()
df_z_final = df_z[df_z['Property - studio'].isin(active_codes)] if not df_z.empty else pd.DataFrame()

# --- HEADER ---
st.title("🚀 Senzera Performance Cockpit")
monat = df_final['Monat'].unique()[-1]
st.info(f"Analyse-Modus: {sel_rl} | Datenstand: {monat}")

# --- GLOBAL KPIs ---
k1, k2, k3, k4 = st.columns(4)

# 1. Google Sterne
current_g = df_final[df_final['Monat'] == monat]['Rating'].mean()
k1.metric("🌟 Google Rating", f"{current_g:.2f} ⭐")

# 2. NPS & Stimmung
nps_val = 0
pos_sentiment_rate = 0
if not df_z_final.empty:
    total_z = len(df_z_final)
    prom = len(df_z_final[df_z_final['score_type'] == 'promoter'])
    detr = len(df_z_final[df_z_final['score_type'] == 'detractor'])
    nps_val = ((prom - detr) / total_z) * 100
    k2.metric("💙 Zenloop NPS", f"{nps_val:.0f}")
    
    # Korrektes Sentiment (Nur auf Kunden mit Text bezogen)
    txt_data = df_z_final.dropna(subset=['comment'])
    if not txt_data.empty:
        pos_sentiment_rate = (len(txt_data[txt_data['sentiment'] == 'positive']) / len(txt_data)) * 100
    k3.metric("😊 Stimmung (Text)", f"{pos_sentiment_rate:.0f}% pos.")
    k4.metric("📝 Feedback-Menge", f"{total_z} Stimmen")

# --- 🚨 ALARM BEREICH (IMMER SICHTBAR) ---
st.write("")
crit_df = df_final[(df_final['Monat'] == monat) & (df_final['Rating'] < 4.2)]
if not crit_df.empty:
    st.error(f"🚨 **ACHTUNG: {len(crit_df)} Studio(s) unter 4,2 Google-Sternen!**")
    cols = st.columns(min(len(crit_df), 5))
    for i, (_, row) in enumerate(crit_df.iterrows()):
        with cols[i % 5]:
            st.warning(f"**{row['Studiokürzel']}**\n({row['Rating']} ⭐)")

st.divider()

# --- ANALYSE TABS ---
t_google, t_zenloop, t_report = st.tabs(["🌟 GOOGLE ANALYTICS", "🧬 ZENLOOP DEEP-DIVE", "📄 MANAGEMENT REPORT"])

with t_google:
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("Google League Table")
        fig_g = px.bar(df_final[df_final['Monat'] == monat].sort_values('Rating'), x='Rating', y='Studiokürzel', orientation='h', color='Rating', color_continuous_scale='RdYlGn', range_x=[1, 5])
        st.plotly_chart(fig_g, use_container_width=True)
    with col_g2:
        st.subheader("Rating Entwicklung")
        trend = df_final.groupby('Monat', sort=False)['Rating'].mean().reset_index()
        fig_t = px.line(trend, x='Monat', y='Rating', markers=True)
        fig_t.update_traces(line_color=PINK, line_width=4)
        st.plotly_chart(fig_t, use_container_width=True)

with t_zenloop:
    if df_z_final.empty:
        st.warning("Keine Zenloop-Daten verfügbar.")
    else:
        st.subheader("🎯 Studio-Detail-Analyse")
        sel_s = st.selectbox("Studio auswählen für Detail-Blick:", active_codes)
        sd = df_z_final[df_z_final['Property - studio'] == sel_s]
        
        sc1, sc2, sc3 = st.columns([1, 1, 2])
        with sc1:
            s_nps = ((len(sd[sd['score_type']=='promoter']) - len(sd[sd['score_type']=='detractor'])) / len(sd)) * 100 if not sd.empty else 0
            st.metric(f"NPS {sel_s}", f"{s_nps:.0f}")
        with sc2:
            st.markdown("**Top Themen im Studio:**")
            if 'labels' in sd.columns:
                lbls = sd['labels'].str.split(';').explode().str.strip().value_counts().head(3)
                for l, c in lbls.items(): st.write(f"- {l}")
        with sc3:
            st.markdown("**Letzte echte Kommentare:**")
            st.dataframe(sd[['score', 'comment']].dropna().head(3), use_container_width=True, hide_index=True)

        st.divider()
        col_z1, col_z2 = st.columns(2)
        with col_z1:
            st.subheader("Wichtigste Kunden-Themen (Gesamt)")
            if 'labels' in df_z_final.columns:
                all_l = df_z_final['labels'].str.split(';').explode().str.strip().value_counts().head(10).reset_index()
                st.plotly_chart(px.bar(all_l, x='count', y='labels', orientation='h', color_discrete_sequence=[BLUE]), use_container_width=True)
        with col_z2:
            st.subheader("NPS nach Behandlung")
            if 'Property - product_segment' in df_z_final.columns:
                seg_data = []
                for seg in df_z_final['Property - product_segment'].dropna().unique():
                    d = df_z_final[df_z_final['Property - product_segment'] == seg]
                    n = ((len(d[d['score_type']=='promoter']) - len(d[d['score_type']=='detractor'])) / len(d)) * 100
                    seg_data.append({'Segment': seg, 'NPS': n})
                st.plotly_chart(px.bar(pd.DataFrame(seg_data), x='Segment', y='NPS', color='NPS', color_continuous_scale='Viridis'), use_container_width=True)

with t_report:
    st.subheader("Management-Bericht zum Kopieren")
    rep = f"BERICHT SENZERA PERFORMANCE | REGION: {sel_rl} | STAND: {monat}\n"
    rep += "="*50 + "\n\n"
    rep += f"📈 GOOGLE-RATING: {current_g:.2f} Sterne\n"
    if not df_z_final.empty:
        rep += f"💙 ZENLOOP NPS: {nps_val:.0f}\n"
        rep += f"😊 KUNDENSTIMMUNG: {pos_sentiment_rate:.0f}% der Kommentare sind positiv\n"
    
    rep += "\nEINZEL-AUSWERTUNG STUDIOS:\n"
    for s_code in active_codes:
        g_val = df_final[(df_final['Studiokürzel'] == s_code) & (df_final['Monat'] == monat)]['Rating'].values[0]
        # NPS pro Studio
        sd_s = df_z_final[df_z_final['Property - studio'] == s_code]
        s_nps_val = int(((len(sd_s[sd_s['score_type']=='promoter']) - len(sd_s[sd_s['score_type']=='detractor'])) / len(sd_s)) * 100) if not sd_s.empty else "--"
        
        rep += f"- {s_code}: Google {g_val} ⭐ | NPS {s_nps_val}\n"
        if g_val < 4.2: rep += "  ⚠️ ALARM: Google-Rating unter 4,2!\n"
    
    st.text_area("Berichtstext (für E-Mail/WhatsApp):", rep, height=400)

# --- EXPORT ---
st.divider()
st.subheader("📥 Daten-Zentrale")
c_ex1, c_ex2 = st.columns(2)
with c_ex1:
    csv = df_final.drop(columns=['Studio_Display']).to_csv(index=False, sep=';').encode('utf-8-sig')
    st.download_button("📥 Google Daten Export", csv, f"Senzera_Google_{monat}.csv", use_container_width=True)
with c_ex2:
    if not df_z_final.empty:
        csv_z = df_z_final.to_csv(index=False, sep=';').encode('utf-8-sig')
        st.download_button("📥 Zenloop Rohdaten Export", csv_z, f"Senzera_Zenloop_{monat}.csv", use_container_width=True)
