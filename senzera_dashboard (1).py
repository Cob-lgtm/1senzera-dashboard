import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
from datetime import datetime

# --- CONFIG & STYLE ---
st.set_page_config(page_title="Senzera Performance Hub", layout="wide")

COLOR_PINK = '#D81B60'
COLOR_BLUE = '#1E88E5'
COLOR_PROMOTER = '#00BFA5'
COLOR_PASSIVE = '#FFB300'
COLOR_DETRACTOR = '#F44336'

# --- DATA ENGINE ---
def load_data():
    df_g = pd.read_csv('Senzera_Dashboard_Data.csv') if os.path.exists('Senzera_Dashboard_Data.csv') else pd.DataFrame()
    df_z = pd.read_csv('Zenloop_Antworten.csv') if os.path.exists('Zenloop_Antworten.csv') else pd.DataFrame()
    if not df_g.empty:
        df_g['Monat'] = df_g.get('Monat', 'März 2026')
        df_g['Studio_Name'] = df_g['Studiokürzel'] + " (" + df_g['Stadt'] + ")"
    return df_g, df_z

df_g, df_z = load_data()

if df_g.empty:
    st.error("Datei 'Senzera_Dashboard_Data.csv' nicht gefunden!")
    st.stop()

# --- SIDEBAR ---
st.sidebar.image("https://senzera.com/wp-content/uploads/2021/05/senzera-logo.svg", width=120)
rl_options = ["Alle"] + sorted(df_g['Regionalleitung'].unique().tolist())
sel_rl = st.sidebar.selectbox("Fokus Regionalleitung", rl_options)

df_f = df_g if sel_rl == "Alle" else df_g[df_g['Regionalleitung'] == sel_rl]
studio_options = sorted(df_f['Studio_Name'].unique().tolist())
sel_studios = st.sidebar.multiselect("Studios wählen", studio_options, default=studio_options)

df_final = df_f[df_f['Studio_Name'].isin(sel_studios)]
selected_codes = df_final['Studiokürzel'].unique()
df_z_final = df_z[df_z['Property - studio'].isin(selected_codes)] if not df_z.empty else pd.DataFrame()

# --- HEADER ---
st.title("🏆 Senzera Management Cockpit")
aktueller_monat = df_final['Monat'].unique()[-1]
st.info(f"Fokus: {sel_rl} | Zeitraum: {aktueller_monat}")

# --- TOP KPIs ---
k1, k2, k3, k4 = st.columns(4)

# 1. Google
curr_g = df_final[df_final['Monat'] == aktueller_monat]['Rating'].mean()
k1.metric("🌟 Google Ø-Rating", f"{curr_g:.2f}", f"+{df_final['NewReviews'].sum()} Rezensionen")

# 2. NPS & Stimmung
if not df_z_final.empty:
    n_tot = len(df_z_final)
    n_prom = len(df_z_final[df_z_final['score_type'] == 'promoter'])
    n_detr = len(df_z_final[df_z_final['score_type'] == 'detractor'])
    nps_val = ((n_prom - n_detr) / n_tot) * 100
    k2.metric("💙 Zenloop NPS", f"{nps_val:.0f}")
    
    comments_only = df_z_final.dropna(subset=['comment'])
    if not comments_only.empty:
        pos_sent = (len(comments_only[comments_only['sentiment'] == 'positive']) / len(comments_only)) * 100
        k3.metric("😊 Stimmung Feedback", f"{pos_sent:.0f}%", help="Nur Kunden mit Textkommentar")
    k4.metric("📝 Antworten", f"{n_tot}")

# --- 🚨 ALARM ZONE ---
crit = df_final[(df_final['Monat'] == aktueller_monat) & (df_final['Rating'] < 4.2)]
if not crit.empty:
    st.error(f"🚨 **HANDLUNGSBEDARF:** {len(crit)} Studio(s) unter 4,2 Sternen")
    cols = st.columns(len(crit) if len(crit) < 4 else 4)
    for i, (_, row) in enumerate(crit.iterrows()):
        with cols[i % 4]:
            st.warning(f"**{row['Studiokürzel']}** ({row['Rating']} ⭐)")

st.divider()

