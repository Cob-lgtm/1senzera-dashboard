"""
Senzera Performance Hub – Management Cockpit v3
================================================
Vertriebssteuerungs-Dashboard für Regionalleiterinnen.

Voraussetzungen:
    pip install streamlit pandas plotly

Datenquellen:
    - Senzera_Dashboard_Data.csv   (Google-Bewertungen pro Studio & Monat)
    - Zenloop_Antworten.csv        (NPS-Umfragen mit Kommentaren & Labels)

Starten:
    streamlit run senzera_dashboard.py
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ══════════════════════════════════════════════
# 1. KONFIGURATION & KONSTANTEN
# ══════════════════════════════════════════════

st.set_page_config(
    page_title="Senzera Performance Hub",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Senzera CI-Farben (aus Corporate Design Manual) ──────────────
C_ORANGE       = "#E8620A"   # Senzera Orange – Primärfarbe (Pantone 165C)
C_ORANGE_LIGHT = "#F47A2A"
C_BLACK        = "#1C1C1A"   # Senzera Black
C_SAND         = "#CFC8B8"   # Sekundär: Sand
C_STONE        = "#A8B9BC"   # Sekundär: Stone
C_SKIN         = "#F0D0C4"   # Sekundär: Skin
C_CREAM        = "#FAF8F5"   # Tertiär: Cream
C_HONEY        = "#D4B86A"   # Tertiär: Honey
C_MINT         = "#A8C4A8"   # Tertiär: Mint
C_LILAC        = "#C8B4C4"   # Tertiär: Lilac

# Chart-Farben (CI-konform)
C_CHART_GREEN = "#5A9A6A"
C_CHART_RED   = "#D44020"

# Schwellwerte
RATING_CRITICAL = 4.2
RATING_GOOD     = 4.5
TOP_LABELS      = 10
TOP_COMMENTS    = 5

# Pflicht-Spalten
REQ_GOOGLE  = {"Studiokürzel", "Stadt", "Regionalleitung", "Rating"}
REQ_ZENLOOP = {"Property - studio", "score_type", "score"}


# ══════════════════════════════════════════════
# 2. THEME-SYSTEM & CSS
# ══════════════════════════════════════════════

THEMES = {
    "☀️ Hell": {
        "bg":          C_CREAM,
        "sidebar_bg":  "#F2EAE4",
        "sidebar_br":  "#E0CEBC",
        "card_bg":     "#FFFFFF",
        "card_br":     "#EDE0D4",
        "text_h":      C_BLACK,
        "text_muted":  "#786858",
        "text_body":   "#3C3428",
        "grid":        "#E8E0D8",
        "divider":     "#E0CEBC",
        "tab_active":  C_BLACK,
        "tab_border":  C_ORANGE,
        "textarea_bg": "#FFFFFF",
        "textarea_fg": "#3C3428",
        "textarea_br": "#D4C0A8",
        "plot_bg":     "rgba(0,0,0,0)",
        "font":        "#3C3428",
        "success_bg":  "#E8F2EC",
        "success_br":  C_CHART_GREEN,
        "warn_bg":     "#FEF5E0",
        "warn_br":     C_HONEY,
        "error_bg":    "#FDEEE8",
        "error_br":    C_CHART_RED,
    },
    "🌙 Dark": {
        "bg":          "#100E0B",
        "sidebar_bg":  "#1A1714",
        "sidebar_br":  "#2C2820",
        "card_bg":     "#1E1B17",
        "card_br":     "#2C2820",
        "text_h":      C_CREAM,
        "text_muted":  "#A09888",
        "text_body":   C_SAND,
        "grid":        "#2C2820",
        "divider":     "#2C2820",
        "tab_active":  C_CREAM,
        "tab_border":  C_ORANGE,
        "textarea_bg": "#100E0B",
        "textarea_fg": C_SAND,
        "textarea_br": "#2C2820",
        "plot_bg":     "rgba(0,0,0,0)",
        "font":        C_SAND,
        "success_bg":  "#182418",
        "success_br":  C_CHART_GREEN,
        "warn_bg":     "#2A2010",
        "warn_br":     C_HONEY,
        "error_bg":    "#2A1008",
        "error_br":    C_CHART_RED,
    },
}

if "theme" not in st.session_state:
    st.session_state["theme"] = "☀️ Hell"


def apply_theme(t: dict) -> None:
    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Jost:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,700;1,400&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Jost', sans-serif !important;
    }}
    [data-testid="stAppViewContainer"] {{
        background: {t["bg"]} !important;
    }}
    [data-testid="stHeader"] {{
        background: transparent !important;
    }}

    /* ─ SIDEBAR ─ */
    [data-testid="stSidebar"] {{
        background: {t["sidebar_bg"]} !important;
        border-right: 1px solid {t["sidebar_br"]} !important;
    }}
    section[data-testid="stSidebar"] * {{
        color: {t["text_body"]} !important;
    }}
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {{
        color: {t["text_h"]} !important;
    }}

    /* ─ HEADLINES ─ */
    h1 {{ color: {t["text_h"]} !important; font-weight: 700 !important; letter-spacing: -0.5px; }}
    h2 {{ color: {t["text_h"]} !important; font-weight: 600 !important; }}
    h3 {{ color: {t["text_h"]} !important; }}
    p, label, .stCaption {{ color: {t["text_muted"]} !important; }}

    /* ─ METRIC CARDS ─ */
    [data-testid="metric-container"] {{
        background: {t["card_bg"]} !important;
        border: 1px solid {t["card_br"]} !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    }}
    [data-testid="metric-container"]:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(232,98,10,0.15) !important;
        border-color: {C_ORANGE} !important;
    }}
    [data-testid="metric-container"] label,
    [data-testid="metric-container"] p {{
        color: {t["text_muted"]} !important;
        font-size: 11px !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
    }}
    [data-testid="metric-container"] [data-testid="stMetricValue"] {{
        color: {t["text_h"]} !important;
        font-size: 26px !important;
        font-weight: 700 !important;
    }}
    [data-testid="stMetricDelta"] svg {{ display: none !important; }}

    /* ─ TABS ─ */
    button[data-baseweb="tab"] {{
        font-family: 'Jost', sans-serif !important;
        font-weight: 600 !important;
        font-size: 12px !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        color: {t["text_muted"]} !important;
        padding: 12px 22px !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {t["tab_active"]} !important;
        border-bottom: 2px solid {C_ORANGE} !important;
    }}

    /* ─ DIVIDER ─ */
    hr {{
        border: none !important;
        border-top: 1px solid {t["divider"]} !important;
        margin: 1.2rem 0 !important;
    }}

    /* ─ DATAFRAME ─ */
    [data-testid="stDataFrameResizable"] {{
        background: {t["card_bg"]} !important;
        border: 1px solid {t["card_br"]} !important;
        border-radius: 8px !important;
    }}

    /* ─ TEXTAREA ─ */
    textarea {{
        font-family: 'Courier New', monospace !important;
        font-size: 12.5px !important;
        background: {t["textarea_bg"]} !important;
        color: {t["textarea_fg"]} !important;
        border: 1px solid {t["textarea_br"]} !important;
        border-radius: 8px !important;
    }}

    /* ─ BUTTONS ─ */
    [data-testid="stDownloadButton"] button,
    [data-testid="stButton"] button {{
        background: {C_ORANGE} !important;
        color: white !important;
        border: none !important;
        border-radius: 100px !important;
        font-family: 'Jost', sans-serif !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        letter-spacing: 0.3px !important;
        padding: 10px 22px !important;
        transition: background 0.2s ease !important;
    }}
    [data-testid="stDownloadButton"] button:hover,
    [data-testid="stButton"] button:hover {{
        background: {C_ORANGE_LIGHT} !important;
    }}
    [data-testid="stButton"] button:disabled {{
        background: {t["card_br"]} !important;
        color: {t["text_muted"]} !important;
    }}

    /* ─ ALERTS ─ */
    div[class*="stSuccess"] {{
        background: {t["success_bg"]} !important;
        border-left: 4px solid {t["success_br"]} !important;
        border-radius: 8px !important;
    }}
    div[class*="stWarning"] {{
        background: {t["warn_bg"]} !important;
        border-left: 4px solid {C_ORANGE} !important;
        border-radius: 8px !important;
    }}
    div[class*="stError"] {{
        background: {t["error_bg"]} !important;
        border-left: 4px solid {t["error_br"]} !important;
        border-radius: 8px !important;
    }}

    /* ─ SELECT ─ */
    [data-baseweb="select"] {{
        border-color: {t["card_br"]} !important;
        background: {t["card_bg"]} !important;
        border-radius: 8px !important;
    }}
    [data-baseweb="tag"] {{
        background: rgba(232,98,10,0.12) !important;
        color: {C_ORANGE} !important;
        border-radius: 100px !important;
    }}

    /* ─ SCROLLBAR ─ */
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: {t["bg"]}; }}
    ::-webkit-scrollbar-thumb {{ background: {C_SAND}; border-radius: 3px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: {C_ORANGE}; }}

    /* ─ CAPTION ─ */
    .stCaption, [data-testid="stCaptionContainer"] {{
        font-size: 11px !important;
        color: {t["text_muted"]} !important;
        letter-spacing: 0.3px !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


T = THEMES[st.session_state["theme"]]
apply_theme(T)

PLOT_BG   = T["plot_bg"]
PLOT_FONT = T["font"]
PLOT_GRID = T["grid"]


# ══════════════════════════════════════════════
# 3. DATEN LADEN
# ══════════════════════════════════════════════

@st.cache_data(show_spinner="📊 Daten werden geladen …")
def load_google(path: str = "Senzera_Dashboard_Data.csv") -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path)
    missing = REQ_GOOGLE - set(df.columns)
    if missing:
        st.error(f"Fehlende Spalten in '{path}': {missing}")
        st.stop()
    if "Monat"      not in df.columns: df["Monat"]      = "Unbekannt"
    if "NewReviews" not in df.columns: df["NewReviews"] = 0
    if "NPS"        not in df.columns: df["NPS"]        = None
    df["Studio_Name"] = df["Studiokürzel"] + " (" + df["Stadt"] + ")"
    df["Rating"]      = pd.to_numeric(df["Rating"],     errors="coerce")
    df["NewReviews"]  = pd.to_numeric(df["NewReviews"], errors="coerce").fillna(0).astype(int)
    df["NPS"]         = pd.to_numeric(df["NPS"],        errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_zenloop(path: str = "Zenloop_Antworten.csv") -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path)
    missing = REQ_ZENLOOP - set(df.columns)
    if missing:
        st.warning(f"Fehlende Zenloop-Spalten: {missing}")
    df["score"] = pd.to_numeric(df.get("score", pd.Series(dtype=float)), errors="coerce")
    if "date_received" in df.columns:
        df["date_received"] = pd.to_datetime(df["date_received"], errors="coerce")
        df["Monat_zen"]     = df["date_received"].dt.to_period("M").astype(str)
    return df


# ══════════════════════════════════════════════
# 4. HILFSFUNKTIONEN
# ══════════════════════════════════════════════

def calc_nps(df: pd.DataFrame) -> Optional[float]:
    if df.empty or "score_type" not in df.columns: return None
    total = len(df)
    if total == 0: return None
    prom = (df["score_type"] == "promoter").sum()
    detr = (df["score_type"] == "detractor").sum()
    return round(((prom - detr) / total) * 100, 1)


def calc_nps_from_score(df: pd.DataFrame) -> Optional[float]:
    if df.empty or "score" not in df.columns: return None
    scores = df["score"].dropna()
    if len(scores) == 0: return None
    return round(((scores >= 9).sum() - (scores <= 6).sum()) / len(scores) * 100, 1)


def calc_sentiment(df: pd.DataFrame) -> Optional[float]:
    if df.empty or "sentiment" not in df.columns: return None
    with_c = df.dropna(subset=["comment"]) if "comment" in df.columns else df
    with_c = with_c[with_c["comment"].astype(str).str.strip().ne("nan")]
    if with_c.empty: return None
    return round((with_c["sentiment"] == "positive").sum() / len(with_c) * 100, 1)


def get_top_labels(df: pd.DataFrame, n: int = 5) -> pd.Series:
    if "labels" not in df.columns: return pd.Series(dtype=int)
    return (
        df["labels"].dropna()
        .str.split(";").explode()
        .str.strip().replace("", pd.NA).dropna()
        .value_counts().head(n)
    )


def get_neg_labels(df: pd.DataFrame, n: int = 5) -> pd.Series:
    if "labels" not in df.columns or "score_type" not in df.columns:
        return pd.Series(dtype=int)
    return get_top_labels(df[df["score_type"] == "detractor"], n)


def rating_emoji(r: float) -> str:
    if r >= RATING_GOOD:     return "✅"
    if r >= RATING_CRITICAL: return "⚠️"
    return "🚨"


def nps_bewertung(nps: float) -> str:
    if nps >= 70: return "Weltklasse 🏆"
    if nps >= 50: return "Exzellent 🌟"
    if nps >= 30: return "Gut 👍"
    if nps >= 0:  return "Verbesserungspotenzial ⚠️"
    return "Kritisch 🚨"


# ══════════════════════════════════════════════
# 5. DATEN LADEN
# ══════════════════════════════════════════════

df_google  = load_google()
df_zenloop = load_zenloop()

if df_google.empty:
    st.error("❌ **'Senzera_Dashboard_Data.csv'** nicht gefunden!")
    st.info("Bitte lege die Datei im selben Ordner wie dieses Skript ab und starte neu.")
    st.stop()


# ══════════════════════════════════════════════
# 6. SIDEBAR – FILTER
# ══════════════════════════════════════════════

with st.sidebar:
    # Senzera Branding
    st.markdown(
        f"""
        <div style="padding:8px 0 16px;text-align:center;">
            <div style="font-size:26px;margin-bottom:4px;">🌸</div>
            <div style="font-family:'Jost',sans-serif;font-size:20px;font-weight:700;
                        color:{C_ORANGE};letter-spacing:-0.5px;">senzera</div>
            <div style="font-size:9px;letter-spacing:3px;text-transform:uppercase;
                        color:{T['text_muted']};margin-top:2px;">waxing & beauty</div>
            <div style="margin-top:10px;font-size:10px;letter-spacing:2px;
                        text-transform:uppercase;color:{C_ORANGE};font-weight:600;">
                Performance Hub
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    theme_choice = st.radio(
        "🎨 Design",
        list(THEMES.keys()),
        horizontal=True,
        index=list(THEMES.keys()).index(st.session_state["theme"]),
    )
    if theme_choice != st.session_state["theme"]:
        st.session_state["theme"] = theme_choice
        st.rerun()

    st.divider()

    st.markdown(
        f"<div style='font-size:10px;letter-spacing:2px;text-transform:uppercase;"
        f"color:{C_ORANGE};font-weight:600;margin-bottom:10px;'>Filter</div>",
        unsafe_allow_html=True,
    )

    rl_options = ["Alle"] + sorted(df_google["Regionalleitung"].dropna().unique().tolist())
    sel_rl     = st.selectbox("Regionalleitung", rl_options)

    df_by_rl       = df_google if sel_rl == "Alle" else df_google[df_google["Regionalleitung"] == sel_rl]
    studio_options = sorted(df_by_rl["Studio_Name"].unique().tolist())

    sel_studios = st.multiselect(
        "Studios", studio_options, default=studio_options,
        help="Mehrfachauswahl möglich",
    )

    if not sel_studios:
        st.warning("⚠️ Bitte mindestens ein Studio auswählen.")
        st.stop()

    st.divider()

    alle_monate = sorted(df_by_rl["Monat"].dropna().unique().tolist())
    sel_monat   = (
        st.selectbox("Monat", alle_monate, index=len(alle_monate) - 1)
        if len(alle_monate) > 1
        else (alle_monate[-1] if alle_monate else "Unbekannt")
    )

    st.markdown(
        f"<div style='font-size:11px;color:{T['text_muted']};margin-top:4px;'>"
        f"📅 Aktiver Monat: <b style='color:{T['text_body']}'>{sel_monat}</b></div>",
        unsafe_allow_html=True,
    )

    st.divider()

    if st.button("🔄 Cache leeren & neu laden", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown(
        f"<div style='font-size:10px;color:{T['text_muted']};text-align:center;"
        f"margin-top:16px;'>Senzera Hub · lokal verarbeitet</div>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════
# 7. GEFILTERTE DATENSÄTZE & KPIs
# ══════════════════════════════════════════════

df_view    = df_by_rl[df_by_rl["Studio_Name"].isin(sel_studios)].copy()
df_current = df_view[df_view["Monat"] == sel_monat].copy()

monate_sorted = sorted(df_view["Monat"].dropna().unique().tolist())
idx_aktuell   = monate_sorted.index(sel_monat) if sel_monat in monate_sorted else -1
vormonat      = monate_sorted[idx_aktuell - 1] if idx_aktuell > 0 else None
df_vormonat   = df_view[df_view["Monat"] == vormonat].copy() if vormonat else pd.DataFrame()

selected_codes = df_current["Studiokürzel"].unique()
df_zen = (
    df_zenloop[df_zenloop["Property - studio"].isin(selected_codes)].copy()
    if not df_zenloop.empty else pd.DataFrame()
)

avg_rating       = df_current["Rating"].mean()         if not df_current.empty else 0.0
total_reviews    = int(df_current["NewReviews"].sum())  if not df_current.empty else 0
nps_gesamt       = calc_nps(df_zen) or calc_nps_from_score(df_zen)
sentiment_pct    = calc_sentiment(df_zen)
total_responses  = len(df_zen)
avg_rating_vm    = df_vormonat["Rating"].mean() if not df_vormonat.empty else None
delta_rating     = round(avg_rating - avg_rating_vm, 2) if avg_rating_vm is not None else None
critical_studios = df_current[df_current["Rating"] < RATING_CRITICAL]
n_critical       = len(critical_studios)


# ══════════════════════════════════════════════
# 8. HEADER
# ══════════════════════════════════════════════

col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown(
        f"""
        <div style="margin-bottom:4px;">
            <span style="font-size:10px;letter-spacing:3px;text-transform:uppercase;
                         color:{C_ORANGE};font-weight:600;">Performance Cockpit</span>
        </div>
        <h1 style="font-family:'Jost',sans-serif;font-size:30px;font-weight:700;
                   letter-spacing:-1px;margin:0 0 6px;color:{T['text_h']};">
            Studio-Übersicht
        </h1>
        <p style="font-size:13px;color:{T['text_muted']};margin:0;">
            Region: <b style="color:{T['text_body']}">{sel_rl}</b>
            &nbsp;·&nbsp; Monat: <b style="color:{T['text_body']}">{sel_monat}</b>
            &nbsp;·&nbsp; {len(sel_studios)} Studio(s) aktiv
        </p>
        """,
        unsafe_allow_html=True,
    )
with col_h2:
    if n_critical > 0:
        st.error(f"🚨 {n_critical} Studio(s) kritisch")
    else:
        st.success("✅ Alle Studios OK")

st.divider()


# ══════════════════════════════════════════════
# 9. TOP KPIs
# ══════════════════════════════════════════════

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric(
    "🌟 Google Ø-Rating",
    f"{avg_rating:.2f} ⭐",
    delta=f"{delta_rating:+.2f} vs. {vormonat}" if delta_rating is not None else None,
    delta_color="normal" if delta_rating and delta_rating >= 0 else "inverse",
)
k2.metric("📝 Neue Rezensionen", f"{total_reviews:,}".replace(",", "."))
if nps_gesamt is not None:
    k3.metric(
        "💙 Zenloop NPS", f"{nps_gesamt:.0f}",
        delta=nps_bewertung(nps_gesamt),
        delta_color="normal" if nps_gesamt >= 0 else "inverse",
    )
else:
    k3.metric("💙 Zenloop NPS", "–")
k4.metric(
    "😊 Positive Stimmung",
    f"{sentiment_pct:.0f}%" if sentiment_pct is not None else "–",
    help="Anteil positiver Kommentare (nur Einträge mit Text)",
)
k5.metric("📨 Zenloop Antworten", f"{total_responses:,}".replace(",", "."))


# ══════════════════════════════════════════════
# 10. ALARM-ZONE
# ══════════════════════════════════════════════

if not critical_studios.empty:
    st.error(
        f"🚨 **HANDLUNGSBEDARF:** {n_critical} Studio{'s' if n_critical > 1 else ''} "
        f"unter {RATING_CRITICAL} Sternen"
    )
    alarm_cols = st.columns(min(n_critical, 4))
    for idx, (_, row) in enumerate(critical_studios.iterrows()):
        with alarm_cols[idx % 4]:
            zen_s   = df_zen[df_zen["Property - studio"] == row["Studiokürzel"]] if not df_zen.empty else pd.DataFrame()
            s_nps   = calc_nps(zen_s)
            neg_lb  = get_neg_labels(zen_s, 2)
            nps_str = f" | NPS: {s_nps:.0f}" if s_nps is not None else ""
            neg_str = f"\n⚠️ Kritik: {', '.join(neg_lb.index.tolist())}" if not neg_lb.empty else ""
            st.warning(
                f"**{row['Studiokürzel']}** – {row['Stadt']}\n\n"
                f"{row['Rating']:.2f} ⭐ | +{row['NewReviews']} Rez.{nps_str}{neg_str}"
            )
else:
    st.success("✅ Alle Studios im grünen Bereich.")

st.divider()


# ══════════════════════════════════════════════
# 11. ANALYSE-TABS
# ══════════════════════════════════════════════

tab1, tab2, tab3 = st.tabs([
    "📊  Performance & Trends",
    "💙  Zenloop Deep-Dive",
    "📝  Management-Bericht",
])


# ── TAB 1: PERFORMANCE & TRENDS ──────────────
with tab1:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Google Ranking")
        df_ranked  = df_current.sort_values("Rating", ascending=True).copy()
        bar_colors = df_ranked["Rating"].apply(
            lambda r: C_CHART_RED if r < RATING_CRITICAL else
                      (C_HONEY    if r < RATING_GOOD      else C_CHART_GREEN)
        ).tolist()

        fig_rank = go.Figure(go.Bar(
            x=df_ranked["Rating"], y=df_ranked["Studiokürzel"],
            orientation="h",
            marker_color=bar_colors,
            marker_line_color="rgba(0,0,0,0.08)",
            marker_line_width=0.5,
            text=df_ranked["Rating"].apply(lambda r: f"{r:.2f}"),
            textposition="outside",
            textfont=dict(color=PLOT_FONT, size=12, family="Jost"),
            hovertemplate="<b>%{y}</b><br>Rating: %{x:.2f}<extra></extra>",
        ))
        fig_rank.add_vline(
            x=RATING_CRITICAL, line_dash="dash", line_color=C_CHART_RED, opacity=0.6,
            annotation_text=f"Grenze {RATING_CRITICAL}",
            annotation_font_color=C_CHART_RED, annotation_font_size=11,
        )
        fig_rank.update_layout(
            plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG,
            font=dict(color=PLOT_FONT, family="Jost"),
            xaxis=dict(range=[3.5, 5.15], gridcolor=PLOT_GRID, zeroline=False),
            yaxis=dict(tickfont=dict(size=11)),
            margin=dict(l=10, r=50, t=10, b=10),
            height=max(300, len(df_ranked) * 28),
        )
        st.plotly_chart(fig_rank, use_container_width=True)

    with c2:
        st.subheader("Entwicklungs-Trend")
        trend = (
            df_view.groupby("Monat", sort=False)["Rating"]
            .mean().reset_index().rename(columns={"Rating": "Ø Rating"})
        )
        fig_t = px.line(trend, x="Monat", y="Ø Rating", markers=True)
        fig_t.update_traces(
            line_color=C_ORANGE, line_width=3,
            marker=dict(size=9, color=C_ORANGE, line=dict(width=2, color=T["bg"])),
        )
        # Füllbereich in Senzera Skin
        fig_t.add_traces(go.Scatter(
            x=trend["Monat"], y=trend["Ø Rating"],
            fill="tozeroy", fillcolor="rgba(232,98,10,0.07)",
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ))
        fig_t.add_hline(y=RATING_CRITICAL, line_dash="dot", line_color=C_CHART_RED,   opacity=0.5)
        fig_t.add_hline(y=RATING_GOOD,     line_dash="dot", line_color=C_CHART_GREEN, opacity=0.4)
        fig_t.update_layout(
            plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG,
            font=dict(color=PLOT_FONT, family="Jost"),
            yaxis=dict(range=[3.5, 5.0], gridcolor=PLOT_GRID, zeroline=False),
            xaxis=dict(gridcolor=PLOT_GRID, zeroline=False),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig_t, use_container_width=True)

    st.subheader("Studio-Übersicht")
    disp_cols = [c for c in ["Studio_Name", "Rating", "NewReviews", "NPS", "Regionalleitung"] if c in df_current.columns]
    df_disp   = df_current[disp_cols].sort_values("Rating", ascending=False).reset_index(drop=True)
    df_disp.insert(0, "Status", df_disp["Rating"].apply(rating_emoji))
    if not df_vormonat.empty:
        vm_map = df_vormonat.set_index("Studiokürzel")["Rating"].to_dict()
        def get_delta(row):
            matches = df_current[df_current["Studio_Name"] == row.get("Studio_Name", "")]["Studiokürzel"]
            if matches.empty: return ""
            old = vm_map.get(matches.values[0])
            if old is None: return ""
            d = round(row["Rating"] - old, 2)
            return f"+{d}" if d > 0 else str(d)
        df_disp["Δ Vormonat"] = df_disp.apply(get_delta, axis=1)
    df_disp.columns = [c.replace("_", " ") for c in df_disp.columns]
    st.dataframe(df_disp, use_container_width=True, hide_index=True)


# ── TAB 2: ZENLOOP DEEP-DIVE ─────────────────
with tab2:
    if df_zen.empty:
        st.warning("⚠️ Keine Zenloop-Daten gefunden. Bitte 'Zenloop_Antworten.csv' bereitstellen.")
    else:
        st.subheader("🎯 Studio-Check")
        codes_mit_zen = sorted(df_zen["Property - studio"].dropna().unique().tolist())
        sel_s = st.selectbox("Detailanalyse für Studio:", options=codes_mit_zen)
        df_s  = df_zen[df_zen["Property - studio"] == sel_s]

        s_nps  = calc_nps(df_s) or calc_nps_from_score(df_s)
        s_sent = calc_sentiment(df_s)
        s_prom = (df_s["score_type"] == "promoter").sum()  if "score_type" in df_s.columns else 0
        s_pass = (df_s["score_type"] == "passive").sum()   if "score_type" in df_s.columns else 0
        s_detr = (df_s["score_type"] == "detractor").sum() if "score_type" in df_s.columns else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric(
            f"NPS {sel_s}",
            f"{s_nps:.0f}" if s_nps is not None else "–",
            delta=nps_bewertung(s_nps) if s_nps is not None else None,
            delta_color="normal" if s_nps and s_nps >= 0 else "inverse",
        )
        m2.metric("😊 Promoter",    str(s_prom))
        m3.metric("😐 Passive",     str(s_pass))
        m4.metric("😠 Detraktoren", str(s_detr))

        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown("**Top Themen dieses Studios:**")
            top_lb = get_top_labels(df_s, 6)
            if not top_lb.empty:
                for label, cnt in top_lb.items():
                    pct = int(cnt / len(df_s) * 100) if len(df_s) > 0 else 0
                    bar_width = max(4, pct)
                    st.markdown(
                        f"<div style='display:flex;align-items:center;gap:8px;margin:4px 0;'>"
                        f"<div style='width:{bar_width}%;max-width:160px;height:6px;"
                        f"background:{C_ORANGE};border-radius:3px;'></div>"
                        f"<span style='font-size:13px;color:{T['text_body']}'>{label}</span>"
                        f"<span style='font-size:11px;color:{T['text_muted']}'>{cnt}×</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("Keine Labels vorhanden.")
            neg_lb = get_neg_labels(df_s, 4)
            if not neg_lb.empty:
                st.markdown("**⚠️ Kritikpunkte (Detraktoren):**")
                for label, cnt in neg_lb.items():
                    st.markdown(f"- **{label}** `{cnt}×`")

        with sc2:
            st.markdown("**Letzte Kommentare:**")
            if "comment" in df_s.columns:
                df_comments = (
                    df_s[["score", "score_type", "comment"]]
                    .dropna(subset=["comment"])
                    .sort_values("score")
                    .head(TOP_COMMENTS)
                )
                st.dataframe(df_comments, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Übergreifende Analyse – alle ausgewählten Studios")

        ov1, ov2 = st.columns(2)
        with ov1:
            st.markdown("**Häufigste Themen gesamt**")
            all_lb = get_top_labels(df_zen, TOP_LABELS).reset_index()
            all_lb.columns = ["Thema", "Anzahl"]
            if not all_lb.empty:
                ci_palette = [C_ORANGE, C_STONE, C_HONEY, C_MINT, C_LILAC,
                              C_SAND, C_ORANGE_LIGHT, C_CHART_GREEN, C_CHART_RED, C_SKIN]
                fig_lb = go.Figure(go.Bar(
                    x=all_lb["Anzahl"], y=all_lb["Thema"], orientation="h",
                    marker_color=ci_palette[:len(all_lb)],
                    text=all_lb["Anzahl"], textposition="outside",
                    textfont=dict(color=PLOT_FONT),
                ))
                fig_lb.update_layout(
                    plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG,
                    font=dict(color=PLOT_FONT, family="Jost"),
                    xaxis=dict(gridcolor=PLOT_GRID, zeroline=False),
                    yaxis=dict(categoryorder="total ascending"),
                    margin=dict(l=10, r=40, t=10, b=10),
                )
                st.plotly_chart(fig_lb, use_container_width=True)

        with ov2:
            st.markdown("**NPS nach Behandlungsart**")
            seg_col = "Property - product_segment"
            if seg_col in df_zen.columns:
                seg_list = []
                for seg in df_zen[seg_col].dropna().unique():
                    d   = df_zen[df_zen[seg_col] == seg]
                    nps = calc_nps(d) or calc_nps_from_score(d)
                    if nps is not None:
                        seg_list.append({"Behandlung": seg, "NPS": nps, "n": len(d)})
                if seg_list:
                    df_seg = pd.DataFrame(seg_list).sort_values("NPS", ascending=False)
                    fig_s = px.bar(
                        df_seg, x="Behandlung", y="NPS",
                        color="NPS",
                        color_continuous_scale=[[0.0, C_CHART_RED], [0.5, C_HONEY], [1.0, C_CHART_GREEN]],
                        range_color=[-100, 100], text="NPS",
                        hover_data={"n": True},
                    )
                    fig_s.update_traces(texttemplate="%{text:.0f}", textposition="outside")
                    fig_s.add_hline(y=0, line_color=T["grid"])
                    fig_s.update_layout(
                        plot_bgcolor=PLOT_BG, paper_bgcolor=PLOT_BG,
                        font=dict(color=PLOT_FONT, family="Jost"),
                        coloraxis_showscale=False,
                        yaxis=dict(gridcolor=PLOT_GRID, zeroline=False),
                        margin=dict(l=10, r=10, t=10, b=10),
                    )
                    st.plotly_chart(fig_s, use_container_width=True)

        # NPS Donut
        if "score_type" in df_zen.columns:
            st.subheader("NPS-Zusammensetzung")
            type_c = df_zen["score_type"].value_counts().reset_index()
            type_c.columns = ["Typ", "Anzahl"]
            fig_d = px.pie(
                type_c, values="Anzahl", names="Typ", hole=0.65,
                color="Typ",
                color_discrete_map={"promoter": C_CHART_GREEN, "passive": C_HONEY, "detractor": C_CHART_RED},
            )
            fig_d.update_traces(
                textfont_size=13,
                marker=dict(line=dict(color=T["bg"], width=3)),
            )
            if nps_gesamt is not None:
                fig_d.add_annotation(
                    text=f"NPS<br><b>{nps_gesamt:.0f}</b>",
                    x=0.5, y=0.5,
                    font=dict(size=20, color=T["text_h"], family="Jost"),
                    showarrow=False,
                )
            fig_d.update_layout(
                paper_bgcolor=PLOT_BG, font=dict(color=PLOT_FONT, family="Jost"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.18, font=dict(size=12)),
                margin=dict(t=10, b=10),
            )
            _, dc, _ = st.columns([1, 2, 1])
            with dc:
                st.plotly_chart(fig_d, use_container_width=True)

        # NPS-Ranking
        st.subheader("NPS-Ranking aller Studios")
        nps_ranking = []
        for code in codes_mit_zen:
            d     = df_zen[df_zen["Property - studio"] == code]
            nps_v = calc_nps(d) or calc_nps_from_score(d)
            g_r   = df_current[df_current["Studiokürzel"] == code]["Rating"].values
            if nps_v is not None:
                nps_ranking.append({
                    "Studio":    code,
                    "NPS":       nps_v,
                    "Google ⭐":  round(g_r[0], 2) if len(g_r) > 0 else None,
                    "Antworten": len(d),
                })
        if nps_ranking:
            df_nps_rank = (
                pd.DataFrame(nps_ranking)
                .sort_values("NPS", ascending=False)
                .reset_index(drop=True)
            )
            df_nps_rank.insert(0, "Rang", range(1, len(df_nps_rank) + 1))
            st.dataframe(df_nps_rank, use_container_width=True, hide_index=True)


# ── TAB 3: MANAGEMENT-BERICHT ────────────────
with tab3:
    st.subheader("📝 Intelligenter Management-Bericht")
    st.caption(
        "Automatisch aus echten Daten generiert – mit Trend-Analyse, "
        "Kundenfeedback-Insights und konkreten Handlungsempfehlungen."
    )

    studios_sorted = df_current.sort_values("Rating", ascending=False)
    top3           = studios_sorted.head(3)
    all_top_labels = get_top_labels(df_zen, 5)
    all_neg_labels = get_neg_labels(df_zen, 5)

    verbessert, verschlechtert = [], []
    if not df_vormonat.empty:
        vm_ratings = df_vormonat.set_index("Studiokürzel")["Rating"]
        for _, row in df_current.iterrows():
            old = vm_ratings.get(row["Studiokürzel"])
            if old is not None:
                d = row["Rating"] - old
                if   d >=  0.1: verbessert.append(f"{row['Studiokürzel']} (+{d:.1f})")
                elif d <= -0.1: verschlechtert.append(f"{row['Studiokürzel']} ({d:.1f})")

    jetzt = datetime.now().strftime("%d.%m.%Y %H:%M")
    sep1  = "═" * 52
    sep2  = "─" * 52

    def fmt_nps(v: Optional[float]) -> str:
        return f"{v:.0f} ({nps_bewertung(v)})" if v is not None else "keine Daten"

    zeilen = [
        "SENZERA MANAGEMENT-BERICHT",
        f"Region : {sel_rl}",
        f"Monat  : {sel_monat}",
        f"Erstellt: {jetzt}",
        sep1, "",
        "I. ÜBERBLICK", sep2,
        f"  Google Ø-Rating     : {avg_rating:.2f} ⭐"
        + (f"  ({delta_rating:+.2f} ggü. {vormonat})" if delta_rating is not None else ""),
        f"  Neue Rezensionen    : {total_reviews}",
        f"  Zenloop NPS         : {fmt_nps(nps_gesamt)}",
        f"  Positive Stimmung   : {f'{sentiment_pct:.0f}%' if sentiment_pct else 'keine Daten'}"
        + (f"  ({total_responses} Antworten)" if total_responses > 0 else ""),
        "",
    ]

    if   avg_rating >= RATING_GOOD:     zeilen.append("  💚 Gesamtbewertung: STARK – Region liegt über Zielmarke.")
    elif avg_rating >= RATING_CRITICAL: zeilen.append("  🟡 Gesamtbewertung: SOLIDE – Einzelne Studios brauchen Aufmerksamkeit.")
    else:                               zeilen.append("  🔴 Gesamtbewertung: KRITISCH – Sofortmaßnahmen erforderlich!")

    zeilen += ["", "II. TREND", sep2]
    if verbessert:
        zeilen.append(f"  📈 Verbessert vs. {vormonat}:     {', '.join(verbessert)}")
    if verschlechtert:
        zeilen.append(f"  📉 Verschlechtert vs. {vormonat}: {', '.join(verschlechtert)}")
    if not verbessert and not verschlechtert:
        zeilen.append("  ➡ Nur ein Monat verfügbar – kein Trendvergleich möglich.")

    zeilen += ["", "III. STUDIO-STATUS", sep2]
    for _, row in studios_sorted.iterrows():
        code   = row["Studiokürzel"]
        rating = row["Rating"]
        rev    = row["NewReviews"]
        zen_s  = df_zen[df_zen["Property - studio"] == code] if not df_zen.empty else pd.DataFrame()
        s_nps  = calc_nps(zen_s)
        nps_s  = f" | NPS: {s_nps:.0f}" if s_nps is not None else ""
        krit_s = "  → KRITISCH!" if rating < RATING_CRITICAL else ""
        zeilen.append(f"  {rating_emoji(rating)}  {code:<5} {rating:.2f} ⭐  (+{rev} Rez.){nps_s}{krit_s}")

    zeilen += ["", "IV. HIGHLIGHTS", sep2, "  🏆 TOP STUDIOS:"]
    for _, row in top3.iterrows():
        zeilen.append(f"      • {row['Studiokürzel']} ({row['Stadt']}): {row['Rating']:.2f} ⭐")

    if n_critical > 0:
        zeilen += ["", "  🚨 HANDLUNGSBEDARF:"]
        for _, row in critical_studios.iterrows():
            code  = row["Studiokürzel"]
            zen_s = df_zen[df_zen["Property - studio"] == code] if not df_zen.empty else pd.DataFrame()
            neg   = get_neg_labels(zen_s, 3)
            zeilen.append(f"      • {code} ({row['Stadt']}): {row['Rating']:.2f} ⭐")
            if not neg.empty:
                zeilen.append(f"        Kundenkritik: {', '.join(neg.index.tolist())}")
        zeilen += [
            "", "  Empfohlene Maßnahmen:",
            "      1. Sofortgespräch mit Studioleitung (diese Woche)",
            "      2. Google-Rezensionen der letzten 30 Tage analysieren",
            "      3. Konkrete Verbesserungsmaßnahmen festlegen (Frist: 2 Wochen)",
            "      4. Wöchentliches Follow-up einplanen",
        ]

    if not all_top_labels.empty or not all_neg_labels.empty:
        zeilen += ["", "V. KUNDENFEEDBACK-INSIGHTS", sep2]
        if not all_top_labels.empty:
            zeilen.append("  📌 Meistgenannte Themen:")
            for lbl, cnt in all_top_labels.items():
                zeilen.append(f"      • {lbl} ({cnt}×)")
        if not all_neg_labels.empty:
            zeilen += ["", "  ⚠️  Hauptkritikpunkte (Detraktoren):"]
            for lbl, cnt in all_neg_labels.items():
                zeilen.append(f"      • {lbl} ({cnt}×)")
            zeilen.append("  → Diese Themen für nächstes Team-Meeting vorbereiten.")

    zeilen += ["", sep1, f"Senzera Performance Hub  ·  {jetzt}", sep1]
    bericht = "\n".join(zeilen)

    st.text_area("Berichtstext:", value=bericht, height=520)

    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            "📄 Bericht als .txt",
            data=bericht.encode("utf-8"),
            file_name=f"Senzera_Bericht_{sel_rl}_{sel_monat}.txt",
            mime="text/plain", use_container_width=True,
        )
    with dl2:
        snap_cols = [c for c in ["Studiokürzel", "Stadt", "Rating", "NewReviews", "NPS"] if c in df_current.columns]
        st.download_button(
            "📥 Daten-Snapshot (CSV)",
            data=df_current[snap_cols].to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
            file_name=f"Senzera_Snapshot_{sel_rl}_{sel_monat}.csv",
            mime="text/csv", use_container_width=True,
        )


# ══════════════════════════════════════════════
# 12. EXPORT & FOOTER
# ══════════════════════════════════════════════

st.divider()
e1, e2 = st.columns(2)
with e1:
    st.download_button(
        "📥 Alle Google-Daten (CSV)",
        data=df_view.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
        file_name=f"Senzera_Google_{sel_monat}.csv",
        mime="text/csv", use_container_width=True,
    )
with e2:
    if not df_zen.empty:
        st.download_button(
            "📥 Zenloop-Daten (CSV)",
            data=df_zen.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
            file_name=f"Senzera_Zenloop_{sel_monat}.csv",
            mime="text/csv", use_container_width=True,
        )
    else:
        st.button("📥 Zenloop (keine Daten)", disabled=True, use_container_width=True)

# Senzera Footer
st.markdown(
    f"""
    <div style="text-align:center;padding:24px 0 8px;
                font-size:11px;letter-spacing:0.5px;color:{T['text_muted']};">
        <span style="color:{C_ORANGE};font-weight:600;">🌸 senzera</span>
        &nbsp;·&nbsp; Performance Hub v3
        &nbsp;·&nbsp; Alle Daten werden lokal verarbeitet
        &nbsp;·&nbsp; Keine externe Übertragung
    </div>
    """,
    unsafe_allow_html=True,
)
