import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))

from main import create_app

app = create_app()
client = app.test_client()

passed = 0
failed = 0

def ok(label, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  PASS  {label}")
        passed += 1
    else:
        print(f"  FAIL  {label} | {detail[:120]}")
        failed += 1
    return condition

def post(url, data, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.post(url, data=json.dumps(data), headers=headers)

def get(url, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.get(url, headers=headers)

# ── tokens e IDs globais ──────────────────────────────────────────
token_org = None
token_cli = None
evento_id = 1

print("\n========== TESTE 1: Registro de Organizacao ==========")
r = post("/auth/register-organizacao", {
    "usuario": {
        "nome": "Admin Org", "cpf": "11111111111",
        "email": "admin@org.com", "senha": "senha123"
    },
    "organizacao": {
        "nome": "Org Teste", "cnpj": "12.345.678/0001-99",
        "acesso_ethereum": "0x1234567890123456789012345678901234567890"
    }
})
ok("Status 201 ou 409 (ja existe)", r.status_code in (201, 409), r.data.decode())

print("\n========== TESTE 2: Login Organizacao ==========")
r = post("/auth/login", {"email": "admin@org.com", "senha": "senha123"})
ok("Status 200", r.status_code == 200, r.data.decode())
token_org = (r.get_json() or {}).get("token")
ok("Token recebido", bool(token_org))

print("\n========== TESTE 3: Criar Evento ==========")
r = post("/api/eventos", {
    "nome": "Show de Teste", "quantidade_ingressos": 100, "id_organizacao": 1
}, token=token_org)
ok("Status 201 ou 200", r.status_code in (200, 201), r.data.decode())
evento_id = (r.get_json() or {}).get("id") or 1
print(f"  INFO  evento_id={evento_id}")

print("\n========== TESTE 4: Registro de Cliente ==========")
r = post("/auth/register-cliente", {
    "nome": "Cliente Teste", "cpf": "22222222222",
    "email": "cliente@teste.com", "senha": "senha123",
    "telefone": "41999999999",
    "acesso_ethereum": "0xABCDEF1234567890ABCDEF1234567890ABCDEF12",
    "endereco": {
        "rua": "Rua Teste", "numero": 100,
        "cidade": "Curitiba", "estado": "PR", "cep": "80000000"
    }
})
ok("Status 201 ou 409 (ja existe)", r.status_code in (201, 409), r.data.decode())

print("\n========== TESTE 5: Login Cliente ==========")
r = post("/auth/login", {"email": "cliente@teste.com", "senha": "senha123"})
ok("Status 200", r.status_code == 200, r.data.decode())
token_cli = (r.get_json() or {}).get("token")
ok("Token recebido", bool(token_cli))

print("\n========== TESTE 6: Registrar Mint (endpoint blockchain) ==========")
r = post("/api/ingressos/registrar-mint", {
    "id_evento": evento_id,
    "token_id": 42,
    "tx_hash": "0xabc123def456abc123def456abc123def456abc123def456abc123def456abc1",
    "carteira_comprador": "0xABCDEF1234567890ABCDEF1234567890ABCDEF12"
}, token=token_cli)
ok("Status 201", r.status_code == 201, r.data.decode())
data_mint = r.get_json() or {}
ok("token_id salvo = 42",  data_mint.get("token_id") == 42)
ok("tx_hash retornado",     bool(data_mint.get("tx_hash")))
ok("ingresso_id retornado", bool(data_mint.get("ingresso_id")))
ingresso_id = data_mint.get("ingresso_id")
print(f"  INFO  ingresso_id={ingresso_id}, token_id={data_mint.get('token_id')}")

print("\n========== TESTE 7: Mint sem JWT (deve falhar 401) ==========")
r = post("/api/ingressos/registrar-mint", {
    "id_evento": evento_id, "token_id": 1,
    "tx_hash": "0xaaa", "carteira_comprador": "0xaaa"
})
ok("Status 401 sem JWT", r.status_code == 401, r.data.decode())

print("\n========== TESTE 8: Mint com evento inexistente (deve falhar 404) ==========")
r = post("/api/ingressos/registrar-mint", {
    "id_evento": 99999, "token_id": 1,
    "tx_hash": "0xaaa", "carteira_comprador": "0xaaa"
}, token=token_cli)
ok("Status 404", r.status_code == 404, r.data.decode())

print("\n========== TESTE 9: Campos obrigatorios faltando (deve falhar 400) ==========")
r = post("/api/ingressos/registrar-mint", {
    "id_evento": evento_id
}, token=token_cli)
ok("Status 400 campos faltando", r.status_code == 400, r.data.decode())

print("\n========== TESTE 10: Meus Ingressos ==========")
r = get("/api/ingressos/meus-ingressos", token=token_cli)
ok("Status 200 ou 404", r.status_code in (200, 404), r.data.decode())

print("\n========== TESTE 11: Listar Ingressos do Evento ==========")
r = get(f"/api/ingressos/evento/{evento_id}")
ok("Status 200", r.status_code == 200, r.data.decode())
data_ev = r.get_json() or {}
ok("Campo 'ingressos' presente", "ingressos" in data_ev)
ok("Campo 'vendidos' presente",  "vendidos" in data_ev)

print("\n========== TESTE 12: Validar Token JWT ==========")
r = post("/auth/validate-token", {}, token=token_cli)
ok("Status 200 token valido", r.status_code == 200, r.data.decode())

print(f"\n{'='*52}")
print(f"  RESULTADO: {passed} passaram | {failed} falharam  {'OK' if failed == 0 else 'ATENCAO'}")
print(f"{'='*52}\n")
sys.exit(0 if failed == 0 else 1)
