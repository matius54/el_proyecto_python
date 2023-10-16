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
        cursor.execute("SELECT id FROM user WHERE username = %s",(user,))
        result=cursor.fetchone()
        return int(result[0])
    
    def getSessionFromUser(cursor,user):
        cursor.execute("SELECT token FROM session_token JOIN user ON user.id = user_id WHERE username = %s",(user,))
        result = cursor.fetchone()
        if cursor.rowcount == 1:
            return result[0]
        print(f"sesiones abiertas = {cursor.rowcount}")
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
    private = result[0][0]
    return totp(private).verify(key)

def login(username,key):
    LOGIN_COUNT_SESSION = "SELECT COUNT(*) FROM session_token WHERE token = %s"
    LOGIN_INSERT_SESSION = "INSERT INTO session_token (user_id, token) VALUES (%s, %s)"
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

def logout(session):
    SESSION_JOIN_USERNAME_TOKEN = "SELECT username FROM user JOIN session_token ON user_id = user.id WHERE token = %s"
    SESSION_DELETE_SESSION = "DELETE FROM session_token WHERE token = %s"
    with db.connection() as (database, cursor):
        cursor.execute(SESSION_JOIN_USERNAME_TOKEN,(session,))
        result = cursor.fetchone()
        if result is not None:
            username = result[0]
            cursor.execute(SESSION_DELETE_SESSION, (session,))
            database.commit()
            print(f"sesion cerrada {cursor.rowcount} para usuario '{username}'")
            if cursor.rowcount > 0:
                return True
    return False

def register(session, user=None, firstname=None, lastname=None, access=None):
    REGISTER_GET_ACCES_FROM_TOKEN = "SELECT access_lvl FROM user JOIN session_token ON user_id = user.id WHERE token = %s"
    REGISTER_TOTP_DUPLICATE_VERIFICATION = "SELECT COUNT(*) FROM user WHERE private = %s"
    REGISTER_INSERT = "INSERT INTO user (private, username, access_lvl, first_name, last_name) VALUES (%s,%s,%s,%s,%s)"
    session = session or None
    newUser = user or None
    newFirstname = firstname or None
    newLastname = lastname or None
    newAccess = access or 0
    if session is not None and newUser is not None:
        with db.connection() as (database, cursor):
            cursor.execute(REGISTER_GET_ACCES_FROM_TOKEN,(session,))
            result = cursor.fetchone()
            if result is not None:
                access = int(result[0])
                if newAccess < access and newAccess >= validation.ACCESS_MIN_VALUE:
                    while True:
                        otptoken = otp_gen()
                        cursor.execute(REGISTER_TOTP_DUPLICATE_VERIFICATION,(otptoken,))
                        if not int(cursor.fetchone()[0]):
                            break
                    cursor.execute(REGISTER_INSERT,(otptoken,newUser,newAccess,newFirstname,newLastname))
                    database.commit()
                    return otptoken
    return None

def unregister(username,key):
    UNREGISTER_JOIN_TOKEN_USERNAME = "SELECT token FROM session_token JOIN user ON user.id = user_id WHERE username = %s"
    UNREGISTER_DELETE_USER = "DELETE FROM user WHERE username = %s"
    if totp_user_verify(username,key):
        with db.connection() as (database, cursor):
            cursor.execute(UNREGISTER_JOIN_TOKEN_USERNAME,(username,))
            result = cursor.fetchone()
            if result is not None: logout(session = result[0])
            cursor.execute(UNREGISTER_DELETE_USER,(username,))
            database.commit()
            return True
    return False

def userinfo(session, userList, infoList, userType, orderBy, order, limit, offset):
    if session:
        userList = userList or ['all']
        infoList = infoList or ['all']
        userType = userType or validation.USER_TYPE_DEFAULT
        orderBy = orderBy or validation.ORDERBY_DEFAULT
        order = order or validation.ORDER_DEFAULT
        limit = limit if limit is not None else validation.LIMIT_DEFAULT
        offset = offset if offset is not None else validation.OFFSET_DEFAULT
        with db.connection() as (_, cursor):
            cursor.execute(f"SELECT {validation.USER[0]}, {validation.ACCESS[0]} FROM user JOIN session_token ON user_id = user.id WHERE token = %s",(session,))
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
