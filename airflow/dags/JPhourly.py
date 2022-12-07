'''
Este script carga continua de datos sísmicos de Japón desde IRIS. A partir de la última hora de carga
se cargan los datos nuevos hasta el momento en que se corre el script.
Para que funcione se tiene que correr primero US_JP_MX_historic.py
'''

from utils import *                 # funciones del proyecto

def main():

    PATH = 'data'
    SHORT_NAME = 'jp_iris'
    
    load_jp(path=PATH, short_name=SHORT_NAME, type='hourly')

if __name__ == "__main__":
    main()