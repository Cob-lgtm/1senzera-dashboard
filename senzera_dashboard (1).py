import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os

st.set_page_config(page_title="Senzera Intelligence Hub", layout="wide")

# --- DESIGN & FARBEN ---
SENZERA_PINK = '#D81B60'
SENZERA_BLUE = '#1f77b4'
COLOR_PROMOTER = '#00BFA5'
COLOR_PASSIVE = '#FFC107'
COLOR_DETRACTOR = '#FF5252'

# --- DATA ENGINE ---
def load_all_data():
    df_g = pd.read_csv('Senzera_Dashboard_Data.csv') if os.path.exists('Senzera_Dashboard_Data.csv') else pd.DataFrame()
    df_z = pd.read_csv('Zenloop_Antworten.csv') if os.path.exists('Zenloop_Antworten.csv') else pd.DataFrame()
    
    # Cleaning
    if not df_g.empty:
        if 'Monat' not in df_g.columns: df_g['Monat'] = 'März 2026'
        df_g['Studio_Display'] = df_g['Studiokürzel'] + " - " + df_g['Stadt']
        
    return df_g, df_z

df_google, df_zenloop = load_all_data()

if df_google.empty:
    st.error("Daten konnten nicht geladen werden.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.title("🎯 Steuerung")
rl_list = ["Alle"] + sorted(df_google['Regionalleitung'].unique().tolist())
sel_rl = st.sidebar.selectbox("Regionalleitung", rl_list)

df_f = df_google if sel_rl == "Alle" else df_google[df_google['Regionalleitung'] == sel_rl]
sel_studios = st.sidebar.multiselect("Studios wählen", sorted(df_f['Studio_Display'].unique()), default=sorted(df_f['Studio_Display'].unique()))
df_final = df_f[df_f['Studio_Display'].isin(sel_studios)]
selected_kuerzel = df_final['Studiokürzel'].unique()

# --- ZENLOOP PROCESSING ---
df_z_final = df_zenloop[df_zenloop['Property - studio'].isin(selected_kuerzel)] if not df_zenloop.empty else pd.DataFrame()

# --- HEADER KPIs ---
st.title("🚀 Senzera Management Cockpit")
k1, k2, k3, k4 = st.columns(4)

# Google Schnitt
avg_g = df_final[df_final['Monat'] == df_final['Monat'].unique()[-1]]['Rating'].mean()
k1.metric("Ø Google Sterne", f"{avg_g:.2f} ⭐")

# NPS Schnitt
if not df_z_final.empty:
    tot = len(df_z_final)
    prom = len(df_z_final[df_z_final['score_type'] == 'promoter'])
    detr = len(df_z_final[df_z_final['score_type'] == 'detractor'])
    nps_total = ((prom - detr) / tot) * 100
    k2.metric("Ø Zenloop NPS", f"{nps_total:.0f}")
    k3.metric("Kunden-Antworten", f"{tot} 📝")
    
    # Stimmung
    pos_sent = (len(df_z_final[df_z_final['sentiment'] == 'positive']) / tot) * 100
    k4.metric("Positive Stimmung", f"{pos_sent:.0f}% 😊")

# --- 🚨 INTELLIGENTER ALARM 🚨 ---
st.write("")
col_a1, col_a2 = st.columns(2)

with col_a1:
    crit_g = df_final[(df_final['Monat'] == df_final['Monat'].unique()[-1]) & (df_final['Rating'] < 4.2)]
    if not crit_g.empty:
        st.error(f"⚠️ **Google Alarm:** {len(crit_g)} Studio(s) unter 4,2 Sterne")
        st.dataframe(crit_g[['Studiokürzel', 'Stadt', 'Rating']], use_container_width=True, hide_index=True)

with col_a2:
    # NPS Alarm auf Studio-Basis
    if not df_z_final.empty:
        s_nps = []
        for s in selected_kuerzel:
            sd = df_z_final[df_z_final['Property - studio'] == s]
            if len(sd) >= 5: # Nur ab 5 Antworten aussagekräftig
                val = ((len(sd[sd['score_type']=='promoter']) - len(sd[sd['score_type']=='detractor'])) / len(sd)) * 100
                if val < 50: s_nps.append({'Studio': s, 'NPS': int(val)})
        
        if s_nps:
            st.warning(f"🚨 **NPS Warnung:** {len(s_nps)} Studio(s) unter NPS 50")
            st.dataframe(pd.DataFrame(s_nps), use_container_width=True, hide_index=True)

st.divider()

# --- TABS ---
t1, t2, t3 = st.tabs(["📊 GOOGLE PERFORMANCE", "🧠 ZENLOOP INSIGHTS", "📝 MANAGEMENT REPORT"])

with t1:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Google Ranking")
        fig = px.bar(df_final[df_final['Monat'] == df_final['Monat'].unique()[-1]].sort_values('Rating'), 
                     x='Rating', y='Studiokürzel', orientation='h', color='Rating', color_continuous_scale='RdYlGn')
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Bewertungs-Trend")
        trend = df_final.groupby('Monat', sort=False)['Rating'].mean().reset_index()
        fig2 = px.line(trend, x='Monat', y='Rating', markers=True, color_discrete_sequence=[SENZERA_PINK])
        st.plotly_chart(fig2, use_container_width=True)

with t2:
    if df_z_final.empty:
        st.info("Keine Zenloop Daten vorhanden.")
    else:
        iz1, iz2 = st.columns(2)
        with iz1:
            st.subheader("Themen-Analyse (Top Labels)")
            if 'labels' in df_z_final.columns:
                labels_series = df_z_final['labels'].str.split(';').explode().str.strip()
                labels_series = labels_series[labels_series != ""]
                top_l = labels_series.value_counts().head(10).reset_index()
                fig_l = px.bar(top_l, x='count', y='labels', orientation='h', color_discrete_sequence=[SENZERA_BLUE])
                st.plotly_chart(fig_l, use_container_width=True)
        
        with iz2:
            st.subheader("NPS nach Behandlungs-Segment")
            if 'Property - product_segment' in df_z_final.columns:
                seg_nps = []
                for seg in df_z_final['Property - product_segment'].dropna().unique():
                    d_s = df_z_final[df_z_final['Property - product_segment'] == seg]
                    n = ((len(d_s[d_s['score_type']=='promoter']) - len(d_s[d_s['score_type']=='detractor'])) / len(d_s)) * 100
                    seg_nps.append({'Segment': seg, 'NPS': n})
                fig_s = px.bar(pd.DataFrame(seg_nps), x='Segment', y='NPS', color='NPS', color_continuous_scale='Viridis')
                st.plotly_chart(fig_s, use_container_width=True)

        st.subheader("💬 Detail-Feedback & Kommentare")
        st.dataframe(df_z_final[['Property - studio', 'score', 'sentiment', 'comment']].dropna(subset=['comment']).sort_values('score'), use_container_width=True)

with t3:
    st.subheader("Individueller Performance-Bericht")
    monat_label = df_final['Monat'].unique()[-1]
    bericht = f"Performance Bericht {sel_rl} - {monat_label}\n"
    bericht += "="*30 + "\n\n"
    
    for s_code in selected_kuerzel:
        # Google Part
        row_g = df_final[(df_final['Studiokürzel'] == s_code) & (df_final['Monat'] == monat_label)].iloc[0]
        stars = row_g['Rating']
        
        # Zenloop Part
        sd = df_z_final[df_z_final['Property - studio'] == s_code]
        nps_val = "--"
        top_topic = "Keine Daten"
        if not sd.empty:
            nps_val = int(((len(sd[sd['score_type']=='promoter']) - len(sd[sd['score_type']=='detractor'])) / len(sd)) * 100)
            if 'labels' in sd.columns:
                top_topic = sd['labels'].str.split(';').explode().str.strip().value_counts().idxmax() if not sd['labels'].dropna().empty else "Allgemein"
        
        bericht += f"📍 STUDIO {row_g['Stadt']} ({s_code}):\n"
        bericht += f"   ⭐ Google: {stars} Sterne | 💙 NPS: {nps_val}\n"
        bericht += f"   🔝 Haupt-Thema der Kunden: {top_topic}\n"
        
        if stars < 4.2 or (isinstance(nps_val, int) and nps_val < 50):
            bericht += "   🚨 ACTION: Kritische Werte! Bitte Team-Gespräch führen und Fokus auf Service-Qualität.\n"
        else:
            bericht += "   ✅ Gute Performance. Weiterhin aktiv Bewertungskarten nutzen.\n"
        bericht += "\n"

    st.text_area("Bericht für E-Mail kopieren:", bericht, height=400)
    
# --- EXPORT ---
st.divider()
st.subheader("📥 Daten-Zentrale")
c_ex1, c_ex2 = st.columns(2)
with c_ex1:
    csv_g = df_final.to_csv(index=False, sep=';').encode('utf-8-sig')
    st.download_button("Download Google Daten (Excel)", csv_g, "Google_Performance.csv", use_container_width=True)
with c_ex2:
    if not df_z_final.empty:
        csv_z = df_z_final.to_csv(index=False, sep=';').encode('utf-8-sig')
        st.download_button("Download Zenloop Rohdaten (Excel)", csv_z, "Zenloop_Details.csv", use_container_width=True)
