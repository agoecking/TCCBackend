# 🚀 Guia de Execução - TCCBackend

## Pré-requisitos
- ✅ Python 3.8+ instalado
- ✅ Docker Desktop instalado e rodando

## Passo 1: Iniciar o MySQL no Docker

Abra o terminal (CMD/PowerShell) e execute:

```bash
docker run -d --name mysql-tcc -e MYSQL_ROOT_PASSWORD=1234 -e MYSQL_DATABASE=tcc_db -p 3306:3306 mysql:8
```

Para confirmar que está rodando:
```bash
docker ps
```

## Passo 2: Configurar e Rodar a Aplicação

### Opção A: Executar o script automático (RECOMENDADO)

Execute o arquivo `run.bat`:
```bash
run.bat
```

Este script fará automaticamente:
- ✅ Criar ambiente virtual (se não existir)
- ✅ Ativar ambiente virtual
- ✅ Criar arquivo `.env` com as variáveis necessárias
- ✅ Instalar dependências
- ✅ Iniciar a aplicação

### Opção B: Executar manualmente

1. **Criar e ativar ambiente virtual:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

2. **Criar arquivo `.env`:**
   ```bash
   # Windows (CMD)
   (
   echo DB_USER=root
   echo DB_PASSWORD=1234
   echo DB_HOST=127.0.0.1
   echo DB_NAME=tcc_db
   ) > .env
   ```

3. **Instalar dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Rodar a aplicação:**
   ```bash
   python main.py
   ```

## ✅ Sucesso!

A aplicação estará rodando em: `http://127.0.0.1:8000`

### Acessar a API:
- **Swagger UI:** http://127.0.0.1:8000/apidocs/
- **API JSON:** http://127.0.0.1:8000/apispec_1.json

## 🛑 Parar a Aplicação

Pressione `CTRL + C` no terminal

## 🐳 Parar o MySQL (Docker)

```bash
docker stop mysql-tcc
docker rm mysql-tcc
```

## 📝 Variáveis de Ambiente

O arquivo `.env` deve conter:
```
DB_USER=root
DB_PASSWORD=1234
DB_HOST=127.0.0.1
DB_NAME=tcc_db
```

## ⚠️ Problemas Comuns

### Porta 3306 já em uso
```bash
docker ps  # Veja containers rodando
docker stop <container_id>
```

### ModuleNotFoundError
Certifique-se que o ambiente virtual está ativado:
```bash
venv\Scripts\activate
```

### Conexão com banco de dados recusada
Verifique se o MySQL está rodando:
```bash
docker ps
```
