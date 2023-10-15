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
        elif url.path == START_API_SERVER_AT + TEST or url.path.startswith(START_API_SERVER_AT + TEST + '/') or url.path.startswith(START_API_SERVER_AT + TEST + '?'):
            url_params = unquote(url.path.replace(START_API_SERVER_AT + TEST,'')).split('/')[1:]
            self.send_response(HTTPStatus.OK)
            self.send_json({
                f"parametros de URL (relativos a '{TEST}')":{index: value for index, value in enumerate(url_params)},
                'parametros de URI o query':uri_params
                })
            errores = 'no'
        elif url.path.startswith(START_API_SERVER_AT + USERINFO + '/'):
            url_params = unquote(url.path.replace(START_API_SERVER_AT + USERINFO,'')).split('/')[1:]
            session_token = url_params[0]
            session_token = validate.session(session_token)
            userType = validate.userType(uri_params)
            userL = validate.userList(uri_params,userType)
            infoL = validate.infoList(uri_params)
            orderBy = validate.orderBy(uri_params)
            order = validate.order(uri_params)
            limit = validate.limit(uri_params)
            offset = validate.offset(uri_params)
            self.send_response(HTTPStatus.OK)
            try:
                result = userinfo(session_token, userL, infoL, userType, orderBy, order, limit, offset)
                if result is not None:
                    self.send_response(HTTPStatus.OK)
                    self.send_json(result)
                else:
                    self.send_response(HTTPStatus.UNAUTHORIZED)
                    self.end_headers()
            except:
                self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
                self.end_headers()
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
