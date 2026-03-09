import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os

st.set_page_config(page_title="Senzera Management Cockpit", layout="wide")

# --- DESIGN FARBEN ---
SENZERA_PINK = '#D81B60'
SENZERA_BLUE = '#1f77b4'
ZENLOOP_GREEN = '#00BFA5'
ZENLOOP_RED = '#FF5252'
ZENLOOP_YELLOW = '#FFC107'

# --- LADE-FUNKTIONEN ---
def load_all_data():
    # 1. Google Daten laden
    df_g = pd.DataFrame()
    if os.path.exists('Senzera_Dashboard_Data.csv'):
        df_g = pd.read_csv('Senzera_Dashboard_Data.csv')
        if 'Monat' not in df_g.columns: df_g['Monat'] = 'März 2026'
        if 'Studio_Display' not in df_g.columns:
            df_g['Studio_Display'] = df_g['Studiokürzel'] + " - " + df_g['Strasse + HNr']
    
    # 2. Zenloop Daten laden
    df_z = pd.DataFrame()
    if os.path.exists('Zenloop_Antworten.csv'):
        df_z = pd.read_csv('Zenloop_Antworten.csv')
    
    return df_g, df_z

df, df_nps = load_all_data()

if df.empty:
    st.error("Datei 'Senzera_Dashboard_Data.csv' nicht gefunden. Bitte lade sie bei GitHub hoch.")
    st.stop()

st.title("📊 Senzera Vertriebssteuerung")
st.markdown("**Management-Cockpit: Google-Bewertungen & Zenloop Kundenfeedback**")

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter-Optionen")
rl_options = ["Alle"] + sorted(df['Regionalleitung'].dropna().unique().tolist())
selected_rl = st.sidebar.selectbox("Regionalleitung wählen", options=rl_options)

# Filter-Logik
df_filtered = df if selected_rl == "Alle" else df[df['Regionalleitung'] == selected_rl]
city_options = sorted(df_filtered['Stadt'].unique())
selected_city = st.sidebar.multiselect("Stadt wählen", options=city_options, default=city_options)
df_filtered = df_filtered[df_filtered['Stadt'].isin(selected_city)]
studio_options = sorted(df_filtered['Studio_Display'].unique())
selected_studios = st.sidebar.multiselect("Studio wählen", options=studio_options, default=studio_options)
filtered_df = df_filtered[df_filtered['Studio_Display'].isin(selected_studios)]

