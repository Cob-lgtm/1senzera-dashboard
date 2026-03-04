import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Senzera Dashboard", layout="wide")
st.title("📊 Senzera Google-Bewertungen Historie")

def load_data():
    df = pd.read_csv('Senzera_Dashboard_Data.csv')
    # Falls die Spalte 'Monat' noch nicht existiert (für den Übergang heute)
    if 'Monat' not in df.columns:
        df['Monat'] = 'März 2026'
    return df

try:
    df = load_data()
except Exception as e:
    st.error("Daten-Datei nicht gefunden.")
    st.stop()

st.sidebar.header("Filter")

# --- RL Filter ---
if 'Regionalleitung' in df.columns:
    rl_liste = ["Alle"] + sorted(df['Regionalleitung'].dropna().unique().tolist())
    auswahl_rl = st.sidebar.selectbox("Regionalleitung", options=rl_liste)
    if auswahl_rl != "Alle":
        df_rl = df[df['Regionalleitung'] == auswahl_rl]
    else:
        df_rl = df
else:
    df_rl = df

# --- Stadt Filter ---
city = st.sidebar.multiselect("Stadt", options=sorted(df_rl['Stadt'].unique()), default=sorted(df_rl['Stadt'].unique()))
filtered_df = df_rl[df_rl['Stadt'].isin(city)]

# --- Das neue Herzstück: Die Auswertung ---
if not filtered_df.empty:
    # Wir filtern die aktuellsten Zahlen für die Info-Kästchen oben
    monate = filtered_df['Monat'].unique()
    aktueller_monat = monate[-1] # Nimmt immer den zuletzt hinzugefügten Monat
    df_aktuell = filtered_df[filtered_df['Monat'] == aktueller_monat]

    st.markdown(f"### Aktueller Stand: **{aktueller_monat}**")

    # KPIs
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Ø-Sterne (Aktuell)", round(df_aktuell['Rating'].mean(), 2))
    kpi2.metric("Gesamt Bewertungen", df_aktuell['TotalReviews'].sum())
    kpi3.metric("Neue Bewertungen im Monat", df_aktuell['NewReviews'].sum())

    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Entwicklung (Neue Bewertungen)")
        # Gruppieren nach Monat für das Liniendiagramm
        trend_df = filtered_df.groupby('Monat', sort=False)['NewReviews'].sum().reset_index()
        fig_trend = px.line(trend_df, x='Monat', y='NewReviews', markers=True)
        fig_trend.update_traces(line_color='#FF4B4B', line_width=4, marker_size=12)
        st.plotly_chart(fig_trend, use_container_width=True)

    with col2:
        st.subheader(f"🏆 Top 10 Zuwächse in {aktueller_monat}")
        top_studios = df_aktuell.sort_values('NewReviews', ascending=False).head(10)
        fig_bar = px.bar(top_studios, x='Studiokürzel', y='NewReviews', color='NewReviews', color_continuous_scale='Viridis')
        st.plotly_chart(fig_bar, use_container_width=True)

    # Tabelle ganz unten
    with st.expander("Gesamte Datenliste einblenden"):
        st.dataframe(filtered_df)

else:
    st.info("Bitte wähle eine Stadt oder Regionalleitung aus.")
