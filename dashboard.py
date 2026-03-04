import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Senzera Google-Bewertungen Dashboard", layout="wide")

# Daten laden (OHNE Cache-Speicher, damit Updates sofort sichtbar sind!)
def load_data():
    df = pd.read_csv('Senzera_Dashboard_Data.csv')
    # Falls die Spalte Monat noch fehlt (für unseren Übergang heute)
    if 'Monat' not in df.columns:
        df['Monat'] = 'März 2026'
    return df

try:
    df = load_data()
except Exception as e:
    st.error("Datei 'Senzera_Dashboard_Data.csv' nicht gefunden. Bitte lade die Daten hoch.")
    st.stop()

st.title("📊 Senzera Vertriebssteuerung: Google-Bewertungen")
st.markdown("Monitoring der Studio-Performance & Entwicklung in Deutschland und Österreich")

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter-Optionen")

rl_options = ["Alle"] + sorted(df['Regionalleitung'].dropna().unique().tolist())
selected_rl = st.sidebar.selectbox("Regionalleitung wählen", options=rl_options)

if selected_rl != "Alle":
    df_rl_filtered = df[df['Regionalleitung'] == selected_rl]
else:
    df_rl_filtered = df

selected_city = st.sidebar.multiselect(
    "Stadt wählen", 
    options=sorted(df_rl_filtered['Stadt'].unique()), 
    default=sorted(df_rl_filtered['Stadt'].unique())
)

filtered_df = df_rl_filtered[df_rl_filtered['Stadt'].isin(selected_city)]

# --- HAUPTBEREICH ---
if not filtered_df.empty:
    # Wir suchen uns den aktuellsten Monat für die Info-Kästchen oben
    monate = filtered_df['Monat'].unique()
    aktueller_monat = monate[-1] 
    df_aktuell = filtered_df[filtered_df['Monat'] == aktueller_monat]

    st.markdown(f"### Aktueller Stand: **{aktueller_monat}**")

    # --- KPI ROW ---
    kpi1, kpi2, kpi3 = st.columns(3)
    avg_rating = df_aktuell['Rating'].mean()
    if pd.isna(avg_rating): avg_rating = 0.0

    kpi1.metric("Durchschnitts-Rating", f"{avg_rating:.2f} ⭐", delta=None)
    kpi2.metric("Gesamt-Rezensionen", f"{df_aktuell['TotalReviews'].sum():,}", delta=None)
    kpi3.metric("Neue Rezensionen (Monat)", f"+{df_aktuell['NewReviews'].sum()}", delta="Zuwachs")

    st.divider()

    # --- CHARTS ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Entwicklung (Neue Bewertungen)")
        # Liniendiagramm für die Historie über die Monate
        trend_df = filtered_df.groupby('Monat', sort=False)['NewReviews'].sum().reset_index()
        fig_trend = px.line(trend_df, x='Monat', y='NewReviews', markers=True)
        fig_trend.update_traces(line_color='#FF4B4B', line_width=4, marker_size=12)
        st.plotly_chart(fig_trend, use_container_width=True)

    with col2:
        st.subheader("🏆 Top 10 Studios nach Rating")
        top_studios = df_aktuell.sort_values('Rating', ascending=False).head(10)
        fig_rating = px.bar(top_studios, x='Studiokürzel', y='Rating', color='Rating',
                            color_continuous_scale='RdYlGn', range_y=[3.5, 5.0])
        st.plotly_chart(fig_rating, use_container_width=True)

    # --- CRITICAL LIST ---
    st.subheader("🚨 Handlungsbedarf (Studios < 4.2 Sterne)")
    critical_df = df_aktuell[df_aktuell['Rating'] < 4.2].sort_values('Rating')
    if not critical_df.empty:
        st.dataframe(critical_df[['Studiokürzel', 'Regionalleitung', 'Stadt', 'Rating', 'TotalReviews', 'NewReviews']], use_container_width=True)
    else:
        st.success("Keine kritischen Studios im gewählten Filter!")

    # --- DATA TABLE ---
    with st.expander("Gesamte Datenliste (inklusive Historie) anzeigen"):
        st.dataframe(filtered_df, use_container_width=True)

else:
    st.info("Bitte wähle eine Stadt oder Regionalleitung aus.")
