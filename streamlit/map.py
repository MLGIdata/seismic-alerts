import streamlit as st 
import pandas as pd 
import pydeck as pdk
import mysql.connector
import numpy as np
import pickle
from sklearn.preprocessing import StandardScaler

st.set_page_config(
    page_title="Mapa de sismos - US, JP, MX",
    page_icon="🌎",
    layout="wide"
)

# Conexión a MySQL en RDS
# Inicializamos la conexión
def init_connection():
    return mysql.connector.connect(**st.secrets["mysql"])

conn = init_connection()

# Query
# Solo corre cuando el query cambia o luego de 10 min
@st.experimental_memo(ttl=600)
def run_query(query):
    with conn.cursor(buffered=True) as cur:
        cur.execute(query)
        col_names = [i[0] for i in cur.description]
        return cur.fetchall(), col_names

query = '''SELECT seism.date, seism.depth, seism.magnitude, seism.latitude, seism.longitude, seism.geoReference, location.country, density.density
            FROM seism
            LEFT JOIN location ON location.idLocation = seism.idLocation
            LEFT JOIN density ON density.idLocation = seism.idLocation'''

rows, col_names = run_query(query)

# Lo transformamos en un dataframe
df = pd.DataFrame(rows, columns=col_names)

df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(by=['date'])

df = df.tail(10000)

# Calculamos la peligrosidad
scaler = StandardScaler()
df['ratio'] = df.depth/df.magnitude
df['ratioT'] = scaler.fit_transform(df.ratio.to_numpy().reshape(-1,1))

# Colocamos una etiqueta de acuerdo a la densidad
df.loc[df.density < 300,'densityLabel'] = 0
df.loc[(df.density < 1500) & (df.density > 300),'densityLabel'] = 1
df.loc[df.density > 1500,'densityLabel'] = 2

with open("streamlit/data/model.pkl", "rb") as f:
    model = pickle.load(f)

# Realizamos la predicción
df['cluster'] = model.predict(df[['ratioT', 'densityLabel']])

# Agregamos colores
df.loc[df.cluster == 0,'r'], df.loc[df.cluster == 0,'g'], df.loc[df.cluster == 0,'b'], df.loc[df.cluster == 0,'a']= [200, 30, 0, 160]
df.loc[df.cluster == 1,'r'], df.loc[df.cluster == 1,'g'], df.loc[df.cluster == 1,'b'], df.loc[df.cluster == 1,'a']= [255, 205, 0, 120]
df.loc[df.cluster == 2,'r'], df.loc[df.cluster == 2,'g'], df.loc[df.cluster == 2,'b'], df.loc[df.cluster == 2,'a']= [251, 134, 1, 130]
df.loc[df.cluster == 3,'r'], df.loc[df.cluster == 3,'g'], df.loc[df.cluster == 3,'b'], df.loc[df.cluster == 3,'a']= [133, 223, 104, 130]

with st.container():

    empty1, note, empty2, legend = st.columns([0.1,4,0.1,1.5])
    
    with empty1:
            st.empty()
    with note:
        st.title('Seism map')
        st.markdown('''In the map below we can find the last 1000 seisms in each country. To read the map correctly note that:
- The size of the points are related to the magnitude of the seism.
- The color of the points are given by the threat level considered by the machine learning model
- The seism with bars are the last ones in the database and have the information of the magnitude and depth in Km.''')
    with empty2:
            st.empty()
    with legend:
        st.markdown('# ')
        st.markdown('### Threat level')
        st.image('streamlit/figures/threat.png', width=170)
    

with st.container():
    option = st.selectbox(
    'Select a country',
    ('Mexico', 'Japan', 'United States'), )

    if option == 'United States':
        lat = 44.427963
        lon = -110.5884550
        data = df[df.country == 'US'].tail(1000)
        zoom = 3

    if option == 'Japan':
        lat = 36.304331
        lon = 138.580069
        data = df[df.country == 'JP'].tail(1000)
        zoom = 4

    if option == 'Mexico':
        lat = 21.412286
        lon = -100.165831
        data = df[df.country == 'MX'].tail(1000)
        zoom = 4

    data['elevation'] = np.exp(data['magnitude'])
    data['radius'] = (np.exp(df['magnitude']/1.01-1.5))*1000

    col_layer = pdk.Layer(
            "ColumnLayer",
            data = data.tail(10),
            get_position=['longitude', 'latitude'],
            get_elevation='elevation',
            auto_highlight=False,
            elevation_scale=3000,
            pickable=True,
            elevation_range=[0, 30000],
            get_fill_color=['r','g','b','a'],
            radius = 25000,
            coverage=1,
            )

    scatter_layer = pdk.Layer(
                'ScatterplotLayer',
                data=data.drop(data.tail(10).index),
                get_position='[longitude, latitude]',
                get_fill_color=['r','g','b','a'],
                get_line_color=[0, 0, 0],
                get_radius= 'radius',
                ) 

    view_state = pdk.ViewState(
            latitude=lat,
            longitude=lon,
            zoom=zoom,
            pitch=60,
        )

    st.pydeck_chart(pdk.Deck(
        map_style=None,
        initial_view_state=view_state,
        layers=[col_layer, scatter_layer],
        tooltip={"text": "{geoReference}\nMagnitude: {magnitude}\nDepth: {depth}"}
        )
    )
