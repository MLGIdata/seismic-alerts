# Importando las librerias
import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import seaborn as sns
from sqlalchemy import create_engine,text    # conexion a sql
import pickle

CLAVE = 'mysql123'
DB = 'seismicdata'
my_conn = create_engine("mysql://admin:{clave}@seismic-mysqldatabase.clzvii6srvy5.us-west-2.rds.amazonaws.com:3306/{db}".format(clave=CLAVE,db=DB), pool_recycle=60*5, pool_pre_ping=True)
conn = my_conn.connect()

# Importamos el dataset
query = '''SELECT seism.*, density.density
            FROM seism
            LEFT JOIN density ON density.idLocation=seism.idLocation;'''
X = pd.read_sql(query,my_conn)
X.head()

# Creando nuevo dataframe
X = X[['magnitude','depth','density']].copy()
X.head()

# Calculamos y escalamos la variable a utilizar
scaler = StandardScaler()
X['ratio'] = X.depth/X.magnitude
X['ratioT'] = scaler.fit_transform(X.ratio.to_numpy().reshape(-1,1))

# Colocamos una etiqueta de acuerdo a la densidad
X.loc[X.density < 300,'densityLabel'] = 0
X.loc[(X.density < 1500) & (X.density > 300),'densityLabel'] = 1
X.loc[X.density > 1500,'densityLabel'] = 2

# Entrenamos el modelo
model = KMeans(n_clusters=4, random_state=9)
model.fit(X[['ratioT','densityLabel']])

# Guardamos el modelo entrenado
with open("../streamlit/data/model.pkl", "wb") as f:
    pickle.dump(model, f)