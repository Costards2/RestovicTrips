from types import SimpleNamespace
 
import pytest
 
import app as app_module
from b_tree import ArvoreB
from tabela_hash import TabelaHash
 
 
def _cliente(id_, nome, pacote=102, status="ativo"):
    """Cria o dicionário de um cliente de teste."""
    return {
        "id": id_,
        "nome": nome,
        "email": f"{nome.split()[0].lower()}@email.com",
        "esim": f"ESIM-{id_:05d}",
        "pacote": pacote,
        "status": status,
    }
 
 
@pytest.fixture
def ctx(monkeypatch):
    """App isolado: árvore e hash pequenas, sem gravar nos JSON reais e com os templates reais."""
    arvore = ArvoreB(ordem=3)
    arvore.carregar(
        [
            _cliente(10100, "Maria Silva", pacote=102, status="ativo"),
            _cliente(10200, "Joao Souza", pacote=201, status="inativo"),
        ]
    )
 
    tabela = TabelaHash()
    tabela.inserir(
        "IT",
        {
            "codigo": "IT",
            "pais": "Itália",
            "regiao": "Europa",
            "operadora": "TIM",
            "tecnologia": "5G",
        },
    )
    tabela.inserir(
        "BR",
        {
            "codigo": "BR",
            "pais": "Brasil",
            "regiao": "América do Sul",
            "operadora": "Vivo",
            "tecnologia": "5G",
        },
    )
 
    salvos = []
    monkeypatch.setattr(app_module, "arvore_clientes", arvore)
    monkeypatch.setattr(app_module, "tabela", tabela)
    monkeypatch.setattr(
        app_module.persistencia,
        "salvar_clientes",
        lambda origem, caminho=None: salvos.append(origem),
    )
    app_module.app.config["TESTING"] = True
 
    return SimpleNamespace(
        client=app_module.app.test_client(),
        arvore=arvore,
        salvos=salvos,
    )
 
 
def pagina(resp):
    """Devolve o HTML da resposta como texto."""
    return resp.get_data(as_text=True)
 
 
FORM_OK = {
    "id": "10300",
    "nome": "Ana Lima",
    "email": "ana@email.com",
    "esim": "",
    "pacote": "101",
    "status": "ativo",
}
 
 
# ==============================================================================
# SUÍTE DE TESTES: LISTAGEM DE CLIENTES
# ==============================================================================
def test_listagem_em_ordem_de_id(ctx):
    """A listagem mostra os clientes em ordem crescente de ID."""
    resp = ctx.client.get("/clientes")
    html = pagina(resp)
 
    assert resp.status_code == 200
    assert html.index("Maria Silva") < html.index("Joao Souza")
 
 
# ==============================================================================
# SUÍTE DE TESTES: CADASTRO DE CLIENTES
# ==============================================================================
def test_cadastro_ok(ctx):
    """Cadastro válido insere na árvore, gera o eSIM e persiste."""
    resp = ctx.client.post("/clientes/cadastrar", data=FORM_OK)
 
    assert resp.status_code == 302
    novo = ctx.arvore.buscar(10300)
    assert novo["nome"] == "Ana Lima"
    assert novo["pacote"] == 101
    assert novo["esim"] == "ESIM-10300"  # gerado quando vazio
    assert len(ctx.salvos) == 1
 
 
def test_cadastro_id_duplicado(ctx):
    """ID já existente é recusado e nada é salvo."""
    resp = ctx.client.post("/clientes/cadastrar", data={**FORM_OK, "id": "10100"})
 
    assert resp.status_code == 200
    assert "Já existe" in pagina(resp)
    assert ctx.arvore.tamanho == 2
    assert ctx.salvos == []
 
 
@pytest.mark.parametrize(
    "campo, valor",
    [
        ("id", "abc"),
        ("id", "-3"),
        ("id", ""),
        ("id", "123"),
        ("id", "100000"),
        ("pacote", "999"),
        ("pacote", "x"),
        ("email", "sem-arroba"),
        ("nome", "  "),
        ("status", "talvez"),
    ],
)
def test_cadastro_dados_invalidos(ctx, campo, valor):
    """Dados inválidos mostram erro e não alteram a árvore."""
    resp = ctx.client.post("/clientes/cadastrar", data={**FORM_OK, campo: valor})
 
    assert resp.status_code == 200
    assert "Erro" in pagina(resp)
    assert ctx.arvore.tamanho == 2
    assert ctx.salvos == []
 
 
# ==============================================================================
# SUÍTE DE TESTES: CONSULTA DE CLIENTES E INTEGRAÇÃO ÁRVORE B x HASH
# ==============================================================================
def test_consulta_existente(ctx):
    """Consulta por ID (via GET) mostra o cliente encontrado na Árvore B."""
    resp = ctx.client.get("/clientes/consultar?id=10100")
 
    assert resp.status_code == 200
    assert "Maria Silva" in pagina(resp)
 
 
