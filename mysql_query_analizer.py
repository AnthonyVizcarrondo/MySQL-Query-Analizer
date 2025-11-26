import streamlit as st
import mysql.connector
import pandas as pd
import sqlparse
import re

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="SQL Optimizer", layout="wide", page_icon="🛡️")

# --- BARRA LATERAL ---
with st.sidebar:
    try:
        st.image("logo.png") 
    except:
        st.warning("⚠️ No se encontró 'logo.png'")
    
    st.divider()
    st.header("1. Conexión MySQL")
    
    db_host = st.text_input("Host", "localhost")
    db_user = st.text_input("Usuario", type="password") 
    db_pass = st.text_input("Contraseña", type="password")
    db_name = st.text_input("Base de Datos", "test_db")
    
# --- LÓGICA DEL BOTÓN DE PRUEBA ---
    if st.button("Probar Conexión", type="primary"):
        try:
            test_conn = mysql.connector.connect(
                host=db_host,
                user=db_user,
                password=db_pass,
                database=db_name,
                connection_timeout=5
            )
            if test_conn.is_connected():
                st.success("✅ ¡Conexión Exitosa!")
                test_conn.close()
        except mysql.connector.Error as err:
            st.error(f"❌ Error de conexión: {err}")
        except Exception as e:
            st.error(f"❌ Error general: {e}")

# --- LÓGICA PRINCIPAL ---
st.title("🛡️ Validador de Calidad SQL")
st.markdown("Analiza consultas buscando **Full Table Scans** y problemas de rendimiento.")

query = st.text_area("2. Escribe tu consulta SQL:", height=150, placeholder="SELECT * FROM tabla...")

if st.button("Validar y Analizar", type="primary"):
    if not query.strip() or not db_name:
        st.error("❌ Por favor completa la conexión y escribe una consulta.")
    else:
        # 1. Formateo Visual
        st.subheader("📝 Consulta Formateada")
        st.code(sqlparse.format(query, reindent=True, keyword_case='upper'), language='sql')

        # 2. Conexión y Ejecución
        try:
            conn = mysql.connector.connect(host=db_host, user=db_user, password=db_pass, database=db_name)
            cursor = conn.cursor(dictionary=True)
            
            # Ejecutamos EXPLAIN
            cursor.execute(f"EXPLAIN {query}")
            explain_df = pd.DataFrame(cursor.fetchall())
            conn.close()

            # 3. Mostrar Tabla EXPLAIN
            with st.expander("Ver detalle técnico (Tabla EXPLAIN)"):
                st.dataframe(explain_df) 

            # 4. ANÁLISIS Y REPORTE
            st.divider()
            st.subheader("📊 Reporte de Optimización")
            
            warnings = []

            # A. Reglas Estáticas
            if re.search(r"SELECT\s+\*", query, re.IGNORECASE):
                warnings.append(("Alto", "Uso de 'SELECT *'", "Traer todas las columnas consume memoria innecesaria. Especifica solo las que usas."))
            if re.search(r"LIKE\s+['\"]%.*['\"]", query, re.IGNORECASE):
                warnings.append(("Alto", "LIKE con '% al inicio'", "Esto impide el uso de índices. La búsqueda será lenta."))
            
            # B. Reglas Dinámicas (del EXPLAIN)
            for _, row in explain_df.iterrows():
                table = row.get('table', 'Desconocida')
                extra = str(row.get('Extra', ''))
                type_ref = row.get('type', '')

                if type_ref == 'ALL':
                    warnings.append(("Crítico", f"Full Table Scan en '{table}'", "El motor lee TODA la tabla fila por fila. Falta un índice en el WHERE."))
                
                if 'Using filesort' in extra:
                    warnings.append(("Medio", f"Filesort en tabla '{table}'", "La BD ordena manualmente. Un índice compuesto ayudaría."))
                
                if 'Using temporary' in extra:
                    warnings.append(("Medio", f"Tabla Temporal en '{table}'", "Se creó una tabla temporal en disco/memoria para resolver la consulta."))

            # 5. RENDERIZADO VISUAL
            if not warnings:
                st.success("✅ **¡Excelente trabajo!** No se detectaron problemas graves de rendimiento.", icon="🎉")
            else:
                # Contamos errores
                n_criticos = sum(1 for w in warnings if w[0] == "Crítico")
                if n_criticos > 0:
                    st.error(f"⚠️ Se encontraron {n_criticos} problemas críticos.")
                
                # Mostramos las tarjetas bonitas
                for nivel, titulo, consejo in warnings:
                    if nivel == "Crítico":
                        st.error(f"**{titulo}**\n\n💡 *{consejo}*", icon="🔥")
                    elif nivel == "Alto":
                        st.warning(f"**{titulo}**\n\n💡 *{consejo}*", icon="⚠️")
                    elif nivel == "Medio":
                        st.info(f"**{titulo}**\n\n💡 *{consejo}*", icon="ℹ️")

        except mysql.connector.Error as err:
            st.error(f"Error de base de datos: {err}")
        except Exception as e:
            st.error(f"Error inesperado: {e}")
