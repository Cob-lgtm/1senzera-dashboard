
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Senzera Performance Dashboard", layout="wide")

# --- FARBEN ---
SENZERA_PINK = '#D81B60'
SENZERA_BLUE = '#1f77b4'
ZENLOOP_GREEN = '#00BFA5'
ZENLOOP_RED = '#FF5252'
ZENLOOP_YELLOW = '#FFC107'

# --- DATEN LADEN ---
@st.cache_data
def load_google_data():
    df = pd.read_csv('Senzera_Dashboard_Data.csv')
    if 'Monat' not in df.columns:
        df['Monat'] = 'März 2026'
    if 'Studio_Display' not in df.columns:
        df['Studio_Display'] = df['Studiokürzel'] + " - " + df['Strasse + HNr']
    if 'NewRating' not in df.columns:
        df['NewRating'] = df['Rating']
    if 'NPS' not in df.columns:
        df['NPS'] = 0 
    return df

@st.cache_data
def load_zenloop_data():
    try:
        df = pd.read_csv('Zenloop_Antworten.csv')
        return df
    except Exception:
        return pd.DataFrame() # Leeres DataFrame, falls Datei fehlt

try:
    df = load_google_data()
except Exception as e:
    st.error("Datei 'Senzera_Dashboard_Data.csv' nicht gefunden. Bitte lade die Daten hoch.")
    st.stop()

df_nps = load_zenloop_data()

st.title("📊 Senzera Vertriebssteuerung")
st.markdown("**Performance Dashboard: Google-Bewertungen & Zenloop Kundenstimmen**")

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

# Die Kürzel der ausgewählten Studios (für den Zenloop Filter)
selected_kuerzel = filtered_df['Studiokürzel'].unique()

