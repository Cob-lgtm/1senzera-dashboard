"""
Senzera Performance Hub – v7.0 (Google Reviews only)
=====================================================
Starten:  streamlit run senzera_dashboard.py
Datei:    Senzera_Dashboard_Data.csv

Schlanke Variante: zeigt ausschließlich Google-Bewertungen je Studio,
mit Trend-Verlauf und auto-generiertem Management-Bericht.
"""

from __future__ import annotations
import os
from datetime import datetime
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ══════════════════════════════════════════════════════════════════
# 1 · PAGE CONFIG
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Senzera Performance Hub",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .hide-from-google { display: none; }
    </style>
    <meta name="robots" content="noindex, nofollow">
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════
# 2 · SENZERA CI
# ══════════════════════════════════════════════════════════════════
C_ORANGE      = "#E8620A"
C_ORANGE_LT   = "#F47A2A"
C_ORANGE_PALE = "#FEF2EB"
C_BLACK       = "#1A1814"
C_SAND        = "#CFC8B8"
C_STONE       = "#8FA4A8"
C_SKIN        = "#F0D0C4"
C_CREAM       = "#FDFAF6"
C_HONEY       = "#C8A84A"
C_HONEY_PALE  = "#FBF5E3"
C_MINT        = "#6EA87E"
C_LILAC       = "#B8A0BC"
C_GREEN       = "#3A8A50"
C_RED         = "#C83010"

RATING_MIN  = 4.2
RATING_GOOD = 4.5
REQ_GOOGLE  = {"Studiokürzel", "Stadt", "Regionalleitung", "Rating"}

# ══════════════════════════════════════════════════════════════════
# 3 · THEME DEFINITIONEN
# ══════════════════════════════════════════════════════════════════
THEMES = {
    "☀️ Hell": {
        "mode": "light",
        "app_bg": "#F7F4F0", "main_bg": "#F7F4F0", "sidebar_bg": "#FFFFFF",
        "card_bg": "#FFFFFF", "card_bg2": "#FDFAF6", "input_bg": "#FFFFFF",
        "table_head_bg": "#F9F6F2", "table_row_bg": "#FFFFFF", "table_row_alt": "#FDFAF6",
        "dropdown_bg": "#FFFFFF", "dropdown_item_hover": "#FEF2EB",
        "sidebar_border": "#EDE5D8", "card_border": "#EDE5D8", "input_border": "#DDD5C8",
        "divider": "#EDE5D8", "table_border": "#EDE5D8",
        "text_h": "#1A1814", "text_body": "#3C342A", "text_second": "#6B5A4A",
        "text_muted": "#9A8878", "text_label": "#7A6858", "text_input": "#1A1814",
        "text_table": "#2A221A",
        "card_shadow": "0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.05)",
        "card_shadow_h": "0 4px 24px rgba(232,98,10,0.13), 0 1px 4px rgba(0,0,0,0.06)",
        "input_shadow_f": "0 0 0 3px rgba(232,98,10,0.10)",
        "sidebar_shadow": "2px 0 12px rgba(0,0,0,0.04)",
        "ok_bg": "#EAF5EE", "ok_br": C_GREEN, "warn_bg": "#FBF5E3", "warn_br": C_HONEY,
        "err_bg": "#FDEEE8", "err_br": C_RED, "info_bg": "#FEF2EB", "info_br": C_ORANGE,
        "tag_bg": "#FEF2EB", "tag_fg": C_ORANGE,
        "plot_bg": "rgba(0,0,0,0)", "plot_font": "#6B5A4A", "plot_grid": "#EDE5D8",
        "scroll": "#DDD5C8", "summary_bg": "#FEF2EB",
    },
    "🌙 Dark": {
        "mode": "dark",
        "app_bg": "#100E0B", "main_bg": "#100E0B", "sidebar_bg": "#161310",
        "card_bg": "#1E1B17", "card_bg2": "#221F1B", "input_bg": "#1E1B17",
        "table_head_bg": "#1A1714", "table_row_bg": "#1E1B17", "table_row_alt": "#221F1B",
        "dropdown_bg": "#1E1B17", "dropdown_item_hover": "rgba(232,98,10,0.12)",
        "sidebar_border": "#2C2820", "card_border": "#2C2820", "input_border": "#2C2820",
        "divider": "#2C2820", "table_border": "#2C2820",
        "text_h": "#FDFAF6", "text_body": "#C8B8A8", "text_second": "#A89888",
        "text_muted": "#7A6858", "text_label": "#A89888", "text_input": "#FDFAF6",
        "text_table": "#C8B8A8",
        "card_shadow": "0 1px 4px rgba(0,0,0,0.4), 0 4px 20px rgba(0,0,0,0.3)",
        "card_shadow_h": "0 4px 28px rgba(232,98,10,0.22)",
        "input_shadow_f": "0 0 0 3px rgba(232,98,10,0.15)",
        "sidebar_shadow": "2px 0 16px rgba(0,0,0,0.4)",
        "ok_bg": "#12201A", "ok_br": C_MINT, "warn_bg": "#201A0A", "warn_br": C_HONEY,
        "err_bg": "#201008", "err_br": C_RED, "info_bg": "#201408", "info_br": C_ORANGE,
        "tag_bg": "rgba(232,98,10,0.14)", "tag_fg": C_ORANGE_LT,
        "plot_bg": "rgba(0,0,0,0)", "plot_font": "#A89888", "plot_grid": "#2C2820",
        "scroll": "#2C2820", "summary_bg": "rgba(232,98,10,0.10)",
    },
}