# --- BERECHNUNGEN ---
if not filtered_df.empty:
    aktueller_monat = filtered_df['Monat'].unique()[-1]
    df_aktuell = filtered_df[filtered_df['Monat'] == aktueller_monat]
    kuerzel_liste = df_aktuell['Studiokürzel'].unique()

    # NPS Berechnung (Übergreifend)
    nps_total = 0
    total_responses = 0
    df_nps_filtered = pd.DataFrame()
    
    if not df_nps.empty and 'Property - studio' in df_nps.columns:
        df_nps_filtered = df_nps[df_nps['Property - studio'].isin(kuerzel_liste)]
        if not df_nps_filtered.empty:
            total_responses = len(df_nps_filtered)
            prom = len(df_nps_filtered[df_nps_filtered['score_type'] == 'promoter'])
            detr = len(df_nps_filtered[df_nps_filtered['score_type'] == 'detractor'])
            nps_total = ((prom - detr) / total_responses) * 100

    # --- TOP KPI REIHE ---
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Ø-Google Sterne", f"{df_aktuell['Rating'].mean():.2f} ⭐")
    k2.metric("Neue Rezensionen", f"+{df_aktuell['NewReviews'].sum()}")
    k3.metric("Ø-NPS (Zenloop)", f"{nps_total:.0f}" if not df_nps_filtered.empty else "--")
    k4.metric("NPS Antworten", f"{total_responses}")

    st.write("")

    # --- 🚨 DER ALARM-BEREICH (Direkt im Blickfeld) 🚨 ---
    critical_df = df_aktuell[df_aktuell['Rating'] < 4.2].sort_values('Rating')
    if not critical_df.empty:
        st.error(f"🚨 **ALARM: Handlungsbedarf!** {len(critical_df)} Studio(s) liegen unter 4,2 Sternen:")
        st.dataframe(critical_df[['Studiokürzel', 'Stadt', 'Rating', 'NewReviews']], use_container_width=True)
        with st.expander("💡 Action-Plan: Was ist jetzt zu tun?"):
            st.markdown("""
            * **Google-Karten:** Sofort neue Karten über die Monatsbestellung ordern.
            * **Team-Call:** Das Team sensibilisieren und den Fokus auf die Verabschiedung legen.
            * **Gästeansprache:** Jede Kundin aktiv nach der Behandlung um eine 5-Sterne-Bewertung bitten.
            """)
    else:
        st.success("✅ **Alles im grünen Bereich:** Alle gefilterten Studios liegen über der 4,2 Sterne Marke!")

    st.divider()

    # --- TABS FÜR DETAILS ---
    tab_g, tab_z = st.tabs(["🌟 GOOGLE ANALYSE", "💙 ZENLOOP DETAILS"])

    with tab_g:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("🏆 Top 10 Ratings")
            fig_g = px.bar(df_aktuell.sort_values('Rating', ascending=False).head(10), 
                           x='Studiokürzel', y='Rating', color='Rating', color_continuous_scale='RdYlGn', range_y=[3.5, 5])
            st.plotly_chart(fig_g, use_container_width=True)
        with col_g2:
            st.subheader("📈 Trend")
            trend = filtered_df.groupby('Monat', sort=False)['Rating'].mean().reset_index()
            fig_t = px.line(trend, x='Monat', y='Rating', markers=True)
            fig_t.update_traces(line_color=SENZERA_PINK, line_width=4)
            st.plotly_chart(fig_t, use_container_width=True)

    with tab_z:
        if df_nps_filtered.empty:
            st.info("Keine Zenloop-Daten für diese Auswahl vorhanden.")
        else:
            col_z1, col_z2 = st.columns(2)
            with col_z1:
                st.subheader("📊 NPS Verteilung")
                pie_df = df_nps_filtered['score_type'].value_counts().reset_index()
                fig_p = px.pie(pie_df, values='count', names='score_type', hole=0.4,
                               color='score_type', color_discrete_map={'promoter': ZENLOOP_GREEN, 'passive': ZENLOOP_YELLOW, 'detractor': ZENLOOP_RED})
                st.plotly_chart(fig_p, use_container_width=True)
            with col_z2:
                st.subheader("💬 Neueste Kommentare")
                df_comm = df_nps_filtered.dropna(subset=['comment']).sort_values('date_received', ascending=False).head(15)
                st.dataframe(df_comm[['Property - studio', 'score', 'comment']].rename(columns={'Property - studio': 'Studio', 'score': 'Punkte'}), use_container_width=True)

    st.divider()

    # --- 📝 AUTOMATISCHER BERICHT (UNTER DEN TABS) ---
    st.subheader("📝 Automatischer Monatsbericht")
    team_name = f"Region {selected_rl}" if selected_rl != "Alle" else "Senzera-Team"
    
    # Bericht generieren
    bericht = f"Hallo liebes {team_name},\n\nhier ist das Performance-Update für {aktueller_monat}:\n\n"
    bericht += f"⭐ Google Rating: {df_aktuell['Rating'].mean():.2f}\n"
    if not df_nps_filtered.empty:
        bericht += f"💙 Zenloop NPS: {nps_total:.0f}\n"
    
    bericht += "\nDie Details pro Studio:\n"
    for _, row in df_aktuell.sort_values('Rating').iterrows():
        # Studio-spezifischer NPS
        s_nps_str = ""
        if not df_nps_filtered.empty:
            s_data = df_nps_filtered[df_nps_filtered['Property - studio'] == row['Studiokürzel']]
            if not s_data.empty:
                s_nps = ((len(s_data[s_data['score_type'] == 'promoter']) - len(s_data[s_data['score_type'] == 'detractor'])) / len(s_data)) * 100
                s_nps_str = f" | NPS: {int(s_nps)}"
        
        bericht += f"- {row['Stadt']} ({row['Studiokürzel']}): {row['Rating']} Sterne{s_nps_str}\n"
        if row['Rating'] < 4.2:
            bericht += "  -> 🚨 Handlungsbedarf: Bitte Google-Karten forcieren!\n"

    st.text_area("Kopiere diesen Text für deine E-Mail:", bericht, height=300)

    # --- 📥 EXPORT SEKTION ---
    st.divider()
    st.subheader("📥 Daten-Export & Tabelle")
    col_ex1, col_ex2 = st.columns([1, 2])
    
    with col_ex1:
        csv_data = filtered_df.drop(columns=['Studio_Display']).to_csv(index=False, sep=';').encode('utf-8-sig')
        st.download_button("📥 Tabelle als Excel-CSV laden", data=csv_data, file_name=f"Senzera_Export_{aktueller_monat}.csv", use_container_width=True)
    
    with st.expander("Ganze Datentabelle anzeigen"):
        st.dataframe(filtered_df.drop(columns=['Studio_Display']), use_container_width=True)

else:
    st.info("Bitte wähle mindestens ein Studio aus.")
