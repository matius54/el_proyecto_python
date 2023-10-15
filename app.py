import database_connector as DB
# libreria base64 para generar contrasenas codificar y decodificar
import base64
# esta libreria sirve para tener acceso a algunas funciones del sistema, como leer/escribir archivos y ejecutar codigo externo
import os
# libreria para verificar codigos otp
from pyotp import TOTP as totp
# libreria para saber el tiempo local del sistema
import time
# libreria para poner el codigo de estado escrito en lugar del 20 o 404
from http import HTTPStatus
# libreria encargada de recibir y administrar las solicitudes http para la api y el servidor
from http.server import HTTPServer, BaseHTTPRequestHandler
# ayuda a convertir extraer y en general administrar informacion y paramentros en las url
from urllib.parse import quote, urlparse, parse_qs, unquote
# para codificar y decodificar formato json muy importante para la api, ya que casi todos los datos se codifican en estes formato
import json
# este sive para deducir el tipo de archivo en http, a partir de su formato, al enviar datos por http deber incluir el formato de lo que estas enviando
import mimetypes
# ngrok esta aqui para utilizar https de la mejor forma posible, gracias ngrok por existir
# from pyngrok import ngrok
# random para generar las tokens de acceso (por ahora)
from validation import validate

from model import login, logout, register, unregister, userinfo

# algunas variables para cambiar facilmente
# ngrok.set_auth_token("23A0NOBgyrOJiOsFigeCZ8jzHu8_7it8m6QLYw8DGDuiZUSoH")

# ajustes del servidor
DEF_SERVER_PORT = 8080
SERVER_OBFUSCATION = True
SERVER_NAME = None
SERVER_DEFAULT_ADMIN_USER = {
    'username'   : 'Admin',
    'firstname'  : 'The Lord',
    'lastname'   : 'Administrator',
    'access_lvl' : 3
}
SERVER_TOTP_SECRET = None
CONECTION_TIME_OUT_SECS = 5
ALLOW_CROSS_ORIGIN = True
START_API_SERVER_AT = '/api'

# direcciones url permitidas para el header de respuesta Access-Control-Allow-Origin para peticiones http a la api.
ALLOWED_URLS = ['*']

# endpoints activos
USERINFO = '/userinfo' # GET
TEST = '/test' # GET
LOGIN = '/login' # POST
LOGOUT = '/logout' # POST
REGISTER = '/register' # POST
UNREGISTER = '/unregister' # POST

# diccionario para convertir de argumento api a base de datos en USERINFO.
REPLACE_API_DB={
    'u':'username',
    'id':'id',
    'fn':'first_name',
    'ln':'last_name',
    'a':'access_lvl',
    'ca':'created_at'
}
# diccionario inverso con el mismo proposito, pero de base de datos a api.
REPLACE_API_DB_R = {v: k for k, v in REPLACE_API_DB.items()}

# esta es la estructura en sql anidado de todas las tablas dentro de la bases de datos
# se usa por la funcion initialize_all_tables() en caso de que sea necesario volver a crear las tablas
# si la cambias solo tendra efecto al crear de nuevo la tabla afectada

HOST = 'localhost'

print(f"puerto seleccionado = {DEF_SERVER_PORT}")

