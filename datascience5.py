import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster

# Configuration de la page
st.set_page_config(layout="wide")

# Style CSS personnalisé
st.markdown("""
<style>
.card {
    border-radius: 15px;
    padding: 20px;
    background: white;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    margin-bottom: 20px;
    border: 1px solid #eee;
}
.no-data {
    text-align: center;
    color: #ff4b4b;
    font-size: 18px;
    margin: 20px 0;
}
</style>
""", unsafe_allow_html=True)

# Chargement des données
@st.cache_data
def load_data():
    df = pd.read_csv('/Users/dana/Data Science/dataset_final.csv')
    df_coords = pd.read_csv("/Users/dana/Downloads/australian_flights_with_coords.csv")
    return df, df_coords

df, df_coords = load_data()

# Nettoyage des données
df.dropna(subset=['Month', 'In_Out', 'Airline'], inplace=True)
df['Month'] = pd.to_datetime(df['Month'], format='%b-%y', errors='coerce')
df['Year'] = df['Month'].dt.year
df['Month_num'] = df['Month'].dt.month

# Sidebar
st.sidebar.title("Filtres")
selected_year = st.sidebar.selectbox("Année", sorted(df['Year'].unique()))
selected_airline = st.sidebar.selectbox("Compagnie aérienne", ['Toutes'] + sorted(df['Airline'].unique()))
selected_city = st.sidebar.selectbox("Ville australienne", df_coords['Australian_City'].unique())

# Fonction pour déterminer les saisons
def get_season(month_num):
    if month_num in [12, 1, 2]: return "Été"
    elif month_num in [3, 4, 5]: return "Automne"
    elif month_num in [6, 7, 8]: return "Hiver"
    else: return "Printemps"

# Filtrage des données
df_filtered = df[df['Year'] == selected_year]
df_kpi = df_filtered if selected_airline == 'Toutes' else df_filtered[df_filtered['Airline'] == selected_airline]
filtered_coords = df_coords[df_coords['Australian_City'] == selected_city]

# Calcul des indicateurs
total = df_kpi['All_Flights'].sum()
domestic = df_kpi[df_kpi['In_Out'] == 'I']['All_Flights'].sum()
international = df_kpi[df_kpi['In_Out'] == 'O']['All_Flights'].sum()

# Données saisonnières (toujours 4 saisons même sans données)
season_data = df_kpi.copy()
season_data['Season'] = season_data['Month_num'].apply(get_season)
all_seasons = ["Été", "Automne", "Hiver", "Printemps"]
season_stats = season_data.groupby('Season')['All_Flights'].sum().reindex(all_seasons, fill_value=0)

# Interface principale
st.title('✈️ Tableau de bord des vols australiens')

# Première ligne - Cartes KPI
col1, col2 = st.columns(2)

# Carte 1 - Total des vols
with col1:
    card_content = f"""
    <div class="card">
        <h3>Total vols ({selected_airline})</h3>
        {f'<h1 style="color:#4285F4;text-align:center;">{total:,}</h1>' if total > 0 else '<p class="no-data">🚫 Aucune donnée disponible</p>'}
    </div>
    """
    st.markdown(card_content, unsafe_allow_html=True)

# Carte 2 - Répartition saisonnière
with col2:
    seasons_html = "".join([f"""
    <div style="display:flex;justify-content:space-between;margin:8px 0;">
        <span>{"🌸🌞🍂❄️"[i]} {s}</span>
        <strong>{v:,} vols</strong>
    </div>
    """ for i, (s,v) in enumerate(season_stats.items())])
    
    card_content = f"""
    <div class="card">
        <h3>Répartition saisonnière</h3>
        {seasons_html if season_stats.sum() > 0 else '<p class="no-data">🚫 Aucune donnée disponible</p>'}
    </div>
    """
    st.markdown(card_content, unsafe_allow_html=True)

# Deuxième ligne - Donuts charts
st.subheader("Répartition des vols")

if total > 0:
    col_d1, col_d2 = st.columns(2)
    
    # Donut national
    with col_d1:
        fig = go.Figure(go.Pie(
            labels=['Nationaux'], values=[domestic],
            hole=0.7, marker_colors=['#4285F4'], textinfo='none'
        ))
        fig.update_layout(
            annotations=[dict(
                text=f"<b>{domestic:,}</b><br>({domestic/total*100:.1f}%)",
                x=0.5, y=0.5, font_size=18, showarrow=False
            )],
            height=250, margin=dict(t=0,b=0,l=0,r=0)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Donut international
    with col_d2:
        fig = go.Figure(go.Pie(
            labels=['Internationaux'], values=[international],
            hole=0.7, marker_colors=['#EA4335'], textinfo='none'
        ))
        fig.update_layout(
            annotations=[dict(
                text=f"<b>{international:,}</b><br>({international/total*100:.1f}%)",
                x=0.5, y=0.5, font_size=18, showarrow=False
            )],
            height=250, margin=dict(t=0,b=0,l=0,r=0)
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.markdown('<p class="no-data">🚫 Aucune donnée disponible pour la répartition</p>', unsafe_allow_html=True)

# Troisième ligne - Carte interactive
st.subheader("Carte des vols")

if not filtered_coords.empty:
    m = folium.Map(location=[-25.0, 133.0], zoom_start=4)
    marker_cluster = MarkerCluster().add_to(m)

    # Marqueurs pour les villes internationales
    for _, row in filtered_coords.iterrows():
        folium.Marker(
            location=[row['Lat'], row['Lon']],
            popup=row['International_City'],
            icon=folium.Icon(color='red')
        ).add_to(marker_cluster)
    
    # Marqueur pour la ville australienne sélectionnée
    australian_row = filtered_coords.iloc[0]
    folium.Marker(
        location=[australian_row['AUS_Lat'], australian_row['AUS_Lon']],
        popup=australian_row['Australian_City'],
        icon=folium.Icon(color='blue')
    ).add_to(m)
    
    # Lignes pour les routes aériennes
    for _, row in filtered_coords.iterrows():
        folium.PolyLine(
            locations=[(row['AUS_Lat'], row['AUS_Lon']), (row['Lat'], row['Lon'])],
            color='green',
            weight=2,
            opacity=0.7
        ).add_to(m)
    
    folium_static(m, width=700)
else:
    st.markdown('<p class="no-data">🚫 Aucune donnée disponible pour la carte</p>', unsafe_allow_html=True)

# Top 10 des compagnies aériennes
airline_ranking = df_filtered.groupby("Airline")["All_Flights"].sum().reset_index()
airline_ranking.columns = ['Compagnie aérienne', 'Total des vols']
airline_ranking = airline_ranking.sort_values(by="Total des vols", ascending=False).head(10)

# Top 10 des routes les plus fréquentées
route_ranking = df_filtered.groupby("Route")["All_Flights"].sum().reset_index()
route_ranking.columns = ['Route', 'Total des vols']
route_ranking = route_ranking.sort_values(by="Total des vols", ascending=False).head(10)

# Création des colonnes pour alignement
col1, col2 = st.columns(2, gap="medium")

# Affichage dans Streamlit
with col1:
    st.subheader(f'Top 10 des compagnies aériennes pour {selected_year}')
    st.dataframe(airline_ranking.reset_index(drop=True), use_container_width=True)

with col2:
    st.subheader(f'Top 10 des routes les plus fréquentées pour {selected_year}')
    st.dataframe(route_ranking.reset_index(drop=True), use_container_width=True)
