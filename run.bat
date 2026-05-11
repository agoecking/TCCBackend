@echo off
cd /d c:\Users\kleyt\TCC\Backend\TCCBackend

echo ===== Verificando Python =====
python --version

echo.
echo ===== Verificando ambiente virtual =====
if exist venv (
    echo Virtual environment encontrado!
) else (
    echo Criando ambiente virtual...
    python -m venv venv
)

echo.
echo ===== Ativando ambiente virtual =====
call venv\Scripts\activate.bat

echo.
echo ===== Verificando .env =====
if exist .env (
    echo Arquivo .env já existe
) else (
    echo Criando arquivo .env...
    (
        echo DB_USER=root
        echo DB_PASSWORD=1234
        echo DB_HOST=127.0.0.1
        echo DB_NAME=tcc_db
    ) > .env
    echo Arquivo .env criado!
)

echo.
echo ===== Instalando dependências =====
pip install -r requirements.txt

echo.
echo ===== Iniciando aplicação =====
python main.py

pause