if "theme" not in st.session_state:
    st.session_state.theme = "☀️ Hell"

T = THEMES[st.session_state.theme]

# ══════════════════════════════════════════════════════════════════
# 4 · CSS INJECTION
# ══════════════════════════════════════════════════════════════════
def inject_css(t: dict) -> None:
    css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&display=swap');

@keyframes fadeSlideUp {{
    from {{ opacity: 0; transform: translateY(12px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes shimmer {{
    0%   {{ background-position: -200% center; }}
    100% {{ background-position: 200% center; }}
}}

[data-testid="stAppViewContainer"]::before {{
    content: '';
    display: block;
    height: 3px;
    background: linear-gradient(90deg, {C_ORANGE}, {C_HONEY}, {C_ORANGE_LT}, {C_ORANGE});
    background-size: 200% auto;
    animation: shimmer 4s linear infinite;
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 9999;
}}

[data-testid="metric-container"] {{ animation: fadeSlideUp 0.4s ease both; }}
[data-testid="column"]:nth-child(1) [data-testid="metric-container"] {{ animation-delay: 0.05s; }}
[data-testid="column"]:nth-child(2) [data-testid="metric-container"] {{ animation-delay: 0.10s; }}
[data-testid="column"]:nth-child(3) [data-testid="metric-container"] {{ animation-delay: 0.15s; }}

*, *::before, *::after {{ box-sizing: border-box !important; }}
html {{
    -webkit-font-smoothing: antialiased !important;
    -moz-osx-font-smoothing: grayscale !important;
    text-rendering: optimizeLegibility !important;
}}
html, body, [class*="css"], [class*="st-"],
div, span, p, label, input, select, textarea, button {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-feature-settings: 'kern' 1, 'liga' 1 !important;
}}

[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main,
.main .block-container {{ background: {t["app_bg"]} !important; }}
.main .block-container {{
    padding-top: 1.8rem !important;
    padding-bottom: 5rem !important;
    max-width: 1500px !important;
}}
[data-testid="stHeader"] {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}

[data-testid="stSidebarCollapseButton"] {{
    color: {C_ORANGE} !important;
    background-color: {t["card_bg"]} !important;
    border-radius: 8px !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
}}
[data-testid="collapsedControl"] {{ z-index: 100000 !important; }}

[data-testid="stSidebarCollapseButton"] button span,
[data-testid="collapsedControl"] button span,
[data-testid="stSidebarCollapsedControl"] button span,
[data-testid="stExpandSidebarButton"] span,
[data-testid="stIconMaterial"] {{
    font-family: "Material Symbols Rounded" !important;
}}

footer {{ visibility: hidden !important; }}
#MainMenu {{ display: none !important; }}

[data-testid="stSidebar"] {{
    background: {t["sidebar_bg"]} !important;
    border-right: 1px solid {t["sidebar_border"]} !important;
    box-shadow: {t["sidebar_shadow"]} !important;
}}
[data-testid="stSidebar"] > div {{ background: {t["sidebar_bg"]} !important; }}
section[data-testid="stSidebar"] * {{ color: {t["text_body"]} !important; }}

h1, h2, h3, h4, h5, h6 {{ color: {t["text_h"]} !important; }}
h1 {{
    font-family: 'Playfair Display', serif !important;
    font-weight: 400 !important;
    font-size: 2rem !important;
    letter-spacing: -0.5px !important;
    line-height: 1.15 !important;
}}

@media (max-width: 768px) {{
    .main .block-container {{
        padding-top: 3rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }}
    h1 {{ font-size: 1.5rem !important; }}
    [data-testid="stMetricValue"] {{ font-size: 1.5rem !important; }}
    [data-testid="metric-container"] {{ padding: 12px 14px 12px !important; }}
    [data-testid="stTabs"] [data-baseweb="tab"] {{
        padding: 10px 12px !important;
        font-size: 9px !important;
    }}
    [data-testid="stSidebar"] {{ width: 85% !important; }}
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"] {{
        position: fixed !important;
        top: 0.5rem !important;
        left: 0.5rem !important;
        z-index: 999999 !important;
    }}
    [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"] button,
    [data-testid="stSidebarCollapsedControl"] button {{
        min-width: 44px !important;
        min-height: 44px !important;
    }}
}}

hr {{
    border: none !important;
    border-top: 1px solid {t["divider"]} !important;
    margin: 1.5rem 0 !important;
}}

[data-testid="stDownloadButton"] button,
[data-testid="stButton"] button {{
    background: {C_ORANGE} !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 100px !important;
    font-weight: 600 !important;
    font-size: 12.5px !important;
    letter-spacing: 0.3px !important;
    padding: 10px 24px !important;
    box-shadow: 0 2px 10px rgba(232,98,10,0.28) !important;
    transition: all 0.2s ease !important;
}}
[data-testid="stDownloadButton"] button:hover,
[data-testid="stButton"] button:hover {{
    background: {C_ORANGE_LT} !important;
    box-shadow: 0 4px 18px rgba(232,98,10,0.4) !important;
    transform: translateY(-1px) !important;
    color: #FFFFFF !important;
}}

[data-baseweb="select"] > div {{
    background: {t["input_bg"]} !important;
    border: 1.5px solid {t["input_border"]} !important;
    border-radius: 11px !important;
    color: {t["text_input"]} !important;
    min-height: 44px !important;
}}
[data-baseweb="select"] > div:focus-within {{
    border-color: {C_ORANGE} !important;
    box-shadow: {t["input_shadow_f"]} !important;
}}
[data-baseweb="select"] span {{ color: {t["text_input"]} !important; }}

[data-testid="metric-container"] {{
    background: {t["card_bg"]} !important;
    border: 1px solid {t["card_border"]} !important;
    border-radius: 18px !important;
    padding: 20px 22px 18px !important;
    box-shadow: {t["card_shadow"]} !important;
    transition: box-shadow 0.2s ease, transform 0.2s ease, border-color 0.2s ease !important;
    position: relative !important;
    overflow: hidden !important;
}}
[data-testid="stMetricLabel"] {{
    font-size: 10.5px !important;
    font-weight: 700 !important;
    letter-spacing: 1.2px !important;
    text-transform: uppercase !important;
    color: {t["text_muted"]} !important;
}}
[data-testid="stMetricValue"] {{
    font-size: 2.2rem !important;
    font-weight: 800 !important;
    color: {t["text_h"]} !important;
    line-height: 1.1 !important;
    letter-spacing: -0.5px !important;
}}

[data-testid="stTabs"] > div:first-child {{
    border-bottom: 1.5px solid {t["divider"]} !important;
    gap: 4px !important;
    padding-bottom: 0 !important;
    background: transparent !important;
}}
button[data-baseweb="tab"] {{
    font-weight: 700 !important;
    font-size: 10.5px !important;
    letter-spacing: 1.2px !important;
    text-transform: uppercase !important;
    color: {t["text_muted"]} !important;
    padding: 12px 18px !important;
    background: transparent !important;
    border: none !important;
    border-radius: 10px 10px 0 0 !important;
    margin-bottom: -1.5px !important;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
    color: {C_ORANGE} !important;
    border-bottom: 2.5px solid {C_ORANGE} !important;
    background: {t["tag_bg"]} !important;
}}
[data-baseweb="tab-panel"] {{ padding-top: 28px !important; background: transparent !important; }}
</style>
"""
    st.markdown(css, unsafe_allow_html=True)
inject_css(T)

PBG  = T["plot_bg"]
PFG  = T["plot_font"]
PGRD = T["plot_grid"]


# ══════════════════════════════════════════════════════════════════
# 5 · DATEN LADEN
# ══════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def load_google(path: str = "Senzera_Dashboard_Data.csv") -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, sep=";")
        if len(df.columns) <= 1:
            df = pd.read_csv(path, sep=",")
    except Exception:
        df = pd.read_csv(path, sep=",")
    missing = REQ_GOOGLE - set(df.columns)
    if missing:
        st.error(f"Fehlende Spalten in Google-CSV: {missing}")
        st.stop()
    for col, default in [("Monat", "Unbekannt"), ("NPS", None)]:
        if col not in df.columns:
            df[col] = default
    if "NewReviews"   not in df.columns: df["NewReviews"]   = 0
    if "TotalReviews" not in df.columns: df["TotalReviews"] = None
    df["Studio_Name"]  = df["Studiokürzel"] + " (" + df["Stadt"] + ")"
    df["Rating"]       = pd.to_numeric(df["Rating"],       errors="coerce")
    df["NewReviews"]   = pd.to_numeric(df["NewReviews"],   errors="coerce").fillna(0).astype(int)
    df["TotalReviews"] = pd.to_numeric(df["TotalReviews"], errors="coerce")
    return df

df_google = load_google()

if df_google.empty:
    st.error("❌ **'Senzera_Dashboard_Data.csv'** nicht gefunden.")
    st.stop()


# ══════════════════════════════════════════════════════════════════
# 6 · HELFER
# ══════════════════════════════════════════════════════════════════
def rating_icon(r: float) -> str:
    return "✅" if r >= RATING_GOOD else ("⚠️" if r >= RATING_MIN else "🚨")

def badge(text: str, bg: str = None, fg: str = None) -> str:
    bg_ = bg or T["tag_bg"]
    fg_ = fg or T["tag_fg"]
    return (f"<span style='display:inline-flex;align-items:center;padding:4px 13px;"
            f"background:{bg_};color:{fg_};border-radius:100px;font-size:10.5px;"
            f"font-weight:700;letter-spacing:0.6px;white-space:nowrap;"
            f"text-transform:uppercase;border:1px solid rgba(232,98,10,0.15);'>{text}</span>")

def section_title(title: str, sub: str = "") -> None:
    sub_html = (f"<div style='font-size:11.5px;color:{T['text_muted']};margin-top:3px;"
                f"letter-spacing:0.1px;font-weight:400;'>{sub}</div>") if sub else ""
    st.markdown(
        f"""<div style='margin-bottom:16px;padding-bottom:10px;border-bottom:1px solid {T["divider"]};'>
            <div style='display:flex;align-items:center;gap:10px;'>
                <div style='width:4px;height:20px;background:linear-gradient(180deg,{C_ORANGE} 0%,{C_ORANGE_LT} 100%);border-radius:3px;flex-shrink:0;'></div>
                <span style='font-size:13.5px;font-weight:700;color:{T["text_h"]};letter-spacing:0.2px;text-transform:uppercase;font-family:"Plus Jakarta Sans",sans-serif;'>{title}</span>
            </div>{sub_html}</div>""", unsafe_allow_html=True)

def plotly_base() -> dict:
    return dict(plot_bgcolor=PBG, paper_bgcolor=PBG, font=dict(color=PFG, family="Plus Jakarta Sans", size=12), showlegend=False)


# ══════════════════════════════════════════════════════════════════
# 7 · SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        f"""<div style='padding:24px 8px 20px;border-bottom:1px solid {T["sidebar_border"]};margin-bottom:22px;'>
            <div style='text-align:center;padding:18px 14px;background:linear-gradient(135deg,{C_CREAM},#FFFFFF);border-radius:16px;box-shadow:0 2px 10px rgba(0,0,0,0.05);'>
                <div style='font-family:"Playfair Display",serif;font-size:32px;font-weight:600;
                            background:linear-gradient(135deg,{C_BLACK},{C_ORANGE});
                            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                            letter-spacing:-1px;line-height:1;'>
                    Senzera
                </div>
                <div style='font-size:9px;letter-spacing:3px;text-transform:uppercase;
                            color:{C_STONE};font-weight:600;margin-top:4px;'>
                    waxing · beauty
                </div>
            </div>
            <div style='text-align:center;margin-top:12px;'>
                <span style='font-size:8.5px;letter-spacing:3.5px;text-transform:uppercase;
                            font-weight:800;
                            background:linear-gradient(135deg,{C_ORANGE},{C_HONEY});
                            -webkit-background-clip:text;-webkit-text-fill-color:transparent;'>
                    Performance Hub
                </span>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""<div style='display:flex;align-items:center;gap:8px;margin-bottom:16px;'>
            <div style='flex:1;height:1px;background:{T["divider"]};'></div>
            <div style='font-size:9px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:{T["text_muted"]};'>Filter</div>
            <div style='flex:1;height:1px;background:{T["divider"]};'></div>
        </div>""", unsafe_allow_html=True)

    rl_opts = ["Alle"] + sorted(df_google["Regionalleitung"].dropna().unique().tolist())
    sel_rl  = st.selectbox("Regionalleitung", rl_opts)
    df_rl   = df_google if sel_rl == "Alle" else df_google[df_google["Regionalleitung"] == sel_rl]

    if "prev_rl" not in st.session_state:
        st.session_state.prev_rl = sel_rl
    rl_changed = sel_rl != st.session_state.prev_rl
    if rl_changed:
        st.session_state.prev_rl = sel_rl
        st.session_state.rl_version = st.session_state.get("rl_version", 0) + 1

    all_months = sorted(df_rl["Monat"].dropna().unique().tolist())
    if len(all_months) > 1:
        sel_monat = st.selectbox("Berichtsmonat", all_months, index=len(all_months) - 1)
    else:
        sel_monat = all_months[-1] if all_months else "Unbekannt"
        st.markdown(f"<div style='padding:10px 12px;background:{T['card_bg']};border:1px solid {T['card_border']};border-radius:11px;font-size:13px;color:{T['text_body']};margin-bottom:12px;'>📅 <b>{sel_monat}</b></div>", unsafe_allow_html=True)

    studio_opts = sorted(df_rl["Studio_Name"].unique().tolist())
    st.markdown(f"<div style='margin-bottom:6px;'><span style='font-size:10px;font-weight:700;letter-spacing:1.2px;text-transform:uppercase;color:{T['text_muted']};'>Studios</span></div>", unsafe_allow_html=True)

    rl_ver = st.session_state.get("rl_version", 0)
    sel_studios = st.multiselect(
        "Studios", studio_opts, default=studio_opts,
        label_visibility="collapsed", key=f"sel_studios_v{rl_ver}",
    )

    if not sel_studios:
        st.warning("⚠️ Bitte mindestens ein Studio wählen.")
        st.stop()

    n_sel = len(sel_studios)
    n_all = len(studio_opts)
    fill_pct = int(n_sel / n_all * 100) if n_all else 0
    st.markdown(
        f"""<div style='margin-top:12px;padding:14px 16px;background:{T["summary_bg"]};border-radius:12px;border:1px solid rgba(232,98,10,0.18);'>
            <div style='display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:8px;'>
                <div>
                    <div style='font-size:9.5px;font-weight:700;letter-spacing:1.3px;text-transform:uppercase;color:{T["text_muted"]};margin-bottom:3px;'>Auswahl</div>
                    <div style='font-size:22px;font-weight:800;color:{T["text_h"]};line-height:1;'>{n_sel}</div>
                </div>
                <div style='font-size:12px;color:{T["text_muted"]};text-align:right;'>von {n_all}<br>Studios</div>
            </div>
            <div style='background:rgba(0,0,0,0.06);height:5px;border-radius:3px;overflow:hidden;'>
                <div style='width:{fill_pct}%;height:100%;background:linear-gradient(90deg,{C_ORANGE},{C_ORANGE_LT});border-radius:3px;'></div>
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown(f"<div style='height:1px;background:linear-gradient(90deg,transparent,{T['sidebar_border']},transparent);margin:18px 0;'></div>", unsafe_allow_html=True)

    if st.button("🔄 Cache leeren & neu laden", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown(
        f"""<div style='display:flex;align-items:center;gap:8px;margin:20px 0 12px;'>
            <div style='flex:1;height:1px;background:{T["divider"]};'></div>
            <div style='font-size:9px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:{T["text_muted"]};'>Darstellung</div>
            <div style='flex:1;height:1px;background:{T["divider"]};'></div>
        </div>""", unsafe_allow_html=True)
    theme_choice = st.radio("Darstellung", list(THEMES.keys()), horizontal=True, index=list(THEMES.keys()).index(st.session_state.theme), label_visibility="collapsed")
    if theme_choice != st.session_state.theme:
        st.session_state.theme = theme_choice
        st.rerun()


# ══════════════════════════════════════════════════════════════════
# 8 · DATEN FILTERN & KPIs
# ══════════════════════════════════════════════════════════════════
df_view  = df_rl[df_rl["Studio_Name"].isin(sel_studios)].copy()
df_curr  = df_view[df_view["Monat"] == sel_monat].copy()
months_s = sorted(df_view["Monat"].dropna().unique().tolist())
idx_curr = months_s.index(sel_monat) if sel_monat in months_s else -1
vormonat = months_s[idx_curr - 1] if idx_curr > 0 else None
df_vm    = df_view[df_view["Monat"] == vormonat].copy() if vormonat else pd.DataFrame()

avg_rating = df_curr["Rating"].mean() if not df_curr.empty else 0.0
new_rev    = int(df_curr["NewReviews"].sum()) if not df_curr.empty else 0
if "TotalReviews" in df_curr.columns and df_curr["TotalReviews"].notna().any():
    total_rev = int(df_curr["TotalReviews"].sum())
else:
    total_rev = int(df_view["NewReviews"].sum())
avg_r_vm  = df_vm["Rating"].mean() if not df_vm.empty else None
delta_r   = round(avg_rating - avg_r_vm, 2) if avg_r_vm is not None else None
crit      = df_curr[df_curr["Rating"] < RATING_MIN]
n_crit    = len(crit)


# ══════════════════════════════════════════════════════════════════
# 9 · HEADER
# ══════════════════════════════════════════════════════════════════
hc1, hc2 = st.columns([5, 1])
with hc1:
    badges_html = " ".join([
        badge("Management Cockpit"),
        badge(sel_monat, T["card_bg"], T["text_second"]),
        badge(sel_rl, T["card_bg"], T["text_second"]),
    ])
    studio_s = "s" if n_sel != 1 else ""
    vgl_html = f"&nbsp;·&nbsp; Vergleich zu <b>{vormonat}</b>" if vormonat else ""
    st.markdown(
        f"""<div style='margin-bottom:20px;'>
            <div style='display:flex;align-items:center;gap:7px;margin-bottom:12px;flex-wrap:wrap;'>{badges_html}</div>
            <div style='display:flex;align-items:flex-end;gap:14px;margin-bottom:6px;'>
                <h1 style='margin:0;font-family:"Playfair Display",serif;font-size:2.2rem;font-weight:400;letter-spacing:-0.5px;line-height:1.1;color:{T["text_h"]};'>Studio-Performance</h1>
                <div style='width:40px;height:3px;background:linear-gradient(90deg,{C_ORANGE},{C_ORANGE_LT});border-radius:2px;margin-bottom:8px;flex-shrink:0;'></div>
            </div>
            <div style='font-size:13.5px;color:{T["text_muted"]};font-weight:400;letter-spacing:0.1px;'>{n_sel} Studio{studio_s} aktiv {vgl_html}</div>
        </div>""", unsafe_allow_html=True)
with hc2:
    if n_crit > 0: st.error(f"🚨 {n_crit} kritisch")
    else: st.success("✅ Alles OK")


# ══════════════════════════════════════════════════════════════════
# 10 · KPIs (3 Google-Kacheln)
# ══════════════════════════════════════════════════════════════════
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
k1, k2, k3 = st.columns(3)
k1.metric(
    "Google Ø-Rating",
    f"{avg_rating:.2f} ⭐",
    delta=f"{delta_r:+.2f} vs. {vormonat}" if delta_r is not None else None,
    delta_color="normal" if delta_r and delta_r >= 0 else "inverse",
    help=f"Durchschnittliches Sterne-Rating der ausgewählten Studios. Unter {RATING_MIN} ★ = kritisch.",
)
k2.metric(
    "Neue Rezensionen",
    f"{new_rev:,}".replace(",", "."),
    delta=sel_monat,
    delta_color="off",
    help="Wie viele neue Google-Bewertungen die ausgewählten Studios diesen Monat dazubekommen haben.",
)
k3.metric(
    "Rezensionen Gesamt",
    f"{total_rev:,}".replace(",", "."),
    delta="alle Monate",
    delta_color="off",
    help="Summe aller verfügbaren Google-Rezensionen der gewählten Studios (alle Monate).",
)


# ══════════════════════════════════════════════════════════════════
# 11 · ALARM
# ══════════════════════════════════════════════════════════════════
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
if not crit.empty:
    st.markdown(
        f"""<div style='background:linear-gradient(135deg,rgba(200,48,16,0.07),rgba(200,48,16,0.03));border:1px solid rgba(200,48,16,0.2);border-left:4px solid {C_RED};border-radius:14px;padding:14px 20px;margin-bottom:16px;display:flex;align-items:center;gap:12px;'>
            <div style='font-size:22px;'>🚨</div>
            <div><div style='font-size:12px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:{C_RED};margin-bottom:2px;'>Handlungsbedarf</div>
            <div style='font-size:13.5px;font-weight:500;color:{T["text_h"]};'>{n_crit} Studio{'s' if n_crit > 1 else ''} unter {RATING_MIN} Sternen</div></div>
        </div>""", unsafe_allow_html=True)
    alarm_cols = st.columns(min(n_crit, 4))
    for idx, (_, row) in enumerate(crit.iterrows()):
        with alarm_cols[idx % 4]:
            r_color = C_RED if row["Rating"] < 4.0 else C_HONEY
            st.markdown(
                f"""<div style='background:{T["card_bg"]};border:1px solid rgba(200,48,16,0.15);border-top:3px solid {r_color};border-radius:14px;padding:16px 18px;margin-bottom:4px;box-shadow:{T["card_shadow"]};'>
                    <div style='font-size:15px;font-weight:700;color:{T["text_h"]};margin-bottom:2px;'>{row["Studiokürzel"]}</div>
                    <div style='font-size:12px;color:{T["text_muted"]};margin-bottom:10px;'>{row["Stadt"]}</div>
                    <div style='display:flex;gap:8px;flex-wrap:wrap;align-items:center;'>
                        <span style='font-size:18px;font-weight:800;color:{r_color};line-height:1;'>{row["Rating"]:.2f}</span>
                        <span style='font-size:11px;color:{T["text_muted"]};padding-top:3px;'>⭐ · +{row["NewReviews"]} Rez.</span>
                    </div></div>""", unsafe_allow_html=True)
else:
    st.markdown(
        f"""<div style='background:{T["ok_bg"]};border:1px solid rgba(58,138,80,0.2);border-left:4px solid {C_MINT};border-radius:14px;padding:14px 20px;margin-bottom:16px;display:flex;align-items:center;gap:12px;'>
            <div style='font-size:20px;'>✅</div>
            <div><div style='font-size:12px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:{C_GREEN};margin-bottom:2px;'>Alles im grünen Bereich</div>
            <div style='font-size:13px;color:{T["text_h"]};'>Alle {n_sel} Studios über {RATING_MIN} Sternen</div></div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# 12 · TABS
# ══════════════════════════════════════════════════════════════════
tab1, tab2 = st.tabs(["  📊  Performance & Trends  ", "  📝  Management-Bericht  "])


# ──────────────────────────────────────────────────────────────────
# TAB 1 · PERFORMANCE & TRENDS
# ──────────────────────────────────────────────────────────────────
with tab1:
    with st.expander("ℹ️ Was sehe ich hier?", expanded=False):
        st.markdown(
            "**Performance & Trends** zeigt das Google-Bewertungs-Ranking aller ausgewählten Studios "
            f"für den **Berichtsmonat** (Sidebar). Studios mit rotem Punkt liegen unter "
            f"**{RATING_MIN} ★** und brauchen Aufmerksamkeit. Rechts: monatlicher Trend des "
            "Durchschnitts-Ratings."
        )

    col_l, col_r = st.columns(2, gap="large")
    with col_l:
        section_title("Google Ranking", f"Bewertungen im Monat {sel_monat}")
        df_rk = df_curr.sort_values("Rating", ascending=True).copy()
        bar_c = df_rk["Rating"].apply(lambda r: C_RED if r < RATING_MIN else (C_HONEY if r < RATING_GOOD else C_MINT)).tolist()
        fig_rk = go.Figure(go.Bar(
            x=df_rk["Rating"], y=df_rk["Studiokürzel"],
            orientation="h",
            marker=dict(color=bar_c, line=dict(width=0)),
            text=df_rk["Rating"].apply(lambda r: f"{r:.2f}"),
            textposition="outside", textfont=dict(color=PFG, size=12),
            hovertemplate="<b>%{y}</b><br>⭐ %{x:.2f}<extra></extra>",
        ))
        fig_rk.add_vline(x=RATING_MIN, line_dash="dash", line_color=C_RED, line_width=1.5, opacity=0.6,
                         annotation=dict(text=f"Min. {RATING_MIN}", font=dict(size=10, color=C_RED), bgcolor="rgba(0,0,0,0)"))
        fig_rk.update_layout(**plotly_base(),
                             xaxis=dict(range=[3.5, 5.25], gridcolor=PGRD, zeroline=False, tickfont=dict(size=11)),
                             yaxis=dict(tickfont=dict(size=11, color=T["text_second"])),
                             margin=dict(l=4, r=55, t=8, b=8),
                             height=max(260, len(df_rk) * 32),
                             bargap=0.38)
        st.plotly_chart(fig_rk, use_container_width=True)

    with col_r:
        section_title("Trend-Verlauf", "Monatlicher Ø-Rating")
        trend = df_view.groupby("Monat", sort=False)["Rating"].mean().reset_index().rename(columns={"Rating": "Ø Rating"})
        if not trend.empty:
            fig_tr = go.Figure()
            fig_tr.add_trace(go.Scatter(
                x=trend["Monat"], y=trend["Ø Rating"],
                fill="tozeroy", fillcolor="rgba(232,98,10,0.06)",
                line=dict(width=0), showlegend=False, hoverinfo="skip"))
            fig_tr.add_trace(go.Scatter(
                x=trend["Monat"], y=trend["Ø Rating"],
                line=dict(color=C_ORANGE, width=2.5),
                marker=dict(size=9, color=C_ORANGE, line=dict(width=2.5, color=T["app_bg"])),
                mode="lines+markers",
                hovertemplate="<b>%{x}</b><br>Ø %{y:.2f}<extra></extra>",
            ))
            fig_tr.add_hline(y=RATING_MIN, line_dash="dot", line_color=C_RED, line_width=1.5,
                             annotation=dict(text=f"Min. {RATING_MIN}", font=dict(size=10, color=C_RED), bgcolor="rgba(0,0,0,0)"))
            fig_tr.update_layout(**plotly_base(),
                                 yaxis=dict(title="Ø Rating", gridcolor=PGRD, zeroline=False, range=[3.8, 5.05], title_font=dict(size=11, color=T["text_muted"])),
                                 xaxis=dict(gridcolor=PGRD, zeroline=False, title=""),
                                 height=max(260, len(df_rk) * 32),
                                 margin=dict(l=4, r=20, t=8, b=8))
            st.plotly_chart(fig_tr, use_container_width=True)

    st.divider()
    section_title("Detail-Tabelle", f"Alle Studios · {sel_monat}")
    disp_c = [c for c in ["Studiokürzel", "Stadt", "Rating", "NewReviews", "TotalReviews", "Regionalleitung"] if c in df_curr.columns]
    df_show = df_curr[disp_c].sort_values("Rating", ascending=False).copy()
    st.dataframe(df_show, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────────
# TAB 2 · MANAGEMENT-BERICHT (alle Downloads hier)
# ──────────────────────────────────────────────────────────────────
with tab2:
    with st.expander("ℹ️ Was sehe ich hier?", expanded=False):
        st.markdown(
            "**Management-Bericht** ist ein automatisch generierter Textbericht für den "
            "Berichtsmonat — eignet sich 1:1 als Mail-Body für die monatliche RL-Runde. "
            "Darunter sind die Download-Buttons gebündelt: Bericht als Text, Snapshot-CSV "
            "und alle Google-Daten."
        )
    section_title("Management-Bericht", "Automatisch aus echten Daten · Trend-Analyse, Insights und Handlungsempfehlungen")

    studios_s = df_curr.sort_values("Rating", ascending=False)
    top3 = studios_s.head(3)

    verbessert, verschlechtert = [], []
    if not df_vm.empty:
        vm_r = df_vm.set_index("Studiokürzel")["Rating"]
        for _, row in df_curr.iterrows():
            old = vm_r.get(row["Studiokürzel"])
            if old is not None:
                dv = row["Rating"] - old
                if dv >= 0.1:    verbessert.append(f"{row['Studiokürzel']} (+{dv:.1f})")
                elif dv <= -0.1: verschlechtert.append(f"{row['Studiokürzel']} ({dv:.1f})")

    jetzt = datetime.now().strftime("%d.%m.%Y %H:%M")
    s1 = "═" * 56
    s2 = "─" * 56

    lines = [
        "SENZERA MANAGEMENT-BERICHT",
        f"Region    : {sel_rl}", f"Monat     : {sel_monat}", f"Erstellt  : {jetzt}",
        s1, "",
        "I.  ÜBERBLICK", s2,
        f"  Google Ø-Rating          : {avg_rating:.2f} ⭐" + (f"   ({delta_r:+.2f} ggü. {vormonat})" if delta_r is not None else ""),
        f"  Neue Rezensionen         : {new_rev}",
        f"  Google Rez. Gesamt       : {total_rev}",
        "",
    ]
    if avg_rating >= RATING_GOOD:    lines.append("  💚 Gesamtbewertung: STARK – Region über Zielmarke.")
    elif avg_rating >= RATING_MIN:   lines.append("  🟡 Gesamtbewertung: SOLIDE – Einzelne Studios brauchen Aufmerksamkeit.")
    else:                            lines.append("  🔴 Gesamtbewertung: KRITISCH – Sofortmaßnahmen erforderlich!")

    lines += ["", "II.  TREND", s2]
    if verbessert:        lines.append(f"  📈 Verbessert vs. {vormonat}     : {', '.join(verbessert)}")
    if verschlechtert:    lines.append(f"  📉 Verschlechtert vs. {vormonat} : {', '.join(verschlechtert)}")
    if not verbessert and not verschlechtert:
        lines.append("  ➡  Nur ein Monat verfügbar – kein Trendvergleich möglich.")

    lines += ["", "III. STUDIO-STATUS", s2]
    for _, row in studios_s.iterrows():
        kstr = "  ← KRITISCH!" if row["Rating"] < RATING_MIN else ""
        lines.append(f"  {rating_icon(row['Rating'])}  {row['Studiokürzel']:<6} {row['Rating']:.2f} ⭐  (+{row['NewReviews']} Rez.){kstr}")

    lines += ["", "IV.  HIGHLIGHTS", s2, "  🏆 TOP-STUDIOS:"]
    for _, row in top3.iterrows():
        lines.append(f"      • {row['Studiokürzel']} ({row['Stadt']}): {row['Rating']:.2f} ⭐")

    if n_crit > 0:
        lines += ["", "  🚨 HANDLUNGSBEDARF:"]
        for _, row in crit.iterrows():
            lines.append(f"      • {row['Studiokürzel']} ({row['Stadt']}): {row['Rating']:.2f} ⭐")
        lines += [
            "",
            "  Empfohlene Maßnahmen:",
            "      1.  Sofortgespräch mit Studioleitung (diese Woche)",
            "      2.  Google-Rezensionen der letzten 30 Tage analysieren",
            "      3.  Konkrete Maßnahmen festlegen (Frist: 2 Wochen)",
            "      4.  Wöchentliches Follow-up einplanen",
        ]

    lines += ["", s1, f"Senzera Performance Hub v7  ·  {jetzt}", s1]
    bericht = "\n".join(lines)
    st.text_area("", value=bericht, height=540, label_visibility="collapsed")

    # ── Downloads ───────────────────────────────────────────────
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    section_title("Downloads", "Berichte und Daten-Exporte")
    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            "📄 Bericht als .txt",
            data=bericht.encode("utf-8"),
            file_name=f"Senzera_Bericht_{sel_rl}_{sel_monat}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with dl2:
        snap = [c for c in ["Studiokürzel", "Stadt", "Rating", "NewReviews", "TotalReviews"] if c in df_curr.columns]
        st.download_button(
            "📥 Daten-Snapshot (CSV)",
            data=df_curr[snap].to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
            file_name=f"Senzera_Snapshot_{sel_rl}_{sel_monat}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    dl3, _ = st.columns(2)
    with dl3:
        st.download_button(
            "📥 Alle Google-Daten (CSV)",
            data=df_view.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
            file_name=f"Senzera_Google_{sel_monat}.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ══════════════════════════════════════════════════════════════════
# 13 · FOOTER
# ══════════════════════════════════════════════════════════════════
st.divider()
st.markdown(
    f"""<div style='display:flex;align-items:center;justify-content:space-between;padding:28px 0 16px;'>
        <div>
            <div style='font-size:13px;font-weight:700;color:{T["text_h"]};font-family:"Playfair Display",serif;'>Performance Hub</div>
            <div style='font-size:10px;color:{T["text_muted"]};letter-spacing:0.3px;'>v7 · waxing & beauty</div>
        </div>
        <div style='text-align:right;'>
            <div style='font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:{T["text_muted"]};margin-bottom:2px;'>Datenschutz</div>
            <div style='font-size:11px;color:{C_ORANGE};font-weight:600;'>Alle Daten lokal · Keine Übertragung</div>
        </div>
    </div>""", unsafe_allow_html=True)
