import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Senzera Google-Bewertungen Dashboard", layout="wide")

# --- SENZERA BRANDING FARBEN ---
SENZERA_PINK = '#D81B60'
SENZERA_BLUE = '#1f77b4'

def load_data():
    df = pd.read_csv('Senzera_Dashboard_Data.csv')
    if 'Monat' not in df.columns:
        df['Monat'] = 'März 2026'
    if 'Studio_Display' not in df.columns:
        df['Studio_Display'] = df['Studiokürzel'] + " - " + df['Strasse + HNr']
    if 'NewRating' not in df.columns:
        df['NewRating'] = df['Rating']
    return df

try:
    df = load_data()
except Exception as e:
    st.error("Datei 'Senzera_Dashboard_Data.csv' nicht gefunden. Bitte lade die Daten hoch.")
    st.stop()

st.title("📊 Senzera Vertriebssteuerung")
st.markdown("**Google-Bewertungen: Monitoring & Entwicklung in Deutschland und Österreich**")

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

    # --- KPI ROW (4 SPALTEN) ---
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    avg_rating = df_aktuell['Rating'].mean()
    if pd.isna(avg_rating): avg_rating = 0.0

    kpi1.metric("Ø-Rating Gesamt", f"{avg_rating:.2f} ⭐")
    kpi2.metric("Gesamt-Rezensionen", f"{df_aktuell['TotalReviews'].sum():,}")
    kpi3.metric("Neue Rezensionen", f"+{df_aktuell['NewReviews'].sum()}")
    
    if df_aktuell['NewReviews'].sum() > 0:
        weighted_new_rating = np.average(df_aktuell['NewRating'], weights=df_aktuell['NewReviews'])
    else:
        weighted_new_rating = 0.0
        
    kpi4.metric("Ø-Rating der Neuen", f"{weighted_new_rating:.2f} ⭐", delta="Diesen Monat")

    st.write("") 

    # --- 🚨 DER ALARM-BEREICH ---
    critical_df = df_aktuell[df_aktuell['Rating'] < 4.2].sort_values('Rating')
    if not critical_df.empty:
        st.error("🚨 **ALARM: Handlungsbedarf!** Folgende Studios sind im aktuellen Monat unter 4,2 Sterne gerutscht:")
        st.dataframe(critical_df[['Studiokürzel', 'Regionalleitung', 'Stadt', 'Rating', 'TotalReviews', 'NewReviews']], use_container_width=True)
        
        with st.expander("💡 Action-Plan: So holen wir die Sterne zurück!"):
            st.markdown("""
            **1. 🛒 Material sichern (Monatsbestellung)** Bitte denkt daran, über die nächste Monatsbestellung sofort frische **Google-Bewertungskarten** für das betroffene Studio zu ordern.
            **2. 📢 Team-Sensibilisierung** Macht das gesamte Team im Studio auf die aktuelle Bewertungssituation aufmerksam.
            **3. ✨ Der perfekte Moment** Erinnert alle Mitarbeiterinnen daran, die Karten **aktiv** nach der Behandlung mitzugeben.
            """)
    else:
        st.success("✅ **Alles im grünen Bereich:** Keine kritischen Studios (unter 4,2 Sterne) im gewählten Filter!")

    st.divider()

    # --- GEWINNER DES MONATS ---
    st.subheader("🚀 Gewinner des Monats (Meiste neue Bewertungen)")
    gewinner_df = df_aktuell[df_aktuell['NewReviews'] > 0].sort_values('NewReviews', ascending=False).head(5)
    
    if not gewinner_df.empty:
        fig_gewinner = px.bar(gewinner_df, x='NewReviews', y='Studiokürzel', orientation='h', 
                              color='NewReviews', color_continuous_scale='Reds',
                              title=f"Top 5 Zuwächse in {aktueller_monat}")
        fig_gewinner.update_layout(yaxis={'categoryorder':'total ascending'}) 
        st.plotly_chart(fig_gewinner, use_container_width=True)
    else:
        st.info("In diesem Monat gibt es in der aktuellen Filterung noch keine neuen Bewertungen.")

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
            fig_trend_reviews.update_traces(line_color=SENZERA_PINK, line_width=4, marker_size=12)
            st.plotly_chart(fig_trend_reviews, use_container_width=True)
        with tab2:
            fig_trend_rating = px.line(trend_df, x='Monat', y='Rating', markers=True)
            fig_trend_rating.update_traces(line_color=SENZERA_BLUE, line_width=4, marker_size=12)
            fig_trend_rating.update_layout(yaxis_range=[3.5, 5.0])
            st.plotly_chart(fig_trend_rating, use_container_width=True)

    st.divider()

    # --- NEU: AUTOMATISCHER BERICHT & EXPORT ---
    st.subheader("📝 Automatischer Monatsbericht & Export")
    
    # Text-Generator für den Bericht
    team_name = f"Region {selected_rl}" if selected_rl != "Alle" else "Senzera-Team"
    
    bericht_text = f"Hallo liebes {team_name},\n\nhier ist unser kurzes Google-Bewertungs-Update für den Monat {aktueller_monat}!\n\n"
    bericht_text += f"📊 UNSERE ZAHLEN IM ÜBERBLICK:\n"
    bericht_text += f"- Durchschnittliche Bewertung: {avg_rating:.2f} Sterne\n"
    bericht_text += f"- Neue Bewertungen in diesem Monat: +{df_aktuell['NewReviews'].sum()}\n"
    bericht_text += f"- Schnitt der NEUEN Bewertungen: {weighted_new_rating:.2f} Sterne\n\n"
    
    if not gewinner_df.empty:
        bericht_text += "🚀 UNSERE TOP-PERFORMER (Meiste neue Bewertungen):\n"
        for _, row in gewinner_df.iterrows():
            bericht_text += f"  • {row['Stadt']} ({row['Studiokürzel']}): +{row['NewReviews']} neue Bewertungen\n"
        bericht_text += "Klasse Arbeit, weiter so!\n\n"
        
    if not critical_df.empty:
        bericht_text += "🚨 WICHTIG: HANDLUNGSBEDARF\n"
        bericht_text += "Folgende Studios liegen aktuell leider unter 4,2 Sternen. Bitte denkt an die Bewertungskarten und sprecht das Thema im Team an:\n"
        for _, row in critical_df.iterrows():
            bericht_text += f"  • {row['Stadt']} ({row['Studiokürzel']}): {row['Rating']} Sterne\n"
        bericht_text += "\n"
        
    bericht_text += "Vielen Dank für euren tollen Einsatz! Lasst uns im nächsten Monat noch mehr Sterne sammeln!\n"

    # Ansicht und Download im Dashboard
    col_text, col_export = st.columns([2, 1])
    
    with col_text:
        st.markdown("**E-Mail Vorlage (wird automatisch aus deinen Filtern generiert):**")
        st.text_area("Kopiere diesen Text einfach heraus:", value=bericht_text, height=300)
        
    with col_export:
        st.markdown("**Bericht herunterladen:**")
        st.download_button(
            label="📄 Bericht als Text-Datei laden",
            data=bericht_text,
            file_name=f'Monatsbericht_{aktueller_monat}_{selected_rl}.txt',
            mime='text/plain',
            use_container_width=True
        )
        
        st.write("")
        st.markdown("**Zahlen herunterladen:**")
        ansicht_df = filtered_df.drop(columns=['Studio_Display'])
        csv_export = ansicht_df.to_csv(index=False, sep=';').encode('utf-8-sig')
        st.download_button(
            label="📥 Tabelle als CSV für Excel laden",
            data=csv_export,
            file_name=f'Senzera_Bewertungen_{aktueller_monat}.csv',
            mime='text/csv',
            use_container_width=True
        )

else:
    st.info("Bitte wähle mindestens ein Studio aus.")
