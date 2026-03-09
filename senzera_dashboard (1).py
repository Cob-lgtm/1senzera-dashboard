"""
Senzera Performance Hub – Management Cockpit
=============================================
Vertriebssteuerungs-Dashboard für Regionalleiterinnen.

Voraussetzungen:
    pip install streamlit pandas plotly numpy

Datenquellen:
    - Senzera_Dashboard_Data.csv  (Google-Bewertungen pro Studio & Monat)
    - Zenloop_Antworten.csv       (NPS-Umfragen mit Kommentaren)

Starten:
    streamlit run senzera_dashboard.py
"""

from __future__ import annotations

import os
from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ──────────────────────────────────────────────
# 1. KONFIGURATION & KONSTANTEN
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="Senzera Performance Hub",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Farbpalette
C_PINK       = "#D81B60"
C_BLUE       = "#1E88E5"
C_PROMOTER   = "#00BFA5"
C_PASSIVE    = "#FFB300"
C_DETRACTOR  = "#F44336"
C_BG_DARK    = "#0F1117"

# Schwellwerte
RATING_CRITICAL = 4.2
RATING_GOOD     = 4.5
TOP_LABELS      = 10   # Wie viele Themen-Labels werden angezeigt
TOP_COMMENTS    = 5    # Wie viele Kommentare im Deep-Dive

# Pflicht-Spalten beider Dateien
REQUIRED_COLS_GOOGLE  = {"Studiokürzel", "Stadt", "Regionalleitung", "Rating", "NewReviews"}
REQUIRED_COLS_ZENLOOP = {"Property - studio", "score_type", "score"}

# ──────────────────────────────────────────────
# 2. CUSTOM CSS
# ──────────────────────────────────────────────

