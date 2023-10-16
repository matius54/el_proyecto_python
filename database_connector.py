import mysql.connector
from urllib.parse import quote, urlparse, parse_qs, unquote
import base64
import os

DB_NAME = 'db1'
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASS = ''
DB_PORT = 3306

# esta es la estructura en sql anidado de todas las tablas dentro de la bases de datos
# se usa por la funcion initialize_all_tables() en caso de que sea necesario volver a crear las tablas
# si la cambias solo tendra efecto al crear de nuevo la tabla afectada



TABLES_STRUCTURE = {
    'user': [
        ('id', 'BIGINT AUTO_INCREMENT PRIMARY KEY'),
        ('private', 'CHAR(16) NOT NULL UNIQUE'),
        ('username', 'VARCHAR(64) NOT NULL UNIQUE'),
        ('first_name', 'VARCHAR(64)'),
        ('last_name', 'VARCHAR(64)'),
        ('access_lvl', 'TINYINT NOT NULL DEFAULT 0'),
        ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    ],
    'session_token': [
        ('id', 'BIGINT AUTO_INCREMENT PRIMARY KEY'),
        ('user_id', 'BIGINT'),
        ('FOREIGN KEY (user_id)', 'REFERENCES user(id)'),
        ('token', 'CHAR(64) NOT NULL UNIQUE'),
        ('created_at','TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    ],
    'event_in': [
        ('id', 'BIGINT AUTO_INCREMENT PRIMARY KEY'),
        ('user_id', 'BIGINT'),
        ('FOREIGN KEY (user_id)', 'REFERENCES user(id)'),
        ('created_at','TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    ],
    'event_out': [
        ('id', 'BIGINT AUTO_INCREMENT PRIMARY KEY'),
        ('event_in_id', 'BIGINT NOT NULL UNIQUE'),
        ('user_id', 'BIGINT'),
        ('FOREIGN KEY (user_id)', 'REFERENCES user(id)'),
        ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    ]
}

def connect(database = True):
    if database:
        return mysql.connector.connect(database=DB_NAME,host=DB_HOST,user=DB_USER,password=DB_PASS,port=DB_PORT)
    return mysql.connector.connect(host=DB_HOST,user=DB_USER,password=DB_PASS,port=DB_PORT)

def create():
    db = connect(database=False)
    mycursor = db.cursor()
    mycursor.execute(f"CREATE DATABASE {DB_NAME}")
    mycursor.fetchone()
    mycursor.close()
    db.close()
    db = connect()
    print(f"base de datos '{DB_NAME}' creada exitosamente.")
    return db

class database():
    def __enter__(self):
        try:
            self.db = connect()
            return self.db
        except mysql.connector.Error as err:
            # si la base de datos no existe la crea
            if err.errno == 1049:
                return create()
                # si hay otro error, termina la ejecucion
            else:
                print(f"error, no se pudo conectar con la base de datos: {err}")
                exit(1)
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

class cursor():
    def __init__(self, db):
        self.db = db
    def __enter__(self):
        self.cursor = self.db.cursor()
        return self.cursor
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.cursor.close()
        except mysql.connector.errors.InternalError as Err:
            if Err.msg == 'Unread result found':
                print("Error en db_cursor() --> cursor.close(), se te olvido usar el fetchall() >:V")
                self.cursor.fetchone()
                self.cursor.close()
            else:
                print("error desconocido en db_cursor() --> cursor.close()")
                print(Err)

class connection():
    def __enter__(self):
        try:
            self.db = connect()
        except mysql.connector.Error as err:
            # si la base de datos no existe la crea
            if err.errno == 1049:
                self.db = create()
                # si hay otro error, termina la ejecucion
            else:
                print(f"error, no se pudo conectar con la base de datos: {err}")
                exit(1)
        self.cursor = self.db.cursor()
        return self.db, self.cursor
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.cursor.close()
        except mysql.connector.errors.InternalError as Err:
            if Err.msg == 'Unread result found':
                print("Error en db_cursor() --> cursor.close(), se te olvido usar el fetchall() >:V")
                self.cursor.fetchone()
                self.cursor.close()
            else:
                print("error desconocido en db_cursor() --> cursor.close()")
                print(Err)
        self.db.close()

def execute(sql_query, sql_values=(), commit=False):
    with connection() as (database, cursor):
        cursor.execute(sql_query,sql_values)
        result = cursor.fetchall()
    if commit: database.commit()
    return result

def initialize_all_tables():
    with connection() as (database, cursor):
        for tabla, campos in TABLES_STRUCTURE.items():
            try:
                # Verificar si la tabla existe
                cursor.execute(f"SELECT 1 FROM {tabla} LIMIT 1")
                cursor.fetchone()
            except mysql.connector.Error as err:
                if err.errno == 1146:  # Codigo de error para "tabla no encontrada"
                    # La tabla no existe, crearla
                    query = f"CREATE TABLE {tabla} ({', '.join([f'{campo[0]} {campo[1]}' for campo in campos])})"
                    cursor.execute(query)
                    print(f"Tabla '{tabla}' creada exitosamente.")
                else:
                    # Ocurrio otro error, manejarlo según tus necesidades
                    print(f"Error al verificar la tabla '{tabla}': {err}")
            else:
                # La tabla ya existe
                print(f"La tabla '{tabla}' ya existe.")
        # Confirmar los cambios y cerrar la conexión
        database.commit()

initialize_all_tables()