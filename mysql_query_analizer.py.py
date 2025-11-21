import streamlit as st
import mysql.connector
import pandas as pd
import sqlparse
import re

# Configuración de la página
st.set_page_config(page_title="SQL Query Optimizer", layout="wide")

st.title("🔍 Validador y Optimizador de Consultas MySQL")
st.markdown("""
Esta herramienta analiza tu consulta SQL utilizando el comando `EXPLAIN` de MySQL y análisis estático 
para detectar problemas comunes de rendimiento.
""")

# --- BARRA LATERAL: CONEXIÓN ---
st.sidebar.header("1. Configuración de Conexión")
db_host = st.sidebar.text_input("Host", "localhost")
db_user = st.sidebar.text_input("Usuario", "root")
db_pass = st.sidebar.text_input("Contraseña", type="password")
db_name = st.sidebar.text_input("Base de Datos")

def get_connection():
    try:
        return mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_pass,
            database=db_name
        )
    except Exception as e:
        st.sidebar.error(f"Error de conexión: {e}")
        return None

# --- LÓGICA DE ANÁLISIS ---

def analyze_static_rules(query):
    """Analiza la consulta a nivel de texto/sintaxis"""
    warnings = []
    
    # Regla 1: Uso de SELECT *
    if re.search(r"SELECT\s+\*", query, re.IGNORECASE):
        warnings.append({
            "Nivel": "Alto",
            "Problema": "Uso de 'SELECT *'",
            "Consejo": "Evita seleccionar todas las columnas. Enumera solo las columnas necesarias para reducir la carga de I/O y red."
        })

    # Regla 2: Uso de LIKE con comodín al inicio
    if re.search(r"LIKE\s+['\"]%.*['\"]", query, re.IGNORECASE):
        warnings.append({
            "Nivel": "Alto",
            "Problema": "Uso de 'LIKE %valor'",
            "Consejo": "Los comodines al inicio (%) inhabilitan el uso de índices normales. Intenta usar índices FULLTEXT o buscar por prefijos."
        })

    # Regla 3: Funciones en columnas indexadas (Detección básica en WHERE)
    # Esto busca patrones como YEAR(fecha) = 2023
    if re.search(r"WHERE\s+\w+\(", query, re.IGNORECASE):
        warnings.append({
            "Nivel": "Medio",
            "Problema": "Posible función en columna filtrada",
            "Consejo": "Si aplicas funciones a una columna en el WHERE (ej: `YEAR(fecha)`), MySQL no usará el índice. Reescribe como rango."
        })
        
    return warnings

def analyze_execution_plan(df_explain):
    """Analiza el resultado del comando EXPLAIN"""
    warnings = []
    
    for index, row in df_explain.iterrows():
        table = row.get('table', 'Desconocida')
        select_type = row.get('select_type', '')
        type_access = row.get('type', '')
        possible_keys = row.get('possible_keys', '')
        key = row.get('key', '')
        rows = row.get('rows', 0)
        extra = row.get('Extra', '')

        # Regla 1: Full Table Scan
        if type_access == 'ALL':
            warnings.append({
                "Nivel": "Crítico",
                "Tabla": table,
                "Problema": "Full Table Scan (type=ALL)",
                "Consejo": f"MySQL está leyendo toda la tabla '{table}'. Falta un índice en la columna del WHERE o JOIN."
            })

        # Regla 2: No uso de índices
        if possible_keys and not key:
            warnings.append({
                "Nivel": "Alto",
                "Tabla": table,
                "Problema": "Índices disponibles pero no usados",
                "Consejo": "Existen índices candidatos pero MySQL decidió no usarlos. Revisa la cardinalidad o fuerza el índice."
            })

        # Regla 3: Archivos temporales y Filesort
        if 'Using temporary' in str(extra) or 'Using filesort' in str(extra):
            warnings.append({
                "Nivel": "Medio",
                "Tabla": table,
                "Problema": "Uso de disco/temp (Filesort/Temporary)",
                "Consejo": "La consulta requiere ordenar o agrupar manualmente. Un índice compuesto que cubra ORDER BY/GROUP BY solucionaría esto."
            })
            
        # Regla 4: Escaneo de demasiadas filas (heurística simple)
        if rows and int(rows) > 10000: # Umbral arbitrario
             warnings.append({
                "Nivel": "Info",
                "Tabla": table,
                "Problema": f"Alto volumen de filas escaneadas ({rows})",
                "Consejo": "Asegúrate de que el filtrado sea eficiente. Si esto es intencional para un reporte, ignora este mensaje."
            })

    return warnings

# --- INTERFAZ PRINCIPAL ---

st.header("2. Ingresa tu Consulta SQL")
query = st.text_area("Escribe tu consulta (SELECT...)", height=150, placeholder="SELECT * FROM usuarios WHERE email = 'test@test.com'")

col1, col2 = st.columns([1, 4])

if col1.button("Validar y Analizar"):
    if not query.strip():
        st.warning("Por favor escribe una consulta.")
    elif not db_name:
        st.warning("Configura la conexión a la base de datos primero.")
    else:
        conn = get_connection()
        if conn:
            # 1. Formateo de SQL
            formatted_sql = sqlparse.format(query, reindent=True, keyword_case='upper')
            st.subheader("Consulta Formateada")
            st.code(formatted_sql, language='sql')

            # 2. Análisis Estático
            static_warnings = analyze_static_rules(query)
            
            # 3. Análisis Dinámico (EXPLAIN)
            dynamic_warnings = []
            explain_df = pd.DataFrame()
            
            try:
                cursor = conn.cursor(dictionary=True)
                # Solo ejecutamos EXPLAIN para no modificar datos
                cursor.execute(f"EXPLAIN {query}")
                result = cursor.fetchall()
                explain_df = pd.DataFrame(result)
                conn.close()
                
                dynamic_warnings = analyze_execution_plan(explain_df)
                
            except mysql.connector.Error as err:
                st.error(f"Error SQL: {err}")
            
            # --- MOSTRAR RESULTADOS ---
            
            st.divider()
            
            # Mostrar Plan de Ejecución
            if not explain_df.empty:
                st.subheader("📊 Plan de Ejecución (EXPLAIN)")
                st.dataframe(explain_df, use_container_width=True)
                st.caption("Este es el plan interno de MySQL. Busca columnas 'type' con valor 'ALL' (malo) vs 'const'/'ref' (bueno).")

            # Mostrar Recomendaciones
            st.subheader("🛡️ Reporte de Optimización")
            
            all_warnings = static_warnings + dynamic_warnings
            
            if not all_warnings:
                st.success("¡Excelente! No se detectaron problemas obvios de rendimiento con las reglas actuales.")
            else:
                for w in all_warnings:
                    nivel = w['Nivel']
                    color = "red" if nivel in ["Crítico", "Alto"] else "orange" if nivel == "Medio" else "blue"
                    
                    with st.container():
                        st.markdown(f"**:{color}[[{nivel}]] {w.get('Problema')}**")
                        if 'Tabla' in w:
                            st.markdown(f"*Tabla afectada:* `{w['Tabla']}`")
                        st.info(f"💡 **Consejo:** {w['Consejo']}")
                        st.markdown("---")
