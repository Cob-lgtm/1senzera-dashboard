"""
Senzera Performance Hub – v5 (Optimized)
============================================
Starten:  streamlit run senzera_dashboard.py
Dateien:  Senzera_Dashboard_Data.csv  +  Zenloop_Antworten.csv

Änderungen in dieser Version:
  - FIX: Logo wird nun sicher über Web-URL mit weißem HG geladen.
  - FIX: Theme-Toggle ("Darstellung") ist nun am Ende der Sidebar.
  - FIX: Tab "Studio Performance" ist nun ein interaktives, schlankes Data-Grid.
"""

from __future__ import annotations
import os
from datetime import datetime
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Optionaler Import für Performer-Tab (cryptography)
try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_OK = True
except ImportError:
    CRYPTO_OK = False

# ══════════════════════════════════════════════════════════════════
# 1 · PAGE CONFIG
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Senzera Performance Hub",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════
# 2 · THEME ENGINE
# ══════════════════════════════════════════════════════════════════
if "theme" not in st.session_state:
    st.session_state.theme = "system"

def get_theme(theme_mode: str) -> dict:
    C_PINK = "#E81B6D"
    C_BLUE = "#1A85FF"
    C_GREEN = "#00BFA5"
    C_ORANGE = "#FF9100"
    C_RED = "#FF3D00"

    if theme_mode == "dark":
        return {
            "mode": "dark",
            "bg": "#0B0F19", "bg_panel": "#111827", "bg_panel_hover": "#1F2937",
            "text": "#F3F4F6", "text_muted": "#9CA3AF", "text_h": "#FFFFFF",
            "border": "#374151", "divider": "#1F2937", "input_bg": "#1F2937",
            "pink": C_PINK, "blue": C_BLUE, "green": C_GREEN, "orange": C_ORANGE, "red": C_RED
        }
    else:
        return {
            "mode": "light",
            "bg": "#F8FAFC", "bg_panel": "#FFFFFF", "bg_panel_hover": "#F1F5F9",
            "text": "#334155", "text_muted": "#64748B", "text_h": "#0F172A",
            "border": "#E2E8F0", "divider": "#F1F5F9", "input_bg": "#FFFFFF",
            "pink": C_PINK, "blue": C_BLUE, "green": C_GREEN, "orange": C_ORANGE, "red": C_RED
        }

T = get_theme("dark" if st.session_state.theme == "dark" else "light")

