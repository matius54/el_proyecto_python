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
ASCENDANT = ('ASC','asc',0,'ascendant','ascendente')
DESCENDANT = ('DESC','desc',1,'descendant','descendente')
LIMIT = ('LIM','lim','limit','limite')
OFFSET = ('OFFSET','OFF','offs','offset')
ORDERBY = ('ORDER BY','order','orderBy','orderby','order_by')
ORDER = ('order','ORDER')
ID = ('id','Id','ID')
INFO = ('info','Info')
USER_TYPE = ('usertype','user_type','type')
SEARCH = ('s','search','buscar')

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

    def userinfo(session, uri):
        user = json_in_list(uri,USER)
        info = json_in_list(uri,INFO)
        userType = json_in_list(uri,USER_TYPE)
        limit = json_in_list(uri,LIMIT)
        offset = json_in_list(uri,OFFSET)
        orderBy = json_in_list(uri,ORDERBY)
        order = json_in_list(uri,ORDER)

        user = user.split(',')
        info = info.split(',')

        list = []

        for u in user:
            u = validate.user(u)
            if u is not None: list.append(u)
        user = list.copy()
        list.clear()

        for i in info:
            if i is not None: list.append(i.strip())
        info = list.copy()
        list.clear()

        #verificar cada uno de los elementos de info sean validos
        if list_in_list(info,ID): list.append(ID[0])
        if list_in_list(info,USER): list.append(USER[0])
        if list_in_list(info,FIRSTNAME): list.append(FIRSTNAME[0])
        if list_in_list(info,LASTNAME): list.append(LASTNAME[0])
        if list_in_list(info,ACCESS): list.append(ACCESS[0])
        if list_in_list(info,CREATED_AT): list.append(CREATED_AT[0])
        info = list.copy()
        list.clear()

        

        print(user)
        print(info)
        return (user,info) 

def test():
    test = []
    test.append(validate.private({"x":"NNHUYNDPJAVVEN2H"}))
    test.append(validate.key({"k":"123456"}))
    if None not in test:
        print("test pasado")
        print(test)

json_uri_test = {
"user": "user, user, user",
"info": "id,u,fn,ln,a,ca",
"limit": "101",
"offset": "1",
"orderby": "id",
"order": "asc",
"nmms": "a"
}

print(validate.userinfo("xd",json_uri_test))
# print(validate.user({"u":"soy subnormal"}))