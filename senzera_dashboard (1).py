import streamlit as st
import pandas as pd
import plotly.express as px

# Set Page Config
st.set_page_config(page_title="Senzera Google-Bewertungen Dashboard", layout="wide")

# Load Data
@st.cache_data
def load_data():
    # In a real scenario, this reads the generated CSV
    df = pd.read_csv('Senzera_Dashboard_Data.csv')
    return df

try:
    df = load_data()
except Exception as e:
    st.error("Datei 'Senzera_Dashboard_Data.csv' nicht gefunden. Bitte erstelle die Datenbasis im Terminal.")
    st.stop()

# Title
st.title("📊 Senzera Vertriebssteuerung: Google-Bewertungen")
st.markdown("Monitoring der Studio-Performance in Deutschland & Österreich")

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter-Optionen")

# 1. Filter: Regionalleitung (RL)
if 'Regionalleitung' in df.columns:
    rl_options = ["Alle"] + sorted(df['Regionalleitung'].dropna().unique().tolist())
    selected_rl = st.sidebar.selectbox("Regionalleitung wählen", options=rl_options)
    
    # Daten nach RL filtern
    if selected_rl != "Alle":
        df_rl_filtered = df[df['Regionalleitung'] == selected_rl]
    else:
        df_rl_filtered = df
else:
    df_rl_filtered = df # Fallback, falls die Spalte mal fehlen sollte

# 2. Filter: Stadt (Passt sich automatisch der gewählten RL an)
selected_city = st.sidebar.multiselect(
    "Stadt wählen", 
    options=sorted(df_rl_filtered['Stadt'].unique()), 
    default=sorted(df_rl_filtered['Stadt'].unique())
)

# Finaler Filter wird angewendet
mask = df_rl_filtered['Stadt'].isin(selected_city)
filtered_df = df_rl_filtered[mask]

# --- KPI ROW ---
kpi1, kpi2, kpi3 = st.columns(3)
avg_rating = filtered_df['Rating'].mean()
total_reviews = filtered_df['TotalReviews'].sum()
new_reviews = filtered_df['NewReviews'].sum()

# Verhindern, dass "NaN" (Not a Number) angezeigt wird, wenn alles weggefiltert ist
if pd.isna(avg_rating): avg_rating = 0.0

kpi1.metric("Durchschnitts-Rating", f"{avg_rating:.2f} ⭐", delta=None)
kpi2.metric("Gesamt-Rezensionen", f"{total_reviews:,}", delta=None)
kpi3.metric("Neue Rezensionen (Monat)", f"+{new_reviews}", delta="Aktivität")

# --- CHARTS ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Top 10 Studios nach Rating")
    top_studios = filtered_df.sort_values('Rating', ascending=False).head(10)
    if not top_studios.empty:
        fig_rating = px.bar(top_studios, x='Studiokürzel', y='Rating', color='Rating',
                            color_continuous_scale='RdYlGn', range_y=[3.5, 5.0])
        st.plotly_chart(fig_rating, use_container_width=True)
    else:
        st.info("Keine Daten vorhanden.")

with col2:
    st.subheader("Bewertungs-Volumen vs. Qualität")
    if not filtered_df.empty:
        # Trick: Wenn alle NewReviews = 0 sind, setzen wir eine Dummy-Größe, damit die Blasen sichtbar bleiben
        plot_df = filtered_df.copy()
        if plot_df['NewReviews'].sum() == 0:
            plot_df['BubbleSize'] = 1
            size_col = 'BubbleSize'
        else:
            size_col = 'NewReviews'
            
        fig_scatter = px.scatter(plot_df, x='TotalReviews', y='Rating', size=size_col, 
                                 hover_name='Studiokürzel', color='Rating',
                                 color_continuous_scale='Viridis', title="Blasengröße = Neue Bewertungen")
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("Keine Daten vorhanden.")

# --- CRITICAL LIST ---
st.subheader("🚨 Handlungsbedarf (Studios < 4.2 Sterne)")
critical_df = filtered_df[filtered_df['Rating'] < 4.2].sort_values('Rating')
if not critical_df.empty:
    # Zeigt jetzt auch an, welche RL betroffen ist
    spalten = ['Studiokürzel', 'Regionalleitung', 'Stadt', 'Rating', 'TotalReviews', 'NewReviews'] if 'Regionalleitung' in critical_df.columns else ['Studiokürzel', 'Stadt', 'Rating', 'TotalReviews', 'NewReviews']
    st.dataframe(critical_df[spalten], use_container_width=True)
else:
    st.success("Keine kritischen Studios im gewählten Filter!")

# --- DATA TABLE ---
with st.expander("Gesamte Datenliste anzeigen"):
    st.dataframe(filtered_df, use_container_width=True)
    
