# 🔍 MySQL Query Optimizer & Validator

Una aplicación web construida con **Python** y **Streamlit** diseñada para ayudar a desarrolladores a validar y optimizar consultas SQL en bases de datos MySQL.

La herramienta realiza dos niveles de análisis:
1.  **Análisis Estático:** Revisa el texto de la consulta en busca de malas prácticas de sintaxis y diseño (ej. `SELECT *`, `LIKE '%...'`).
2.  **Análisis Dinámico:** Se conecta a la base de datos y utiliza el comando `EXPLAIN` de MySQL para entender cómo el motor ejecutará la consulta, detectando escaneos completos de tabla y uso ineficiente de índices.

## 📋 Requisitos Previos

*   Python 3.8 o superior.
*   Acceso a una base de datos MySQL (Host, Usuario, Contraseña y Nombre de la BD).
*   El usuario de base de datos debe tener permisos de lectura (`SELECT`) sobre las tablas a consultar.

## 🚀 Instalación

Sigue estos pasos para configurar el proyecto en tu máquina local.

1. Clonar el repositorio
2. Descarga el código en tu máquina
3. Crear un Entorno Virtual
   
Es altamente recomendado usar un entorno virtual para evitar conflictos con las librerías del sistema (especialmente en Linux/Ubuntu).

En Linux / macOS:

python3 -m venv venv
source venv/bin/activate

En Windows:

python -m venv venv
.\venv\Scripts\activate

4. Instalar Dependencias
Instala las librerías necesarias (streamlit, mysql-connector-python, pandas, sqlparse) ejecutando:

pip install -r requirements.txt

(Si no tienes el archivo requirements.txt, puedes instalar manualmente con: pip install streamlit mysql-connector-python pandas sqlparse)

## 🛠️ Uso

Asegúrate de tener el entorno virtual activado.

Ejecuta la aplicación con Streamlit:

streamlit run mysql_query_analizer.py

Se abrirá automáticamente una pestaña en tu navegador (usualmente en http://localhost:8501).

En la barra lateral, ingresa las credenciales de tu conexión MySQL.

Escribe tu consulta en el área de texto y presiona "Validar y Analizar".

## 🛡️ Qué detecta esta herramienta

# Reglas Estáticas (Sintaxis)

⛔ SELECT *: Selección ineficiente de columnas.

⛔ LIKE '%valor': Comodines al inicio que invalidan el uso de índices B-Tree.

⚠️ Funciones en WHERE: Uso de funciones (ej. YEAR(fecha)) sobre columnas indexadas, lo que impide el uso del índice.

# Reglas Dinámicas (MySQL EXPLAIN)

🔥 Full Table Scan (type=ALL): El motor lee toda la tabla fila por fila. Es el problema de rendimiento más crítico.

🐌 Filesort / Temporary: Indica que MySQL debe crear tablas temporales en disco o memoria para ordenar o agrupar los resultados.

❌ Índices no usados: Detecta cuando existen índices disponibles (possible_keys) pero MySQL decide no usarlos (key vacío).

## 📝 Notas Técnicas

Seguridad: La aplicación utiliza EXPLAIN, lo cual simula la ejecución para obtener el plan. No modifica datos, pero se recomienda usar un usuario de base de datos con permisos de solo lectura en entornos productivos.
Conector: Utiliza el conector oficial mysql-connector-python.

## 📄 Licencia

Este proyecto está bajo la licencia MIT.

