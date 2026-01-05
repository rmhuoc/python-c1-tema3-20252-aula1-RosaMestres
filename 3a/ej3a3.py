"""
Enunciado:
En este ejercicio aprenderás a trabajar con bases de datos SQLite existentes.
Aprenderás a:
1. Conectar a una base de datos SQLite existente
2. Convertir datos de SQLite a formatos compatibles con JSON
3. Extraer datos de SQLite a pandas DataFrame

El archivo ventas_comerciales.db contiene datos de ventas con tablas relacionadas
que incluyen productos, vendedores, regiones y ventas. Debes analizar estos datos
usando diferentes técnicas.
"""

import sqlite3
import pandas as pd
import os
import json
from typing import List, Dict, Any, Optional, Tuple, Union

# Ruta a la base de datos SQLite
DB_PATH = os.path.join(os.path.dirname(__file__), 'ventas_comerciales.db')

def conectar_bd() -> sqlite3.Connection:
    """
    Conecta a una base de datos SQLite existente

    Returns:
        sqlite3.Connection: Objeto de conexión a la base de datos SQLite
    """
    # Implementa aquí la conexión a la base de datos:
    # 1. Verifica que el archivo de base de datos existe
    # 2. Conecta a la base de datos
    # 3. Configura la conexión para que devuelva las filas como diccionarios (opcional)
    # 4. Retorna la conexión

    #1) verifica que existe el archivo
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"No s encontro la base de datos en: {DB_PATH}")
    
    #2) conecta
    conn = sqlite3.connect(DB_PATH)

    #3) configura row_factory para devolver filss como "diccionarios"
    conn.row_factory = sqlite3.Row

    try:
        conn.execute("PRAGMA foreign_keys = ON;")
    except sqlite3.Error:
        # do nothing
        pass
    
    return conn

    

def convertir_a_json(conexion: sqlite3.Connection) -> Dict[str, List[Dict[str, Any]]]:
    """
    Convierte los datos de la base de datos en un objeto compatible con JSON

    Args:
        conexion (sqlite3.Connection): Conexión a la base de datos SQLite

    Returns:
        Dict[str, List[Dict[str, Any]]]: Diccionario con todas las tablas y sus registros
        en formato JSON-serializable
    """
    # Implementa aquí la conversión de datos a formato JSON:
    # 1. Crea un diccionario vacío para almacenar el resultado
    # 2. Obtén la lista de tablas de la base de datos
    # 3. Para cada tabla:
    #    a. Ejecuta una consulta SELECT * FROM tabla
    #    b. Obtén los nombres de las columnas
    #    c. Convierte cada fila a un diccionario (clave: nombre columna, valor: valor celda)
    #    d. Añade el diccionario a una lista para esa tabla
    # 4. Retorna el diccionario completo con todas las tablas

    #1) crea diccionario vacio
    resultado: Dict[str, List[Dict[str, any]]] = {}
    cur = conexion.cursor()

    #2) lista de tablas 
    cur.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name;
                """)
    
    tablas = [row[0] for row in cur.fetchall()]
    
     #3) para cada tabla, SELECT * y convertir filas a dict
    for tabla in tablas:
        cur.execute(f"SELECT * FROM {tabla};")
        rows = cur.fetchall()

        resultado[tabla] = [dict(r) for r in rows]
    
    return resultado


    


def convertir_a_dataframes(conexion: sqlite3.Connection) -> Dict[str, pd.DataFrame]:
    """
    Extrae los datos de la base de datos a DataFrames de pandas

    Args:
        conexion (sqlite3.Connection): Conexión a la base de datos SQLite

    Returns:
        Dict[str, pd.DataFrame]: Diccionario con DataFrames para cada tabla y para
        consultas combinadas relevantes
    """
    # Implementa aquí la extracción de datos a DataFrames:
    # 1. Crea un diccionario vacío para los DataFrames
    # 2. Obtén la lista de tablas de la base de datos
    # 3. Para cada tabla, crea un DataFrame usando pd.read_sql_query
    # 4. Añade consultas JOIN para relaciones importantes:
    #    - Ventas con información de productos
    #    - Ventas con información de vendedores
    #    - Vendedores con regiones
    # 5. Retorna el diccionario con todos los DataFrames

    # 1. Crea un diccionario vacío para los DataFrames
    dfs: Dict[str, pd.DataFrame] = {}

    # 2. lista las tablas
    tablas_df = pd.read_sql_query("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name;
    """, conexion)
    tablas = tablas_df["name"].tolist()

    # 3) DataFrame por tabla
    for tabla in tablas:
        dfs[tabla] = pd.read_sql_query(f"SELECT * FROM {tabla};", conexion)

    # Helper: comprobar si existe tabla y columna (para JOINs “seguros”)
    def table_exists(t: str) -> bool:
        return t in dfs

    def col_exists(t: str, c: str) -> bool:
        return table_exists(t) and c in dfs[t].columns

    # 4) JOINs relevantes (los intentamos crear de forma flexible)
    # Asumimos nombres típicos. Si tu BD usa otros, ajusta los campos.
    # - ventas con productos: ventas.producto_id = productos.id
    if table_exists("ventas") and table_exists("productos"):
        if col_exists("ventas", "producto_id") and (col_exists("productos", "id") or col_exists("productos", "producto_id")):
            productos_pk = "id" if col_exists("productos", "id") else "producto_id"
            q = f"""
                SELECT v.*, p.*
                FROM ventas v
                LEFT JOIN productos p
                  ON v.producto_id = p.{productos_pk};
            """
            dfs["ventas_productos"] = pd.read_sql_query(q, conexion)

    # - ventas con vendedores: ventas.vendedor_id = vendedores.id
    if table_exists("ventas") and table_exists("vendedores"):
        if col_exists("ventas", "vendedor_id") and (col_exists("vendedores", "id") or col_exists("vendedores", "vendedor_id")):
            vendedores_pk = "id" if col_exists("vendedores", "id") else "vendedor_id"
            q = f"""
                SELECT v.*, ve.*
                FROM ventas v
                LEFT JOIN vendedores ve
                  ON v.vendedor_id = ve.{vendedores_pk};
            """
            dfs["ventas_vendedores"] = pd.read_sql_query(q, conexion)

    # - vendedores con regiones: vendedores.region_id = regiones.id
    if table_exists("vendedores") and table_exists("regiones"):
        if col_exists("vendedores", "region_id") and (col_exists("regiones", "id") or col_exists("regiones", "region_id")):
            regiones_pk = "id" if col_exists("regiones", "id") else "region_id"
            q = f"""
                SELECT ve.*, r.*
                FROM vendedores ve
                LEFT JOIN regiones r
                  ON ve.region_id = r.{regiones_pk};
            """
            dfs["vendedores_regiones"] = pd.read_sql_query(q, conexion)

    return dfs


