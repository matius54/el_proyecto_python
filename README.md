# el_proyecto_python
servidor api escrito en python, su objetivo es proporcionar un puente entre una base de datos sql y solicitudes http con un sistema de usuarios, aun faltan muchas caracteristicas asi que esta es una implementacion incompleta.
## Para instalar y ejecutar en windows:
1) Requisitos:
   - PC con _Windows 10_ o una versión mas reciente instalado (no esta probado en otras versiones)
   - Servidor de base de datos SQL (de preferencia: _MariaDB_)
   - Tener _python 3.11_ o una versión mas reciente instalado
   - Navegador web, con _Google Chrome_ o _Brave_, esta perfecto (opcional, ya que solo es para probar)
2) Instalacion:
   - Descarga el repositorio en un ```zip``` o usando ```git clone <direccion de este repositorio>``` si tienes git instalado
   - Extrae si es necesario y entra dentro de la carpeta de ```/el_proyecto_python-main```
   - Abre una consola o CMD con la direccion de la carpeta
   - crea un entorno virtual de python usando ```python -m venv el_proyecto python```
   - instala los requerimientos o librerias adicionales necesarias para que funcione con ```pip install -r requirements.txt```
   - cambia las variables de la base de de datos dentro del archivo `database_connector.py` si asi lo requieres
3) Ejecucion:
   - activa el entorno virtual de python usando ```el_proyecto\Scripts\activate.bat```
   - y por ultimo inicia el servidor usando ```python app.py```
   - entra en http://localhost:8080/api y deberia responder con un _Test, OK_ si esta funcionando todo
   - puedes usar esta [pagina](https://matius54.github.io/el_proyecto_api_webpage_test/) para hacer una prueba de cada endpoint por separado, (recuerda poner la direccion de la api)
4) Por Ultimo:
   - utiliza _Ctrl + C_ para detenerlo
   - y cada vez que necesites reiniciar el servidor debe repetir los pasos de Ejecucion.
## endpoints en funcionamiento
   - /test
   - /login
   - /logout
   - /register
   - /unregister
   - /userinfo
