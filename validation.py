from database_connector import execute

# USERINFO = '/userinfo' # GET
# TEST = '/test' # GET
# LOGIN = '/login' # POST
# LOGOUT = '/logout' # POST
# REGISTER = '/register' # POST
# UNREGISTER = '/unregister' # POST

BASE32_CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
UNALLOWED_CHARSET_IN_NAMES = ","

#limits
ACCESS_MIN_VALUE = -1
ACCESS_MAX_VALUE = 3
NAMES_MAX_LENGTH = 64
SESSION_LENGTH = 64
PRIVATE_LENGTH = 16
KEY_LENGTH = 6
LIMIT_MIN = 0
LIMIT_MAX = 1000
OFFSET_MIN = 0
OFFSET_MAX = 1000

# el primer elemento de algunas de las lista es como
# esta definido por defecto en las tablas de la base de datos sql
#json verify
DB_NULL = None
ALLOWED_NULLS = ("null","NULL","Null","nulo","",None)
ALL = ('all','ALL','All','todo')
USER = ('username','u','user','usuario')
KEY = ('k','key','totp','pass')
ACCESS = ('access_lvl','a','access','acceso')
FIRSTNAME = ('first_name','fn','firstname','nombre')
LASTNAME = ('last_name','ln','lastname','apellido')
SESSION = ('token','s','session','sesion')
PRIVATE = ('private','x','X','qr','secreto')
CREATED_AT = ('created_at','ca','fecha_de_creacion')

#list verify
ASCENDANT = ('ASC','asc','ascendant','ascendente')
DESCENDANT = ('DESC','desc','descendant','descendente')
LIMIT = ('LIMIT','lim','limit','limite')
OFFSET = ('OFFSET','OFF','offs','offset')
ORDERBY = ('ORDER BY','orderBy','orderby','order_by')
ORDER = ('order','ORDER')
ID = ('id','Id','ID')
INFO = ('info','Info')
USER_TYPE = ('usertype','user_type','type')
SEARCH = ('s','search','buscar')

#default values
LIMIT_DEFAULT = 100
OFFSET_DEFAULT = 0
ORDERBY_DEFAULT = ID[0]
ORDER_DEFAULT = DESCENDANT[0]
USER_TYPE_DEFAULT = ID[0]

INFO_FOR_USER = ((ID[0],ID),(USER[0],USER),(FIRSTNAME[0],FIRSTNAME),(LASTNAME[0],LASTNAME),(ACCESS[0],ACCESS),(CREATED_AT[0],CREATED_AT))

USERINFO_JSON = {
    ID[0]: 'id',
    USER[0]: 'u',
    FIRSTNAME[0]: 'fn',
    LASTNAME[0]: 'ln',
    ACCESS[0]: 'a',
    CREATED_AT[0]: 'ca'
    }

#all_items = [ALL[0],USER[0],KEY[0],ACCESS[0],FIRSTNAME[0],LASTNAME[0],SESSION[0],PRIVATE[0],CREATED_AT[0],LIMIT[0],OFFSET[0]]

def json_in_list(json,list):
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

def list_in_list(list,list_to_find):
    for l in list:
        if l in list_to_find:
            return True
    return False

def CheckNull(data):
    if data is None or data in ALLOWED_NULLS:
        #Si es Nulo retorna Nulo
        return None
    else:
        #Si no es Nulo retorna el valor
        return data

class validate():
    def user(json_data):
        data = json_in_list(json_data,USER)
        data = CheckNull(data)
        if data is None:
            return None
        else:
            for char in UNALLOWED_CHARSET_IN_NAMES:
                data = data.replace(char,'')
            return data[:NAMES_MAX_LENGTH]
        
    def firstname(json_data):
        data = json_in_list(json_data,FIRSTNAME)
        data = CheckNull(data)
        if data is None:
            return None
        else:
            for char in UNALLOWED_CHARSET_IN_NAMES:
                data.replace(char,'')
            return data[:NAMES_MAX_LENGTH]
    
    def lastname(json_data):
        data = json_in_list(json_data,LASTNAME)
        data = CheckNull(data)
        if data is None:
            return None
        else:
            for char in UNALLOWED_CHARSET_IN_NAMES:
                data.replace(char,'')
            return data[:NAMES_MAX_LENGTH]

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
        userList = [validate.user(u) for u in userList.split(',') if u is not None and u.strip() in allowed_users]
        
        return userList
    
    def infoList(json_data):
        infoList = json_in_list(json_data,INFO)

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

        return NewUserType or ID[0]
    
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

def test():
    test = []
    test.append(validate.private({"x":"NNHUYNDPJAVVEN2H"}))
    test.append(validate.key({"k":"123456"}))
    if None not in test:
        print("test pasado")
        print(test)

json_uri_test = {
"user": "Admin, user, user, Marcos, Franchezco, virgolimi, fieaaauu, la maquina mas veloz, de tote, italie, fiiii",
"usertype":"user",
"info": "fn,id,u,ln,a,ca",
"limit": "101",
"offset": "1",
"orderby": "fn",
"order": 'ascendente',
"nmms": "a"
}

# print(validate.user({"u":"soy subnormal"}))