def test_consulta_integrada_com_destino(ctx):
    """Cliente + destino mostram o cliente (Árvore B) e o país (Tabela Hash)."""
    resp = ctx.client.post(
        "/clientes/consultar",
        data={"id_cliente": "10100", "codigo_pais": "it"},
    )
    html = pagina(resp)
 
    assert "Maria Silva" in html
    assert "Itália" in html
 
 
def test_consulta_destino_inexistente(ctx):
    """Destino sem cobertura mostra aviso, mas o cliente continua aparecendo."""
    resp = ctx.client.post(
        "/clientes/consultar",
        data={"id_cliente": "10100", "codigo_pais": "XX"},
    )
    html = pagina(resp)
 
    assert "Maria Silva" in html
    assert "não encontrado" in html
 
 
def test_consulta_cliente_inexistente(ctx):
    """ID que não existe na árvore mostra mensagem de erro."""
    resp = ctx.client.post(
        "/clientes/consultar",
        data={"id_cliente": "99999", "codigo_pais": "IT"},
    )
 
    assert "não encontrado" in pagina(resp)
 
 
@pytest.mark.parametrize("texto", ["12a", "-1", "1.5"])
def test_consulta_id_invalido(ctx, texto):
    """ID com letras, sinal ou ponto não quebra a página."""
    resp = ctx.client.post(
        "/clientes/consultar",
        data={"id_cliente": texto, "codigo_pais": ""},
    )
 
    assert resp.status_code == 200
    assert "ID numérico válido" in pagina(resp)
 
 
# ==============================================================================
# SUÍTE DE TESTES: EDIÇÃO DE CLIENTES
# ==============================================================================
def test_editar_ok_mantem_id(ctx):
    """Edição válida altera os campos, mantém o ID e preserva o eSIM em branco."""
    dados = {
        "nome": "Maria S. Nova",
        "email": "nova@email.com",
        "esim": "",
        "pacote": "301",
        "status": "inativo",
    }
    resp = ctx.client.post("/clientes/editar/10100", data=dados)
 
    assert resp.status_code == 302
    cliente = ctx.arvore.buscar(10100)
    assert cliente["nome"] == "Maria S. Nova"
    assert cliente["pacote"] == 301
    assert cliente["status"] == "inativo"
    assert cliente["id"] == 10100
    assert cliente["esim"] == "ESIM-10100"  # eSIM em branco mantém o atual
    assert len(ctx.salvos) == 1
 
 
def test_editar_troca_esim(ctx):
    """Um novo eSIM informado substitui o anterior (em maiúsculas)."""
    dados = {
        "nome": "Maria Silva",
        "email": "maria@email.com",
        "esim": "esim-99999",
        "pacote": "102",
        "status": "ativo",
    }
    ctx.client.post("/clientes/editar/10100", data=dados)
 
    assert ctx.arvore.buscar(10100)["esim"] == "ESIM-99999"
 
 
def test_editar_inexistente_redireciona(ctx):
    """Editar um cliente que não existe volta para a listagem."""
    resp = ctx.client.get("/clientes/editar/99999")
 
    assert resp.status_code == 302
    assert "/clientes" in resp.headers["Location"]
 
 
@pytest.mark.parametrize(
    "campo, valor",
    [
        ("pacote", "999"),
        ("nome", ""),
        ("email", "semarroba"),
        ("status", "talvez"),
    ],
)
def test_editar_dados_invalidos_nao_altera(ctx, campo, valor):
    """Edição com dado inválido mostra erro e não altera o cliente."""
    dados = {
        "nome": "X Y",
        "email": "x@email.com",
        "esim": "",
        "pacote": "101",
        "status": "ativo",
    }
    resp = ctx.client.post("/clientes/editar/10100", data={**dados, campo: valor})
 
    assert resp.status_code == 200
    assert ctx.arvore.buscar(10100)["nome"] == "Maria Silva"
    assert ctx.salvos == []
 
 
# ==============================================================================
# SUÍTE DE TESTES: ESTATÍSTICAS E ETAPA 1 PRESERVADA
# ==============================================================================
def test_estatisticas_com_painel_da_arvore_b(ctx):
    """A página de estatísticas mostra o painel da Árvore B."""
    resp = ctx.client.get("/estatisticas")
 
    assert resp.status_code == 200
    assert "Árvore B" in pagina(resp)
 
 
def test_rotas_da_etapa1_continuam(ctx):
    """As rotas da Etapa 1 continuam respondendo normalmente."""
    for rota in ["/", "/paises", "/consulta", "/cadastro", "/estatisticas"]:
        assert ctx.client.get(rota).status_code == 200