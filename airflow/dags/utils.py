import requests
import os.path                                      # manejo de paths
import pandas as pd                                 # manejo de datos
import numpy as np                                  # manejo de arrays
from datetime import datetime, date                 # manejo de fechas
from dateutil.relativedelta import relativedelta    # delta de tiempo
from geopy.geocoders import Nominatim               # Obtener estado de lat y lon

#### Funciones generales ####

def format_str(df, column):
    """Formatear strings colocando iniciales en mayuscula 
    y eliminando espacios en blanco a izquiera y derecha

    Parameters
    ----------
    df : DataFrame
        Dataframe donde se encuentra la columna a formatear
    column : str
        Nombre de la columna a formatear
    Returns
    ------
    df: DataFrame
        Dataframe con la columna formateada
    """

    return df[column].astype(str).str.strip().str.title()

def format_int(df, column):
    """Formatea columnas numéricas a int

    Parameters
    ----------
    df : DataFrame
        Dataframe donde se encuentra la columna a formatear
    column : str
        Nombre de la columna a formatear
    Returns
    ------
    df: DataFrame
        Dataframe con la columna formateada
    """

    return df[column].astype(int)

def format_float(df, column):
    """Formatea columnas numéricas a float
    
    Parameters
    ----------
    df : DataFrame
        Dataframe donde se encuentra la columna a formatear
    column : str
        Nombre de la columna a formatear
    Returns
    ------
    df: DataFrame
        Dataframe con la columna formateada
    """
    
    return df[column].astype(float)

def format_epoch_time(x):
    """Transforma tiempo Unix en formato fecha y hora
    
    Parameters
    ----------
    x : str
        String con el tiempo en formato Unix
    Returns
    ------
    str
        Fecha en formato datetime
    """
    time = x/1000
    return datetime.fromtimestamp(time)#.strftime('%Y-%m-%d %H:%M:%S.%f')

def get_state(row, country ='United States'):
    """A partir de una fila que posea latitud y longitud, te devuelve el Estado
    si el estado se encuentra en el país escogido
    
    Parameters
    ----------
    row : Series
        Fila de un dataframe
    country : str
        Nombre del país en el idioma oficial
    Returns
    ------
    str
        Estado al que pertenece el lugar si se encuentra en el pais pasado 
        en country
    """
    geolocator = Nominatim(user_agent="seismic")
    try:
        location = geolocator.reverse(str(row.latitude)+','+str(row.longitude))
        if location.raw['address']['country'] == country:
            try:
                return location.raw['address']['state']
            except:
                return location.raw['address']['city']
        else: 
            return None
    except:
        return None

def separate_date_time(row):
    """Separa fecha de tiempo para los datos de IRIS
    
    Parameters
    ----------
    row : Series
        Fila de un dataframe que contenga columna Time, donde se encuentra
        la hora y fecha con formato "fechaThoraZ"
    Returns
    ------
    str
        Fila con la fecha y hora en dos columnas
    """
    part = row.Time.split("T")
    row['date'] = part[0]
    row['time'] = part[1].strip("Z")
    return row

#### Transformaciones ####

#### US ####

def transform_usgs(df):
    """Transforma el cojunto de datos de USGS disminuyendo dimensiones y
    transformando las columnas al tipo de dato correcto
    
    Parameters
    ----------
    df : DataFrame
        DataFrame de eventos sísmicos de USGS
        
    Returns
    ------
    df : DataFrame
        DataFrame formateado con las columnas: time, date, magnitude, depth, 
        latitude, longitude, geoReference
    """
    # Renombramos las columnas
    # Quitamos properties de los nombres de columnas
    lista_names = [palabra.replace('properties.', '') for palabra in df.columns.to_list()]
    new_names = dict(zip(df.columns.to_list(), lista_names))
    # Cambiamos los nombres
    df.rename(new_names, axis='columns', inplace=True)
    
    # Dropeamos columnas que no vamos a usar
    col_drop = ['type', 'id', 'updated', 'tz', 'url', 'detail', 'felt', 'cdi', 'mmi', 'alert', 'status', 
            'tsunami', 'sig', 'net', 'code', 'ids', 'sources', 'types' , 'nst', 'dmin', 'rms', 
            'gap', 'magType', 'type', 'title', 'geometry.type'] 

    df.drop(col_drop, axis='columns', inplace=True)

    # Separamos la columna de coordenadas en longitud, latitud y profundidad
    df.rename({'geometry.coordinates':'coordinates'}, axis='columns', inplace=True)
    df[['longitude','latitude', 'depth']] = pd.DataFrame(df.coordinates.tolist(), index= df.index)

    # Transformamos desde epoch a formato fecha-hora en str
    df.time = df.time.apply(format_epoch_time)
    
    # Obtenemos hora y fecha 
    df['date'] = df.time.dt.date
    df['time_hour'] = df.time.dt.time
    df['time_hour'] = df['time_hour'].apply(lambda x: x.replace(microsecond=0))

    # Eliminamos columnas que no vamos a utilizar
    df.drop(['coordinates', 'time'], axis='columns', inplace=True)

    # Renombramos las columnas
    names = {'mag':'magnitude', 'place':'geoReference', 'time_hour':'time'}
    df.rename(names, axis='columns', inplace=True)

    # Transformamos los tipos de las columnas
    type_str = ['geoReference']
    type_float = ['magnitude', 'longitude', 'latitude', 'depth']
    
    # Formateamos con funciones 
    for columna in type_str:
        df[columna] = format_str(df, columna)

    for columna in type_float:
        df[columna] = format_float(df, columna)

    return df

