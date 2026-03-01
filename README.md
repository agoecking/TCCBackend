**Installar docker**

https://www.docker.com/products/docker-desktop/

-------

**Clonar repositório** 

git clone https://github.com/agoecking/TCCBackend

-------
**Criar ambiente virtual e ativar**

(bash) python -m venv .venv
(bash) .venv\Scripts\activate

-------
**Instalar dependências**

(bash) pip install -r requirements.txt

-------
**Criar arquivo .env**

(bash) touch .env

**Colocar dentro:**

DB_USER=root
DB_PASSWORD=1234
DB_HOST=127.0.0.1
DB_NAME=tcc_db

-------

**Abrir o Docker e subir o MySQL. No bash rodar:**

(bash) docker run -d --name mysql-tcc -e MYSQL_ROOT_PASSWORD=1234 -e MYSQL_DATABASE=tcc_db -p 3306:3306 mysql:8

**confirme que está rodando com**

(bash) docker ps

