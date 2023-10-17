from database_connector import execute, TABLES_STRUCTURE

# USERINFO = '/userinfo' # GET
# TEST = '/test' # GET
# LOGIN = '/login' # POST
# LOGOUT = '/logout' # POST
# REGISTER = '/register' # POST
# UNREGISTER = '/unregister' # POST

BASE32_CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
UNALLOWED_CHARSET_IN_NAMES = ","

#limits
NAMES_MAX_LENGTH = 64
NAMES_MIN_LENGTH = 0
SESSION_LENGTH = 64
PRIVATE_LENGTH = 16
KEY_LENGTH = 6
ACCESS_MIN_VALUE = -1
ACCESS_MAX_VALUE = 3
LIMIT_MIN = 0
LIMIT_MAX = 1000
OFFSET_MIN = 0
OFFSET_MAX = 1000

# el primer elemento de algunas de las lista es como
# esta definido por defecto en las tablas de la base de datos sql
# el segundo elemento de algunas tablas esta definido como el
# default que se usara en las respuestas de los json
# (por ahora solo usado en userinfo)


DB_NULL = None
ALLOWED_NULLS = ("null","NULL","Null","nulo","",None)

# list verify
USER_TYPE = ('usertype','user_type','type')
INFO = ('info','Info')
SEARCH = ('s','search','buscar')
KEY = ('k','key','totp','pass')

        # Database tables
    #user
ID =        (TABLES_STRUCTURE['user'][0][0],'id','ID','Id')
PRIVATE =   (TABLES_STRUCTURE['user'][1][0],'x','X','qr','secreto')
USER =      (TABLES_STRUCTURE['user'][2][0],'u','user','usuario')
FIRSTNAME = (TABLES_STRUCTURE['user'][3][0],'fn','name','firstname','nombre')
LASTNAME =  (TABLES_STRUCTURE['user'][4][0],'ln','lastname','apellido')
ACCESS =    (TABLES_STRUCTURE['user'][5][0],'a','access','acceso')
CREATED_AT = (TABLES_STRUCTURE['user'][6][0],'ca','fecha_de_creacion')
    #session_token
SESSION =   (TABLES_STRUCTURE['session_token'][3][0],'s','session','sesion')

# SQL Database
ALL = ('ALL','all','All','todo')
ASCENDANT = ('ASC','asc','ascendant','ascendente')
DESCENDANT = ('DESC','desc','descendant','descendente')
LIMIT = ('LIMIT','lim','limit','limite')
OFFSET = ('OFFSET','OFF','offs','offset')
ORDERBY = ('ORDER BY','orderBy','orderby','order_by')
ORDER = ('ORDER','order')

# default values
LIMIT_DEFAULT = 100
OFFSET_DEFAULT = 0
ORDERBY_DEFAULT = ID[0]
ORDER_DEFAULT = DESCENDANT[0]
USER_TYPE_DEFAULT = ID[0]

# userinfo
INFO_FOR_USER = ((ID[0],ID),(USER[0],USER),(FIRSTNAME[0],FIRSTNAME),(LASTNAME[0],LASTNAME),(ACCESS[0],ACCESS),(CREATED_AT[0],CREATED_AT))
USERINFO_JSON = {v[0] : v[1][1] for v in INFO_FOR_USER}
ITEMS = 'items'
ITEM_COUNT = 'item_count'
LOCAL_TIME = 'local_time'

def json_in_list(json,list):
    # esta funcion como su nombre lo indica,
    # busca por cada elemento de la lista una
    # clave valida en el json, y si la encuentra
    # retorna el valor del json
    for key in list:
        try:
            return str(json[key]).strip()
        except KeyError:
            continue
        except TypeError:
            try:
                return str(json).strip()
            except:
                break
    return None

def CheckNull(data):
    # recibe un string que puede ser Nulo
    # y busca similitudes en una lista ALLOWED_NULLS
    if data is None or data in ALLOWED_NULLS:
        #Si es Nulo retorna Nulo
        return None
    else:
        #Si no es Nulo retorna el valor
        return data