def get_states_usa(df, place = 'US'):
    """Obtener los estados para los datos de Estados Unidos
    
    Parameters
    ----------
    df : DataFrame
        DataFrame de eventos sísmicos de USGS formateado con `transform_usgs`
    place : str
        String con el lugar a considerar. Las opciones son US para Estados Unidos
        continental, AK para Alaska y HI para Hawaii
        
    Returns
    ------
    df : DataFrame
        DataFrame con columna de estado
    """
    if place == 'US':
        # leemos los estados de USA
        states = pd.read_csv('../datasets/us-states.csv', skiprows=1)

        # Eliminamos registros de otros paises
        other_country = ['Mx', 'Canada']
        df = df[~df.geoReference.str.contains("|".join(other_country), regex=True)]

        # Buscamos el estado que se encuentre en la localizacion y lo extraemos
        pattern = states.State.to_list()
        df.loc[:,'state'] = df["geoReference"].str.extract(f"({'|'.join(pattern)})")

        # Los que no tengan estado, intentamos buscarlo como iniciales
        # en la ultima parte del string
        df.loc[df.state.isna(), 'state'] = df.geoReference.str.split(',').apply(lambda x: x[-1])

        # Las abreviaciones las volvemos mayusculas
        df.loc[df.state.str.strip().str.len() == 2,'state'] = df.state.str.strip().str.upper()
        # Sustituimos las abreviaciones por el nombre de los estados
        df = pd.merge(df, states, left_on=  ['state'], right_on= ['Abbreviation'], how = 'left')
        df.loc[df.state.str.strip().str.len() == 2,'state'] = df.State

        # Eliminamos las columnas que utilizamos previamente
        df.drop(['State', 'Abbreviation'], axis='columns', inplace=True)

        # Sustituimos los valores que se encuentran en state pero no son estados de US
        # por None
        df.loc[~df.state.str.contains("|".join(pattern), regex=True), 'state'] = None

        # Obtenemos los faltantes con geopy
        df.loc[df.state.isna(), 'state'] = df[df.state.isna()].apply(get_state, axis=1)

        # Eliminamos filas de sismos que no se encuentran en ningún estado
        df = df[~df.state.isna()]

    elif place == 'AK':
        df.loc[df.geoReference.str.contains('Alaska|Ak', regex=True),'state'] = 'Alaska'
        df.loc[df.state.isna(), 'state'] = df[df.state.isna()].apply(get_state, axis=1)
        df = df[~df.state.isna()]
    elif place == 'HI':
        df.loc[df.geoReference.str.contains('Hawaii|Hi', regex=True),'state'] = 'Hawaii'
        df.loc[df.state.isna(), 'state'] = df[df.state.isna()].apply(get_state, axis=1)
        df = df[~df.state.isna()]

    # Colocamos el idLocation
    path_locations = os.path.join('../datasets','locations.csv') ############### Poner path del archivo de localidades
    df_state = pd.read_csv(path_locations) 
    df_state = df_state[df_state.country == 'US']

    df = pd.merge(df, df_state, left_on=  ['state'], right_on= ['state'], how = 'left')
    df.drop(['state'], axis=1, inplace=True)

    df = df[['date','time','magnitude','depth','longitude','latitude','idLocation','geoReference']]

    return df

#### JP ####