class MyapiHTTP(BaseHTTPRequestHandler):
    #tiempo de espera en segundos antes de cerrar coneccion por timeout 
    timeout = CONECTION_TIME_OUT_SECS
    #se esta sobreescribiendo el metodo send_response() para no enviar informacion sensible del servidor en las solicitudes
    def send_response(self, code, message=None):
        self.log_request(code)
        self.send_response_only(code, message)
        if SERVER_OBFUSCATION: self.send_header('Server', SERVER_NAME or 'Not GlassFish')
        else: self.send_header('Server', self.version_string())
        self.send_header('Date', self.date_time_string())

        #Esto solo soluciona las solicitudes GET
        if ALLOW_CROSS_ORIGIN: self.send_header('Access-Control-Allow-Origin','*')

    def send_json(self, value):
        try:
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.send_header("Content-Length",len(json.dumps(value)))
            self.end_headers()
            self.wfile.write(json.dumps(value).encode())
            #self.log_request(HTTPStatus.CONTINUE)
            return True
        except Exception as Err:
            print('Error codificando JSON')
            print(Err)
            return False

    def get_json(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            return json.loads(post_data.decode('utf-8'))
        except Exception as Err:
            print('Error decodificando JSON')
            print(Err)

    def is_cgi(self):
        self.send_error(HTTPStatus.UNAUTHORIZED, "Acceso denegado")
        return False

    def do_OPTIONS(self):
        #Esto solo soluciona las solicitudes OPTIONS y POST
        if ALLOW_CROSS_ORIGIN:
            self.send_response(HTTPStatus.OK)
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS, POST')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_GET(self):
        errores='Recurso No Encontrado 404'
        url = urlparse(self.path)
        uri_params = None
        try:
            uri_params = {v: k[0] for v, k in parse_qs(url.query).items()}
        except Exception as Err:
            print(Err)
            print('Error extrayendo parametros uri de la url')
        if url.path == START_API_SERVER_AT:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(bytes("Test, OK", "utf-8"))
            errores = 'no'
        elif url.path.startswith(START_API_SERVER_AT + USERINFO + '/'):
            url_params = unquote(url.path.replace(START_API_SERVER_AT + USERINFO,'')).split('/')[1:]
            user_session = url_params[0]
            try:
                with DB.connection() as (database, cursor):
                    cursor.execute("SELECT user_id FROM session_token WHERE token = %s",(user_session[:64],))
                    user_id = int(cursor.fetchone()[0])
                    cursor.execute(f"SELECT username,access_lvl FROM user WHERE id = {user_id}")
                    res = cursor.fetchone()
                    username = res[0]
                    access_level = int(res[1])
                    cursor.execute("SELECT username,access_lvl,id FROM user LIMIT 1000")
                    res = cursor.fetchall()
                    all_users = [user[0] for user in res]
                    all_users_levels_ids={r[0]:{'level':int(r[1]),'id':int(r[2])} for r in res}
                    all_id_users={all_users_levels_ids[user]['id'] : user for user in all_users}
                    users = []
                    users_errs = []
                    info = []
                    info_parse = []
                    parse_errs = []
                    response = {}
                    try:
                        users = uri_params['user'].split(',')
                        if uri_params['user'].lower()=='all':
                            users.clear()
                            users.append(username)
                            if access_level>0:
                                for user in all_users:
                                    # si tu nivel de acceso es mayor a uno o a algun usuario, se añade a tu lista
                                    if access_level > all_users_levels_ids[user]['level'] and user not in users:
                                        users.append(user)
                    except:
                        #si no incluyes ningun username se añade el username de quien realiza la consulta
                        users.clear()
                        users.append(username)
                    try:
                        info = uri_params['info'].split(',')
                    except:
                        #si no incluyes la info se añade toda la disponible
                        info = ['id','u','fn','ln','a','ca']
                    for inf in info:
                        try:
                            if REPLACE_API_DB[inf] not in info_parse:
                                info_parse.append(REPLACE_API_DB[inf])
                        except Exception as Err:
                            parse_errs.append(inf)
                    for user in users:
                        try:
                            users[users.index(user)]=all_id_users[int(user)]
                        except Exception as Err:
                            user
                    for user in users:
                        if user not in all_users:
                            users_errs.append(user)
                    users = [user for user in users if user in all_users]
                    if not bool(users):users.append(username)
                    print(f"En la solicitud de usuario '{username}' al endpoint '{USERINFO}'\nlos argumentos de info '{parse_errs}' y user '{users_errs}' fueron ignorados\nY los argumentos de info '{info_parse}' y user {users} fueron aceptados")
                    try:
                        db_limit = abs(int(uri_params['limit']))
                    except:
                        db_limit = 100
                    try:
                        db_offset = abs(int(uri_params['offset']))
                    except:
                        db_offset = 0
                    sql_query=(f"SELECT {', '.join([f'{q}' for q in info_parse])} FROM user WHERE " + (' OR '.join([f"username = '{user}'"for user in users]))+f" ORDER BY id LIMIT {db_limit} OFFSET {db_offset}")
                    cursor.execute(sql_query)
                    result = cursor.fetchall()
                    for row_index, row in enumerate(result):
                        response[row_index + db_offset] = {}
                        for column_index, value in enumerate(row):
                            column_name = cursor.column_names[column_index]
                            if column_name != 'created_at':
                                response[row_index + db_offset][REPLACE_API_DB_R[column_name]] = value
                            else:
                                response[row_index + db_offset][REPLACE_API_DB_R[column_name]] = value.isoformat()
                    self.send_response(HTTPStatus.OK)
                    self.send_json(response)
                    errores = 'no'
            except Exception as Err:
                print(Err)
                self.send_error(HTTPStatus.UNAUTHORIZED)
                self.end_headers()
                errores = 'Token de sesion no existe en base de datos'

        elif url.path == START_API_SERVER_AT + TEST or url.path.startswith(START_API_SERVER_AT + TEST + '/') or url.path.startswith(START_API_SERVER_AT + TEST + '?'):
            url_params = unquote(url.path.replace(START_API_SERVER_AT + TEST,'')).split('/')[1:]
            self.send_response(HTTPStatus.OK)
            self.send_json({
                f"parametros de URL (relativos a '{TEST}')":{index: value for index, value in enumerate(url_params)},
                'parametros de URI o query':uri_params
                })
            errores = 'no'
        elif self.path == '/web' or self.path == '/web/' or self.path == '/':
            self.send_response(HTTPStatus.MOVED_PERMANENTLY)
            self.send_header('Location', '/web/index.html')
            self.end_headers()
            print(f"\t--- redireccionado correctamente ---\n'{self.path}' --> '/web/index.html'")
            errores = 'no'
        path = os.path.abspath(os.getcwd() + '\App')
        if path.startswith(os.getcwd()+'\App') and not self.path.endswith('.py') and errores == 'Recurso No Encontrado 404':
            path = f'{path}{unquote(self.path).replace("/", os.path.sep)}'
            try:
                with open(path,'rb') as file:
                    content = file.read()
                    self.send_response(HTTPStatus.OK)
                    self.send_header('Content-type', mimetypes.guess_type(os.path.basename(path))[0]+"; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(content)
                    errores = 'no'
            except Exception as Err:
                print(Err)
                print("archivo no encontrado")
        if(errores!='no'):print(f'{self.client_address[0]} - - [{time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())}] "{self.requestline}" - (Empty HTTP response) Razon: {errores}')
    def do_POST(self):
        errores='Recurso No Encontrado 404'
        if urlparse(self.path).path == START_API_SERVER_AT + REGISTER:
            json_data = self.get_json()
            session = validate.session(json_data)
            user = validate.user(json_data)
            firstname = validate.firstname(json_data)
            lastname = validate.lastname(json_data)
            access = validate.access(json_data)
            try:
                result = register(session=session,user=user,firstname=firstname,lastname=lastname,access=access)
                if result is None:
                    self.send_response(HTTPStatus.UNAUTHORIZED)
                    self.end_headers()
                else:
                    self.send_json({"u":user,"x":result})
            except Exception as Err:
                print(Err)
                self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
                self.end_headers()
        elif urlparse(self.path).path == START_API_SERVER_AT + LOGIN:
            json_data = self.get_json()
            try:
                user = validate.user(json_data)
                totpkey = validate.key(json_data)
                session_token = login(username = user, key = totpkey)
                if session_token is None:
                    self.send_response(HTTPStatus.UNAUTHORIZED)
                    self.end_headers()
                else:
                    self.send_response(HTTPStatus.OK)
                    self.send_json({'s':session_token})
            except Exception as Err:
                print(Err)
                self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
                self.end_headers()
        elif urlparse(self.path).path == START_API_SERVER_AT + LOGOUT:
            json_data = self.get_json()
            try:
                session = validate.session(json_data)
                result = logout(session)
                if not result:
                    self.send_response(HTTPStatus.UNAUTHORIZED)
                elif result:
                    self.send_response(HTTPStatus.OK)
            except Exception as Err:
                print(Err)
                self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
            self.end_headers()
        elif urlparse(self.path).path == START_API_SERVER_AT + UNREGISTER:
            json_data = self.get_json()
            user = validate.user(json_data)
            totpkey = validate.key(json_data)
            with DB.connection() as (database, cursor):
                try:
                    result = unregister(username=user, key=totpkey)
                    if result:
                        self.send_response(HTTPStatus.OK)
                    else:
                        self.send_response(HTTPStatus.UNAUTHORIZED)
                except Exception as Err:
                    print(Err)
                    self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
            self.end_headers()
        if(errores!='no'):print(f'-- {self.client_address[0]} - - [{time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())}] "{self.requestline}" - (Empty HTTP response) Razon: {errores}')
        

server = HTTPServer((HOST, DEF_SERVER_PORT), MyapiHTTP)
print(f"Running api on http://{HOST}:{DEF_SERVER_PORT}{START_API_SERVER_AT}")
print(f"Running webpage on http://{HOST}:{DEF_SERVER_PORT}/web/index.html")
print(f"Running cdn on http://{HOST}:{DEF_SERVER_PORT}/cdn")
server.serve_forever()
