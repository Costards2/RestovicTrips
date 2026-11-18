from types import SimpleNamespace

import pytest

import app as app_module
from b_tree import ArvoreB
from tabela_hash import TabelaHash


def _cliente(id_, nome, pacote=102, status="ativo"):
    return {"id": id_, "nome": nome, "email": f"{nome.split()[0].lower()}@email.com",
            "esim": f"ESIM-{id_:05d}", "pacote": pacote, "status": status}


@pytest.fixture
def ctx(monkeypatch):
    """App isolado: árvore e hash pequenas, sem gravar JSON e sem depender dos templates."""
    arvore = ArvoreB(ordem=3)
    arvore.carregar([
        _cliente(100, "Maria Silva", pacote=102, status="ativo"),
        _cliente(200, "Joao Souza", pacote=201, status="inativo"),
    ])

    tabela = TabelaHash()
    tabela.inserir("IT", {"codigo": "IT", "pais": "Itália", "regiao": "Europa",
                          "operadora": "TIM", "tecnologia": "5G"})
    tabela.inserir("BR", {"codigo": "BR", "pais": "Brasil", "regiao": "América do Sul",
                          "operadora": "Vivo", "tecnologia": "5G"})

    salvos, renders = [], []

    def falso_render(nome, **contexto):
        renders.append((nome, contexto))
        return "ok"

    monkeypatch.setattr(app_module, "arvore_clientes", arvore)
    monkeypatch.setattr(app_module, "tabela", tabela)
    monkeypatch.setattr(app_module, "render_template", falso_render)
    monkeypatch.setattr(app_module.persistencia, "salvar_clientes",
                        lambda origem, caminho=None: salvos.append(origem))
    app_module.app.config["TESTING"] = True

    return SimpleNamespace(client=app_module.app.test_client(), arvore=arvore,
                           salvos=salvos, renders=renders)


def mensagens(client):
    with client.session_transaction() as sessao:
        return [msg for _categoria, msg in sessao.get("_flashes", [])]


def ultimo_contexto(ctx):
    return ctx.renders[-1][1]


FORM_OK = {"id": "300", "nome": "Ana Lima", "email": "ana@email.com",
           "esim": "", "pacote": "101", "status": "ativo"}


# ------------------------------------------------------------------ listagem
def test_listagem_paginada(ctx):
    for i in range(1, 121):
        if i not in (100,):
            ctx.arvore.inserir(1000 + i, _cliente(1000 + i, f"Cliente{i} Teste"))
    resp = ctx.client.get("/clientes?pagina=2")
    c = ultimo_contexto(ctx)
    assert resp.status_code == 200
    assert c["pagina"] == 2 and len(c["clientes"]) == 50
    assert c["total"] == 121 and c["total_paginas"] == 3
    ids = [x["id"] for x in c["clientes"]]
    assert ids == sorted(ids)


@pytest.mark.parametrize("param, esperado", [("999", 1), ("abc", 1), ("-5", 1), ("0", 1)])
def test_listagem_pagina_invalida_nao_quebra(ctx, param, esperado):
    resp = ctx.client.get(f"/clientes?pagina={param}")
    assert resp.status_code == 200
    assert ultimo_contexto(ctx)["pagina"] == esperado


# ----------------------------------------------------------------- cadastro
def test_cadastro_ok(ctx):
    resp = ctx.client.post("/clientes/cadastrar", data=FORM_OK)
    assert resp.status_code == 302
    assert "/clientes/consultar?id=300" in resp.headers["Location"]
    novo = ctx.arvore.buscar(300)
    assert novo["nome"] == "Ana Lima" and novo["pacote"] == 101
    assert novo["esim"] == "ESIM-00300"  # gerado quando vazio
    assert len(ctx.salvos) == 1


def test_cadastro_id_duplicado(ctx):
    resp = ctx.client.post("/clientes/cadastrar", data={**FORM_OK, "id": "100"})
    assert resp.status_code == 200
    assert any("Já existe" in m for m in mensagens(ctx.client))
    assert ctx.arvore.tamanho == 2 and ctx.salvos == []


@pytest.mark.parametrize("campo, valor", [
    ("id", "abc"), ("id", "-3"), ("id", ""), ("pacote", "999"), ("pacote", "x"),
    ("email", "sem-arroba"), ("nome", "  "), ("status", "talvez"),
])
def test_cadastro_dados_invalidos(ctx, campo, valor):
    resp = ctx.client.post("/clientes/cadastrar", data={**FORM_OK, campo: valor})
    assert resp.status_code == 200
    assert mensagens(ctx.client)
    assert ctx.arvore.tamanho == 2 and ctx.salvos == []


# ----------------------------------------------------------------- consulta
def test_consulta_existente(ctx):
    resp = ctx.client.get("/clientes/consultar?id=100")
    c = ultimo_contexto(ctx)
    assert resp.status_code == 200
    assert c["cliente"]["nome"] == "Maria Silva"
    assert c["pacote"]["nome"] == "Europa Plus"
    assert c["busca"]["paginas_visitadas"] >= 1


