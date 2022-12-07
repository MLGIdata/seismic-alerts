import streamlit as st 
import pandas as pd 
import pydeck as pdk
import numpy as np
from sklearn.preprocessing import StandardScaler
import pickle
import mysql.connector
from datetime import timedelta

st.set_page_config(
    page_title="Alerta sísmica México",
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

query = '''SELECT seism.date, seism.time, seism.depth, seism.magnitude, seism.latitude, seism.longitude, location.state, location.country, density.density
            FROM seism
            LEFT JOIN location ON location.idLocation = seism.idLocation
            LEFT JOIN density ON density.idLocation = seism.idLocation
            WHERE location.country = "MX"'''

rows, col_names = run_query(query)

# Lo transformamos en un dataframe
df = pd.DataFrame(rows, columns=col_names)

# Colocamos una etiqueta de acuerdo a la densidad
df.loc[df.density < 300,'densityLabel'] = 'rural'
df.loc[(df.density < 1500) & (df.density > 300),'densityLabel'] = 'pueblo'
df.loc[df.density > 1500,'densityLabel'] = 'ciudad'

# Colocamos la barra de arriba trasparente
page_bg = """
<style>
[data-testid="stHeader"] {
    background-color: rgba(0, 0, 0, 0);
}
<\style>
"""

st.markdown(page_bg, unsafe_allow_html=True)

# Seleccionamos el ultimo sismo de MX que haya en la base de datos
df['date'] = pd.to_datetime(df['date'])
last_mx = df[df.date == df.date.max()]

# Calculamos y escalamos la variable a utilizar
scaler = StandardScaler()
last_mx['ratio'] = last_mx.depth/last_mx.magnitude
last_mx['ratioT'] = scaler.fit_transform(last_mx.ratio.to_numpy().reshape(-1,1))


# Abrimos el modelo de machine learning entrenado
with open("./data/model.pkl", "rb") as f:
    model = pickle.load(f)

# Realizamos la predicción
last_mx['cluster'] = model.predict(last_mx[['ratioT']])

# Colocamos el label
last_mx.loc[last_mx.cluster == 3, 'peligrosidad'] = 'muy baja'
last_mx.loc[last_mx.cluster == 1, 'peligrosidad'] = 'baja'
last_mx.loc[last_mx.cluster == 2, 'peligrosidad'] = 'media'
last_mx.loc[last_mx.cluster == 0, 'peligrosidad'] = 'alta'

# Obtenemos la etiqueta de peligro
peligro = last_mx.iloc[0]['peligrosidad']

with st.container():
    # Guardamos hora y fecha
    state = str(last_mx.iloc[0]['state'])
    date = str(last_mx.iloc[0]['date'].date())
    # Colocamos la hora local
    last_mx.time = pd.to_datetime(last_mx.time)
    last_mx.time = last_mx.time - timedelta(hours=6)
    time = str(last_mx.iloc[0]['time'].time())

    # El color y los mensajes varian con la peligrosidad
    if peligro == 'muy baja':
        color = '85DF68'
        color_rgba = '[133, 223, 104, 130]'
        message = 'Manten la calma, no hay nada de que preocuparse'
        emoji = '😴'
    elif peligro == 'baja':
        color = 'FFDE59'
        color_rgba = '[255, 205, 0, 120]'
        message = 'Mantente alerta, pueden haber replicas'
        emoji = '👀'
    elif peligro == 'media':
        color = 'F08307'
        color_rgba = '[251, 134, 1, 130]'
        message = 'Sigue las recomendaciones a continuación'
        emoji = '😵'
    elif peligro == 'alta':
        color = 'FF5757'
        color_rgba = '[200, 30, 0, 160]'
        message = 'Sigue las recomendaciones a continuación'
        emoji = '⚠️'
    
    st.image('figures/peligrosidad.png', width=450)
    st.markdown('''<div style="background-color:#{color}; border: 2px solid #{color}; border-radius: 5px; text-align:center; vertical-align: middle;">
    <a><h4>{emoji}</h4><h3>Sismo en {state}</h3><h6><br>Fecha: {date} &nbsp; &nbsp; Hora: {time}</h6></a></div>'''.format(color=color, emoji=emoji, state=state, date=date, time=time), unsafe_allow_html=True)
    if peligro == 'muy baja':
        st.success("{message}".format(message=message))
    elif peligro == 'baja':
        st.warning("{message}".format(message=message))
    else:
        st.error("{message}".format(message=message))

with st.container():

    empty1, alerta, empty2, mapa = st.columns([0.1,2.8,0.2,2.8])

    with empty1:
            st.empty()
    with alerta:
        
        # Las recomendaciones varian con la peligrosidad
        st.markdown('''### Recomendaciones''')

        if peligro == 'muy baja':
            st.image("figures/calm.png")

        elif peligro == 'baja':
            st.image("figures/alert_chill.png")

        else:
            # Cuando los terremotos son de peligrosidad media o
            # alta, las recomendaciones varian con la densidad poblacional
            tipoLocalidad = last_mx.iloc[0]['densityLabel']
            tipoLocalidad = 'rural'

            if tipoLocalidad == 'ciudad':
                option = st.selectbox(
                'Dónde te encuentras?',
                ('Interior (piso 2 o menor)', 'Interior (piso 2 o mayor)', 'Exterior'))

            if tipoLocalidad == 'pueblo':
                option = st.selectbox(
                'Dónde te encuentras?',
                ('Interior', 'Exterior'))

            if tipoLocalidad == 'rural':
                option = st.selectbox(
                'Dónde te encuentras?',
                ('Interior', 'Exterior'))
            
            if option == 'Interior (piso 2 o menor)':
                st.image("figures/alert_lower.png")

            elif option == 'Interior (piso 2 o mayor)':
                st.image("figures/alert_upper.png")

            elif option == 'Interior':
                st.image("figures/alert_lower.png")

            elif option == 'Exterior':
                st.image("figures/alert_exterior.png")

    with empty2:
            st.empty()

    with mapa:
        st.markdown('''### Localidad''')
        radius = (np.exp(last_mx.iloc[0]['magnitude']/1.01-0.13))*1000
        lat = last_mx.iloc[0]['latitude']
        lon = last_mx.iloc[0]['longitude']

        st.pydeck_chart(pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=lat,
            longitude=lon,
            zoom=4,
            min_zoom=3,
            max_zoom=6,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                'ScatterplotLayer',
                data=last_mx,
                get_position='[longitude, latitude]',
                get_color=color_rgba,
                get_radius= radius,
            ),
        ],
    ))