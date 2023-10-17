import database_connector as DB
# esta libreria sirve para tener acceso a algunas funciones del sistema, como leer/escribir archivos y ejecutar codigo externo
import os
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
# la clase validate se usara para validar toda la informacion
from validation import validate, USER, ACCESS_MAX_VALUE
# el modelo procesa la mayor parte de la informacion
from model import login, logout, register, unregister, userinfo
# algunas variables para cambiar facilmente

# ajustes del servidor
HOST = 'localhost'
# cambia el puerto de escucha del servidor
DEF_SERVER_PORT = 8080
# cambia la cabecera de respuesta server
SERVER_OBFUSCATION = True
# cambia el nombre en la cabecera de respuesta server, si es None no envia la cabecera
SERVER_NAME = "Not GlassFish"

class default_admin():
    username = 'Admin'
    firstname = 'The Lord'
    lastname = 'Administrator'
    access = ACCESS_MAX_VALUE
    secret = "NNHUYNDPJAVVEN2H"
    # secret = None

# Se usara para autenticar el usuario de arriba, si es None
# se generara una aleatoria y se imprimira en pantalla el primer inicio
# el tiempo que espera en segundos el servidor a que se complete una solicitud
# por defecto 5, si se pasa de ese tiempo se genera un timeout 
CONECTION_TIME_OUT_SECS = 5
# permite que si realizen peticiones desde origenes desconocidos
# o que cualquier pagina pueda usar esta api
ALLOW_CROSS_ORIGIN = True
# punto de inicio del servidor api
START_API_SERVER_AT = 'api'

# direcciones url permitidas para el header de respuesta Access-Control-Allow-Origin para peticiones http a la api.
ALLOWED_URLS = ['*']

# endpoints activos y sus direcciones parametrizadas
USERINFO = 'userinfo' # GET
TEST = 'test' # GET
LOGIN = 'login' # POST
LOGOUT = 'logout' # POST
REGISTER = 'register' # POST
UNREGISTER = 'unregister' # POST

def check_admin_user():
    if not DB.execute(f"SELECT COUNT(*) FROM user")[0][0]:
        try:
            user = validate.user(default_admin.username)
            secret = register(
                session=None,
                user=user,
                firstname=validate.firstname(default_admin.firstname),
                lastname=validate.lastname(default_admin.lastname),
                access=validate.access(default_admin.access),
                secret=validate.private(default_admin.secret),
                override=True
                )
            print(f"\nusuario administrador inicializado correctamente.\n\nusername: '{user}'\nsecret: '{secret}'")
        except Exception as Err:
            print(Err)
            print('\nerror inicializando el usuario administrador\n')
        return

DB.initialize_all_tables()
check_admin_user()

print(f"\nhost seleccionado: '{HOST}', puerto seleccionado: {DEF_SERVER_PORT}")

class MyapiHTTP(BaseHTTPRequestHandler):
    #tiempo de espera en segundos antes de cerrar coneccion por timeout 
    timeout = CONECTION_TIME_OUT_SECS
    #se esta sobreescribiendo el metodo send_response() para opcionalmente
    # no enviar informacion sensible del servidor en las solicitudes
    def send_response(self, code, message=None):
        self.log_request(code)
        self.send_response_only(code, message)
        if SERVER_OBFUSCATION: 
            if SERVER_NAME is not None: self.send_header('Server', SERVER_NAME)
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
        url_params = unquote(urlparse(self.path).path).split('/')[1:]
        uri_params = {v: k[0] for v, k in parse_qs(urlparse(self.path).query).items()}
        if len(url_params) == 1 and url_params[0] == START_API_SERVER_AT:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(bytes("Test, OK", "utf-8"))
        elif url_params[1] == TEST:
            self.send_response(HTTPStatus.OK)
            self.send_json({
                f"parametros de URL (relativos a '{TEST}')":{index: value for index, value in enumerate(url_params[2:])},
                'parametros de URI o query':uri_params
                })
        elif url_params[1] == USERINFO:
            session_token = url_params[2]
            session_token = validate.session(session_token)
            userType = validate.userType(uri_params)
            userL = validate.userList(uri_params,userType)
            infoL = validate.infoList(uri_params)
            orderBy = validate.orderBy(uri_params)
            order = validate.order(uri_params)
            limit = validate.limit(uri_params)
            offset = validate.offset(uri_params)
            try:
                result = userinfo(session_token, userL, infoL, userType, orderBy, order, limit, offset)
                if result is not None:
                    self.send_response(HTTPStatus.OK)
                    self.send_json(result)
                else:
                    self.send_response(HTTPStatus.UNAUTHORIZED)
                    self.end_headers()
            except Exception as Err:
                print(Err)
                self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
                self.end_headers()
        path = os.path.abspath(os.getcwd() + '\App')
        if path.startswith(os.getcwd()+'\App') and not self.path.endswith('.py') and False:
            path = f'{path}{unquote(self.path).replace("/", os.path.sep)}'
            try:
                with open(path,'rb') as file:
                    content = file.read()
                    self.send_response(HTTPStatus.OK)
                    self.send_header('Content-type', mimetypes.guess_type(os.path.basename(path))[0]+"; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(content)
            except Exception as Err:
                print(Err)
                print("archivo no encontrado")

    def do_POST(self):
        url_params = unquote(urlparse(self.path).path).split('/')[1:]
        json_data = self.get_json()
        try:
            if len(url_params) >= 1:
                if url_params[1] == REGISTER:
                    session = validate.session(json_data)
                    user = validate.user(json_data)
                    firstname = validate.firstname(json_data)
                    lastname = validate.lastname(json_data)
                    access = validate.access(json_data)
                    result = register(session=session,user=user,firstname=firstname,lastname=lastname,access=access)
                    if result is None:
                        self.send_response(HTTPStatus.UNAUTHORIZED)
                        self.end_headers()
                    else:
                        self.send_response(HTTPStatus.OK)
                        self.send_json({"u":user,"x":result})
                elif url_params[1] == LOGIN:
                    user = validate.user(json_data)
                    totpkey = validate.key(json_data)
                    session_token = login(username = user, key = totpkey)
                    if session_token is None:
                        self.send_response(HTTPStatus.UNAUTHORIZED)
                        self.end_headers()
                    else:
                        self.send_response(HTTPStatus.OK)
                        self.send_json({'s':session_token})
                elif url_params[1] == LOGOUT:
                    session = validate.session(json_data)
                    result = logout(session)
                    if not result:
                        self.send_response(HTTPStatus.UNAUTHORIZED)
                    elif result:
                        self.send_response(HTTPStatus.OK)
                    self.end_headers()
                elif url_params[1] == UNREGISTER:
                    user = validate.user(json_data)
                    totpkey = validate.key(json_data)
                    result = unregister(username=user, key=totpkey)
                    if result:
                        self.send_response(HTTPStatus.OK)
                    else:
                        self.send_response(HTTPStatus.UNAUTHORIZED)
                    self.end_headers()
        except Exception as Err:
            print(Err)
            self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
            self.end_headers()

# print(f'-- {self.client_address[0]} - - [{time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())}] "{self.requestline}" - (Empty HTTP response) Razon: {errores}')
        

server = HTTPServer((HOST, DEF_SERVER_PORT), MyapiHTTP)
print(f"\nRunning api on http://{HOST}:{DEF_SERVER_PORT}/{START_API_SERVER_AT}")
server.serve_forever()