if __name__ == "__main__":
    try:
        # Conectar a la base de datos existente
        print("Conectando a la base de datos...")
        conexion = conectar_bd()
        print("Conexión establecida correctamente.")

        # Verificar la conexión mostrando las tablas disponibles
        cursor = conexion.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = cursor.fetchall()
        print(f"\nTablas en la base de datos: {[t[0] for t in tablas]}")

        # Conversión a JSON
        print("\n--- Convertir datos a formato JSON ---")
        datos_json = convertir_a_json(conexion)
        print("Estructura JSON (ejemplo de una tabla):")
        if datos_json:
            # Muestra un ejemplo de la primera tabla encontrada
            primera_tabla = list(datos_json.keys())[0]
            print(f"Tabla: {primera_tabla}")
            if datos_json[primera_tabla]:
                print(f"Primer registro: {datos_json[primera_tabla][0]}")

            # Opcional: guardar los datos en un archivo JSON
            # ruta_json = os.path.join(os.path.dirname(__file__), 'ventas_comerciales.json')
            # with open(ruta_json, 'w', encoding='utf-8') as f:
            #     json.dump(datos_json, f, ensure_ascii=False, indent=2)
            # print(f"Datos guardados en {ruta_json}")

        # Conversión a DataFrames de pandas
        print("\n--- Convertir datos a DataFrames de pandas ---")
        dataframes = convertir_a_dataframes(conexion)
        if dataframes:
            print(f"Se han creado {len(dataframes)} DataFrames:")
            for nombre, df in dataframes.items():
                print(f"- {nombre}: {len(df)} filas x {len(df.columns)} columnas")
                print(f"  Columnas: {', '.join(df.columns.tolist())}")
                print(f"  Vista previa:\n{df.head(2)}\n")

    except sqlite3.Error as e:
        print(f"Error de SQLite: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conexion' in locals() and conexion:
            conexion.close()
            print("\nConexión cerrada.")
