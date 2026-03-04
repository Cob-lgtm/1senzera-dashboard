import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Senzera Google-Bewertungen Dashboard", layout="wide")

# Daten laden
def load_data():
    df = pd.read_csv('Senzera_Dashboard_Data.csv')
    # Falls die Spalte Monat noch fehlt (für unseren Übergang heute)
    if 'Monat' not in df.columns:
        df['Monat'] = 'März 2026'
        
    # Neue, hübsche Spalte für unseren Studio-Filter basteln
    if 'Studio_Display' not in df.columns:
        df['Studio_Display'] = df['Studiokürzel'] + " - " + df['Strasse + HNr']
        
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

# 1. Filter: Regionalleitung
rl_options = ["Alle"] + sorted(df['Regionalleitung'].dropna().unique().tolist())
selected_rl = st.sidebar.selectbox("Regionalleitung wählen", options=rl_options)

if selected_rl != "Alle":
    df_rl = df[df['Regionalleitung'] == selected_rl]
else:
    df_rl = df

# 2. Filter: Stadt
city_options = sorted(df_rl['Stadt'].unique())
selected_city = st.sidebar.multiselect(
    "Stadt wählen", 
    options=city_options, 
    default=city_options
)
df_city = df_rl[df_rl['Stadt'].isin(selected_city)]

# 3. Filter: Einzelnes Studio (NEU)
studio_options = sorted(df_city['Studio_Display'].unique())
selected_studios = st.sidebar.multiselect(
    "Studio wählen",
    options=studio_options,
    default=studio_options
)

# Finaler Filter wird angewendet
filtered_df = df_city[df_city['Studio_Display'].isin(selected_studios)]


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
        st.subheader("🏆 Top 10 Studios nach Rating")
        top_studios = df_aktuell.sort_values('Rating', ascending=False).head(10)
        fig_rating = px.bar(top_studios, x='Studiokürzel', y='Rating', color='Rating',
                            color_continuous_scale='RdYlGn', range_y=[3.5, 5.0])
        st.plotly_chart(fig_rating, use_container_width=True)

    with col2:
        st.subheader("📈 Entwicklung über die Monate")
        
        # Daten für den zeitlichen Verlauf gruppieren
        trend_df = filtered_df.groupby('Monat', sort=False).agg(
            NewReviews=('NewReviews', 'sum'),
            Rating=('Rating', 'mean')
        ).reset_index()

        tab1, tab2 = st.tabs(["Anzahl neue Bewertungen", "Ø-Sterne"])
        
        with tab1:
            fig_trend_reviews = px.line(trend_df, x='Monat', y='NewReviews', markers=True)
            fig_trend_reviews.update_traces(line_color='#FF4B4B', line_width=4, marker_size=12)
            st.plotly_chart(fig_trend_reviews, use_container_width=True)
            
        with tab2:
            fig_trend_rating = px.line(trend_df, x='Monat', y='Rating', markers=True)
            fig_trend_rating.update_traces(line_color='#1f77b4', line_width=4, marker_size=12)
            fig_trend_rating.update_layout(yaxis_range=[3.5, 5.0])
            st.plotly_chart(fig_trend_rating, use_container_width=True)

    # --- CRITICAL LIST ---
    st.subheader("🚨 Handlungsbedarf (Studios < 4.2 Sterne)")
    critical_df = df_aktuell[df_aktuell['Rating'] < 4.2].sort_values('Rating')
    if not critical_df.empty:
        st.dataframe(critical_df[['Studiokürzel', 'Regionalleitung', 'Stadt', 'Rating', 'TotalReviews', 'NewReviews']], use_container_width=True)
    else:
        st.success("Keine kritischen Studios im gewählten Filter!")

    # --- DATA TABLE ---
    with st.expander("Gesamte Datenliste (inklusive Historie) anzeigen"):
        # Wir blenden die Hilfsspalte 'Studio_Display' für die Ansicht wieder aus, damit es sauber aussieht
        st.dataframe(filtered_df.drop(columns=['Studio_Display']), use_container_width=True)

else:
    st.info("Bitte wähle mindestens ein Studio aus.")