def transform_jp(df):
    """Transforma el cojunto de datos de IRIS para Japón disminuyendo dimensiones y
    transformando las columnas al tipo de dato correcto
    
    Parameters
    ----------
    df : DataFrame
        DataFrame de eventos sísmicos de Japón proviniente de IRIS

    Returns
    ------
    df : DataFrame
        DataFrame con las columnas: time, date, magnitude, depth, 
        latitude, longitude, geoReference
    """
    # Dropeamos columnas que no vamos a utilizar
    df.drop(['EventID', 'Author', 'Catalog', 'Contributor','ContributorID','MagType','MagAuthor'], 
            axis='columns', inplace=True)
    #Acomodamos las fechas
    df = df.apply(separate_date_time, axis=1)
    df.drop('Time', axis='columns', inplace=True)
    #Renombramos columnas
    df.rename(columns={"Latitude":"latitude","Longitude":"longitude","Depth":"depth",
                    "EventLocationName":"geoReference","Magnitude":"magnitude"},inplace=True)
    
    # Formateamos tipo
     # Transformamos los tipos de las columnas
    type_str = ['geoReference']
    type_float = ['magnitude', 'longitude', 'latitude', 'depth']
    
    # Formateamos con funciones 
    for columna in type_str:
        df[columna] = format_str(df, columna)

    for columna in type_float:
        df[columna] = format_float(df, columna)

    # Eliminamos 'Japon' de la referencia
    df.geoReference = df.geoReference.str.replace(', Japan', '')

    return df

def get_states_jp(df):
    """Obtener los estados para los datos de Japón
    
    Parameters
    ----------
    df : DataFrame
        DataFrame de eventos sísmicos de Japón de IRIS formateado con `transform_usgs`

    Returns
    ------
    df : DataFrame
        DataFrame con columna de estado
    """
    # Buscamos el estado que se encuentre en la localizacion y lo extraemos
    pattern = ['honshu','hokkaido','shikoku','kyushu','ryukyu']
    df.loc[:,'state'] = df["geoReference"].str.lower().str.extract(f"({'|'.join(pattern)})")
    # Okinawa está dentro de Ryukyu
    df.state = df.state.replace('okinawa', 'ryukyu')
    df.state = format_str(df,'state')
    # Buscamos los estados que no se hayan encontrado en la geoRef
    df.loc[df.state.isna(),'state'] = df[df.state.isna()].apply(lambda row: get_state(row, country='中国'), axis=1)

    # Colocamos el idLocation
    path_locations = os.path.join('../datasets','locations.csv') ############### Poner path del archivo de localidades
    df_state = pd.read_csv(path_locations) 
    df_state = df_state[df_state.country == 'JP']
    df = pd.merge(df, df_state, left_on= ['state'], right_on=['state'], how = 'left')
    df = df[~(df.idLocation.isna())]
    df.idLocation = df.idLocation.astype(int)
    df = df[['date','time','magnitude','depth','longitude','latitude','idLocation','geoReference']]

    return df

def load_jp(path, short_name, type='hourly'):
    """Carga de archivos de Japón desde IRIS
    
    Parameters
    ----------
    path : str
        Path de la carpeta de los datos
    short_name : str
        Nombre de referencia para los archivos generados
    type : str
        Tipo de carga. Opciones 'hourly': carga desde la última fecha de carga
        hasta el momento que se corra la función, 'historic': carga los datos 
        desde 01/01/1988 hasta el 23/11/2022
    Returns
    ------
    df : DataFrame
        DataFrame con columna de estado
    """
    # Si es la carga horaria, sacar la ultima hora del archivo de texto
    if type == 'hourly':
        with open(os.path.join(path,'last_date_{}.txt'.format(short_name)), 'r') as f:
            last_date = f.readlines()[-1].strip()
    
        start_date = datetime.strptime(last_date, '%m/%d/%Y %H:%M:%S')
        end_date = datetime.today().replace(microsecond=0)

        # nombre del archivo
        name = short_name+'.csv' 

    # Si es la carga histórica, tiene fechas definidas
    elif type == 'historic':
        start_date = datetime(1988, 1, 1, 00, 00, 00)
        end_date = datetime(2022, 11, 23, 00, 00, 00)

        name = 'jp_iris.csv'
    
    # path completo
    file = os.path.join(path,name)
    # Cargamos los datos
    # Se obtiene el url
    url = iris_query(start_date, end_date)
    # Leemos los registros
    df = read_iris(url)

    # Transformamos
    # Si no esta vacio
    if not df.empty:
        ### Transformaciones
        df = transform_jp(df)
        ## Obtenemos estados
        df = get_states_jp(df)

        df.to_csv(file, index=False)

        # Guardamos el nombre del archivo
        # with open(os.path.join(path,'files_'+short_name+'.txt'), "a") as text_file:
        #     text_file.write(file+'\n')

    else:
        df.to_csv(file, index=False)

    # Guardamos la última hora de actualización en el txt
    end_date_str = end_date.strftime("%m/%d/%Y %H:%M:%S")
    with open(os.path.join(path,'last_date_'+short_name+'.txt'), "a") as text_file:
        text_file.write(end_date_str+'\n')

##### USGS ####

