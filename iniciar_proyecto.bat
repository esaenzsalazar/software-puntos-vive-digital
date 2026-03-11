@echo off
:: 1. Abrir la URL del proyecto en el navegador predeterminado
start http://127.0.0.1:8000/registrar/

:: 2. Ejecutar el servidor de Django
echo Iniciando el servidor para el Punto Vive Digital Bugalagrande...
python manage.py runserver