# --- HAUPTBEREICH (TABS) ---
if not filtered_df.empty:
    monate = filtered_df['Monat'].unique()
    aktueller_monat = monate[-1] 
    df_aktuell = filtered_df[filtered_df['Monat'] == aktueller_monat]

    # Wir filtern die Zenloop Daten passend zu den ausgewählten Studios
    if not df_nps.empty:
        df_nps_aktuell = df_nps[df_nps['Property - studio'].isin(selected_kuerzel)]
    else:
        df_nps_aktuell = pd.DataFrame()

    # --- DIE BEIDEN HAUPT-TABS ---
    tab_google, tab_zenloop = st.tabs(["🌟 GOOGLE BEWERTUNGEN", "💙 ZENLOOP NPS & FEEDBACK"])

    # ==========================================
    # TAB 1: GOOGLE BEWERTUNGEN
    # ==========================================
    with tab_google:
        st.markdown(f"### Aktueller Google-Stand: **{aktueller_monat}**")

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
        kpi4.metric("Ø-Rating der Neuen", f"{weighted_new_rating:.2f} ⭐")

        st.write("") 

        # 🚨 ALARM-BEREICH
        critical_df = df_aktuell[df_aktuell['Rating'] < 4.2].sort_values('Rating')
        if not critical_df.empty:
            st.error("🚨 **ALARM: Handlungsbedarf!** Folgende Studios sind im aktuellen Monat unter 4,2 Sterne gerutscht:")
            st.dataframe(critical_df[['Studiokürzel', 'Stadt', 'Rating', 'TotalReviews', 'NewReviews']], use_container_width=True)
            
            with st.expander("💡 Action-Plan: So holen wir die Sterne zurück!"):
                st.markdown("""
                **1. 🛒 Material sichern:** Frische Google-Bewertungskarten ordern.
                **2. 📢 Team-Sensibilisierung:** Das gesamte Team auf die Situation hinweisen.
                **3. ✨ Der perfekte Moment:** Karten aktiv nach der Behandlung mitgeben.
                """)
        else:
            st.success("✅ **Alles im grünen Bereich:** Keine kritischen Google-Studios im gewählten Filter!")

        st.divider()

        # GEWINNER DES MONATS
        st.subheader("🚀 Gewinner des Monats (Meiste neue Bewertungen)")
        gewinner_df = df_aktuell[df_aktuell['NewReviews'] > 0].sort_values('NewReviews', ascending=False).head(5)
        
        if not gewinner_df.empty:
            fig_gewinner = px.bar(gewinner_df, x='NewReviews', y='Studiokürzel', orientation='h', 
                                  color='NewReviews', color_continuous_scale='Reds')
            fig_gewinner.update_layout(yaxis={'categoryorder':'total ascending'}) 
            st.plotly_chart(fig_gewinner, use_container_width=True)
        else:
            st.info("In diesem Monat gibt es noch keine neuen Bewertungen.")

        st.divider()

        # CHARTS
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

            tab_trend1, tab_trend2 = st.tabs(["Neue Bewertungen", "Ø-Sterne"])
            with tab_trend1:
                fig_tr = px.line(trend_df, x='Monat', y='NewReviews', markers=True)
                fig_tr.update_traces(line_color=SENZERA_PINK, line_width=4, marker_size=12)
                st.plotly_chart(fig_tr, use_container_width=True)
            with tab_trend2:
                fig_ta = px.line(trend_df, x='Monat', y='Rating', markers=True)
                fig_ta.update_traces(line_color=SENZERA_BLUE, line_width=4, marker_size=12)
                fig_ta.update_layout(yaxis_range=[3.5, 5.0])
                st.plotly_chart(fig_ta, use_container_width=True)


    # ==========================================
    # TAB 2: ZENLOOP NPS & FEEDBACK
    # ==========================================
    with tab_zenloop:
        if df_nps_aktuell.empty:
            st.warning("⚠️ Keine Zenloop-Daten gefunden. Bitte lade die 'Zenloop_Antworten.csv' hoch.")
        else:
            st.markdown(f"### Zenloop Insights für deine Auswahl")
            
            # --- NPS BERECHNUNG ---
            total_answers = len(df_nps_aktuell)
            promoters = len(df_nps_aktuell[df_nps_aktuell['score_type'] == 'promoter'])
            detractors = len(df_nps_aktuell[df_nps_aktuell['score_type'] == 'detractor'])
            passives = len(df_nps_aktuell[df_nps_aktuell['score_type'] == 'passive'])
            
            if total_answers > 0:
                calc_nps = ((promoters - detractors) / total_answers) * 100
            else:
                calc_nps = 0.0

            # --- KPI ROW ZENLOOP ---
            z_kpi1, z_kpi2, z_kpi3, z_kpi4 = st.columns(4)
            z_kpi1.metric("💙 Ø-NPS Score", f"{calc_nps:.0f}")
            z_kpi2.metric("📝 Anzahl Antworten", f"{total_answers}")
            z_kpi3.metric("🟢 Promotoren (Fans)", f"{promoters}")
            z_kpi4.metric("🔴 Detraktoren (Kritiker)", f"{detractors}")

            st.divider()

            # --- CHARTS ZENLOOP ---
            z_col1, z_col2 = st.columns(2)
            
            with z_col1:
                st.subheader("📊 Kunden-Verteilung")
                pie_data = pd.DataFrame({
                    'Typ': ['Promotoren (9-10)', 'Passive (7-8)', 'Detraktoren (0-6)'],
                    'Anzahl': [promoters, passives, detractors]
                })
                fig_pie = px.pie(pie_data, values='Anzahl', names='Typ', hole=0.4, 
                                 color='Typ', color_discrete_map={
                                     'Promotoren (9-10)': ZENLOOP_GREEN,
                                     'Passive (7-8)': ZENLOOP_YELLOW,
                                     'Detraktoren (0-6)': ZENLOOP_RED
                                 })
                st.plotly_chart(fig_pie, use_container_width=True)

            with z_col2:
                st.subheader("🏆 Top NPS pro Studio")
                # NPS pro Studio berechnen
                studio_nps_list = []
                for s in df_nps_aktuell['Property - studio'].unique():
                    s_data = df_nps_aktuell[df_nps_aktuell['Property - studio'] == s]
                    s_tot = len(s_data)
                    s_pro = len(s_data[s_data['score_type'] == 'promoter'])
                    s_det = len(s_data[s_data['score_type'] == 'detractor'])
                    if s_tot > 0:
                        s_nps = ((s_pro - s_det) / s_tot) * 100
                        studio_nps_list.append({'Studio': s, 'NPS': s_nps, 'Antworten': s_tot})
                
                df_studio_nps = pd.DataFrame(studio_nps_list).sort_values('NPS', ascending=False).head(10)
                if not df_studio_nps.empty:
                    fig_snps = px.bar(df_studio_nps, x='Studio', y='NPS', color='NPS', color_continuous_scale='Teal')
                    st.plotly_chart(fig_snps, use_container_width=True)

            st.divider()

            # --- KUNDENSTIMMEN TABELLE ---
            st.subheader("💬 Echte Kundenstimmen & Kommentare")
            # Nur Antworten mit Kommentar filtern
            df_comments = df_nps_aktuell.dropna(subset=['comment'])
            if not df_comments.empty:
                df_comments_display = df_comments[['Property - studio', 'score', 'score_type', 'sentiment', 'comment']].copy()
                df_comments_display.rename(columns={
                    'Property - studio': 'Studio',
                    'score': 'Punkte',
                    'score_type': 'Kunden-Typ',
                    'sentiment': 'Stimmung',
                    'comment': 'Kommentar'
                }, inplace=True)
                st.dataframe(df_comments_display.sort_values('Punkte'), use_container_width=True)
            else:
                st.info("Aktuell liegen für diese Auswahl keine schriftlichen Kommentare vor.")


    # ==========================================
    # GEMEINSAMER BEREICH (EXPORT & BERICHT)
    # ==========================================
    st.divider()
    st.subheader("📝 Automatischer Monatsbericht (Google & NPS)")
    
    team_name = f"Region {selected_rl}" if selected_rl != "Alle" else "Senzera-Team"
    bericht_text = f"Hallo liebes {team_name},\n\nhier ist unser aktuelles Performance-Update (Google & Zenloop) für den Monat {aktueller_monat}.\n\n"
    
    bericht_text += f"📊 UNSERE ZAHLEN IM ÜBERBLICK:\n"
    bericht_text += f"• Durchschnittliche Google-Bewertung: {avg_rating:.2f} Sterne\n"
    bericht_text += f"• Neue Google-Bewertungen: +{df_aktuell['NewReviews'].sum()}\n"
    if not df_nps_aktuell.empty:
        bericht_text += f"• Unser Zenloop NPS: {calc_nps:.0f} (aus {total_answers} Antworten)\n"
    bericht_text += "\n🏢 STATUS DER EINZELNEN STUDIOS:\n\n"
    
    for _, row in df_aktuell.sort_values(by=['Stadt', 'Studiokürzel']).iterrows():
        # NPS für dieses Studio finden
        s_nps_val = df_studio_nps[df_studio_nps['Studio'] == row['Studiokürzel']]['NPS'].values if not df_nps_aktuell.empty else []
        nps_str = f"| NPS: {int(s_nps_val[0])}" if len(s_nps_val) > 0 else ""

        bericht_text += f"📍 {row['Stadt']} ({row['Studiokürzel']}) – Google: {row['Rating']} ⭐ {nps_str}\n"
        
        if row['Rating'] < 4.2:
            bericht_text += "   🚨 Google unter 4,2: Bitte bestellt dringend neue Google-Bewertungskarten, sensibilisiert das Team und gebt die Karten aktiv nach jeder Behandlung mit!\n\n"
        elif 4.2 <= row['Rating'] <= 4.7:
            bericht_text += "   💡 Guter Weg! Bitte pusht die Google-Bewertungen weiter und gebt fleißig die Bewertungskarten mit.\n\n"
        else:
            bericht_text += "   🌟 Hervorragend auf Google! Absolute Spitzenklasse. Macht weiter genau so!\n\n"

    bericht_text += "Vielen Dank für euren tollen Einsatz! Lasst uns weiterhin gemeinsam für großartige Bewertungen und zufriedene Kundinnen sorgen.\n"

    st.text_area("Diesen Text kannst du einfach in eine E-Mail kopieren:", value=bericht_text, height=350)
    
    st.divider()

    st.subheader("📋 Gesamte Google-Datenliste & Export")
    ansicht_df = filtered_df.drop(columns=['Studio_Display'])
    st.dataframe(ansicht_df, use_container_width=True)
    
    csv_export = ansicht_df.to_csv(index=False, sep=';').encode('utf-8-sig')
    st.download_button("📥 Tabelle als CSV für Excel laden", data=csv_export, file_name=f'Senzera_Bewertungen_{aktueller_monat}.csv', mime='text/csv')

else:
    st.info("Bitte wähle mindestens ein Studio aus.")
