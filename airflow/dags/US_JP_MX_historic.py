import pandas as pd                                 # manejo de datos
from datetime import datetime, date                 # manejo de fechas
from utils import *                                 # funciones comunes para los scripts
import os.path                                      # manejo de paths
pd.set_option('mode.chained_assignment', None)

def load_transform(start_date, max_date, path, months=6, days=0, place='US'):
    '''En una ventana de 6 meses, obtiene los datos de la ventana máxima de 
    tiempo con menos de 20000 registros, los transforma y los guarda'''

    try: 
        end_date =  start_date + relativedelta(months=+months, days=+days)

        if end_date > max_date:
            end_date = max_date
            
        url = usgs_query(start_date, end_date, place=place)
        df = read_usgs(url)

        if (df.empty) and (start_date != end_date):
            pass

        else: 
             ### Transformaciones
            df = transform_usgs(df)

            # Obtenemos los estados
            df = get_states_usa(df, place=place)

            # Guardamos
            # si el archivo existe
            if os.path.isfile(path):
                # concatenar al csv
                df.to_csv(path, mode='a', index=False, header=False)
            else:
                # guardar csv con header
                df.to_csv(path, index=False)
    
    except: 
        months -=1
        if months <= 0:
            days+=10
            end_date = load_transform(start_date, max_date=max_date, path=path, months=0, days=days, place=place)
        else:
            end_date = load_transform(start_date, max_date=max_date, path=path, months=months, place=place)
    
    return end_date

def load_us_historic(place, path, short_name):
    '''Función para la carga historica de archivos de USGS'''

    # Path para guardar el archivo de salida
    file = os.path.join(path,short_name+'.csv')

    # Definimos fechas para mantener el conteo
    start_date = datetime(1988, 1, 1, 00, 00, 00)
    end_date =  datetime(2022, 11, 23, 00, 00, 00)

    # Hacemos la recursión
    new_date = start_date
    while new_date.date() < end_date.date():
        new_date = load_transform(new_date, max_date=end_date, path=file, place=place)

    # Guardamos el nombre del archivo
    # if place == 'HI':
    #     with open(os.path.join(path,'files_'+short_name+'.txt'), "a") as text_file:
    #         text_file.write(file+'\n')

    # Guardamos la última fecha en el txt
    if place == 'HI':
        end_date_str = end_date.strftime("%m/%d/%Y %H:%M:%S")
        with open(os.path.join(path,'last_date_'+short_name+'.txt'), "a") as text_file:
            text_file.write(end_date_str+'\n')  

def transform_mx_historic(df):
    # Eliminamos las columnas que no vamos a utilizar
    df.drop(['Fecha local','Hora local', 'Estatus'], axis='columns', inplace=True)
    # Renombrams las columnas
    names = {'Fecha UTC':'date', 'Hora UTC':'time', 'Latitud':'latitude', 'Longitud':'longitude', 
            'Profundidad':'depth', 'Referencia de localizacion':'geoReference', 'Magnitud':'magnitude'}
    df.rename(names, axis='columns', inplace=True)
    # Eliminamos registros donde el depth es un str
    df = df[~(df.depth.str.len() > 5)]
    # Formateamos tipo
    # Transformamos los tipos de las columnas
    type_str = ['geoReference']
    type_float = ['magnitude', 'longitude', 'latitude', 'depth']

    # Formateamos con funciones 
    for columna in type_str:
            df[columna] = format_str(df, columna)

    for columna in type_float:
            df[columna] = format_float(df, columna)
    return df