st.markdown(f"""
<style>
/* Base */
.stApp {{ background-color: {T["bg"]}; color: {T["text"]}; font-family: 'Inter', -apple-system, sans-serif; -webkit-font-smoothing: antialiased; }}
h1, h2, h3, h4, h5, h6 {{ color: {T["text_h"]} !important; font-family: 'Playfair Display', serif; font-weight: 700; }}
p, span, div {{ color: {T["text"]}; }}
hr {{ border-color: {T["divider"]}; margin: 32px 0; }}
[data-testid="stSidebar"] {{ background-color: {T["bg_panel"]}; border-right: 1px solid {T["border"]}; }}

/* Panels */
.kpi-card {{ background: {T["bg_panel"]}; border: 1px solid {T["border"]}; border-radius: 16px; padding: 24px; transition: transform 0.2s, box-shadow 0.2s; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
.kpi-card:hover {{ transform: translateY(-3px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }}
.kpi-title {{ font-size: 13px; font-weight: 600; color: {T["text_muted"]}; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 8px; }}
.kpi-val {{ font-size: 36px; font-weight: 800; color: {T["text_h"]}; line-height: 1.1; margin-bottom: 4px; font-family: 'Playfair Display', serif; }}
.kpi-sub {{ font-size: 14px; font-weight: 500; }}

/* Typography / Utilities */
.section-title {{ font-size: 22px; font-weight: 700; margin-top: 16px; margin-bottom: 24px; color: {T["text_h"]}; border-bottom: 2px solid {T["pink"]}; padding-bottom: 8px; display: inline-block; font-family: 'Playfair Display', serif; }}
.nav-label {{ font-size: 11px; font-weight: 700; color: {T["text_muted"]}; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; }}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{ gap: 32px; border-bottom: 2px solid {T["divider"]}; }}
.stTabs [data-baseweb="tab"] {{ height: 50px; white-space: pre-wrap; color: {T["text_muted"]}; font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; }}
.stTabs [aria-selected="true"] {{ color: {T["pink"]} !important; border-bottom: 3px solid {T["pink"]} !important; }}

/* DataFrames */
[data-testid="stDataFrame"] {{ background: {T["bg_panel"]}; border-radius: 12px; border: 1px solid {T["border"]}; overflow: hidden; }}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# 3 · DATA LOADING
# ══════════════════════════════════════════════════════════════════
@st.cache_data
def load_all_data():
    df_g = pd.read_csv('Senzera_Dashboard_Data.csv') if os.path.exists('Senzera_Dashboard_Data.csv') else pd.DataFrame()
    df_z = pd.read_csv('Zenloop_Antworten.csv') if os.path.exists('Zenloop_Antworten.csv') else pd.DataFrame()
    
    if not df_g.empty:
        if 'Monat' not in df_g.columns: df_g['Monat'] = 'März 2026'
        df_g['Studio_Display'] = df_g['Studiokürzel'] + " - " + df_g['Stadt']
        
    return df_g, df_z

df_g, df_z = load_all_data()
if df_g.empty:
    st.error("⚠️ 'Senzera_Dashboard_Data.csv' nicht gefunden!")
    st.stop()

# ══════════════════════════════════════════════════════════════════
# 4 · SIDEBAR
# ══════════════════════════════════════════════════════════════════
def sidebar(df_g: pd.DataFrame):
    global T
    with st.sidebar:
        # LOGO FIX: Web-Logo in sicherer weißer Box
        st.markdown(
            f"""
            <div style='background:white; padding:15px; border-radius:12px; margin-bottom:32px; text-align:center; border: 1px solid {T["border"]};'>
                <img src='https://senzera.com/wp-content/uploads/2021/05/senzera-logo.svg' style='width:120px; height:auto;'/>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(f"<div class='nav-label'>Navigation</div>", unsafe_allow_html=True)

        rl_options = ["Alle Regionalleitungen"] + sorted(df_g['Regionalleitung'].unique().tolist())
        sel_rl = st.selectbox("Fokus Regionalleitung", rl_options, label_visibility="collapsed")

        df_f = df_g if sel_rl == "Alle Regionalleitungen" else df_g[df_g['Regionalleitung'] == sel_rl]
        
        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:13px; color:{T['text']}; margin-bottom:4px;'>Städte filtern</div>", unsafe_allow_html=True)
        sel_cities = st.multiselect("Städte", sorted(df_f['Stadt'].unique().tolist()), default=sorted(df_f['Stadt'].unique().tolist()), label_visibility="collapsed")
        
        df_f2 = df_f[df_f['Stadt'].isin(sel_cities)]
        
        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:13px; color:{T['text']}; margin-bottom:4px;'>Studios filtern</div>", unsafe_allow_html=True)
        sel_studios = st.multiselect("Studios", sorted(df_f2['Studio_Display'].unique().tolist()), default=sorted(df_f2['Studio_Display'].unique().tolist()), label_visibility="collapsed")

        st.markdown(f"<hr style='border-color:{T['divider']};margin:32px 0 24px;'>", unsafe_allow_html=True)

        # DARSTELLUNG (nach unten verschoben)
        st.markdown(f"<div class='nav-label'>Darstellung</div>", unsafe_allow_html=True)
        theme_choice = st.radio(
            "Darstellung",
            ["Hell", "Dunkel", "System"],
            index=0 if st.session_state.theme == "light" else 1 if st.session_state.theme == "dark" else 2,
            horizontal=True,
            label_visibility="collapsed"
        )
        new_theme = "light" if theme_choice == "Hell" else "dark" if theme_choice == "Dunkel" else "system"
        if new_theme != st.session_state.theme:
            st.session_state.theme = new_theme
            st.rerun()

    return sel_rl, sel_cities, sel_studios

sel_rl, sel_cities, sel_studios = sidebar(df_g)

df_final = df_g[df_g['Stadt'].isin(sel_cities) & df_g['Studio_Display'].isin(sel_studios)]
active_codes = df_final['Studiokürzel'].unique()
df_z_final = df_z[df_z['Property - studio'].isin(active_codes)] if not df_z.empty else pd.DataFrame()

# ══════════════════════════════════════════════════════════════════
# 5 · HEADER & GLOBAL KPIs
# ══════════════════════════════════════════════════════════════════
monat = df_final['Monat'].unique()[-1] if not df_final.empty else "N/A"

st.markdown(f"""
<div style='display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:8px;'>
    <div>
        <h1 style='margin:0; padding:0; font-size:32px;'>Executive Cockpit</h1>
        <div style='color:{T["text_muted"]}; font-size:15px; margin-top:4px;'>Performance Hub v5 · Region: <span style='color:{T["pink"]}; font-weight:600;'>{sel_rl}</span></div>
    </div>
    <div style='background:{T["pink"]}15; color:{T["pink"]}; padding:6px 16px; border-radius:20px; font-weight:700; font-size:13px;'>
        {monat}
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

if df_final.empty:
    st.info("Bitte Filter in der Sidebar anpassen.")
    st.stop()

# KPIs
c_g = df_final[df_final['Monat'] == monat]['Rating'].mean()
n_revs = df_final[df_final['Monat'] == monat]['NewReviews'].sum()

nps_val = 0
total_z = 0
pos_sent = 0

if not df_z_final.empty:
    total_z = len(df_z_final)
    if total_z > 0:
        prom = len(df_z_final[df_z_final['score_type'] == 'promoter'])
        detr = len(df_z_final[df_z_final['score_type'] == 'detractor'])
        nps_val = ((prom - detr) / total_z) * 100
        
    txt_data = df_z_final.dropna(subset=['comment'])
    if not txt_data.empty:
        pos_sent = (len(txt_data[txt_data['sentiment'] == 'positive']) / len(txt_data)) * 100

def kpi_card(title, value, sub, color):
    return f"""
    <div class='kpi-card'>
        <div class='kpi-title'>{title}</div>
        <div class='kpi-val' style='color:{color};'>{value}</div>
        <div class='kpi-sub' style='color:{color}CC;'>{sub}</div>
    </div>
    """

col1, col2, col3, col4 = st.columns(4)
with col1: st.markdown(kpi_card("Google Sterne", f"{c_g:.2f}", f"+{n_revs} neue Rezensionen", T["pink"]), unsafe_allow_html=True)
with col2: st.markdown(kpi_card("Zenloop NPS", f"{nps_val:.0f}", "Kundenzufriedenheit", T["blue"]), unsafe_allow_html=True)
with col3: st.markdown(kpi_card("Stimmung (Text)", f"{pos_sent:.0f}%", "Positive Kommentare", T["green"]), unsafe_allow_html=True)
with col4: st.markdown(kpi_card("Feedbacks", f"{total_z}", "Abgegebene Stimmen", T["orange"]), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# 6 · ALERTS
# ══════════════════════════════════════════════════════════════════
st.markdown("<div style='height:32px;'></div>", unsafe_allow_html=True)
crit_df = df_final[(df_final['Monat'] == monat) & (df_final['Rating'] < 4.2)]

if not crit_df.empty:
    st.markdown(f"""
    <div style='background:{T["red"]}15; border-left:4px solid {T["red"]}; padding:16px 20px; border-radius:8px; margin-bottom:24px;'>
        <div style='color:{T["red"]}; font-weight:700; font-size:15px; margin-bottom:8px; display:flex; align-items:center; gap:8px;'>
            <span style='font-size:18px;'>🚨</span> HANDLUNGSBEDARF: {len(crit_df)} Studio(s) unter 4,2 Sterne
        </div>
        <div style='display:flex; gap:12px; flex-wrap:wrap;'>
            {"".join([f"<div style='background:white; color:{T['red']}; border:1px solid {T['red']}40; padding:4px 12px; border-radius:16px; font-size:13px; font-weight:600;'>{row['Studiokürzel']} ({row['Rating']} ⭐)</div>" for _, row in crit_df.iterrows()])}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# 7 · TABS & CHARTS
# ══════════════════════════════════════════════════════════════════
t_google, t_zenloop, t_league, t_report = st.tabs([
    "🌟 GOOGLE ANALYTICS", 
    "🧬 ZENLOOP INSIGHTS", 
    "🏆 STUDIO PERFORMANCE", 
    "📄 MANAGEMENT BERICHT"
])

def create_bar(df, x, y, color_col, cmap, title=""):
    fig = px.bar(df, x=x, y=y, orientation='h', color=color_col, color_continuous_scale=cmap)
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color=T["text"], title=title, title_font_size=18,
        margin=dict(l=0, r=0, t=40, b=0), xaxis_title="", yaxis_title=""
    )
    return fig

with t_google:
    st.markdown(f"<div class='section-title' style='color:{T['text']};'>Google Rating & Trends</div>", unsafe_allow_html=True)
    cg1, cg2 = st.columns(2)
    with cg1:
        d_g = df_final[df_final['Monat'] == monat].sort_values('Rating')
        st.plotly_chart(create_bar(d_g, 'Rating', 'Studiokürzel', 'Rating', 'RdYlGn'), use_container_width=True)
    with cg2:
        trend = df_final.groupby('Monat', sort=False)['Rating'].mean().reset_index()
        fig_t = px.line(trend, x='Monat', y='Rating', markers=True)
        fig_t.update_traces(line_color=T["pink"], line_width=4, marker=dict(size=8))
        fig_t.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color=T["text"],
            margin=dict(l=0, r=0, t=40, b=0), xaxis_title="", yaxis_title="Ø Sterne"
        )
        st.plotly_chart(fig_t, use_container_width=True)

