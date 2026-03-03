import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Senzera Dashboard", layout="wide")
st.title("📊 Senzera Google-Bewertungen")

@st.cache_data
def load_data():
    return pd.read_csv('Senzera_Dashboard_Data.csv')

df = load_data()

st.sidebar.header("Filter")

# --- NEUER FILTER: Regionalleitung ---
# Wir holen alle Kürzel (z.B. REK, JOS) aus der Datei
rl_liste = ["Alle"] + sorted(df['Regionalleitung'].dropna().unique().tolist())
auswahl_rl = st.sidebar.selectbox("Regionalleitung", options=rl_liste)

# Filtern nach RL (wenn nicht "Alle" gewählt ist)
if auswahl_rl != "Alle":
    df_rl = df[df['Regionalleitung'] == auswahl_rl]
else:
    df_rl = df

# --- ALTER FILTER: Stadt (passt sich jetzt an die RL an) ---
city = st.sidebar.multiselect("Stadt", options=df_rl['Stadt'].unique(), default=df_rl['Stadt'].unique())
filtered_df = df_rl[df_rl['Stadt'].isin(city)]

# --- KPIs ---
kpi1, kpi2 = st.columns(2)
# Abfangen, falls mal alles weggefiltert wird (verhindert Fehlermeldungen)
if not filtered_df.empty:
    kpi1.metric("Ø-Sterne", round(filtered_df['Rating'].mean(), 2))
    kpi2.metric("Neue Bewertungen", filtered_df['NewReviews'].sum())
    
    # Diagramm
    fig = px.bar(filtered_df.sort_values('Rating'), x='Studiokürzel', y='Rating', color='Rating', range_y=[3,5])
    st.plotly_chart(fig, use_container_width=True)
else:
    kpi1.metric("Ø-Sterne", 0)
    kpi2.metric("Neue Bewertungen", 0)
    st.info("Bitte wähle eine Stadt oder Regionalleitung aus.")

# Tabelle
st.dataframe(filtered_df)
