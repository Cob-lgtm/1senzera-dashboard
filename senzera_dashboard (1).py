import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Senzera Google-Bewertungen Dashboard", layout="wide")

def load_data():
    df = pd.read_csv('Senzera_Dashboard_Data.csv')
    if 'Monat' not in df.columns:
        df['Monat'] = 'März 2026'
    if 'Studio_Display' not in df.columns:
        df['Studio_Display'] = df['Studiokürzel'] + " - " + df['Strasse + HNr']
    # Falls die neue Spalte bei alten Daten fehlt, füllen wir sie mit dem normalen Rating auf
    if 'NewRating' not in df.columns:
        df['NewRating'] = df['Rating']
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
    df_rl = df[df['Regionalleitung'] == selected_rl]
else:
    df_rl = df

city_options = sorted(df_rl['Stadt'].unique())
selected_city = st.sidebar.multiselect("Stadt wählen", options=city_options, default=city_options)
df_city = df_rl[df_rl['Stadt'].isin(selected_city)]

studio_options = sorted(df_city['Studio_Display'].unique())
selected_studios = st.sidebar.multiselect("Studio wählen", options=studio_options, default=studio_options)
filtered_df = df_city[df_city['Studio_Display'].isin(selected_studios)]

# --- HAUPTBEREICH ---
if not filtered_df.empty:
    monate = filtered_df['Monat'].unique()
    aktueller_monat = monate[-1] 
    df_aktuell = filtered_df[filtered_df['Monat'] == aktueller_monat]

    st.markdown(f"### Aktueller Stand: **{aktueller_monat}**")

    # --- KPI ROW (JETZT 4 SPALTEN!) ---
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    avg_rating = df_aktuell['Rating'].mean()
    if pd.isna(avg_rating): avg_rating = 0.0

    kpi1.metric("Ø-Rating Gesamt", f"{avg_rating:.2f} ⭐")
    kpi2.metric("Gesamt-Rezensionen", f"{df_aktuell['TotalReviews'].sum():,}")
    kpi3.metric("Neue Rezensionen", f"+{df_aktuell['NewReviews'].sum()}")
    
    # Berechnung des Durchschnitts der neuen Sterne (Gewichtet)
    if df_aktuell['NewReviews'].sum() > 0:
        weighted_new_rating = np.average(df_aktuell['NewRating'], weights=df_aktuell['NewReviews'])
    else:
        weighted_new_rating = 0.0
        
    kpi4.metric("Ø-Rating der Neuen", f"{weighted_new_rating:.2f} ⭐", delta="Diesen Monat")

    st.divider()

    # --- CHARTS ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏆 Top 10 Studios nach Rating")
        top_studios = df_aktuell.sort_values('Rating', ascending=False).head(10)
        fig_rating = px.bar(top_studios, x='Studiokürzel', y='Rating', color='Rating',
                            color_continuous_scale='RdYlGn', range_y=[3.5, 5.0])
        st.plotly_chart(fig_rating, use_container_width=True)

    with col2:
        st.subheader("📈 Entwicklung über die Monate")
        trend_df = filtered_df.groupby('Monat', sort=False).agg(
            NewReviews=('NewReviews', 'sum'),
            Rating=('Rating', 'mean')
        ).reset_index()

        tab1, tab2 = st.tabs(["Anzahl neue Bewertungen", "Ø-Sterne Gesamt"])
        with tab1:
            fig_trend_reviews = px.line(trend_df, x='Monat', y='NewReviews', markers=True)
            fig_trend_reviews.update_traces(line_color='#FF4B4B', line_width=4, marker_size=12)
            st.plotly_chart(fig_trend_reviews, use_container_width=True)
        with tab2:
            fig_trend_rating = px.line(trend_df, x='Monat', y='Rating', markers=True)
            fig_trend_rating.update_traces(line_color='#1f77b4', line_width=4, marker_size=12)
            fig_trend_rating.update_layout(yaxis_range=[3.5, 5.0])
            st.plotly_chart(fig_trend_rating, use_container_width=True)

    # --- DATA TABLE ---
    with st.expander("Gesamte Datenliste (inkl. Ø-Sterne der Neuen) anzeigen"):
        ansicht_df = filtered_df.drop(columns=['Studio_Display'])
        st.dataframe(ansicht_df, use_container_width=True)

else:
    st.info("Bitte wähle mindestens ein Studio aus.")
