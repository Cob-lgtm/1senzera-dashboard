import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
from datetime import datetime

# --- CONFIG & STYLE ---
st.set_page_config(page_title="Senzera Performance Masterpiece", layout="wide", initial_sidebar_state="expanded")

# Senzera Brand Colors
COLOR_PINK = '#D81B60'
COLOR_BLUE = '#1E88E5'
COLOR_PROMOTER = '#00BFA5'
COLOR_PASSIVE = '#FFB300'
COLOR_DETRACTOR = '#F44336'
BG_LIGHT = '#F8F9FA'

# Custom CSS for a professional look
st.markdown(f"""
    <style>
    .main {{ background-color: {BG_LIGHT}; }}
    .stMetric {{ background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 24px; }}
    .stTabs [data-baseweb="tab"] {{ height: 50px; white-space: pre-wrap; font-weight: bold; font-size: 16px; }}
    </style>
    """, unsafe_allow_stdio=True)

# --- DATA ENGINE ---
@st.cache_data
def load_data():
    df_g = pd.read_csv('Senzera_Dashboard_Data.csv') if os.path.exists('Senzera_Dashboard_Data.csv') else pd.DataFrame()
    df_z = pd.read_csv('Zenloop_Antworten.csv') if os.path.exists('Zenloop_Antworten.csv') else pd.DataFrame()
    
    if not df_g.empty:
        df_g['Monat'] = df_g.get('Monat', 'März 2026')
        df_g['Studio_Name'] = df_g['Studiokürzel'] + " (" + df_g['Stadt'] + ")"
    
    return df_g, df_z

df_g, df_z = load_data()

if df_g.empty:
    st.error("⚠️ Senzera_Dashboard_Data.csv nicht gefunden!")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.image("https://senzera.com/wp-content/uploads/2021/05/senzera-logo.svg", width=150)
st.sidebar.title("Navigation")

# Region Filter
rl_options = ["Alle Regionalleitungen"] + sorted(df_g['Regionalleitung'].unique().tolist())
sel_rl = st.sidebar.selectbox("Fokus Region", rl_options)

df_f = df_g if sel_rl == "Alle Regionalleitungen" else df_g[df_g['Regionalleitung'] == sel_rl]

# Studio Filter
studio_options = sorted(df_f['Studio_Name'].unique().tolist())
sel_studios = st.sidebar.multiselect("Studios auswählen", studio_options, default=studio_options)

# Filtered Dataframes
df_final = df_f[df_f['Studio_Name'].isin(sel_studios)]
selected_codes = df_final['Studiokürzel'].unique()
df_z_final = df_z[df_z['Property - studio'].isin(selected_codes)] if not df_z.empty else pd.DataFrame()

# --- HEADER SECTION ---
st.title("🏆 Senzera Performance Cockpit")
monat_label = df_final['Monat'].unique()[-1]
st.markdown(f"**Datenstand: {monat_label}** | Fokus: `{sel_rl}`")

# --- TOP LEVEL KPIs ---
k1, k2, k3, k4 = st.columns(4)

# 1. Google Sterne
current_rating = df_final[df_final['Monat'] == monat_label]['Rating'].mean()
k1.metric("🌟 Google Ø-Rating", f"{current_rating:.2f}", delta=f"{df_final['NewReviews'].sum()} neue Rezensionen")

# 2. NPS
if not df_z_final.empty:
    n_tot = len(df_z_final)
    n_prom = len(df_z_final[df_z_final['score_type'] == 'promoter'])
    n_detr = len(df_z_final[df_z_final['score_type'] == 'detractor'])
    nps_val = ((n_prom - n_detr) / n_tot) * 100
    k2.metric("💙 Zenloop NPS", f"{nps_val:.0f}", help="Promotoren minus Kritiker")
    
    # 3. Sentiment (KORRIGIERT: Nur auf Kommentare bezogen)
    comments_only = df_z_final.dropna(subset=['comment'])
    if not comments_only.empty:
        pos_sent = (len(comments_only[comments_only['sentiment'] == 'positive']) / len(comments_only)) * 100
        k3.metric("😊 Feedback Stimmung", f"{pos_sent:.0f}%", help="Prozent der geschriebenen Kommentare mit positiver Stimmung")
    else:
        k3.metric("😊 Feedback Stimmung", "--")
    
    k4.metric("📝 Kundenstimmen", f"{n_tot}")

# --- 🚨 CRITICAL WATCHLIST ---
st.write("")
crit_studios = df_final[(df_final['Monat'] == monat_label) & (df_final['Rating'] < 4.2)]
if not crit_studios.empty:
    with st.container():
        st.error(f"🚨 **ACHTUNG: Handlungsbedarf in {len(crit_studios)} Studio(s)**")
        cols = st.columns(len(crit_studios) if len(crit_studios) < 4 else 4)
        for i, row in crit_studios.iterrows():
            with cols[i % 4]:
                st.markdown(f"**{row['Studiokürzel']} ({row['Stadt'])**")
                st.markdown(f"Rating: `{row['Rating']} ⭐` | [Karten ordern ↗️]")

st.divider()

# --- ANALYTICS TABS ---
tab_ranking, tab_zenloop, tab_report = st.tabs(["🏆 LEAGUE TABLE", "🧬 ZENLOOP ANALYTICS", "📧 MANAGEMENT REPORT"])