def get_states_mx(df):
    # obtenemos las iniciales de los estados
    df['state'] = df.geoReference.str.strip().str.split(',').apply(lambda x: x[-1])
    df.state = df.state.str.upper().str.strip()
    df.head()

    # Sustituimos las abreviaciones por los nombres 
    states = pd.read_html('https://en.wikipedia.org/wiki/Template:Mexico_State-Abbreviation_Codes')[0]
    names = {'Name of federative entity':'State', '3-letter code (ISO 3166-2:MX)':'abbreviation_3', '2-letter code*':'abbreviation_2', 'Conventional abbreviation':'abbreviation_other'}
    states.rename(names, axis=1, inplace=True)
    states.abbreviation_3 = states.abbreviation_3.str.replace('MX-', '', regex=False).str.strip()
    states.abbreviation_2 = states.abbreviation_2.str.replace('MX - ', '', regex=False).str.strip()
    states.abbreviation_other = states.abbreviation_other.str.replace('.','', regex=False).str.upper()
    states.State = states.State.str.replace('Mexico City', 'Ciudad De Mexico')

    for abbreviation in ['abbreviation_3', 'abbreviation_2', 'abbreviation_other']:
        df = pd.merge(df, states, left_on=['state'], right_on= [abbreviation], how = 'left')
        df.loc[df.State.notna(), 'state'] = df.State
        df.drop(['State', 'abbreviation_3',  'abbreviation_2', 'abbreviation_other'], axis=1, inplace=True)

    # Sustituimos los valores que se encuentran en state pero no son estados de MX
    # por None
    pattern = states.State.to_list()
    df.loc[~df.state.str.contains("|".join(pattern), regex=True), 'state'] = None

    # Obtenemos los faltantes con geopy
    df.loc[df.state.isna(), 'state'] = df[df.state.isna()].apply(lambda row: get_state(row, country='México'), axis=1)
    df = df[~df.state.isna()]

    # Agregamos idLocation
    path_locations = os.path.join('..\datasets','locations.csv') ############### Poner path del archivo de localidades
    df_state = pd.read_csv(path_locations) 
    df_state = df_state[df_state.country == 'MX']

    # Normalizamos los nombres para evitar problemas con tildes
    df_state.state = df_state.state.str.strip().str.title().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
    df.state = df.state.str.strip().str.title().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

    # Juntamos para agregar el id
    df = pd.merge(df, df_state, left_on= ['state'], right_on= ['state'], how = 'left')
    df.dropna(inplace=True)
    df.idLocation = df.idLocation.astype(int)

    df = df[['date','time','magnitude','depth','longitude','latitude','idLocation','geoReference']]
    
    return df 

def main():
    
    PATH = '..\datasets'

    ##### JP #####

    SHORT_NAME_JP = 'jp_iris'

    print('Carga JP')
    load_jp(path=PATH, short_name=SHORT_NAME_JP, type='historic')

    ##### MX #####

    NAME = 'SSNMX_catalogo_19880101_20221123_utc_m09_100_profMD1_350.csv'
    FILE = os.path.join(PATH,NAME)
    SHORT_NAME_MX = 'mx_sns'

    print('Carga MX')
    # Cargamos el archivo
    df = pd.read_csv(FILE,skiprows=4, skipfooter=7, engine='python')
    # Transformamos
    df = transform_mx_historic(df)
    # Agregamos estados
    df= get_states_mx(df)

    # Guardamos
    df.to_csv(os.path.join(PATH,'mx_sns.csv'), index=False)

    # Guardamos el nombre del archivo
    # with open(os.path.join(PATH,'files_'+SHORT_NAME_MX+'.txt'), "a") as text_file:
    #     text_file.write(os.path.join(PATH,SHORT_NAME_MX+'.csv'+'\n'))

    # Guardamos la última hora de actualización en el txt
    end_date = datetime(2022, 11, 23, 00, 00, 00)
    end_date_str = end_date.strftime("%m/%d/%Y %H:%M:%S")
    with open(os.path.join(PATH,'last_date_'+SHORT_NAME_MX+'.txt'), "a") as text_file:
        text_file.write(end_date_str+'\n')

    ##### US #####

    SHORT_NAME_US = 'usa_usgs'

    print('Carga US')
    load_us_historic(place='US', path=PATH, short_name=SHORT_NAME_US)

    print('Carga AK')
    load_us_historic(place='AK', path=PATH, short_name=SHORT_NAME_US)

    print('Carga HI')
    load_us_historic(place='HI', path=PATH, short_name=SHORT_NAME_US)

    #### Juntamos los df generados #####

    lista_files = []

    for short_name in [SHORT_NAME_US, SHORT_NAME_JP, SHORT_NAME_MX]:

        with open(os.path.join(PATH,'files_{}.txt'.format(short_name)), 'r') as f:
            lista_files.append(f.readlines()[-1].strip())

    df_us = pd.read_csv(lista_files[0])
    df_jp = pd.read_csv(lista_files[1])
    df_mx = pd.read_csv(lista_files[2])

    df = pd.concat([df_us, df_jp, df_mx])

    # Lo guardamos
    df.to_csv(os.path.join(PATH, 'historicSeism.csv'), index=False)

    # Eliminamos los archivos individuales
    for file in lista_files:
        os.remove(file)

if __name__ == "__main__":
    main()