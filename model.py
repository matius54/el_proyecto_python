import database_connector as db
from pyotp import TOTP as totp
import base64
import os
from datetime import datetime
import validation

class DBHelp():
    def isDuplicated(cursor,sqlquery,value):
        cursor.execute(sqlquery,value)
        if (int(cursor.fetchone()[0])==0):
            False
        else:
            True

    def getIdFromUser(cursor,user):
        cursor.execute(f"SELECT {validation.ID[0]} FROM user WHERE {validation.USER[0]} = %s",(user,))
        result=cursor.fetchone()
        return int(result[0])
    
    def getSessionFromUser(cursor,user):
        cursor.execute(f"SELECT {validation.SESSION[0]} FROM session_token JOIN user ON user.id = user_id WHERE {validation.USER[0]} = %s",(user,))
        result = cursor.fetchone()
        if cursor.rowcount == 1:
            return result[0]
        return None

def b64token_gen(length=64):
    token = base64.b64encode(os.urandom(length)).decode('utf-8')
    return token[:length].replace('/', '-').replace('+', '_')
    # CHARS_ALLOWED='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_'
    # return ''.join(random.choice(CHARS_ALLOWED) for _ in range(length))

# funcion encargada de generar una cadena de 16 caracteres aleatoria
def otp_gen():
    # Generar una cadena aleatoria de 16 bytes
    cadena_bytes = os.urandom(16)
    # Codificar la cadena en base64
    secreto = base64.b64encode(cadena_bytes).decode('utf-8')
    return base64.b32encode(secreto.encode()).decode()[:16]

def totp_user_verify(username,key):
    result = db.execute("SELECT private FROM user WHERE username = %s",(username,))
    # "list index out of range" si el usuario no existe en la base de datos
    if result: return totp(result[0][0]).verify(key)
    return False

def login(payload):
    username, key = payload
    LOGIN_COUNT_SESSION = f"SELECT COUNT(*) FROM session_token WHERE {validation.SESSION[0]} = %s"
    LOGIN_INSERT_SESSION = f"INSERT INTO session_token (user_id, {validation.SESSION[0]}) VALUES (%s, %s)"
    if totp_user_verify(username,key):
        with db.connection() as (database, cursor):
            session_token = DBHelp.getSessionFromUser(cursor,username)
            if session_token is None:
                while True:
                    session_token=b64token_gen()
                    if not DBHelp.isDuplicated(cursor,LOGIN_COUNT_SESSION,(session_token,)):
                        break
                id_user = DBHelp.getIdFromUser(cursor,username)
                cursor.execute(LOGIN_INSERT_SESSION, (id_user,session_token))
                database.commit()
            return session_token
    return None

def logout(payload):
    session = payload
    SESSION_JOIN_USERNAME_TOKEN = f"SELECT {validation.USER[0]} FROM user JOIN session_token ON user_id = user.id WHERE {validation.SESSION[0]} = %s"
    SESSION_DELETE_SESSION = f"DELETE FROM session_token WHERE {validation.SESSION[0]} = %s"
    with db.connection() as (database, cursor):
        cursor.execute(SESSION_JOIN_USERNAME_TOKEN,(session,))
        result = cursor.fetchone()
        if result is not None:
            username = result[0]
            cursor.execute(SESSION_DELETE_SESSION, (session,))
            database.commit()
            print(f"{cursor.rowcount} sesion cerrada vinculada al usuario '{username}'")
            if cursor.rowcount > 0:
                return True
    return False