def usgs_query(start_date, end_date, place='US'):
    """Crea el query de USGS a partir de las fechas y el lugar para extraer
    eventos sísmicos con magnitud mayor a 3 y profundidad menor a 350 Km
    
    Parameters
    ----------
    start_date : datetime
        Fecha de inicio de la extracción
    end_date : datetime
        Fecha final de la extracción
    place : str
        País para el cual se desea extraer datos. Opciones: 'US': Estados Unidos
        Continental, 'AK': Alaska, 'HI': Hawaii, 'JP': Japón, 'MX': México
    Returns
    ------
    url : str
        URL de USGS para extraer eventos
    """

    base_url = 'https://earthquake.usgs.gov/fdsnws/event/1/query.geojson?'
    # Parámetros
    # Definimos ventana de tiempo
    start_time = str(start_date.date())+'%20'+str(start_date.time())
    end_time = str(end_date.date())+'%20'+str(end_date.time())

    # Posición
    if place == 'US':
        max_latitude = '50'
        min_latitude = '24.6'
        max_longitude = '-65'
        min_longitude = '-125'

    elif place == 'AK':
        max_latitude = '71.413'
        min_latitude = '56.072'
        max_longitude = '-141.064'
        min_longitude = '-168.012'

    elif place == 'HI':
        max_latitude = '22.796'
        min_latitude = '18.75'
        max_longitude = '-154.811'
        min_longitude = '-160.313'

    elif place == 'JP':
        max_latitude = '45.557'
        min_latitude = '20.9325'
        max_longitude = '153.986'
        min_longitude = '122.932'

    elif place == 'MX':
        max_latitude = '32.769'
        min_latitude = '15.199'
        max_longitude = '-86.66'
        min_longitude = '-117.422'

    # Magnitud mínima de los sismos
    min_magnitude = '3'
    max_depth = '350'
    # Orden de los registros
    order = 'time-asc'
    
    # Armamos el query
    time_window = 'starttime='+start_time+'&endtime='+end_time
    position = '&maxlatitude='+max_latitude+'&minlatitude='+min_latitude+'&maxlongitude='+max_longitude+'&minlongitude='+min_longitude

    return base_url+time_window+position+'&minmagnitude='+min_magnitude+'&maxdepth='+max_depth+'&orderby='+order

def read_usgs(url):
    """Lectura de archivos GeoJSON de USGS
    
    Parameters
    ----------
    url : str
        URL del GeoJSON proviniente de IRIS
    Returns
    ------
    df : DataFrame
        DataFrame con los datos del archivo GeoJSON
    """
    # Hacemos un request porque hay json anidados
    data_json = requests.get(url).json()
    # el diccionario de features es el que tiene la infomación
    df = pd.json_normalize(data_json, record_path =['features'])

    return df

##### IRIS ####

def iris_query(start_date, end_date):
    """Crea el query de IRIS para eventos sísmicos en Japón con magnitud mayor a 3 
    y profundidad menor a 350 Km a partir de las fechas 
    
    Parameters
    ----------
    start_date : datetime
        Fecha de inicio de la extracción
    end_date : datetime
        Fecha final de la extracción
    Returns
    ------
    url : str
        URL de IRIS para extraer eventos sísmicos de Japón
    """
    '''Crea el query de IRIS a partir de las fechas y el lugar '''

    base_url = 'http://service.iris.edu/fdsnws/event/1/query?'
    # parámetros
    start_time = str(start_date.date())+'T'+str(start_date.time())
    end_time = str(end_date.date())+'T'+str(end_date.time())
    # coordenadas de japon
    max_latitude = '45.557'
    min_latitude = '20.9325'
    max_longitude = '153.986'
    min_longitude = '122.932'
    # magnitud de los sismos
    min_magnitude = '3'
    # orden de los registros
    order = 'time-asc'
    # formato del archivo
    format_type = 'geocsv'
    # maxima profundidad
    maxdepth= '350'

    time_window = 'starttime='+start_time+'&endtime='+end_time

    position = '&maxlat='+max_latitude+'&minlon='+min_longitude+'&maxlon='+max_longitude+'&minlat='+min_latitude

    return base_url+time_window+'&minmag='+min_magnitude+'&orderby='+order+'&format='+format_type+'&maxdepth='+maxdepth+position+'&nodata=404'

def read_iris(url):
    """Lectura de archivos GeoCSV de IRIS para eventos en Japón
    
    Parameters
    ----------
    url : str
        URL del GeoCSV proviniente de IRIS
    Returns
    ------
    df : DataFrame
        DataFrame del archivo
    """
    df = pd.read_csv(url, sep='|', skiprows=4, low_memory=False)
    
    return df[df.EventLocationName.str.contains('JAPAN')]