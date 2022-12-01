<p align="center">
  <img src="../figuras/mlgi-logo.png"
  width="70%" 
  height="auto" />
</p>

# KPIs
> *Key Performance Indicator* ⇒ *Indicador Clave de Desempeño*
> 
Los KPIs o Medidores de Desempeño son una serie de métricas que se utilizan para sintetizar la información sobre la eficacia y productividad de las acciones que se lleven a cabo en un trabajo con el fin de poder tomar decisiones y determinar aquellas que han sido más efectivas a la hora de cumplir con los objetivos marcados en una tarea o proyecto concreto.
Una métrica es un dato que nos sirve para ver la evolución de algo que pueda ser medible. Sin embargo, un KPI es una métrica clave, es una métrica que será fundamental para medir el desempeño de la estrategia propuesta, para lograr los objetivos o metas que se planteen.
Para esto tenemos que tener en claro nuestros objetivos, metas o nuestra estrategia de trabajo ya que esto nos permitirá saber si está conseguido o no el objetivo que se busca y posteriormente el cómo mejorar el resultado final, en el caso de ser posible.

Este concepto es más simple de ejemplificar en proyectos de negocio. Por ejemplo, para una empresa que fabrica un producto específico podríamos tener una campaña que tenga:
	- **Meta**: Aumentar las ventas de una categoría específica.
	- **Objetivo**: Aumentar un 3% el total de ventas de esta categoría en un plazo de 6 meses.
	- **KPI**: CAC Coste de Adquisición de Clientes (o Customer Acquisition Cost), la cantidad que se debe invertir para reclutar un nuevo cliente.
	- **Métrica**: Huella de Carbono por cada x cantidad de productos vendidos.

Utilizamos únicamente un ejemplo de cada uno, primero la meta y el objetivo.
Según la Universidad de Tulane, Nueva Orleans; “las metas son más amplias, son principios que guían el proceso de toma de decisiones; por su lado, los objetivos son específicos, medibles, son pequeños pasos para alcanzar la meta”.
Con respecto al KPI, utilizamos uno muy popular a modo de ejemplo, vemos que es una métrica fundamental para el objetivo y meta planteado. Sin embargo, la métrica “Huella de Carbono por cada x cantidad de productos vendidos” no es clave con respecto a la meta y el objetivo planteado, es interesante pensar que para otras metas y objetivos si puede ser un KPI y el CAC dejar de serlo.

Básicamente un KPI es una medida del rendimiento o comportamiento pasado de algo que es importante para el objetivo puntual o la estrategia planteada para llegar a ese objetivo

## Metas y objetivos del trabajo solicitado.
Las Metas del trabajo pedido son: 
- Desarrollar mejores herramientas para el acceso fácil y eficiente a la información sismológica de México, Estados Unidos y Japón
- Facilitar la visualización de los datos que se poseen sobre el tema, buscando generar un mayor entendimiento colectivo de la situación sismológica.

Y los objetivos que poseen un plazo máximo de 4 semanas: 
- Generar un sistema web que emita alertas sísmicas con un lenguaje que sea fácil de entender para el total de la población. 
- La creación de una base de datos alimentada automáticamente que incluya eventos sísmicos de México, Estados Unidos y Japón con el fin de mejorar el análisis de estos sucesos y la capacidad de predicción.
- La clasificación de eventos sísmicos por medio de un modelo de aprendizaje automático no supervisado, de acuerdo a variables sociales como la densidad de población (lo cual lleva a la densidad de edificios en ciudades desarrolladas, que aumenta la peligrosidad de un sismo).

## KPIs propuestos.
En los KPIs planteados utilizamos la frase “alta peligrosidad” que deberá ser definida previamente. Según la USGS que compara valores de Magnitud e Intensidad, este valor será entre 6 y 9 de magnitud en la escala de Richter .

1. Daños en base a la profundidad del sismo.
    Cruzar los datos que se poseen con los daños por Localidades para medir las consecuencias de un sismo según su profundidad, es fundamental para definir la peligrosidad de un determinado sismo. 

2. Frecuencia histórica de los sismos más intensos en México.
    Este KPI tiene como importancia medir la frecuencia de los sismos relevantes, para así poder predecir un rango esperable de sismos de una determinada magnitud, para cuando el sistema de alarmas y la base de datos estén en funcionamiento.
3. Desfase temporal entre el evento y la carga de los datos en las APIs utilizadas.
    La carga incremental de los datos que nos permitirá tener la base de datos actualizada se realizará por medio de APIs específicas, las mismas tienen un desfase temporal entre la carga de los datos y el tiempo en el que ocurrió el sismo.
    Aunque no podamos minimizar este desfase es fundamental para el entendimiento de la efectividad del sistema de alarma planteado en los objetivos.
4. Precisión de clasificación del modelo propuesto de sismos de “alta peligrosidad”.
    Debemos medir la precisión del modelo de aprendizaje automático no supervisado de clasificación de eventos sísmicos. 
5. Desfase temporal entre la carga de los datos y la generación de la alerta.
    Este desfase temporal puede ser controlado por el equipo por medio de la mejora del rendimiento del algoritmo de carga, limpieza y consulta de los datos en la base de datos.