# esta clase se encarga de validar todos los tipos de datos
# que entran a travez de json, uri, url, basicamente
# toda la informacion de entrada
class validate():
    def user(json_data):
        data = json_in_list(json_data,USER)
        data = CheckNull(data)
        if data is not None:
            for char in UNALLOWED_CHARSET_IN_NAMES:
                data = data.replace(char,'')
            if len(data) >= NAMES_MIN_LENGTH: 
                return data[:NAMES_MAX_LENGTH]
        return None
        
    def firstname(json_data):
        data = json_in_list(json_data,FIRSTNAME)
        data = CheckNull(data)
        if data is not None:
            for char in UNALLOWED_CHARSET_IN_NAMES:
                data.replace(char,'')
            if len(data) >= NAMES_MIN_LENGTH: 
                return data[:NAMES_MAX_LENGTH]
        return None
    
    def lastname(json_data):
        data = json_in_list(json_data,LASTNAME)
        data = CheckNull(data)
        if data is not None:
            for char in UNALLOWED_CHARSET_IN_NAMES:
                data.replace(char,'')
            if len(data) >= NAMES_MIN_LENGTH: 
                return data[:NAMES_MAX_LENGTH]
        return None

    def key(json_data):
        data = json_in_list(json_data,KEY)
        data = CheckNull(data)
        if data is None:
            return None
        else:
            try:
                data = str(int(data))
                if len(data) == KEY_LENGTH:
                    return data
            except:
                print(f"Fallo verificando formato del key '{data}'")
        return None
    
    def access(json_data):
        data = json_in_list(json_data,ACCESS)
        data = CheckNull(data)
        if data is None:
            return None
        else:
            try:
                access = int(data)
                if access >= ACCESS_MIN_VALUE and access <= ACCESS_MAX_VALUE:
                    return access
            except:
                print(f"Fallo verificando formato del access '{data}'")
        return None

    def session(json_data):
        data = json_in_list(json_data,SESSION)
        if data is None:
            return None
        else:
            if len(data) == SESSION_LENGTH:
                return data
    
    def private(json_data):
        data = json_in_list(json_data,PRIVATE)
        if data is None:
            return None
        else:
            try:
                if len(data) == PRIVATE_LENGTH:
                    for char in data:
                        if char not in BASE32_CHARSET:
                            return None
                    return data
            except:
                return None

    def userList(json_data, userType):
        USERLIST_SQL_QUERY = f"SELECT {userType} FROM user"

        userList = json_in_list(json_data,USER)

        allowed_users = execute(USERLIST_SQL_QUERY)
        if allowed_users: allowed_users = [u[0] for u in allowed_users if u is not None]
        if userList is not None: userList = [validate.user(u) for u in userList.split(',') if u is not None and u.strip() in allowed_users]
        
        return userList
    
    def infoList(json_data):
        infoList = json_in_list(json_data,INFO)

        if infoList is not None:
            infoList = [i.strip() for i in infoList.split(',') if i is not None]
            list = []
            for i in infoList:
                for name_default, list_of_names in INFO_FOR_USER:
                    if i in list_of_names:
                        list.append(name_default)
                        break
            infoList = list.copy()
            list.clear()

        return infoList
    
    def userType(json_data):
        value = json_in_list(json_data,USER_TYPE)
        NewUserType = None
        for name_default, list_of_names in INFO_FOR_USER:
            for l in list_of_names:
                if value == l:
                    NewUserType = name_default
                    break
        return NewUserType if NewUserType is not None else ID[0]
    
    def limit(json_data):
        value = json_in_list(json_data,LIMIT)
        try:
            limit = int(value)
            if limit >= LIMIT_MIN and limit <= LIMIT_MAX:
                return limit
            else:
                return LIMIT_DEFAULT
        except:
            return None

    def offset(json_data):
        value = json_in_list(json_data,OFFSET)
        try:
            offset = int(value)
            if offset >= OFFSET_MIN and offset <= OFFSET_MAX:
                return offset
            else:
                return OFFSET_DEFAULT
        except:
            return None
    
    def orderBy(json_data):
        value = json_in_list(json_data,ORDERBY)
        NewOrderBy = None
        for name_default, list_of_names in INFO_FOR_USER:
            for l in list_of_names:
                if value == l:
                    NewOrderBy = name_default
                    break
        return NewOrderBy or ORDERBY_DEFAULT
    
    def order(json_data):
        value = json_in_list(json_data,ORDER)
        order = None
        if value in ASCENDANT: order = ASCENDANT[0]
        elif value in DESCENDANT: order = DESCENDANT[0]
        order = order or ORDER_DEFAULT
        return order