def test_consulta_via_post(ctx):
    ctx.client.post("/clientes/consultar", data={"id": "200"})
    assert ultimo_contexto(ctx)["cliente"]["nome"] == "Joao Souza"


def test_consulta_inexistente(ctx):
    ctx.client.get("/clientes/consultar?id=999")
    assert ultimo_contexto(ctx)["cliente"] is None
    assert any("não encontrado" in m for m in mensagens(ctx.client))


@pytest.mark.parametrize("texto", ["12a", "-1", "0", "1.5"])
def test_consulta_id_invalido(ctx, texto):
    resp = ctx.client.get(f"/clientes/consultar?id={texto}")
    assert resp.status_code == 200
    assert ultimo_contexto(ctx)["cliente"] is None
    assert any("inválido" in m for m in mensagens(ctx.client))


def test_consulta_sem_id_nao_busca(ctx):
    ctx.client.get("/clientes/consultar")
    assert ultimo_contexto(ctx)["busca"] is None


# ------------------------------------------------------------------- edição
def test_editar_ok_mantem_id(ctx):
    dados = {"nome": "Maria S. Nova", "email": "nova@email.com", "esim": "",
             "pacote": "301", "status": "inativo"}
    resp = ctx.client.post("/clientes/editar/100", data=dados)
    assert resp.status_code == 302
    c = ctx.arvore.buscar(100)
    assert c["nome"] == "Maria S. Nova" and c["pacote"] == 301
    assert c["status"] == "inativo" and c["id"] == 100
    assert c["esim"] == "ESIM-00100"  # esim em branco mantém o atual
    assert len(ctx.salvos) == 1


def test_editar_inexistente_redireciona(ctx):
    resp = ctx.client.get("/clientes/editar/999")
    assert resp.status_code == 302 and "/clientes" in resp.headers["Location"]
    assert any("não encontrado" in m for m in mensagens(ctx.client))


def test_editar_id_invalido_na_url(ctx):
    resp = ctx.client.get("/clientes/editar/abc")
    assert resp.status_code == 302


def test_editar_pacote_invalido_nao_altera(ctx):
    dados = {"nome": "X Y", "email": "x@email.com", "esim": "", "pacote": "999", "status": "ativo"}
    ctx.client.post("/clientes/editar/100", data=dados)
    assert ctx.arvore.buscar(100)["nome"] == "Maria Silva"
    assert ctx.salvos == []


# --------------------------------------------------------------- integração
def test_integrada_ok(ctx):
    ctx.client.post("/clientes/integrada", data={"cliente": "100", "destino": "it"})
    ficha = ultimo_contexto(ctx)["ficha"]
    assert ficha["cliente"]["nome"] == "Maria Silva"
    assert ficha["pacote"]["nome"] == "Europa Plus"
    assert ficha["pais"]["pais"] == "Itália" and ficha["pais"]["tecnologia"] == "5G"
    assert ficha["cobertura"] is True and ficha["avisos"] == []
    assert ficha["busca_arvore"]["paginas_visitadas"] >= 1


def test_integrada_avisos_pacote_e_status(ctx):
    ctx.client.post("/clientes/integrada", data={"cliente": "200", "destino": "IT"})
    avisos = " ".join(ultimo_contexto(ctx)["ficha"]["avisos"])
    assert "inativo" in avisos and "não cobre" in avisos


def test_integrada_destino_inexistente(ctx):
    ctx.client.post("/clientes/integrada", data={"cliente": "100", "destino": "XX"})
    ficha = ultimo_contexto(ctx)["ficha"]
    assert ficha["cobertura"] is False and ficha["pais"] is None
    assert any("não encontrado" in m for m in mensagens(ctx.client))


def test_integrada_cliente_inexistente(ctx):
    ctx.client.post("/clientes/integrada", data={"cliente": "999", "destino": "IT"})
    assert ultimo_contexto(ctx)["ficha"] is None
    assert any("não encontrado" in m for m in mensagens(ctx.client))


@pytest.mark.parametrize("dados", [{"cliente": "abc", "destino": "IT"},
                                   {"cliente": "100", "destino": ""},
                                   {"cliente": "", "destino": ""}])
def test_integrada_entrada_invalida(ctx, dados):
    resp = ctx.client.post("/clientes/integrada", data=dados)
    assert resp.status_code == 200
    assert ultimo_contexto(ctx)["ficha"] is None and mensagens(ctx.client)


# ----------------------------------------------------- Etapa 1 preservada
def test_rotas_da_etapa1_continuam(ctx):
    for rota in ["/", "/paises", "/consulta", "/cadastro", "/estatisticas"]:
        assert ctx.client.get(rota).status_code == 200
    assert "stats_arvore" in ultimo_contexto(ctx)