def register(payload, secret=None, override=False):
    session, user, firstname, lastname, access = payload
    REGISTER_GET_ACCES_FROM_TOKEN = f"SELECT {validation.ACCESS[0]} FROM user JOIN session_token ON user_id = user.id WHERE {validation.SESSION[0]} = %s"
    REGISTER_TOTP_DUPLICATE_VERIFICATION = f"SELECT COUNT(*) FROM user WHERE {validation.PRIVATE[0]} = %s"
    REGISTER_INSERT = f"INSERT INTO user ({validation.PRIVATE[0]}, {validation.USER[0]}, {validation.ACCESS[0]}, {validation.FIRSTNAME[0]}, {validation.LASTNAME[0]}) VALUES (%s,%s,%s,%s,%s)"
    session = session or None
    newUser = user or None
    newFirstname = firstname or None
    newLastname = lastname or None
    newAccess = access or 0
    otptoken = None
    if (override is not None or session is not None) and newUser:
        with db.connection() as (database, cursor):
            if not override:
                cursor.execute(REGISTER_GET_ACCES_FROM_TOKEN,(session,))
                result = cursor.fetchone()
            else:
                result = (validation.ACCESS_MAX_VALUE + 1,)
            if result is not None:
                access = int(result[0])
                if newAccess < access and newAccess >= validation.ACCESS_MIN_VALUE:
                    while True:
                        otptoken = secret if otptoken is None and secret is not None and override and validation.validate.private(secret) else otp_gen()
                        cursor.execute(REGISTER_TOTP_DUPLICATE_VERIFICATION,(otptoken,))
                        if not int(cursor.fetchone()[0]):
                            break
                    cursor.execute(REGISTER_INSERT,(otptoken,newUser,newAccess,newFirstname,newLastname))
                    database.commit()
                    return otptoken
    return None

def unregister(payload):
    username, key = payload
    UNREGISTER_JOIN_TOKEN_USERNAME = f"SELECT token FROM session_token JOIN user ON user.id = user_id WHERE {validation.USER[0]} = %s"
    UNREGISTER_DELETE_USER = f"DELETE FROM user WHERE {validation.USER[0]} = %s"
    if totp_user_verify(username,key):
        with db.connection() as (database, cursor):
            cursor.execute(UNREGISTER_JOIN_TOKEN_USERNAME,(username,))
            result = cursor.fetchone()
            if result is not None: logout(session = result[0])
            cursor.execute(UNREGISTER_DELETE_USER,(username,))
            print(f"usuario '{username}' eliminado del sistema correctamente.")
            database.commit()
            return True
    return False

def userinfo(payload):
    session, userType, userList, infoList, orderBy, order, limit, offset = payload
    if session:
        userList = userList or ['all']
        infoList = infoList or ['all']
        userType = userType or validation.USER_TYPE_DEFAULT
        orderBy = orderBy or validation.ORDERBY_DEFAULT
        order = order or validation.ORDER_DEFAULT
        limit = limit if limit is not None else validation.LIMIT_DEFAULT
        offset = offset if offset is not None else validation.OFFSET_DEFAULT
        with db.connection() as (_, cursor):
            cursor.execute(f"SELECT {validation.USER[0]}, {validation.ACCESS[0]} FROM user JOIN session_token ON user_id = user.id WHERE {validation.SESSION[0]} = %s",(session,))
            result = cursor.fetchone()
            if result is not None:
                (userName, access) = result
                access = int(access)
                cursor.execute(f"SELECT {userType} FROM user WHERE {validation.ACCESS[0]} <= %s",(access,))
                allowed_users = cursor.fetchall()
                if allowed_users: allowed_users = [u[0] for u in allowed_users if u is not None]
                if len(userList) == 1 and userList[0] in validation.ALL: userList = allowed_users.copy()
                if len(infoList) == 1 and infoList[0] in validation.ALL: infoList = [u[0] for u in validation.INFO_FOR_USER]
                # esta parte de la consulta sql es muy mejorable, que bien que mariadb permite comparar numeros enteros en forma de 'string'
                userinfo_sql_query = (
                    f"SELECT {', '.join([f'{q}' for q in infoList])} FROM user WHERE "
                    + (' OR '.join([f"{userType} = '{user}'"for user in userList]))
                    + f" ORDER BY {orderBy} {order} LIMIT {limit} OFFSET {offset}"
                )
                cursor.execute(userinfo_sql_query)
                result = cursor.fetchall()

                # construccion de la respuesta
                response = {}
                response[validation.ITEM_COUNT]=len(result)
                response[validation.LOCAL_TIME]=datetime.now().isoformat()
                response[validation.ITEMS] = {}
                for row_index, row in enumerate(result):
                    response[validation.ITEMS][row_index + offset] = {}
                    for column_index, value in enumerate(row):
                        column_name = cursor.column_names[column_index]
                        response[validation.ITEMS][row_index + offset][validation.USERINFO_JSON[column_name]] = value if column_name != validation.CREATED_AT[0] else value.isoformat()
                print(f"usuario '{userName}' ha solicitado informacion en userinfo")
                return response
    return None
