@echo off
echo ============================================
echo   Sistema PVD - Bugalagrande
echo ============================================
echo.
call entorno\Scripts\activate
echo Verificando base de datos...
python manage.py migrate --run-syncdb
echo.
start http://127.0.0.1:8000/
echo Servidor iniciando en http://127.0.0.1:8000/
echo Presiona Ctrl+C para detener.
echo.
python manage.py runserver