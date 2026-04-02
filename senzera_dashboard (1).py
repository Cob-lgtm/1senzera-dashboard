"""
Senzera Performance Hub – v5.2 (Mobile Optimized)
============================================
Starten:  streamlit run senzera_dashboard.py
Dateien:  Senzera_Dashboard_Data.csv  +  Zenloop_Antworten.csv
"""

from __future__ import annotations
import base64
import json
import os
from datetime import datetime
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_OK = True
except ImportError:
    CRYPTO_OK = False

# ══════════════════════════════════════════════════════════════════════════════════════════
# 1 · PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Senzera Performance Hub",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- GOOGLE UNSICHTBAR-MANTEL ---
st.markdown(
    """
    <style>
        .hide-from-google { display: none; }
    </style>
    <meta name="robots" content="noindex, nofollow">
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════════════════
# 2 · SENZERA CI
# ══════════════════════════════════════════════════════════════════════════════════════════
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
C_MINT_PALE   = "#EAF4ED"
C_LILAC       = "#B8A0BC"
C_GREEN       = "#3A8A50"
C_RED         = "#C83010"
C_RED_PALE    = "#FDEEE8"

RATING_MIN  = 4.2
RATING_GOOD = 4.5
REQ_GOOGLE  = {"Studiokürzel", "Stadt", "Regionalleitung", "Rating"}
REQ_ZEN     = {"Property - studio", "score_type", "score"}

# ══════════════════════════════════════════════════════════════════════════════════════════
# 3 · THEME DEFINITIONEN
# ══════════════════════════════════════════════════════════════════════════════════════════
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

# ══════════════════════════════════════════════════════════════════════════════════════════
# 4 · CSS INJECTION
# ══════════════════════════════════════════════════════════════════════════════════════════
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

[data-testid="metric-container"] {{
    animation: fadeSlideUp 0.4s ease both;
}}
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
.main .block-container {{
    background: {t["app_bg"]} !important;
}}
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

/* WICHTIG: Hamburger-Menü auf Handys sichtbar machen! */
[data-testid="stSidebarCollapseButton"] {{
    color: {C_ORANGE} !important;
    background-color: {t["card_bg"]} !important;
    border-radius: 8px !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
}}
[data-testid="collapsedControl"] {{
    z-index: 100000 !important;
}}

/* Fix: Material Icons für Sidebar-Toggle wiederherstellen */
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
[data-testid="stSidebar"] > div {{
    background: {t["sidebar_bg"]} !important;
}}
section[data-testid="stSidebar"] * {{
    color: {t["text_body"]} !important;
}}

h1, h2, h3, h4, h5, h6 {{ color: {t["text_h"]} !important; }}
h1 {{
    font-family: 'Playfair Display', serif !important;
    font-weight: 400 !important;
    font-size: 2rem !important;
    letter-spacing: -0.5px !important;
    line-height: 1.15 !important;
}}

/* MOBILE OPTIMIERUNGEN */
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
    [data-testid="stSidebar"] {{
        width: 85% !important;
    }}
    /* Mobile: Burger-Button besser sichtbar und klickbar */
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


# ══════════════════════════════════════════════════════════════════════════════════════════
# 5 · DATEN LADEN
# ══════════════════════════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner="🌸  Daten werden geladen …")
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
    df["NewReviews"]   = pd.to_numeric(df["NewReviews"],  errors="coerce").fillna(0).astype(int)
    df["NPS"]          = pd.to_numeric(df["NPS"],          errors="coerce")
    df["TotalReviews"] = pd.to_numeric(df["TotalReviews"], errors="coerce")
    return df

@st.cache_data(show_spinner=False)
def load_zenloop(path: str = "Zenloop_Antworten.csv") -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, sep=";")
        if len(df.columns) <= 1:
            df = pd.read_csv(path, sep=",")
    except Exception:
        df = pd.read_csv(path, sep=",")
    df["score"] = pd.to_numeric(df.get("score", pd.Series(dtype=float)), errors="coerce")
    if "date_received" in df.columns:
        df["date_received"] = pd.to_datetime(df["date_received"], errors="coerce")
        df["Monat_zen"]     = df["date_received"].dt.to_period("M").astype(str)
    return df

df_google  = load_google()
df_zenloop = load_zenloop()

if df_google.empty:
    st.error("❌ **'Senzera_Dashboard_Data.csv'** nicht gefunden.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════════════════
# 6 · HELFER
# ══════════════════════════════════════════════════════════════════════════════════════════
def calc_nps(df: pd.DataFrame) -> Optional[float]:
    if df.empty or "score_type" not in df.columns: return None
    total = len(df)
    if total == 0: return None
    p = (df["score_type"] == "promoter").sum()
    d = (df["score_type"] == "detractor").sum()
    return round((p - d) / total * 100, 1)

def calc_nps_score(df: pd.DataFrame) -> Optional[float]:
    if df.empty or "score" not in df.columns: return None
    s = df["score"].dropna()
    if s.empty: return None
    return round(((s >= 9).sum() - (s <= 6).sum()) / len(s) * 100, 1)

def get_nps(df: pd.DataFrame) -> Optional[float]:
    return calc_nps(df) or calc_nps_score(df)

def calc_sentiment(df: pd.DataFrame) -> Optional[float]:
    if df.empty or "sentiment" not in df.columns: return None
    c = df.dropna(subset=["comment"]) if "comment" in df.columns else df
    c = c[c["comment"].astype(str).str.strip().ne("nan")]
    if c.empty: return None
    return round((c["sentiment"] == "positive").sum() / len(c) * 100, 1)

def top_labels(df: pd.DataFrame, n: int = 6) -> pd.Series:
    if "labels" not in df.columns: return pd.Series(dtype=int)
    return (df["labels"].dropna().str.split(";").explode().str.strip().replace("", pd.NA).dropna().value_counts().head(n))

def neg_labels(df: pd.DataFrame, n: int = 4) -> pd.Series:
    if "labels" not in df.columns or "score_type" not in df.columns:
        return pd.Series(dtype=int)
    return top_labels(df[df["score_type"] == "detractor"], n)

def rating_icon(r: float) -> str:
    return "✅" if r >= RATING_GOOD else ("⚠️" if r >= RATING_MIN else "🚨")

def nps_label(n: float) -> str:
    if n >= 70: return "Weltklasse 🏆"
    if n >= 50: return "Exzellent 🌟"
    if n >= 30: return "Gut 👍"
    if n >= 0:  return "Ausbaufähig ⚠️"
    return "Kritisch 🚨"

def fmt_n(v: Optional[float]) -> str:
    return f"{v:.0f} ({nps_label(v)})" if v is not None else "keine Daten"

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

def label_bar(label: str, cnt: int, max_cnt: int, color: str = C_ORANGE, bg: str = None) -> None:
    pct = int(cnt / max_cnt * 100) if max_cnt > 0 else 0
    bg_ = bg or T["card_bg"]
    st.markdown(
        f"""<div style='display:flex;align-items:center;gap:10px;margin:5px 0;padding:9px 13px;background:{bg_};border:1px solid {T["card_border"]};border-radius:10px;'>
            <div style='flex:1;min-width:0;'>
                <div style='display:flex;justify-content:space-between;margin-bottom:5px;'>
                    <span style='font-size:13px;font-weight:500;color:{T["text_body"]};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:75%;'>{label}</span>
                    <span style='font-size:11.5px;font-weight:700;color:{color};'>{cnt}×</span>
                </div>
                <div style='background:{T["divider"]};height:4px;border-radius:3px;overflow:hidden;'>
                    <div style='width:{pct}%;height:100%;background:{color};border-radius:3px;transition:width 0.3s ease;'></div>
                </div>
            </div></div>""", unsafe_allow_html=True)

def plotly_base() -> dict:
    return dict(plot_bgcolor=PBG, paper_bgcolor=PBG, font=dict(color=PFG, family="Plus Jakarta Sans", size=12), showlegend=False)

# ══════════════════════════════════════════════════════════════════════════════════════════
# 7 · SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        f"""<div style='padding:24px 8px 20px;border-bottom:1px solid {T["sidebar_border"]};margin-bottom:22px;'>
            <div style='background:#FFFFFF;border-radius:18px;padding:24px 24px 20px;text-align:center;
                        box-shadow:0 4px 20px rgba(0,0,0,0.10), 0 1px 4px rgba(232,98,10,0.08);
                        position:relative;overflow:hidden;'>
                <div style='position:absolute;top:0;left:0;right:0;height:2.5px;
                            background:linear-gradient(90deg,{C_ORANGE},{C_HONEY},{C_ORANGE});'></div>
                <div style='font-family:"Playfair Display",serif;font-size:26px;font-weight:600;
                            color:{C_BLACK};letter-spacing:2px;line-height:1.2;'>
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


# ══════════════════════════════════════════════════════════════════════════════════════════
# 8 · DATEN FILTERN & KPIs
# ══════════════════════════════════════════════════════════════════════════════════════════
df_view  = df_rl[df_rl["Studio_Name"].isin(sel_studios)].copy()
df_curr  = df_view[df_view["Monat"] == sel_monat].copy()
months_s = sorted(df_view["Monat"].dropna().unique().tolist())
idx_curr = months_s.index(sel_monat) if sel_monat in months_s else -1
vormonat = months_s[idx_curr - 1] if idx_curr > 0 else None
df_vm    = df_view[df_view["Monat"] == vormonat].copy() if vormonat else pd.DataFrame()
sel_codes = df_curr["Studiokürzel"].unique()
df_zen   = df_zenloop[df_zenloop["Property - studio"].isin(sel_codes)].copy() if not df_zenloop.empty else pd.DataFrame()

avg_rating = df_curr["Rating"].mean() if not df_curr.empty else 0.0
new_rev    = int(df_curr["NewReviews"].sum()) if not df_curr.empty else 0
if "TotalReviews" in df_curr.columns and df_curr["TotalReviews"].notna().any():
    total_rev = int(df_curr["TotalReviews"].sum())
else:
    total_rev = int(df_view["NewReviews"].sum())
nps_ges   = get_nps(df_zen)
sentiment = calc_sentiment(df_zen)
n_zen     = len(df_zen)
avg_r_vm  = df_vm["Rating"].mean() if not df_vm.empty else None
delta_r   = round(avg_rating - avg_r_vm, 2) if avg_r_vm is not None else None
crit      = df_curr[df_curr["Rating"] < RATING_MIN]
n_crit    = len(crit)
codes_zen = sorted(df_zen["Property - studio"].dropna().unique().tolist()) if not df_zen.empty else []


# ══════════════════════════════════════════════════════════════════════════════════════════
# 9 · HEADER
# ══════════════════════════════════════════════════════════════════════════════════════════
hc1, hc2 = st.columns([5, 1])
with hc1:
    badges_html = " ".join([badge("Management Cockpit"), badge(sel_monat, T["card_bg"], T["text_second"]), badge(sel_rl, T["card_bg"], T["text_second"])])
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

# ══════════════════════════════════════════════════════════════════════════════════════════
# 10 · KPIs (3 + 3 Layout)
# ══════════════════════════════════════════════════════════════════════════════════════════
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
k1, k2, k3 = st.columns(3)
k1.metric("Google Ø-Rating", f"{avg_rating:.2f} ⭐", delta=f"{delta_r:+.2f} vs. {vormonat}" if delta_r is not None else None, delta_color="normal" if delta_r and delta_r >= 0 else "inverse")
k2.metric("Neue Rezensionen", f"{new_rev:,}".replace(",", "."), delta=sel_monat, delta_color="off")
k3.metric("Rezensionen Gesamt", f"{total_rev:,}".replace(",", "."), delta="alle Monate", delta_color="off", help="Summe aller verfügbaren Google-Rezensionen der gewählten Studios")

st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
k4, k5, k6 = st.columns(3)
if nps_ges is not None:
    k4.metric("Zenloop NPS", f"{nps_ges:.0f}", delta=nps_label(nps_ges), delta_color="normal" if nps_ges >= 0 else "inverse")
else:
    k4.metric("Zenloop NPS", "–", delta="keine Daten", delta_color="off")
k5.metric("Positive Stimmung", f"{sentiment:.0f}%" if sentiment is not None else "–", delta="der Kommentare", delta_color="off", help="Anteil positiver Kommentare")
k6.metric("Zenloop Antworten", f"{n_zen:,}".replace(",", "."), delta="Gesamtzeitraum", delta_color="off")

# ══════════════════════════════════════════════════════════════════════════════════════════
# 11 · ALARM
# ══════════════════════════════════════════════════════════════════════════════════════════
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
            zs = df_zen[df_zen["Property - studio"] == row["Studiokürzel"]] if not df_zen.empty else pd.DataFrame()
            sn = get_nps(zs)
            nl = neg_labels(zs, 2)
            nstr = f"NPS: <b>{sn:.0f}</b>" if sn is not None else ""
            nlstr = (f"<div style='margin-top:6px;font-size:11px;color:{C_RED};'>⚠️ {chr(160).join(nl.index.tolist())}</div>") if not nl.empty else ""
            r_color = C_RED if row["Rating"] < 4.0 else C_HONEY
            st.markdown(
                f"""<div style='background:{T["card_bg"]};border:1px solid rgba(200,48,16,0.15);border-top:3px solid {r_color};border-radius:14px;padding:16px 18px;margin-bottom:4px;box-shadow:{T["card_shadow"]};'>
                    <div style='font-size:15px;font-weight:700;color:{T["text_h"]};margin-bottom:2px;'>{row["Studiokürzel"]}</div>
                    <div style='font-size:12px;color:{T["text_muted"]};margin-bottom:10px;'>{row["Stadt"]}</div>
                    <div style='display:flex;gap:8px;flex-wrap:wrap;align-items:center;'>
                        <span style='font-size:18px;font-weight:800;color:{r_color};line-height:1;'>{row["Rating"]:.2f}</span>
                        <span style='font-size:11px;color:{T["text_muted"]};padding-top:3px;'>⭐ · +{row["NewReviews"]} Rez.</span>
                        {f'<span style="font-size:11px;color:{T["text_muted"]};padding-top:3px;">' + '·' + ' {nstr}</span>' if nstr else ""}
                    </div>{nlstr}</div>""", unsafe_allow_html=True)
else:
    st.markdown(
        f"""<div style='background:{T["ok_bg"]};border:1px solid rgba(58,138,80,0.2);border-left:4px solid {C_MINT};border-radius:14px;padding:14px 20px;margin-bottom:16px;display:flex;align-items:center;gap:12px;'>
            <div style='font-size:20px;'>✅</div>
            <div><div style='font-size:12px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:{C_GREEN};margin-bottom:2px;'>Alles im grünen Bereich</div>
            <div style='font-size:13px;color:{T["text_h"]};'>Alle {n_sel} Studios über {RATING_MIN} Sternen</div></div>
        </div>""", unsafe_allow_html=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════════════════
# 12 · TABS
# ══════════════════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs(["  📊  Performance & Trends  ", "  💙  Zenloop Deep-Dive  ", "  📝  Management-Bericht  ", "  🔐  Team-Performer  "])

# ──────────────────────────────────────────────────────────────────────────────────────────
# TAB 1 · PERFORMANCE & TRENDS
# ──────────────────────────────────────────────────────────────────────────────────────────
with tab1:
    col_l, col_r = st.columns(2, gap="large")
    with col_l:
        section_title("Google Ranking", f"Bewertungen im Monat {sel_monat}")
        df_rk = df_curr.sort_values("Rating", ascending=True).copy()
        bar_c = df_rk["Rating"].apply(lambda r: C_RED if r < RATING_MIN else (C_HONEY if r < RATING_GOOD else C_MINT)).tolist()
        fig_rk = go.Figure(go.Bar(x=df_rk["Rating"], y=df_rk["Studiokürzel"], orientation="h", marker=dict(color=bar_c, line=dict(width=0)), text=df_rk["Rating"].apply(lambda r: f"{r:.2f}"), textposition="outside", textfont=dict(color=PFG, size=12), hovertemplate="<b>%{y}</b><br>⭐ %{x:.2f}<extra></extra>"))
        fig_rk.add_vline(x=RATING_MIN, line_dash="dash", line_color=C_RED, line_width=1.5, opacity=0.6, annotation=dict(text=f"Min. {RATING_MIN}", font=dict(size=10, color=C_RED), bgcolor="rgba(0,0,0,0)"))
        fig_rk.update_layout(**plotly_base(), xaxis=dict(range=[3.5, 5.25], gridcolor=PGRD, zeroline=False, tickfont=dict(size=11)), yaxis=dict(tickfont=dict(size=11, color=T["text_second"])), margin=dict(l=4, r=55, t=8, b=8), height=max(260, len(df_rk) * 32), bargap=0.38)
        st.plotly_chart(fig_rk, use_container_width=True)

    with col_r:
        section_title("Trend-Verlauf", "Monatlicher Ø-Rating")
        trend = df_view.groupby("Monat", sort=False)["Rating"].mean().reset_index().rename(columns={"Rating": "Ø Rating"})
        fig_tr = go.Figure()
        fig_tr.add_trace(go.Scatter(x=trend["Monat"], y=trend["Ø Rating"], fill="tozeroy", fillcolor="rgba(232,98,10,0.07)", line=dict(width=0), showlegend=False, hoverinfo="skip"))
        fig_tr.add_trace(go.Scatter(x=trend["Monat"], y=trend["Ø Rating"], line=dict(color=C_ORANGE, width=2.5), marker=dict(size=8, color=C_ORANGE, line=dict(width=2.5, color=T["app_bg"])), mode="lines+markers", hovertemplate="<b>%{x}</b><br>Ø Rating: %{y:.2f}<extra></extra>"))
        y_min = max(3.0, trend["Ø Rating"].min() - 0.4)
        y_max = min(5.1, trend["Ø Rating"].max() + 0.3)
        fig_tr.add_hline(y=RATING_MIN, line_dash="dot", line_color=C_RED, line_width=1.5, opacity=0.5, annotation=dict(text=f"Kritisch {RATING_MIN}", font=dict(size=10, color=C_RED), bgcolor="rgba(0,0,0,0)"))
        fig_tr.add_hline(y=RATING_GOOD, line_dash="dot", line_color=C_MINT, line_width=1.5, opacity=0.5, annotation=dict(text=f"Gut {RATING_GOOD}", font=dict(size=10, color=C_MINT), bgcolor="rgba(0,0,0,0)"))
        fig_tr.update_layout(**plotly_base(), yaxis=dict(range=[y_min, y_max], gridcolor=PGRD, zeroline=False, tickfont=dict(size=11)), xaxis=dict(gridcolor=PGRD, zeroline=False, tickfont=dict(size=11)), margin=dict(l=4, r=68, t=8, b=8))
        st.plotly_chart(fig_tr, use_container_width=True)

    if len(months_s) > 1:
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        section_title("Neue Rezensionen / Monat", "Monatlicher Google-Zuwachs")
        rev_t = df_view.groupby("Monat", sort=False)["NewReviews"].sum().reset_index()
        fig_rv = go.Figure(go.Bar(x=rev_t["Monat"], y=rev_t["NewReviews"], marker=dict(color=[C_ORANGE if m == sel_monat else C_STONE for m in rev_t["Monat"]], line=dict(width=0)), text=rev_t["NewReviews"], textposition="outside", textfont=dict(color=PFG, size=11), hovertemplate="<b>%{x}</b><br>%{y} neue Rez.<extra></extra>"))
        fig_rv.update_layout(**plotly_base(), yaxis=dict(gridcolor=PGRD, zeroline=False), xaxis=dict(gridcolor="rgba(0,0,0,0)", zeroline=False), height=190, bargap=0.42, margin=dict(l=4, r=10, t=8, b=8))
        st.plotly_chart(fig_rv, use_container_width=True)

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    section_title("Studio-Übersicht", f"Sortiert nach Rating · {sel_monat}")
    disp_c = [c for c in ["Studio_Name", "Rating", "NewReviews", "TotalReviews", "NPS", "Regionalleitung"] if c in df_curr.columns]
    df_d = df_curr[disp_c].sort_values("Rating", ascending=False).reset_index(drop=True)
    df_d.insert(0, "Status", df_d["Rating"].apply(rating_icon))
    if not df_vm.empty:
        vm_map = df_vm.set_index("Studiokürzel")["Rating"].to_dict()
        def row_delta(row):
            m = df_curr[df_curr["Studio_Name"] == row.get("Studio_Name", "")]["Studiokürzel"]
            if m.empty: return ""
            old = vm_map.get(m.values[0])
            if old is None: return ""
            dv = round(row["Rating"] - old, 2)
            return f"+{dv}" if dv > 0 else str(dv)
        df_d["Δ Vormonat"] = df_d.apply(row_delta, axis=1)
    df_d.columns = [c.replace("_", " ") for c in df_d.columns]
    st.dataframe(df_d, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────────────────────────────────
# TAB 2 · ZENLOOP DEEP-DIVE
# ──────────────────────────────────────────────────────────────────────────────────────────
with tab2:
    if df_zen.empty:
        st.warning("⚠️ Keine Zenloop-Daten. Bitte 'Zenloop_Antworten.csv' bereitstellen.")
    else:
        pc1, pc2 = st.columns([1, 3])
        with pc1:
            section_title("Studio-Check")
            sel_s = st.selectbox("Studio wählen", codes_zen, label_visibility="collapsed")
        df_s = df_zen[df_zen["Property - studio"] == sel_s]
        s_nps  = get_nps(df_s)
        s_prom = int((df_s["score_type"] == "promoter").sum()) if "score_type" in df_s.columns else 0
        s_pass = int((df_s["score_type"] == "passive").sum()) if "score_type" in df_s.columns else 0
        s_detr = int((df_s["score_type"] == "detractor").sum()) if "score_type" in df_s.columns else 0
        with pc2:
            section_title(f"Studio-Analyse: {sel_s}", f"{len(df_s)} Zenloop-Antworten gesamt")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("NPS", f"{s_nps:.0f}" if s_nps is not None else "–", delta=nps_label(s_nps) if s_nps is not None else None, delta_color="normal" if s_nps and s_nps >= 0 else "inverse")
        m2.metric("Promoter 😊", str(s_prom))
        m3.metric("Passive 😐", str(s_pass))
        m4.metric("Detraktoren 😠", str(s_detr))

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        lc, rc = st.columns(2, gap="large")
        with lc:
            section_title("Top-Themen", "Häufigkeit im Feedback")
            tlb = top_labels(df_s, 7)
            if not tlb.empty:
                max_cnt = int(tlb.max())
                for lbl, cnt in tlb.items(): label_bar(lbl, cnt, max_cnt)
            else: st.caption("Keine Labels vorhanden.")
            nlb = neg_labels(df_s, 4)
            if not nlb.empty:
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                section_title("⚠️ Kritikpunkte", "Themen der Detraktoren")
                for lbl, cnt in nlb.items(): label_bar(lbl, cnt, int(nlb.max()), color=C_RED, bg=T["err_bg"])
        with rc:
            section_title("Letzte Kommentare", "Niedrigste Scores zuerst")
            if "comment" in df_s.columns:
                df_com = df_s[["score", "score_type", "comment"]].dropna(subset=["comment"]).query("comment.str.strip() != ''").sort_values("score").head(5)
                for _, row in df_com.iterrows():
                    type_color = C_MINT if row["score_type"] == "promoter" else C_RED if row["score_type"] == "detractor" else C_HONEY
                    type_bg = T["ok_bg"] if row["score_type"] == "promoter" else T["err_bg"] if row["score_type"] == "detractor" else T["warn_bg"]
                    st.markdown(
                        f"""<div style='padding:13px 15px;background:{T["card_bg"]};border:1px solid {T["card_border"]};border-radius:13px;margin-bottom:9px;'>
                            <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>
                                <span style='font-size:22px;font-weight:800;color:{type_color};line-height:1;'>{int(row["score"])}</span>
                                <span style='font-size:10px;font-weight:700;color:{type_color};background:{type_bg};padding:3px 9px;border-radius:100px;text-transform:uppercase;letter-spacing:0.6px;'>{row["score_type"]}</span>
                            </div>
                            <div style='font-size:12.5px;color:{T["text_second"]};line-height:1.6;font-style:italic;'> „{str(row["comment"])[:200]}{"…" if len(str(row["comment"])) > 200 else ""}"</div>
                        </div>""", unsafe_allow_html=True)

        st.divider()
        section_title("Regionale Übersicht", "Alle ausgewählten Studios")
        ov1, ov2 = st.columns(2, gap="large")
        with ov1:
            st.markdown(f"<div style='font-size:13px;font-weight:600;color:{T['text_h']};margin-bottom:12px;'>Häufigste Themen gesamt</div>", unsafe_allow_html=True)
            all_lb = top_labels(df_zen, 10).reset_index()
            all_lb.columns = ["Thema", "Anzahl"]
            if not all_lb.empty:
                ci = [C_ORANGE, C_STONE, C_HONEY, C_MINT, C_LILAC, C_SAND, C_ORANGE_LT, C_GREEN, C_RED, C_SKIN]
                fig_lb = go.Figure(go.Bar(x=all_lb["Anzahl"], y=all_lb["Thema"], orientation="h", marker=dict(color=ci[:len(all_lb)], line=dict(width=0)), text=all_lb["Anzahl"], textposition="outside", textfont=dict(color=PFG, size=11), hovertemplate="<b>%{y}</b><br>%{x}×<extra></extra>"))
                fig_lb.update_layout(**plotly_base(), xaxis=dict(gridcolor=PGRD, zeroline=False), yaxis=dict(categoryorder="total ascending", tickfont=dict(size=11)), margin=dict(l=4, r=40, t=4, b=4), bargap=0.38)
                st.plotly_chart(fig_lb, use_container_width=True)
        with ov2:
            st.markdown(f"<div style='font-size:13px;font-weight:600;color:{T['text_h']};margin-bottom:12px;'>NPS nach Behandlungsart</div>", unsafe_allow_html=True)
            seg_col = "Property - product_segment"
            if seg_col in df_zen.columns:
                seg_list = []
                for seg in df_zen[seg_col].dropna().unique():
                    dsg = df_zen[df_zen[seg_col] == seg]
                    npsv = get_nps(dsg)
                    if npsv is not None: seg_list.append({"Behandlung": seg, "NPS": npsv, "n": len(dsg)})
                if seg_list:
                    df_sg = pd.DataFrame(seg_list).sort_values("NPS", ascending=False)
                    bc = [C_MINT if v >= 30 else (C_HONEY if v >= 0 else C_RED) for v in df_sg["NPS"]]
                    fig_sg = go.Figure(go.Bar(x=df_sg["Behandlung"], y=df_sg["NPS"], marker=dict(color=bc, line=dict(width=0)), text=df_sg["NPS"].apply(lambda v: f"{v:.0f}"), textposition="outside", textfont=dict(color=PFG, size=12), hovertemplate="<b>%{x}</b><br>NPS: %{y:.0f}<extra></extra>"))
                    fig_sg.add_hline(y=0, line_color=T["divider"], line_width=1.5)
                    fig_sg.update_layout(**plotly_base(), yaxis=dict(gridcolor=PGRD, zeroline=False), xaxis=dict(gridcolor="rgba(0,0,0,0)", zeroline=False), bargap=0.42)
                    st.plotly_chart(fig_sg, use_container_width=True)
            else: st.caption("Spalte 'Property - product_segment' nicht vorhanden.")

        if "score_type" in df_zen.columns:
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            section_title("NPS-Zusammensetzung", "Alle ausgewählten Studios")
            tc = df_zen["score_type"].value_counts().reset_index()
            tc.columns = ["Typ", "Anzahl"]
            color_map = {"promoter": C_MINT, "passive": C_HONEY, "detractor": C_RED}
            fig_d = go.Figure(go.Pie(labels=tc["Typ"], values=tc["Anzahl"], hole=0.68, marker=dict(colors=[color_map.get(t, C_STONE) for t in tc["Typ"]], line=dict(color=T["app_bg"], width=3)), textfont=dict(size=13), hovertemplate="<b>%{label}</b><br>%{value} (%{percent})<extra></extra>"))
            if nps_ges is not None:
                fig_d.add_annotation(text=f"<b>{nps_ges:.0f}</b>", x=0.5, y=0.55, showarrow=False, font=dict(size=26, color=T["text_h"], family="Plus Jakarta Sans"))
                fig_d.add_annotation(text="NPS", x=0.5, y=0.38, showarrow=False, font=dict(size=12, color=T["text_muted"], family="Plus Jakarta Sans"))
            fig_d.update_layout(plot_bgcolor=PBG, paper_bgcolor=PBG, font=dict(color=PFG, family="Plus Jakarta Sans", size=12), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.18, font=dict(size=12)), margin=dict(t=10, b=10, l=10, r=10), height=280)
            _, dc, _ = st.columns([1, 2, 1])
            with dc: st.plotly_chart(fig_d, use_container_width=True)

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        section_title("NPS-Ranking", "Studios mit Zenloop-Daten")
        nps_rows = []
        for code in codes_zen:
            d = df_zen[df_zen["Property - studio"] == code]
            nv = get_nps(d)
            gr = df_curr[df_curr["Studiokürzel"] == code]["Rating"].values
            if nv is not None: nps_rows.append({"Studio": code, "NPS": nv, "Bewertung": nps_label(nv), "Google ⭐": round(gr[0], 2) if len(gr) > 0 else None, "Antworten": len(d)})
        if nps_rows:
            df_nr = pd.DataFrame(nps_rows).sort_values("NPS", ascending=False).reset_index(drop=True)
            df_nr.insert(0, "Rang", [f"#{i}" for i in range(1, len(df_nr) + 1)])
            st.dataframe(df_nr, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────────────────────────────────
# TAB 3 · MANAGEMENT-BERICHT (alle Downloads hier)
# ──────────────────────────────────────────────────────────────────────────────────────────
with tab3:
    section_title("Management-Bericht", "Automatisch aus echten Daten · Trend-Analyse, Insights und Handlungsempfehlungen")

    studios_s = df_curr.sort_values("Rating", ascending=False)
    top3 = studios_s.head(3)
    atl = top_labels(df_zen, 5)
    anl = neg_labels(df_zen, 5)

    verbessert, verschlechtert = [], []
    if not df_vm.empty:
        vm_r = df_vm.set_index("Studiokürzel")["Rating"]
        for _, row in df_curr.iterrows():
            old = vm_r.get(row["Studiokürzel"])
            if old is not None:
                dv = row["Rating"] - old
                if dv >= 0.1: verbessert.append(f"{row['Studiokürzel']} (+{dv:.1f})")
                elif dv <= -0.1: verschlechtert.append(f"{row['Studiokürzel']} ({dv:.1f})")

    jetzt = datetime.now().strftime("%d.%m.%Y %H:%M")
    s1 = "═" * 56
    s2 = "─" * 56

    lines = [
        "SENZERA MANAGEMENT-BERICHT",
        f"Region    : {sel_rl}", f"Monat     : {sel_monat}", f"Erstellt  : {jetzt}",
        s1, "",
        "I.  ÜBERBLICK", s2,
        f"  Google Ø-Rating    : {avg_rating:.2f} ⭐" + (f"   ({delta_r:+.2f} ggü. {vormonat})" if delta_r is not None else ""),
        f"  Neue Rezensionen         : {new_rev}",
        f"  Google Rez. Gesamt       : {total_rev}",
        f"  Zenloop NPS              : {fmt_n(nps_ges)}",
        f"  Positive Stimmung        : {f'{sentiment:.0f}%' if sentiment else 'keine Daten'}" + (f"   ({n_zen} Antworten)" if n_zen > 0 else ""),
        "",
    ]
    if avg_rating >= RATING_GOOD: lines.append("  💙 Gesamtbewertung: STARK – Region über Zielmarke.")
    elif avg_rating >= RATING_MIN: lines.append("  🟡 Gesamtbewertung: SOLIDE – Einzelne Studios brauchen Aufmerksamkeit.")
    else: lines.append("  🔴 Gesamtbewertung: KRITISCH – Sofortmaßnahmen erforderlich!")

    lines += ["", "II.  TREND", s2]
    if verbessert: lines.append(f"  📈 Verbessert vs. {vormonat}     : {', '.join(verbessert)}")
    if verschlechtert: lines.append(f"  📉 Verschlechtert vs. {vormonat} : {', '.join(verschlechtert)}")
    if not verbessert and not verschlechtert: lines.append("  ➡  Nur ein Monat verfügbar – kein Trendvergleich möglich.")

    lines += ["", "III. STUDIO-STATUS", s2]
    for _, row in studios_s.iterrows():
        code = row["Studiokürzel"]
        zs = df_zen[df_zen["Property - studio"] == code] if not df_zen.empty else pd.DataFrame()
        sn = get_nps(zs)
        nstr = f" | NPS: {sn:.0f}" if sn is not None else ""
        kstr = "  ← KRITISCH!" if row["Rating"] < RATING_MIN else ""
        lines.append(f"  {rating_icon(row['Rating'])}  {code:<6} {row['Rating']:.2f} ⭐  (+{row['NewReviews']} Rez.){nstr}{kstr}")

    lines += ["", "IV.  HIGHLIGHTS", s2, "  🏆 TOP-STUDIOS:"]
    for _, row in top3.iterrows():
        lines.append(f"      • {row['Studiokürzel']} ({row['Stadt']}): {row['Rating']:.2f} ⭐")

    if n_crit > 0:
        lines += ["", "  🚨 HANDLUNGSBEDARF:"]
        for _, row in crit.iterrows():
            code = row["Studiokürzel"]
            zs = df_zen[df_zen["Property - studio"] == code] if not df_zen.empty else pd.DataFrame()
            nl = neg_labels(zs, 3)
            lines.append(f"      • {code} ({row['Stadt']}): {row['Rating']:.2f} ⭐")
            if not nl.empty: lines.append(f"        Kundenkritik: {', '.join(nl.index.tolist())}")
        lines += ["", "  Empfohlene Maßnahmen:", "      1.  Sofortgespräch mit Studioleitung (diese Woche)", "      2.  Google-Rezensionen der letzten 30 Tage analysieren", "      3.  Konkrete Maßnahmen festlegen (Frist: 2 Wochen)", "      4.  Wöchentliches Follow-up einplanen"]

    if not atl.empty or not anl.empty:
        lines += ["", "V.  KUNDENFEEDBACK-INSIGHTS", s2]
        if not atl.empty:
            lines.append("  📋 Meistgenannte Themen:")
            for lbl, cnt in atl.items(): lines.append(f"      • {lbl} ({cnt}×)")
        if not anl.empty:
            lines += ["", "  ⚠️  Hauptkritikpunkte (Detraktoren):"]
            for lbl, cnt in anl.items(): lines.append(f"      • {lbl} ({cnt}×)")
            lines.append("  →  Für nächstes Team-Meeting priorisieren.")

    lines += ["", s1, f"Senzera Performance Hub v5  ·  {jetzt}", s1]
    bericht = "\n".join(lines)
    st.text_area("", value=bericht, height=540, label_visibility="collapsed")

    # ── ALLE DOWNLOADS ───────────────────────────────────────────────────────────────────
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    section_title("Alle Downloads", "Berichte und Daten-Exporte")
    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button("📄 Bericht als .txt", data=bericht.encode("utf-8"), file_name=f"Senzera_Bericht_{sel_rl}_{sel_monat}.txt", mime="text/plain", use_container_width=True)
    with dl2:
        snap = [c for c in ["Studiokürzel", "Stadt", "Rating", "NewReviews", "TotalReviews", "NPS"] if c in df_curr.columns]
        st.download_button("📦 Daten-Snapshot (CSV)", data=df_curr[snap].to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"), file_name=f"Senzera_Snapshot_{sel_rl}_{sel_monat}.csv", mime="text/csv", use_container_width=True)
    dl3, dl4 = st.columns(2)
    with dl3:
        st.download_button("📦 Alle Google-Daten (CSV)", data=df_view.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"), file_name=f"Senzera_Google_{sel_monat}.csv", mime="text/csv", use_container_width=True)
    with dl4:
        if not df_zen.empty:
            st.download_button("📦 Zenloop-Daten (CSV)", data=df_zen.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"), file_name=f"Senzera_Zenloop_{sel_monat}.csv", mime="text/csv", use_container_width=True)
        else:
            st.button("📦 Zenloop – keine Daten", disabled=True, use_container_width=True)


# ──────────────────────────────────────────────────────────────────────────────────────────
# TAB 4 · TEAM-PERFORMER (passwortgeschützt)
# ──────────────────────────────────────────────────────────────────────────────────────────
PERFORMER_BIN = "performer_encrypted.bin"

def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480_000)
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))

def _decrypt_performer(password: str) -> dict:
    with open(PERFORMER_BIN, "rb") as f: raw = f.read()
    salt, encrypted = raw[:16], raw[16:]
    key = _derive_key(password, salt)
    fernet = Fernet(key)
    try: data = fernet.decrypt(encrypted)
    except (InvalidToken, Exception): raise ValueError("Falsches Passwort")
    return json.loads(data.decode("utf-8"))

def _performer_kpi_card(title: str, value: str, sub: str = "", color: str = None) -> None:
    c = color or C_ORANGE
    st.markdown(
        f"""<div style='background:{T["card_bg"]};border:1px solid {T["card_border"]};border-radius:16px;padding:18px 20px;box-shadow:{T["card_shadow"]};'>
            <div style='font-size:10px;font-weight:700;letter-spacing:1.3px;text-transform:uppercase;color:{T["text_muted"]};margin-bottom:6px;'>{title}</div>
            <div style='font-size:1.7rem;font-weight:800;color:{T["text_h"]};letter-spacing:-0.5px;line-height:1.1;'>{value}</div>
            <div style='font-size:11.5px;color:{T["text_muted"]};margin-top:5px;'>{sub}</div>
        </div>""", unsafe_allow_html=True)

with tab4:
    if not CRYPTO_OK:
        st.error("❌ Bibliothek fehlt: `pip install cryptography`")
        st.stop()
    if not os.path.exists(PERFORMER_BIN):
        st.warning(f"⚠️ Verschlüsselte Datei **'{PERFORMER_BIN}'** nicht gefunden.\n\nBitte zuerst das Update-Skript ausführen:\n```\npython performer_update.py\n```")
        st.stop()

    if "performer_unlocked" not in st.session_state: st.session_state.performer_unlocked = False
    if "performer_data" not in st.session_state: st.session_state.performer_data = None

    if not st.session_state.performer_unlocked:
        file_stat = os.stat(PERFORMER_BIN)
        file_date = datetime.fromtimestamp(file_stat.st_mtime).strftime("%d.%m.%Y %H:%M")
        _, lock_col, _ = st.columns([1, 2, 1])
        with lock_col:
            st.markdown(
                f"""<div style='text-align:center;padding:40px 32px;background:{T["card_bg"]};border:1px solid {T["card_border"]};border-radius:20px;box-shadow:{T["card_shadow"]};margin-top:24px;'>
                    <div style='font-size:48px;margin-bottom:16px;'>🔐</div>
                    <div style='font-family:"Playfair Display",serif;font-size:22px;color:{T["text_h"]};margin-bottom:6px;'>Team-Performer</div>
                    <div style='font-size:13px;color:{T["text_muted"]};margin-bottom:6px;'>Geschützter Bereich</div>
                    <div style='font-size:11px;color:{T["text_muted"]};padding:6px 14px;background:{T["app_bg"]};border-radius:8px;display:inline-block;margin-bottom:24px;'>📁 Datei vom {file_date}</div>
                </div>""", unsafe_allow_html=True)
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            pw_input = st.text_input("Passwort", type="password", placeholder="Passwort eingeben …", label_visibility="collapsed")
            _, btn_col, _ = st.columns([1, 2, 1])
            with btn_col: unlock_btn = st.button("🔓 Entsperren", use_container_width=True)
            if unlock_btn:
                if not pw_input.strip(): st.error("Bitte Passwort eingeben.")
                else:
                    with st.spinner("Wird entschlüsselt …"):
                        try:
                            data = _decrypt_performer(pw_input.strip())
                            st.session_state.performer_data = data
                            st.session_state.performer_unlocked = True
                            st.rerun()
                        except ValueError: st.error("❌ Falsches Passwort. Bitte erneut versuchen.")
                        except Exception as e: st.error(f"❌ Fehler beim Entschlüsseln: {e}")
    else:
        data = st.session_state.performer_data
        df_pf_raw = pd.DataFrame(data["performer"])
        df_kr_raw = pd.DataFrame(data["krankentage"])
        monate = data.get("monate", [])
        gen_time = data.get("generated", "")[:10]

        lock_h, lock_info = st.columns([4, 1])
        with lock_h: section_title("Team-Performer", f"Umsatz- & Krankentage-Analyse · Datenstand: {gen_time}")
        with lock_info:
            if st.button("🔒 Sperren", use_container_width=True):
                st.session_state.performer_unlocked = False
                st.session_state.performer_data = None
                st.rerun()

        if sel_rl != "Alle":
            rl_kuerzel = df_curr["Studiokürzel"].unique().tolist()
            df_pf = df_pf_raw[df_pf_raw["Kürzel"].isin(rl_kuerzel)].copy()
            df_kr = df_kr_raw[df_kr_raw["Kürzel"].isin(rl_kuerzel)].copy()
            if df_pf.empty:
                teams_in_rl = df_pf_raw[df_pf_raw["Standort"].str.contains("|".join([k.split()[0] for k in rl_kuerzel[:3]]), na=False, case=False)]["Team"].unique()
                df_pf = df_pf_raw[df_pf_raw["Team"].isin(teams_in_rl)].copy()
                df_kr = df_kr_raw[df_kr_raw["Team"].isin(teams_in_rl)].copy()
        else:
            df_pf = df_pf_raw.copy()
            df_kr = df_kr_raw.copy()
        if df_pf.empty:
            df_pf = df_pf_raw.copy()
            df_kr = df_kr_raw.copy()

        avail_months = [m for m in monate if m in df_pf.columns]
        if not avail_months: st.warning("Keine Monatsdaten verfügbar."); st.stop()
        pf_monat = st.selectbox("Analysen-Monat", avail_months, index=len(avail_months) - 1, key="pf_monat_sel")

        df_pf_m = df_pf[df_pf[pf_monat].notna() & (df_pf[pf_monat] > 0)].copy()
        df_pf_m = df_pf_m[df_pf_m["Position"].isin(["KM", "SL", "Standortleitung"])]
        avg_umsatz = df_pf_m[pf_monat].mean() if not df_pf_m.empty else 0
        top_row = df_pf_m.loc[df_pf_m[pf_monat].idxmax()] if not df_pf_m.empty else None
        n_aktiv = len(df_pf_m)
        kr_col = pf_monat if pf_monat in df_kr.columns else None
        avg_krank = df_kr[kr_col].mean() if kr_col else 0
        total_krank = int(df_kr[kr_col].sum()) if kr_col else 0

        pk1, pk2, pk3, pk4 = st.columns(4)
        with pk1: _performer_kpi_card("Ø Umsatz / Person", f"{avg_umsatz:,.0f} €".replace(",", "."), f"Monat {pf_monat}")
        with pk2: _performer_kpi_card("Top Performer", top_row["Name"] if top_row is not None else "–", f"{top_row[pf_monat]:,.0f} €".replace(",", ".") if top_row is not None else "", color=C_HONEY)
        with pk3: _performer_kpi_card("Aktive MA (Vertrieb)", str(n_aktiv), f"mit Umsatz in {pf_monat}")
        with pk4: _performer_kpi_card("Ø Krankentage", f"{avg_krank:.1f} Tage", f"Gesamt {pf_monat}: {total_krank} Tage", color=C_RED if avg_krank > 3 else C_MINT)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        ch1, ch2 = st.columns([3, 2], gap="large")
        with ch1:
            section_title(f"Umsatz-Ranking – {pf_monat}", "Alle Vertriebsmitarbeiterinnen mit positivem Umsatz")
            df_rank_pf = df_pf_m.sort_values(pf_monat, ascending=True).tail(25)
            n_bars = len(df_rank_pf)
            bar_colors_pf = [C_ORANGE if i >= n_bars - 3 else C_STONE for i in range(n_bars)]
            fig_pf = go.Figure(go.Bar(x=df_rank_pf[pf_monat], y=df_rank_pf["Name"], orientation="h", marker=dict(color=bar_colors_pf, line=dict(width=0)), text=df_rank_pf[pf_monat].apply(lambda v: f"{v:,.0f} €".replace(",", ".")), textposition="outside", textfont=dict(color=PFG, size=11), hovertemplate="<b>%{y}</b><br>%{x:,.0f} €<extra></extra>"))
            fig_pf.add_vline(x=avg_umsatz, line_dash="dot", line_color=C_HONEY, line_width=2, annotation=dict(text=f"Ø {avg_umsatz:,.0f}".replace(",", "."), font=dict(size=10, color=C_HONEY), bgcolor="rgba(0,0,0,0)"))
            fig_pf.update_layout(**plotly_base(), xaxis=dict(gridcolor=PGRD, zeroline=False, tickformat=",.0f"), yaxis=dict(tickfont=dict(size=10, color=T["text_second"])), height=max(300, n_bars * 26), margin=dict(l=4, r=80, t=8, b=8), bargap=0.3)
            st.plotly_chart(fig_pf, use_container_width=True)
        with ch2:
            section_title(f"Krankentage – {pf_monat}", "Top 15 nach Krankentagen")
            if kr_col and not df_kr.empty:
                df_kr_m = df_kr[df_kr[kr_col].notna() & (df_kr[kr_col] > 0)][["Name", "Position", "Standort", kr_col]].sort_values(kr_col, ascending=False).head(15)
                if not df_kr_m.empty:
                    k_colors = df_kr_m[kr_col].apply(lambda v: C_RED if v >= 8 else (C_HONEY if v >= 4 else C_STONE)).tolist()
                    fig_kr = go.Figure(go.Bar(x=df_kr_m[kr_col], y=df_kr_m["Name"], orientation="h", marker=dict(color=k_colors, line=dict(width=0)), text=df_kr_m[kr_col].apply(lambda v: f"{int(v)} T"), textposition="outside", textfont=dict(color=PFG, size=11), hovertemplate="<b>%{y}</b><br>%{x} Krankentage<extra></extra>"))
                    fig_kr.update_layout(**plotly_base(), xaxis=dict(gridcolor=PGRD, zeroline=False), yaxis=dict(tickfont=dict(size=10, color=T["text_second"])), height=max(300, len(df_kr_m) * 26), margin=dict(l=4, r=50, t=8, b=8), bargap=0.3)
                    st.plotly_chart(fig_kr, use_container_width=True)
                else: st.info(f"Keine Krankentage im {pf_monat} verzeichnet. ✅")
            else: st.caption("Keine Krankentage-Daten für diesen Monat.")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        section_title("Monatstrend", "Ø Umsatz pro Monat")
        trend_data = []
        for m in avail_months:
            sub = df_pf_raw[df_pf_raw[m].notna() & (df_pf_raw[m] > 0) & df_pf_raw["Position"].isin(["KM", "SL", "Standortleitung"])]
            if not sub.empty: trend_data.append({"Monat": m, "Ø Umsatz": sub[m].mean(), "Anz. MA": len(sub), "Ø Krank": df_kr_raw[m].mean() if m in df_kr_raw.columns else 0})
        if trend_data:
            df_trend = pd.DataFrame(trend_data)
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(x=df_trend["Monat"], y=df_trend["Ø Umsatz"], fill="tozeroy", fillcolor="rgba(232,98,10,0.06)", line=dict(width=0), showlegend=False, hoverinfo="skip"))
            fig_trend.add_trace(go.Scatter(x=df_trend["Monat"], y=df_trend["Ø Umsatz"], name="Ø Umsatz", line=dict(color=C_ORANGE, width=2.5), marker=dict(size=8, color=C_ORANGE, line=dict(width=2.5, color=T["app_bg"])), mode="lines+markers", hovertemplate="<b>%{x}</b><br>Ø Umsatz: %{y:,.0f} €<extra></extra>"))
            if "Ø Krank" in df_trend.columns:
                fig_trend.add_trace(go.Scatter(x=df_trend["Monat"], y=df_trend["Ø Krank"], name="Ø Krankentage", line=dict(color=C_RED, width=2, dash="dot"), marker=dict(size=6, color=C_RED), mode="lines+markers", yaxis="y2", hovertemplate="<b>%{x}</b><br>Ø Krank: %{y:.1f} Tage<extra></extra>"))
            fig_trend.update_layout(plot_bgcolor=PBG, paper_bgcolor=PBG, font=dict(color=PFG, family="Plus Jakarta Sans", size=12), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=12)), yaxis=dict(title="Ø Umsatz (€)", gridcolor=PGRD, zeroline=False, tickformat=",.0f", title_font=dict(size=11, color=T["text_muted"])), yaxis2=dict(title="Ø Krankentage", overlaying="y", side="right", gridcolor="rgba(0,0,0,0)", zeroline=False, title_font=dict(size=11, color=C_RED), tickfont=dict(color=C_RED)), xaxis=dict(gridcolor=PGRD, zeroline=False), height=300, margin=dict(l=4, r=60, t=30, b=8))
            st.plotly_chart(fig_trend, use_container_width=True)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        section_title("Detailtabelle", f"Alle Vertriebsmitarbeiterinnen · Monat {pf_monat}")
        disp_cols_pf = ["Name", "Position", "Standort", "Status", pf_monat]
        if kr_col and kr_col in df_kr.columns:
            df_kr_join = df_kr[["Name", kr_col]].rename(columns={kr_col: "Krankentage"})
            df_detail = df_pf[disp_cols_pf].merge(df_kr_join, on="Name", how="left")
        else: df_detail = df_pf[disp_cols_pf].copy()
        df_detail = df_detail.rename(columns={pf_monat: "Umsatz (€)"})
        df_detail = df_detail.sort_values("Umsatz (€)", ascending=False, na_position="last")
        df_detail["Umsatz (€)"] = df_detail["Umsatz (€)"].apply(lambda v: f"{v:,.0f}".replace(",", ".") if pd.notna(v) else "–")
        st.dataframe(df_detail, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════════════════
# 13 · FOOTER
# ══════════════════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown(
    f"""<div style='display:flex;align-items:center;justify-content:space-between;padding:28px 0 16px;'>
        <div>
            <div style='font-size:13px;font-weight:700;color:{T["text_h"]};font-family:"Playfair Display",serif;'>Performance Hub</div>
            <div style='font-size:10px;color:{T["text_muted"]};letter-spacing:0.3px;'>v5 · waxing & beauty</div>
        </div>
        <div style='text-align:right;'>
            <div style='font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:{T["text_muted"]};margin-bottom:2px;'>Datenschutz</div>
            <div style='font-size:11px;color:{C_ORANGE};font-weight:600;'>Alle Daten lokal · Keine Übertragung</div>
        </div>
    </div>""", unsafe_allow_html=True)