with t_zenloop:
    if df_z_final.empty:
        st.info("Keine Zenloop Daten vorhanden.")
    else:
        st.markdown(f"<div class='section-title' style='color:{T['text']};'>Kunden-Feedbacks & Themen</div>", unsafe_allow_html=True)
        cz1, cz2 = st.columns(2)
        with cz1:
            if 'labels' in df_z_final.columns:
                l_s = df_z_final['labels'].str.split(';').explode().str.strip().value_counts().head(8).reset_index()
                st.plotly_chart(create_bar(l_s, 'count', 'labels', 'count', 'Blues', "Top 8 Kunden-Themen"), use_container_width=True)
        with cz2:
            if 'Property - product_segment' in df_z_final.columns:
                seg_data = []
                for seg in df_z_final['Property - product_segment'].dropna().unique():
                    d = df_z_final[df_z_final['Property - product_segment'] == seg]
                    n = ((len(d[d['score_type']=='promoter']) - len(d[d['score_type']=='detractor'])) / len(d)) * 100 if len(d)>0 else 0
                    seg_data.append({'Segment': seg, 'NPS': n})
                st.plotly_chart(create_bar(pd.DataFrame(seg_data), 'NPS', 'Segment', 'NPS', 'Viridis', "NPS nach Behandlung"), use_container_width=True)

        st.markdown(f"<div class='section-title' style='color:{T['text']}; margin-top:32px;'>Deep Dive: Studio-Lupe</div>", unsafe_allow_html=True)
        sel_s = st.selectbox("Wähle ein Studio für Detail-Feedbacks:", active_codes)
        sd = df_z_final[df_z_final['Property - studio'] == sel_s]
        
        c_dd1, c_dd2 = st.columns([1, 2])
        with c_dd1:
            s_nps = ((len(sd[sd['score_type']=='promoter']) - len(sd[sd['score_type']=='detractor'])) / len(sd)) * 100 if not sd.empty else 0
            st.markdown(f"<div style='background:{T['bg_panel_hover']}; padding:20px; border-radius:12px;'>", unsafe_allow_html=True)
            st.metric(f"NPS Score für {sel_s}", f"{s_nps:.0f}")
            st.markdown(f"<div style='font-size:13px; color:{T['text_muted']};'>{len(sd)} Antworten gesamt</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with c_dd2:
            st.dataframe(sd[['score', 'comment', 'sentiment']].dropna().sort_values('score'), use_container_width=True, hide_index=True)

# ==========================================
# STUDIO PERFORMANCE (NEUES DATA-GRID)
# ==========================================
with t_league:
    st.markdown(f"<div class='section-title' style='color:{T['text']};'>Studio Performance Tabelle</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='color:{T['text_muted']};margin-bottom:24px;'>Sortierbare Übersicht aller gewählten Studios. Ranking basierend auf Google Rating (50%) und Zenloop NPS (50%).</div>", unsafe_allow_html=True)

    ranking_data = []
    for code in active_codes:
        g_row = df_final[(df_final['Studiokürzel'] == code) & (df_final['Monat'] == monat)]
        if g_row.empty: continue
        g_row = g_row.iloc[0]

        z_studio = df_z_final[df_z_final['Property - studio'] == code]
        if not z_studio.empty:
            prom = len(z_studio[z_studio['score_type'] == 'promoter'])
            detr = len(z_studio[z_studio['score_type'] == 'detractor'])
            s_nps = ((prom - detr) / len(z_studio)) * 100
        else:
            s_nps = 0
        
        # Performance Score berechnen (0-100)
        score = ((g_row['Rating'] / 5) * 50) + (((s_nps + 100) / 200) * 50)
        
        ranking_data.append({
            "Studio": f"{code} ({g_row['Stadt']})",
            "Google ⭐": float(g_row['Rating']),
            "NPS 💙": int(s_nps),
            "Neu 💬": int(g_row['NewReviews']),
            "Feedback 📝": len(z_studio),
            "Score": round(score, 1)
        })

    if ranking_data:
        df_rank = pd.DataFrame(ranking_data).sort_values('Score', ascending=False)

        st.dataframe(
            df_rank,
            column_config={
                "Studio": st.column_config.TextColumn("Studio", width="medium"),
                "Google ⭐": st.column_config.NumberColumn("Google ⭐", format="%.2f", width="small"),
                "NPS 💙": st.column_config.NumberColumn("NPS 💙", width="small"),
                "Neu 💬": st.column_config.NumberColumn("Neue Rez.", width="small"),
                "Feedback 📝": st.column_config.NumberColumn("Antworten", width="small"),
                "Score": st.column_config.ProgressColumn(
                    "Performance Score",
                    help="Kombinierter Score aus Google (50%) & NPS (50%)",
                    format="%.1f",
                    min_value=0,
                    max_value=100,
                    width="medium"
                ),
            },
            hide_index=True,
            use_container_width=True,
            height=min(600, 40 + (len(df_rank) * 36)) # Dynamische Höhe
        )
    else:
        st.info("Keine Daten zum Anzeigen vorhanden.")

with t_report:
    st.markdown(f"<div class='section-title' style='color:{T['text']};'>E-Mail & Datencenter</div>", unsafe_allow_html=True)
    c_r1, c_r2 = st.columns([2, 1])
    
    with c_r1:
        st.markdown(f"<div style='font-weight:600; margin-bottom:12px; color:{T['text']};'>Automatischer Bericht ({sel_rl})</div>", unsafe_allow_html=True)
        rep = f"BERICHT SENZERA | REGION: {sel_rl} | {monat}\n" + "="*45 + "\n"
        rep += f"Google Sterne: {c_g:.2f} ⭐\n"
        if not df_z_final.empty:
            rep += f"Zenloop NPS: {nps_val:.0f} 💙 | Stimmung: {pos_sent:.0f}% positiv\n"
        rep += "\nSTATUS STUDIOS:\n"
        for code in active_codes:
            g_val = df_final[(df_final['Studiokürzel'] == code) & (df_final['Monat'] == monat)]['Rating'].values[0]
            sd_s = df_z_final[df_z_final['Property - studio'] == code]
            s_nps_val = int(((len(sd_s[sd_s['score_type']=='promoter']) - len(sd_s[sd_s['score_type']=='detractor'])) / len(sd_s)) * 100) if not sd_s.empty else "--"
            
            rep += f"- {code}: Google {g_val} ⭐ | NPS {s_nps_val}"
            if g_val < 4.2: rep += " -> 🚨 ALARM"
            rep += "\n"
            
        st.text_area("Bericht kopieren", rep, height=300, label_visibility="collapsed")
        
    with c_r2:
        st.markdown(f"<div style='font-weight:600; margin-bottom:12px; color:{T['text']};'>Daten als CSV exportieren</div>", unsafe_allow_html=True)
        
        csv_g = df_final.drop(columns=['Studio_Display']).to_csv(index=False, sep=';').encode('utf-8-sig')
        st.download_button("📥 Google Performance Liste", csv_g, f"Senzera_Google_{monat}.csv", use_container_width=True)
        
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        if not df_z_final.empty:
            csv_z = df_z_final.to_csv(index=False, sep=';').encode('utf-8-sig')
            st.download_button("📥 Zenloop Detail-Rohdaten", csv_z, f"Senzera_Zenloop_{monat}.csv", use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════
st.divider()
st.markdown(
    f"""<div style='display:flex;align-items:center;justify-content:space-between;
                    padding:16px 0;
                    border-top:2px solid {T["divider"]}'>
        <div>
            <div style='font-size:13px;font-weight:700;color:{T["text_h"]}; font-family:"Playfair Display",serif;'>
                Performance Hub
            </div>
            <div style='font-size:10px;color:{T["text_muted"]};letter-spacing:0.3px;'>
                v5.1 · waxing & beauty
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True
)
