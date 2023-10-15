import database_connector as db
from pyotp import TOTP as totp
import base64
import os
from validation import ACCESS_MIN_VALUE

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
                if newAccess < access and newAccess >= ACCESS_MIN_VALUE:
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

def userinfo(session, user = ['all'], info = ['all'], usertype = "id", orderby = 'id', order = "asc", limit = 100, offset = 0):
    # codigo para recuperar la informacion de usuarios desde una base de datos a partir de un token de sesion administrador
    return {}