st.markdown(
    """
    <style>
        /* Globales Styling */
        [data-testid="stAppViewContainer"] {background: #0F1117;}
        [data-testid="stSidebar"]          {background: #161B22;}
        [data-testid="stHeader"]           {background: transparent;}

        /* Metric-Cards */
        [data-testid="metric-container"] {
            background: #161B22;
            border: 1px solid #30363D;
            border-radius: 12px;
            padding: 16px 20px;
        }

        /* Tabs */
        button[data-baseweb="tab"] {
            font-weight: 600;
            font-size: 14px;
            letter-spacing: 0.5px;
        }

        /* Subtitles */
        h3 {color: #E6EDF3 !important; letter-spacing: 0.5px;}

        /* Divider */
        hr {border-color: #30363D;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# 3. DATEN LADEN & VALIDIEREN
# ──────────────────────────────────────────────

@st.cache_data(show_spinner="Daten werden geladen …")
def load_google_data(path: str = "Senzera_Dashboard_Data.csv") -> pd.DataFrame:
    """Lädt und bereinigt die Google-Bewertungsdaten."""
    if not os.path.exists(path):
        return pd.DataFrame()

    df = pd.read_csv(path)

    missing = REQUIRED_COLS_GOOGLE - set(df.columns)
    if missing:
        st.error(f"Fehlende Spalten in '{path}': {missing}")
        st.stop()

    # Monatsspalte absichern
    if "Monat" not in df.columns:
        df["Monat"] = "Unbekannt"

    # Anzeigename kombinieren
    df["Studio_Name"] = df["Studiokürzel"] + " (" + df["Stadt"] + ")"

    # Typen sicherstellen
    df["Rating"]     = pd.to_numeric(df["Rating"],     errors="coerce")
    df["NewReviews"] = pd.to_numeric(df["NewReviews"], errors="coerce").fillna(0).astype(int)

    return df


@st.cache_data(show_spinner=False)
def load_zenloop_data(path: str = "Zenloop_Antworten.csv") -> pd.DataFrame:
    """Lädt und bereinigt die Zenloop-NPS-Daten."""
    if not os.path.exists(path):
        return pd.DataFrame()

    df = pd.read_csv(path)

    missing = REQUIRED_COLS_ZENLOOP - set(df.columns)
    if missing:
        st.warning(f"Fehlende Zenloop-Spalten: {missing} – einige Widgets werden ausgeblendet.")

    df["score"] = pd.to_numeric(df.get("score", pd.Series(dtype=float)), errors="coerce")
    return df


# ──────────────────────────────────────────────
# 4. HILFS-FUNKTIONEN
# ──────────────────────────────────────────────

def calc_nps(df: pd.DataFrame) -> Optional[float]:
    """Berechnet den NPS-Wert. Gibt None zurück wenn keine Daten vorhanden."""
    if df.empty or "score_type" not in df.columns:
        return None
    total = len(df)
    if total == 0:
        return None
    promoters   = (df["score_type"] == "promoter").sum()
    detractors  = (df["score_type"] == "detractor").sum()
    return round(((promoters - detractors) / total) * 100, 1)


def calc_positive_sentiment(df: pd.DataFrame) -> Optional[float]:
    """Berechnet Anteil positiver Kommentare in Prozent."""
    if df.empty or "sentiment" not in df.columns:
        return None
    comments = df.dropna(subset=["comment"]) if "comment" in df.columns else df
    if comments.empty:
        return None
    positive = (comments["sentiment"] == "positive").sum()
    return round((positive / len(comments)) * 100, 1)


def nps_color(nps: float) -> str:
    """Gibt eine Farbe passend zum NPS-Wert zurück."""
    if nps >= 50:
        return C_PROMOTER
    if nps >= 0:
        return C_PASSIVE
    return C_DETRACTOR


def studio_status_emoji(rating: float) -> str:
    if rating >= RATING_GOOD:
        return "✅"
    if rating >= RATING_CRITICAL:
        return "⚠️"
    return "🚨"


# ──────────────────────────────────────────────
# 5. DATEN LADEN
# ──────────────────────────────────────────────

df_google  = load_google_data()
df_zenloop = load_zenloop_data()

if df_google.empty:
    st.error("❌ Datei **'Senzera_Dashboard_Data.csv'** nicht gefunden!")
    st.info("Bitte lege die Datei im selben Ordner wie dieses Skript ab und starte neu.")
    st.stop()

# ──────────────────────────────────────────────
# 6. SIDEBAR – FILTER
# ──────────────────────────────────────────────

with st.sidebar:
    st.image(
        "https://senzera.com/wp-content/uploads/2021/05/senzera-logo.svg",
        width=130,
    )
    st.markdown("---")
    st.markdown("### 🔍 Filter")

    # Regionalleitung
    rl_options = ["Alle"] + sorted(df_google["Regionalleitung"].dropna().unique().tolist())
    sel_rl = st.selectbox("Regionalleitung", rl_options)

    df_by_rl = df_google if sel_rl == "Alle" else df_google[df_google["Regionalleitung"] == sel_rl]

    # Studios
    studio_options = sorted(df_by_rl["Studio_Name"].unique().tolist())
    sel_studios = st.multiselect(
        "Studios",
        studio_options,
        default=studio_options,
        help="Mehrfachauswahl möglich",
    )

    if not sel_studios:
        st.warning("Bitte mindestens ein Studio auswählen.")
        st.stop()

    st.markdown("---")
    st.caption("📌 Daten werden gecacht. Seite neu laden um zu aktualisieren.")
    if st.button("🔄 Cache leeren", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ──────────────────────────────────────────────
# 7. GEFILTERTE DATENSÄTZE
# ──────────────────────────────────────────────

df_view = df_by_rl[df_by_rl["Studio_Name"].isin(sel_studios)].copy()

# Letzter verfügbarer Monat
aktueller_monat: str = df_view["Monat"].dropna().unique()[-1]
df_current = df_view[df_view["Monat"] == aktueller_monat]

# Zugehörige Zenloop-Daten
selected_codes = df_view["Studiokürzel"].unique()
df_zen_view = (
    df_zenloop[df_zenloop["Property - studio"].isin(selected_codes)].copy()
    if not df_zenloop.empty
    else pd.DataFrame()
)

# Vorab berechnete KPIs (einmalig, nicht in mehreren Tabs neu berechnen)
avg_google_rating = df_current["Rating"].mean()
total_new_reviews  = df_current["NewReviews"].sum()
nps_total          = calc_nps(df_zen_view)
sentiment_pct      = calc_positive_sentiment(df_zen_view)
total_responses    = len(df_zen_view) if not df_zen_view.empty else 0

# ──────────────────────────────────────────────
# 8. HEADER
# ──────────────────────────────────────────────

st.title("🏆 Senzera Management Cockpit")
st.markdown(
    f"<span style='color:#8B949E;font-size:14px;'>"
    f"Fokus: <b>{sel_rl}</b> &nbsp;|&nbsp; Zeitraum: <b>{aktueller_monat}</b> &nbsp;|&nbsp; "
    f"{len(sel_studios)} Studio(s) aktiv</span>",
    unsafe_allow_html=True,
)
st.divider()

# ──────────────────────────────────────────────
# 9. TOP KPIs
# ──────────────────────────────────────────────

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "🌟 Google Ø-Rating",
    f"{avg_google_rating:.2f} ⭐",
    delta=f"+{total_new_reviews} neue Rezensionen",
)

if nps_total is not None:
    k2.metric(
        "💙 Zenloop NPS",
        f"{nps_total:.0f}",
        delta="Promoter − Detraktoren" if nps_total >= 0 else "Negativ – Handlungsbedarf",
        delta_color="normal" if nps_total >= 0 else "inverse",
    )
else:
    k2.metric("💙 Zenloop NPS", "Keine Daten")

if sentiment_pct is not None:
    k3.metric(
        "😊 Positive Stimmung",
        f"{sentiment_pct:.0f}%",
        help="Anteil positiver Kommentare (nur Einträge mit Text)",
    )
else:
    k3.metric("😊 Positive Stimmung", "Keine Daten")

k4.metric("📝 Zenloop Antworten", f"{total_responses:,}".replace(",", "."))

# ──────────────────────────────────────────────
# 10. ALARM-ZONE
# ──────────────────────────────────────────────

critical_studios = df_current[df_current["Rating"] < RATING_CRITICAL]

if not critical_studios.empty:
    count = len(critical_studios)
    st.error(
        f"🚨 **HANDLUNGSBEDARF:** {count} Studio{'s' if count > 1 else ''} "
        f"unter {RATING_CRITICAL} Sternen"
    )
    alarm_cols = st.columns(min(count, 4))
    for idx, (_, row) in enumerate(critical_studios.iterrows()):
        with alarm_cols[idx % 4]:
            st.warning(
                f"**{row['Studiokürzel']}** – {row['Stadt']}\n\n"
                f"{row['Rating']:.2f} ⭐ | {row['NewReviews']} Rezensionen"
            )
else:
    st.success("✅ Alle Studios im grünen Bereich.")

st.divider()

# ──────────────────────────────────────────────
# 11. ANALYSE-TABS
# ──────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs(
    ["📊 Performance & Trends", "💙 Zenloop Deep-Dive", "📝 Management-Bericht"]
)

# ── TAB 1: Performance & Trends ────────────────
with tab1:
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Google Ranking – aktueller Monat")
        df_ranked = df_current.sort_values("Rating", ascending=True)
        fig_rank = px.bar(
            df_ranked,
            x="Rating",
            y="Studiokürzel",
            orientation="h",
            color="Rating",
            color_continuous_scale="RdYlGn",
            range_x=[3.5, 5.0],
            text="Rating",
            labels={"Rating": "Ø-Bewertung", "Studiokürzel": "Studio"},
        )
        fig_rank.update_traces(
            texttemplate="%{text:.2f}",
            textposition="outside",
        )
        fig_rank.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#C9D1D9",
            coloraxis_showscale=False,
            xaxis=dict(gridcolor="#30363D"),
        )
        # Kritische Linie einzeichnen
        fig_rank.add_vline(
            x=RATING_CRITICAL,
            line_dash="dash",
            line_color=C_DETRACTOR,
            annotation_text=f"Kritisch ({RATING_CRITICAL})",
            annotation_font_color=C_DETRACTOR,
        )
        st.plotly_chart(fig_rank, use_container_width=True)

    with col_right:
        st.subheader("Entwicklungs-Trend (Ø alle Studios)")
        trend = (
            df_view.groupby("Monat", sort=False)["Rating"]
            .mean()
            .reset_index()
            .rename(columns={"Rating": "Ø Rating"})
        )
        fig_trend = px.line(
            trend,
            x="Monat",
            y="Ø Rating",
            markers=True,
            labels={"Ø Rating": "Durchschnitt"},
        )
        fig_trend.update_traces(
            line_color=C_PINK,
            line_width=3,
            marker=dict(size=8, color=C_PINK),
        )
        fig_trend.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#C9D1D9",
            yaxis=dict(range=[3.5, 5.0], gridcolor="#30363D"),
            xaxis=dict(gridcolor="#30363D"),
        )
        fig_trend.add_hline(
            y=RATING_CRITICAL,
            line_dash="dash",
            line_color=C_DETRACTOR,
            opacity=0.5,
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    # Detailtabelle
    st.subheader("Studio-Übersicht")
    display_cols = [c for c in ["Studio_Name", "Rating", "NewReviews", "Regionalleitung"] if c in df_current.columns]
    df_display = df_current[display_cols].sort_values("Rating", ascending=False).reset_index(drop=True)
    df_display.columns = [c.replace("_", " ") for c in df_display.columns]
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
    )

# ── TAB 2: Zenloop Deep-Dive ───────────────────
with tab2:
    if df_zen_view.empty:
        st.warning("⚠️ Keine Zenloop-Daten gefunden. Bitte 'Zenloop_Antworten.csv' bereitstellen.")
    else:
        # ── Studio-Selektor
        st.subheader("🎯 Studio-Check")
        sel_studio_code = st.selectbox(
            "Detailanalyse für Studio:",
            options=sorted(selected_codes),
        )
        df_studio = df_zen_view[df_zen_view["Property - studio"] == sel_studio_code]

        studio_nps = calc_nps(df_studio)
        studio_sentiment = calc_positive_sentiment(df_studio)

        sc1, sc2, sc3 = st.columns([1, 1, 2])

        with sc1:
            if studio_nps is not None:
                st.metric(
                    f"NPS {sel_studio_code}",
                    f"{studio_nps:.0f}",
                    delta="positiv" if studio_nps >= 0 else "negativ",
                    delta_color="normal" if studio_nps >= 0 else "inverse",
                )
            else:
                st.metric(f"NPS {sel_studio_code}", "–")

            if studio_sentiment is not None:
                st.metric("Stimmung", f"{studio_sentiment:.0f}%")

        with sc2:
            st.markdown("**Top Themen:**")
            if "labels" in df_studio.columns:
                top_labels = (
                    df_studio["labels"]
                    .dropna()
                    .str.split(";")
                    .explode()
                    .str.strip()
                    .value_counts()
                    .head(5)
                )
                for label, count in top_labels.items():
                    st.markdown(f"- **{label}** ({count}×)")
            else:
                st.caption("Keine Label-Spalte vorhanden.")

        with sc3:
            st.markdown("**Letzte Kommentare:**")
            if "comment" in df_studio.columns:
                latest_comments = (
                    df_studio[["score", "comment"]]
                    .dropna(subset=["comment"])
                    .head(TOP_COMMENTS)
                )
                st.dataframe(latest_comments, use_container_width=True, hide_index=True)
            else:
                st.caption("Keine Kommentar-Spalte vorhanden.")

        st.divider()

        # ── Übergreifende Analyse
        st.subheader("Übergreifende Analyse")
        zcol1, zcol2 = st.columns(2)

        with zcol1:
            st.markdown("**Häufigste Themen (alle Studios)**")
            if "labels" in df_zen_view.columns:
                label_counts = (
                    df_zen_view["labels"]
                    .dropna()
                    .str.split(";")
                    .explode()
                    .str.strip()
                    .value_counts()
                    .head(TOP_LABELS)
                    .reset_index()
                    .rename(columns={"index": "Thema", "labels": "Anzahl"})
                )
                fig_labels = px.bar(
                    label_counts,
                    x="count",
                    y="labels",
                    orientation="h",
                    color_discrete_sequence=[C_BLUE],
                    labels={"count": "Nennungen", "labels": "Thema"},
                )
                fig_labels.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#C9D1D9",
                    xaxis=dict(gridcolor="#30363D"),
                    yaxis=dict(categoryorder="total ascending"),
                )
                st.plotly_chart(fig_labels, use_container_width=True)
            else:
                st.caption("Keine Label-Daten verfügbar.")

        with zcol2:
            st.markdown("**NPS nach Behandlungsart**")
            seg_col = "Property - product_segment"
            if seg_col in df_zen_view.columns:
                seg_nps_list = []
                for segment in df_zen_view[seg_col].dropna().unique():
                    df_seg = df_zen_view[df_zen_view[seg_col] == segment]
                    nps_seg = calc_nps(df_seg)
                    if nps_seg is not None:
                        seg_nps_list.append({"Behandlung": segment, "NPS": nps_seg})

                if seg_nps_list:
                    df_seg_nps = pd.DataFrame(seg_nps_list).sort_values("NPS", ascending=False)
                    fig_seg = px.bar(
                        df_seg_nps,
                        x="Behandlung",
                        y="NPS",
                        color="NPS",
                        color_continuous_scale="RdYlGn",
                        range_color=[-100, 100],
                        text="NPS",
                    )
                    fig_seg.update_traces(texttemplate="%{text:.0f}", textposition="outside")
                    fig_seg.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_color="#C9D1D9",
                        coloraxis_showscale=False,
                        yaxis=dict(gridcolor="#30363D"),
                    )
                    fig_seg.add_hline(y=0, line_color="#30363D")
                    st.plotly_chart(fig_seg, use_container_width=True)
            else:
                st.caption("Keine Segment-Daten verfügbar.")

        # ── NPS Promoter / Passive / Detractor Donut
        if "score_type" in df_zen_view.columns:
            st.subheader("NPS-Zusammensetzung")
            type_counts = df_zen_view["score_type"].value_counts().reset_index()
            type_counts.columns = ["Typ", "Anzahl"]
            color_map = {
                "promoter":  C_PROMOTER,
                "passive":   C_PASSIVE,
                "detractor": C_DETRACTOR,
            }
            fig_donut = px.pie(
                type_counts,
                values="Anzahl",
                names="Typ",
                hole=0.55,
                color="Typ",
                color_discrete_map=color_map,
            )
            fig_donut.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#C9D1D9",
                legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            )
            if nps_total is not None:
                fig_donut.add_annotation(
                    text=f"NPS<br><b>{nps_total:.0f}</b>",
                    x=0.5, y=0.5,
                    font_size=18,
                    font_color="#E6EDF3",
                    showarrow=False,
                )
            # Donut in schmaler Spalte zentrieren
            _, donut_col, _ = st.columns([1, 2, 1])
            with donut_col:
                st.plotly_chart(fig_donut, use_container_width=True)

# ── TAB 3: Management-Bericht ──────────────────
with tab3:
    st.subheader("Management-Bericht – Copy & Paste")
    st.caption("Automatisch generierter Statusbericht für deine Region.")

    # Bericht zusammenstellen
    sep = "=" * 40
    lines = [
        f"SENZERA MANAGEMENT-BERICHT",
        f"Region: {sel_rl}  |  Stand: {aktueller_monat}",
        sep,
        "",
        "KENNZAHLEN ÜBERBLICK",
        f"  Google Ø-Rating    : {avg_google_rating:.2f} ⭐  ({total_new_reviews} neue Rezensionen)",
    ]

    if nps_total is not None:
        lines.append(f"  Zenloop NPS        : {nps_total:.0f}")
    if sentiment_pct is not None:
        lines.append(f"  Positive Stimmung  : {sentiment_pct:.0f}%  (aus {total_responses} Antworten)")

    lines += ["", sep, "", "STUDIO STATUS:"]

    for code in sorted(selected_codes):
        row_data = df_current[df_current["Studiokürzel"] == code]
        if row_data.empty:
            continue
        rating = row_data["Rating"].values[0]
        reviews = row_data["NewReviews"].values[0]
        status = studio_status_emoji(rating)
        lines.append(
            f"  {status}  {code:<6} {rating:.2f} ⭐  ({reviews} Rez.)  "
            + ("→ KRITISCH – Maßnahmen erforderlich!" if rating < RATING_CRITICAL else "")
        )

    if not critical_studios.empty:
        lines += [
            "",
            sep,
            "",
            "HANDLUNGSBEDARF:",
        ]
        for _, row in critical_studios.iterrows():
            lines.append(
                f"  🚨 {row['Studiokürzel']} ({row['Stadt']}): "
                f"{row['Rating']:.2f} ⭐ – unter Schwelle von {RATING_CRITICAL}"
            )

    lines += ["", sep, f"Erstellt: {pd.Timestamp.now().strftime('%d.%m.%Y %H:%M')}"]

    report_text = "\n".join(lines)
    st.text_area("Berichtstext:", value=report_text, height=420)

    # Bericht als .txt herunterladen
    st.download_button(
        label="📄 Bericht als .txt herunterladen",
        data=report_text.encode("utf-8"),
        file_name=f"Senzera_Bericht_{sel_rl}_{aktueller_monat}.txt",
        mime="text/plain",
    )

# ──────────────────────────────────────────────
# 12. EXPORT
# ──────────────────────────────────────────────

st.divider()
export_col1, export_col2 = st.columns(2)

with export_col1:
    csv_data = df_view.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
    st.download_button(
        label="📥 Google-Daten als CSV exportieren",
        data=csv_data,
        file_name=f"Senzera_GoogleDaten_{aktueller_monat}.csv",
        mime="text/csv",
        use_container_width=True,
    )

with export_col2:
    if not df_zen_view.empty:
        zen_csv = df_zen_view.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
        st.download_button(
            label="📥 Zenloop-Daten als CSV exportieren",
            data=zen_csv,
            file_name=f"Senzera_Zenloop_{aktueller_monat}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.button("📥 Zenloop-Export (keine Daten)", disabled=True, use_container_width=True)

st.caption("Senzera Performance Hub · Powered by Streamlit · Daten werden lokal verarbeitet.")
