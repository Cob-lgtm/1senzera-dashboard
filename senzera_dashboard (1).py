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
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Farben
C_PINK      = "#D81B60"
C_BLUE      = "#1E88E5"
C_GREEN     = "#00BFA5"
C_YELLOW    = "#FFB300"
C_RED       = "#F44336"

# Schwellwerte
RATING_CRITICAL = 4.2
RATING_GOOD     = 4.5
TOP_LABELS      = 10
TOP_COMMENTS    = 5

# Pflicht-Spalten
REQ_GOOGLE  = {"Studiokürzel", "Stadt", "Regionalleitung", "Rating"}
REQ_ZENLOOP = {"Property - studio", "score_type", "score"}

# ══════════════════════════════════════════════
# 2. CUSTOM CSS – Dark Cockpit Design
# ══════════════════════════════════════════════

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: #0D1117; }
    [data-testid="stSidebar"]          { background: #161B22; border-right: 1px solid #21262D; }
    [data-testid="stHeader"]           { background: transparent; }

    [data-testid="metric-container"] {
        background: #161B22;
        border: 1px solid #21262D;
        border-radius: 10px;
        padding: 14px 18px;
    }

    button[data-baseweb="tab"] {
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 0.4px;
        color: #8B949E !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #E6EDF3 !important;
        border-bottom-color: #D81B60 !important;
    }

    h1, h2, h3 { color: #E6EDF3 !important; }
    h3 { letter-spacing: 0.3px; }
    p, label, .stCaption { color: #8B949E; }
    hr { border-color: #21262D; margin: 1rem 0; }

    textarea {
        font-family: 'Courier New', monospace !important;
        font-size: 13px !important;
        background: #0D1117 !important;
        color: #C9D1D9 !important;
        border: 1px solid #30363D !important;
    }

    .senzera-logo {
        font-size: 22px;
        font-weight: 800;
        letter-spacing: 2px;
        color: #D81B60;
        padding: 8px 0 16px 0;
    }
</style>
""", unsafe_allow_html=True)


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
    """NPS aus score_type-Spalte ('promoter'/'passive'/'detractor')."""
    if df.empty or "score_type" not in df.columns:
        return None
    total = len(df)
    if total == 0:
        return None
    prom = (df["score_type"] == "promoter").sum()
    detr = (df["score_type"] == "detractor").sum()
    return round(((prom - detr) / total) * 100, 1)


def calc_nps_from_score(df: pd.DataFrame) -> Optional[float]:
    """NPS direkt aus numerischem Score (Fallback)."""
    if df.empty or "score" not in df.columns:
        return None
    scores = df["score"].dropna()
    if len(scores) == 0:
        return None
    return round(((scores >= 9).sum() - (scores <= 6).sum()) / len(scores) * 100, 1)


def calc_sentiment(df: pd.DataFrame) -> Optional[float]:
    """Anteil positiver Kommentare in Prozent."""
    if df.empty or "sentiment" not in df.columns:
        return None
    with_c = df.dropna(subset=["comment"]) if "comment" in df.columns else df
    with_c = with_c[with_c["comment"].astype(str).str.strip().ne("nan")]
    if with_c.empty:
        return None
    return round((with_c["sentiment"] == "positive").sum() / len(with_c) * 100, 1)


def get_top_labels(df: pd.DataFrame, n: int = 5) -> pd.Series:
    if "labels" not in df.columns:
        return pd.Series(dtype=int)
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
    # Robustes Logo ohne externe URL
    st.markdown('<div class="senzera-logo">✦ SENZERA</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 🔍 Filter")

    rl_options = ["Alle"] + sorted(df_google["Regionalleitung"].dropna().unique().tolist())
    sel_rl     = st.selectbox("Regionalleitung", rl_options)

    df_by_rl      = df_google if sel_rl == "Alle" else df_google[df_google["Regionalleitung"] == sel_rl]
    studio_options = sorted(df_by_rl["Studio_Name"].unique().tolist())

    sel_studios = st.multiselect(
        "Studios", studio_options, default=studio_options,
        help="Mehrfachauswahl möglich",
    )

    if not sel_studios:
        st.warning("⚠️ Bitte mindestens ein Studio auswählen.")
        st.stop()

    st.markdown("---")

    alle_monate = sorted(df_by_rl["Monat"].dropna().unique().tolist())
    sel_monat   = st.selectbox("Monat", alle_monate, index=len(alle_monate) - 1) if len(alle_monate) > 1 else (alle_monate[-1] if alle_monate else "Unbekannt")

    st.caption(f"📅 Aktiver Monat: **{sel_monat}**")
    st.markdown("---")

    if st.button("🔄 Cache leeren & neu laden", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.caption("Senzera Hub · Daten lokal verarbeitet")


# ══════════════════════════════════════════════
# 7. GEFILTERTE DATENSÄTZE & KPIs
# ══════════════════════════════════════════════

df_view    = df_by_rl[df_by_rl["Studio_Name"].isin(sel_studios)].copy()
df_current = df_view[df_view["Monat"] == sel_monat].copy()

# Vormonat für Vergleiche
monate_sorted = sorted(df_view["Monat"].dropna().unique().tolist())
idx_aktuell   = monate_sorted.index(sel_monat) if sel_monat in monate_sorted else -1
vormonat      = monate_sorted[idx_aktuell - 1] if idx_aktuell > 0 else None
df_vormonat   = df_view[df_view["Monat"] == vormonat].copy() if vormonat else pd.DataFrame()

selected_codes = df_current["Studiokürzel"].unique()

df_zen = (
    df_zenloop[df_zenloop["Property - studio"].isin(selected_codes)].copy()
    if not df_zenloop.empty else pd.DataFrame()
)

# KPIs einmalig berechnen
avg_rating      = df_current["Rating"].mean()      if not df_current.empty else 0.0
total_reviews   = int(df_current["NewReviews"].sum()) if not df_current.empty else 0
nps_gesamt      = calc_nps(df_zen) or calc_nps_from_score(df_zen)
sentiment_pct   = calc_sentiment(df_zen)
total_responses = len(df_zen)
avg_rating_vm   = df_vormonat["Rating"].mean() if not df_vormonat.empty else None
delta_rating    = round(avg_rating - avg_rating_vm, 2) if avg_rating_vm is not None else None
critical_studios = df_current[df_current["Rating"] < RATING_CRITICAL]
n_critical       = len(critical_studios)


# ══════════════════════════════════════════════
# 8. HEADER
# ══════════════════════════════════════════════

col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("🏆 Senzera Management Cockpit")
    st.markdown(
        f"<span style='color:#8B949E;font-size:13px;'>"
        f"Fokus: <b style='color:#C9D1D9'>{sel_rl}</b> &nbsp;·&nbsp; "
        f"Monat: <b style='color:#C9D1D9'>{sel_monat}</b> &nbsp;·&nbsp; "
        f"{len(sel_studios)} Studio(s) aktiv"
        f"</span>",
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

k4.metric("😊 Positive Stimmung", f"{sentiment_pct:.0f}%" if sentiment_pct is not None else "–",
          help="Anteil positiver Kommentare (nur Einträge mit Text)")
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
    "📊 Performance & Trends",
    "💙 Zenloop Deep-Dive",
    "📝 Management-Bericht",
])


# ── TAB 1: PERFORMANCE & TRENDS ───────────────
with tab1:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Google Ranking")
        df_ranked = df_current.sort_values("Rating", ascending=True).copy()
        bar_colors = df_ranked["Rating"].apply(
            lambda r: C_RED if r < RATING_CRITICAL else (C_YELLOW if r < RATING_GOOD else C_GREEN)
        ).tolist()

        fig_rank = go.Figure(go.Bar(
            x=df_ranked["Rating"], y=df_ranked["Studiokürzel"],
            orientation="h", marker_color=bar_colors,
            text=df_ranked["Rating"].apply(lambda r: f"{r:.2f}"),
            textposition="outside", textfont=dict(color="#C9D1D9", size=12),
            hovertemplate="<b>%{y}</b><br>Rating: %{x:.2f}<extra></extra>",
        ))
        fig_rank.add_vline(
            x=RATING_CRITICAL, line_dash="dash", line_color=C_RED, opacity=0.7,
            annotation_text=f"Grenze {RATING_CRITICAL}",
            annotation_font_color=C_RED, annotation_font_size=11,
        )
        fig_rank.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#C9D1D9", xaxis=dict(range=[3.5, 5.15], gridcolor="#21262D"),
            yaxis=dict(tickfont=dict(size=11)),
            margin=dict(l=10, r=40, t=10, b=10),
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
            line_color=C_PINK, line_width=3,
            marker=dict(size=9, color=C_PINK, line=dict(width=2, color="#0D1117")),
        )
        fig_t.add_hline(y=RATING_CRITICAL, line_dash="dot", line_color=C_RED,   opacity=0.5)
        fig_t.add_hline(y=RATING_GOOD,     line_dash="dot", line_color=C_GREEN, opacity=0.4)
        fig_t.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#C9D1D9",
            yaxis=dict(range=[3.5, 5.0], gridcolor="#21262D"),
            xaxis=dict(gridcolor="#21262D"),
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


# ── TAB 2: ZENLOOP DEEP-DIVE ──────────────────
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
        m1.metric(f"NPS {sel_s}",
                  f"{s_nps:.0f}" if s_nps is not None else "–",
                  delta=nps_bewertung(s_nps) if s_nps is not None else None,
                  delta_color="normal" if s_nps and s_nps >= 0 else "inverse")
        m2.metric("😊 Promoter",    str(s_prom))
        m3.metric("😐 Passive",     str(s_pass))
        m4.metric("😠 Detraktoren", str(s_detr))

        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown("**Top Themen dieses Studios:**")
            top_lb = get_top_labels(df_s, 6)
            if not top_lb.empty:
                for label, cnt in top_lb.items():
                    st.markdown(f"- {label} &nbsp;`{cnt}×`", unsafe_allow_html=True)
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
                fig_lb = px.bar(all_lb, x="Anzahl", y="Thema", orientation="h",
                                color_discrete_sequence=[C_BLUE])
                fig_lb.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#C9D1D9", xaxis=dict(gridcolor="#21262D"),
                    yaxis=dict(categoryorder="total ascending"),
                    margin=dict(l=10, r=10, t=10, b=10),
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
                    fig_s = px.bar(df_seg, x="Behandlung", y="NPS",
                                   color="NPS", color_continuous_scale="RdYlGn",
                                   range_color=[-100, 100], text="NPS",
                                   hover_data={"n": True})
                    fig_s.update_traces(texttemplate="%{text:.0f}", textposition="outside")
                    fig_s.add_hline(y=0, line_color="#30363D")
                    fig_s.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                        font_color="#C9D1D9", coloraxis_showscale=False,
                        yaxis=dict(gridcolor="#21262D"),
                        margin=dict(l=10, r=10, t=10, b=10),
                    )
                    st.plotly_chart(fig_s, use_container_width=True)

        # NPS Donut
        if "score_type" in df_zen.columns:
            st.subheader("NPS-Zusammensetzung")
            type_c = df_zen["score_type"].value_counts().reset_index()
            type_c.columns = ["Typ", "Anzahl"]
            fig_d = px.pie(type_c, values="Anzahl", names="Typ", hole=0.6,
                           color="Typ",
                           color_discrete_map={"promoter": C_GREEN, "passive": C_YELLOW, "detractor": C_RED})
            if nps_gesamt is not None:
                fig_d.add_annotation(
                    text=f"NPS<br><b>{nps_gesamt:.0f}</b>",
                    x=0.5, y=0.5, font_size=18, font_color="#E6EDF3", showarrow=False,
                )
            fig_d.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", font_color="#C9D1D9",
                legend=dict(orientation="h", yanchor="bottom", y=-0.15),
                margin=dict(t=10, b=10),
            )
            _, dc, _ = st.columns([1, 2, 1])
            with dc:
                st.plotly_chart(fig_d, use_container_width=True)

        # NPS-Ranking pro Studio
        st.subheader("NPS-Ranking aller Studios")
        nps_ranking = []
        for code in codes_mit_zen:
            d     = df_zen[df_zen["Property - studio"] == code]
            nps_v = calc_nps(d) or calc_nps_from_score(d)
            g_r   = df_current[df_current["Studiokürzel"] == code]["Rating"].values
            if nps_v is not None:
                nps_ranking.append({
                    "Studio": code,
                    "NPS": nps_v,
                    "Google ⭐": round(g_r[0], 2) if len(g_r) > 0 else None,
                    "Antworten": len(d),
                })
        if nps_ranking:
            df_nps_rank = pd.DataFrame(nps_ranking).sort_values("NPS", ascending=False).reset_index(drop=True)
            df_nps_rank.insert(0, "Rang", range(1, len(df_nps_rank) + 1))
            st.dataframe(df_nps_rank, use_container_width=True, hide_index=True)


# ── TAB 3: MANAGEMENT-BERICHT ─────────────────
with tab3:
    st.subheader("📝 Intelligenter Management-Bericht")
    st.caption(
        "Automatisch aus echten Daten generiert – mit Trend-Analyse, "
        "Kundenfeedback-Insights und konkreten Handlungsempfehlungen."
    )

    # Daten für Bericht
    studios_sorted  = df_current.sort_values("Rating", ascending=False)
    top3            = studios_sorted.head(3)
    all_top_labels  = get_top_labels(df_zen, 5)
    all_neg_labels  = get_neg_labels(df_zen, 5)

    verbessert, verschlechtert = [], []
    if not df_vormonat.empty:
        vm_ratings = df_vormonat.set_index("Studiokürzel")["Rating"]
        for _, row in df_current.iterrows():
            old = vm_ratings.get(row["Studiokürzel"])
            if old is not None:
                d = row["Rating"] - old
                if   d >=  0.1: verbessert.append(f"{row['Studiokürzel']} (+{d:.1f})")
                elif d <= -0.1: verschlechtert.append(f"{row['Studiokürzel']} ({d:.1f})")

    # Bericht aufbauen
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
        "I. ÜBERBLICK",
        sep2,
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
            "",
            "  Empfohlene Maßnahmen:",
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
# 12. EXPORT
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

st.caption(
    "Senzera Performance Hub v3 · Powered by Streamlit · "
    "Alle Daten werden lokal verarbeitet – keine externe Übertragung."
)
