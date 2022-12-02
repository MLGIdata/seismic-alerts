from utils import *                 # funciones del proyecto

def main():

    PATH = '..\datasets'
    SHORT_NAME = 'jp_iris'
    
    load_jp(path=PATH, short_name=SHORT_NAME, type='hourly')

if __name__ == "__main__":
    main()