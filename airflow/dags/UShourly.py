import os.path                                      # manejo de paths
import pandas as pd                                 # manejo de datos
from datetime import datetime, date                 # manejo de fechas
from dateutil.relativedelta import relativedelta    # delta de tiempo
from utils import *                                 # funciones comunes para los scripts

def load_us(place, path, short_name):
    '''Función para la carga continua de archivos de USGS'''

    # Leemos la útltima fecha de actualización
    txt_date = os.path.join(path,'last_date_{}.txt'.format(short_name))

    with open((txt_date), 'r') as f:
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
        df = get_states_usa(df, place=place)
            
        if place == 'US':
            if os.path.isfile(file):
                os.remove(file)

        # Guardamos el archivo
        # si el archivo existe
        if os.path.isfile(file):
            # concatenar al csv
            df.to_csv(file, mode='a', index=False, header=False)
        else:
            # guardar csv con header
            df.to_csv(file, index=False)
        
        # # Guardamos el nombre del archivo
        # with open(os.path.join(path,'files_'+short_name+'.txt'), "a") as text_file:
        #     text_file.write(file+'\n')
    
    else:
        if os.path.isfile(path):
            # concatenar al csv
            df.to_csv(path, mode='a', index=False, header=False)
        else:
            # guardar csv con header
            df.to_csv(path, index=False)

    if place == 'HI':
        # Guardamos la última hora de actualización en el txt
        end_date_str = end_time.strftime("%m/%d/%Y %H:%M:%S")

        with open(txt_date, "a") as text_file:
            text_file.write(end_date_str+'\n')

def main():

    PATH = '..\datasets'
    SHORT_NAME_US = 'usa_usgs'

    load_us(place='US', path=PATH, short_name=SHORT_NAME_US)

    load_us(place='AK', path=PATH, short_name=SHORT_NAME_US)

    load_us(place='HI', path=PATH, short_name=SHORT_NAME_US)

if __name__ == "__main__":
    main()