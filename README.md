# el_proyecto
servidor api escrito en python para el proyecto sociotecnologico

## Para instalar y ejecutar en windows:
1) Requisitos:
   - PC con `Windows 10` o una versión mas reciente instalado (no esta probado en otras versiones)
   - Servidor de base de datos SQL (de preferencia: `MariaDB`)
   - Tener `python 3.11` o una versión mas reciente instalado
   - Navegador web, con `Google Chrome` o `Brave`, esta perfecto (opcional, ya que solo es para probar)
2) Instalacion:
   - Descarga el repositorio en un `ZIP` o usando `GIT CLONE`
   - Extrae si es necesario y entra dentro de la carpeta de `el_proyecto-main`
   - Abre una consola o CMD con la direccion de la carpeta
   - crea un entorno virtual de python usando `python -m venv el_proyecto`
   - instala los requerimientos o librerias adicionales necesarias para que funcione con `pip install -r requirements.txt`
   - cambia las variables de la base de de datos dentro del archivo `database_connector.py` si asi lo requieres
3) Ejecucion:
   - activa el entorno virtual de python usando `el_proyecto\Scripts\activate.bat`
   - y por ultimo inicia el servidor usando `python app.py`
   - entra en http://localhost:8080/api y deberia responder con un `Test, OK` si esta funcionando todo
4) Por Ultimo:
   - utiliza `Ctrl + C` para detenerlo
   - y cada vez que necesites reiniciar el servidor debe repetir los pasos de Ejecucion.
  
## endpoints en funcionamiento
   - /test
   - /login
   - /logout
   - /register
   - /unregister
   - /userinfo
   