# ==========================================
# TAB 1: LEAGUE TABLE (Die Rangliste)
# ==========================================
with tab_ranking:
    st.subheader("Das interne Ranking: Google vs. Zenloop")
    
    # Ranking berechnen
    ranking_data = []
    for code in selected_codes:
        # Google
        g_row = df_final[(df_final['Studiokürzel'] == code) & (df_final['Monat'] == monat_label)].iloc[0]
        # NPS
        z_studio = df_z_final[df_z_final['Property - studio'] == code]
        z_val = ((len(z_studio[z_studio['score_type']=='promoter']) - len(z_studio[z_studio['score_type']=='detractor'])) / len(z_studio)) * 100 if not z_studio.empty else 0
        
        # Score 0-100 (Gewichtung: 50% Google, 50% NPS)
        perf_score = ((g_row['Rating']/5)*50) + (((z_val+100)/200)*50)
        
        ranking_data.append({
            'Studio': code,
            'Stadt': g_row['Stadt'],
            'Google ⭐': g_row['Rating'],
            'NPS 💙': int(z_val),
            'Antworten': len(z_studio),
            'Perf. Score': round(perf_score, 1)
        })
    
    df_rank = pd.DataFrame(ranking_data).sort_values('Perf. Score', ascending=False)
    
    # Highlight Top 3
    c_top1, c_top2 = st.columns([2, 1])
    with c_top1:
        st.dataframe(df_rank.style.background_gradient(subset=['Perf. Score'], cmap='RdYlGn'), use_container_width=True, hide_index=True)
    with c_top2:
        st.info("**Performance Score:**\nKombiniert Google Rating (50%) und NPS (50%).")
        fig_trend = px.line(df_final.groupby('Monat', sort=False)['Rating'].mean().reset_index(), x='Monat', y='Rating', title="Google Trend Gesamt")
        fig_trend.update_traces(line_color=COLOR_PINK)
        st.plotly_chart(fig_trend, use_container_width=True)

# ==========================================
# TAB 2: ZENLOOP DEEP DIVE
# ==========================================
with tab_zenloop:
    if df_z_final.empty:
        st.info("Keine Detaildaten vorhanden.")
    else:
        z_col1, z_col2 = st.columns(2)
        with z_col1:
            st.subheader("Worüber sprechen die Kunden?")
            if 'labels' in df_z_final.columns:
                labels = df_z_final['labels'].str.split(';').explode().str.strip().value_counts().head(12).reset_index()
                fig_l = px.bar(labels, x='count', y='labels', orientation='h', color_discrete_sequence=[COLOR_BLUE])
                st.plotly_chart(fig_l, use_container_width=True)
        
        with z_col2:
            st.subheader("Performance nach Segment")
            if 'Property - product_segment' in df_z_final.columns:
                seg_list = []
                for seg in df_z_final['Property - product_segment'].dropna().unique():
                    d = df_z_final[df_z_final['Property - product_segment'] == seg]
                    n = ((len(d[d['score_type']=='promoter']) - len(d[d['score_type']=='detractor'])) / len(d)) * 100
                    seg_list.append({'Behandlung': seg, 'NPS': n, 'Count': len(d)})
                df_seg = pd.DataFrame(seg_list).sort_values('NPS', ascending=False)
                fig_s = px.bar(df_seg, x='NPS', y='Behandlung', orientation='h', color='NPS', color_continuous_scale='Viridis')
                st.plotly_chart(fig_s, use_container_width=True)

        st.subheader("Kundenkommentare im Fokus")
        # Filter nach sentiment
        sent_filter = st.radio("Nach Stimmung filtern:", ["Alle", "Positive Stimmung 😊", "Kritisch 🔴"], horizontal=True)
        df_comm = df_z_final.dropna(subset=['comment'])
        if sent_filter == "Positive Stimmung 😊": df_comm = df_comm[df_comm['sentiment'] == 'positive']
        if sent_filter == "Kritisch 🔴": df_comm = df_comm[df_comm['score'] <= 6]
        
        st.dataframe(df_comm[['Property - studio', 'score', 'comment', 'labels']].sort_values('score'), use_container_width=True)

# ==========================================
# TAB 3: MANAGEMENT REPORT (Copy-Paste Ready)
# ==========================================
with tab_report:
    st.subheader("Dein fertiges Reporting für E-Mail & WhatsApp")
    
    # Automatischer Text
    status_rl = f"EXECUTIVE SUMMARY - {sel_rl.upper()}"
    report_text = f"📢 {status_rl}\n"
    report_text += f"Berichtszeitraum: {monat_label}\n"
    report_text += "="*30 + "\n\n"
    
    report_text += f"Gesamt-Performance Google: {current_rating:.2f} ⭐\n"
    if not df_z_final.empty:
        report_text += f"Gesamt-Performance NPS: {nps_total:.0f} 💙\n"
        report_text += f"Kunden-Sentiment: {pos_sent:.0f}% positiv\n"
    
    report_text += "\n📍 STUDIO ANALYSE:\n"
    for _, row in df_rank.iterrows():
        alert = "🚨 HANDLUNGSBEDARF" if row['Google ⭐'] < 4.2 else "✅ GUT"
        report_text += f"• {row['Studio']} ({row['Stadt']}): Google {row['Google ⭐']} | NPS {row['NPS 💙']} -> {alert}\n"
    
    if not df_z_final.empty and 'labels' in df_z_final.columns:
        top_topic = df_z_final['labels'].str.split(';').explode().str.strip().value_counts().idxmax()
        report_text += f"\n💡 TOP THEMA DIESER MONAT: {top_topic}\n"
    
    report_text += "\nViele Grüße,\nDein Dashboard-System"
    
    st.text_area("Bericht kopieren:", report_text, height=450)
    st.download_button("📥 Als Textdatei speichern", report_text, file_name=f"Senzera_Report_{monat_label}.txt")

# --- FOOTER ---
st.divider()
st.caption(f"Senzera Intelligence Hub v4.0 | Erstellt am {datetime.now().strftime('%d.%m.%Y')}")
