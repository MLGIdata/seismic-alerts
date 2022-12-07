'''
Este script carga continua de datos sísmicos de México desde USGS. A partir de la última hora de carga
se cargan los datos nuevos hasta el momento en que se corre el script.
Para que funcione se tiene que correr primero US_JP_MX_historic.py
'''

import os.path                                      # manejo de paths
import pandas as pd                                 # manejo de datos
from datetime import datetime, date                 # manejo de fechas
from dateutil.relativedelta import relativedelta    # delta de tiempo
from utils import *                                 # funciones comunes para los scripts

def get_states_mx(df):
    """Obtiene los estados para los datos sísmicos de México obtenidos de USGS
    
    Parameters
    ----------
    df : DataFrame
        DataFrame de eventos sísmicos de USGS formateado con `transform_usgs`
        
    Returns
    ------
    df : DataFrame
        DataFrame con columna de estado
    """
    
    states = pd.read_csv('data/locations.csv')
    df.loc[:, 'state'] = df.apply(lambda row: get_state(row, country='México'), axis=1)
    df.state = df.state.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
    df = df.dropna()
    df = df.merge(states, how='left', on='state')
    df.drop(['country','state'], axis='columns', inplace=True)
    df = df[['date','time','magnitude','depth','longitude','latitude','idLocation','geoReference']]
    
    return df

def load_mx(path, short_name, place='MX'):
    """Carga y tranformación de los datos sísmicos de México
    
    Parameters
    ----------
    df : DataFrame
        DataFrame de eventos sísmicos de USGS formateado con `transform_usgs`
    
    short_name : str
        Nombre de referencia para los archivos generados

    place : str
        String con el lugar a considerar. MX es el default

    Returns
    ------
    df : DataFrame
        DataFrame con columna de estado
    """
    
    # Leemos la útltima fecha de actualización
    txt_date = os.path.join(path,'last_date_{}.txt'.format(short_name))

    with open(txt_date, 'r') as f:
        last_date = f.readlines()[-1].strip()

    # definimos las fechas desde la ultima fecha
    # hasta el momento que se corre el script
    start_time = datetime.strptime(last_date, '%m/%d/%Y %H:%M:%S')
    end_time = datetime.today().replace(microsecond=0)

    # nombre del archivo 
    name = short_name+'.csv' # nombre del archivo
    file = os.path.join(path,name) 

    # Se obtiene el url
    url = usgs_query(start_time, end_time, place=place)

    # Leemos los registros
    df = read_usgs(url)

    # Si no esta vacio
    if not df.empty:

        ### Transformaciones
        df = transform_usgs(df)

        # Obtenemos los estados
        df = get_states_mx(df)
            
        # Guardamos el archivo
        df.to_csv(file, index=False)
        
        # Guardamos el nombre del archivo
        # with open(os.path.join(path,'files_'+short_name+'.txt'), "a") as text_file:
        #     text_file.write(file+'\n')
    
    else:
        df.to_csv(file, index=False)

    # Guardamos la última hora de actualización en el txt
    end_date_str = end_time.strftime("%m/%d/%Y %H:%M:%S")
    with open(txt_date, "a") as text_file:
        text_file.write(end_date_str+'\n')

def main():

    PATH = 'data'
    SHORT_NAME_MX = 'mx_sns'

    load_mx(place='MX', path=PATH, short_name=SHORT_NAME_MX)

if __name__ == "__main__":
    main()