# --- ANALYSE TABS ---
tab1, tab2, tab3 = st.tabs(["📊 PERFORMANCE & TRENDS", "💙 ZENLOOP DEEP-DIVE", "📝 MANAGEMENT REPORT"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Google Ranking (Top 10)")
        fig = px.bar(df_final[df_final['Monat'] == aktueller_monat].sort_values('Rating'), x='Rating', y='Studiokürzel', orientation='h', color='Rating', color_continuous_scale='RdYlGn', range_x=[1, 5])
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Entwicklungs-Trend")
        trend = df_final.groupby('Monat', sort=False)['Rating'].mean().reset_index()
        fig_t = px.line(trend, x='Monat', y='Rating', markers=True)
        fig_t.update_traces(line_color=COLOR_PINK, line_width=4)
        st.plotly_chart(fig_t, use_container_width=True)

with tab2:
    if df_z_final.empty:
        st.warning("Keine Zenloop Daten gefunden.")
    else:
        # Deep Dive Selektor
        st.subheader("🎯 Studio-Check")
        sel_s = st.selectbox("Details für welches Studio?", selected_codes)
        sd = df_z_final[df_z_final['Property - studio'] == sel_s]
        
        sc1, sc2, sc3 = st.columns([1, 1, 2])
        with sc1:
            s_nps = ((len(sd[sd['score_type']=='promoter']) - len(sd[sd['score_type']=='detractor'])) / len(sd)) * 100 if not sd.empty else 0
            st.metric(f"NPS {sel_s}", f"{s_nps:.0f}")
        with sc2:
            st.write("**Top Themen:**")
            if 'labels' in sd.columns:
                labels = sd['labels'].str.split(';').explode().str.strip().value_counts().head(3)
                for l, c in labels.items(): st.write(f"- {l}")
        with sc3:
            st.write("**Letzte Kommentare:**")
            st.dataframe(sd[['score', 'comment']].dropna().head(3), use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Übergreifende Themen")
        col_z1, col_z2 = st.columns(2)
        with col_z1:
            if 'labels' in df_z_final.columns:
                l_series = df_z_final['labels'].str.split(';').explode().str.strip().value_counts().head(10).reset_index()
                fig_l = px.bar(l_series, x='count', y='labels', orientation='h', color_discrete_sequence=[COLOR_BLUE])
                st.plotly_chart(fig_l, use_container_width=True)
        with col_z2:
            if 'Property - product_segment' in df_z_final.columns:
                seg_nps = []
                for seg in df_z_final['Property - product_segment'].dropna().unique():
                    d = df_z_final[df_z_final['Property - product_segment'] == seg]
                    n = ((len(d[d['score_type']=='promoter']) - len(d[d['score_type']=='detractor'])) / len(d)) * 100
                    seg_nps.append({'Behandlung': seg, 'NPS': n})
                st.plotly_chart(px.bar(pd.DataFrame(seg_nps), x='Behandlung', y='NPS', color='NPS', color_continuous_scale='Viridis'), use_container_width=True)

with tab3:
    st.subheader("Management-Bericht (Copy & Paste)")
    rep = f"BERICHT {sel_rl} | STAND {aktueller_monat}\n" + "="*35 + "\n"
    rep += f"Google Sterne: {curr_g:.2f} ⭐\n"
    if not df_z_final.empty:
        rep += f"Zenloop NPS: {nps_total:.0f} 💙 | Stimmung: {pos_sent:.0f}% pos.\n"
    
    rep += "\nSTUDIO STATUS:\n"
    for s_code in selected_codes:
        g_val = df_final[(df_final['Studiokürzel'] == s_code) & (df_final['Monat'] == aktueller_monat)]['Rating'].values[0]
        rep += f"- {s_code}: {g_val} Sterne"
        if g_val < 4.2: rep += " -> 🚨 KRITISCH"
        rep += "\n"
    
    st.text_area("Berichtstext:", rep, height=350)
    
# --- EXPORT ---
st.divider()
csv = df_final.to_csv(index=False, sep=';').encode('utf-8-sig')
st.download_button("📥 Google-Daten als Excel laden", csv, f"Senzera_Export_{aktueller_monat}.csv")
