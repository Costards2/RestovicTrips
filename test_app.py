import json
import os
import random
import pytest

from tabela_hash import TabelaHash
from b_tree import ArvoreB
import persistencia
from gerar_clientes import gerar_clientes, salvar_clientes_em_arquivo, PACOTES_VALIDOS, STATUS_VALIDOS


@pytest.fixture
def fabrica_cliente():
    """Cria dicionários de clientes padronizados para os testes da Árvore B."""

    def _criar(cid, nome="Maria Silva", pacote=102, status="ativo"):
        return {
            "id": cid,
            "nome": nome,
            "email": f"cliente{cid}@email.com",
            "esim": f"ESIM-{cid}",
            "pacote": pacote,
            "status": status,
        }

    return _criar


# ==============================================================================
# SUÍTE DE TESTES: TABELA HASH (ETAPA 1)
# ==============================================================================
class TestTabelaHash:
    def test_insercao_e_busca_case_insensitive(self):
        th = TabelaHash()
        th.inserir("BR", {"codigo": "BR", "pais": "Brasil"})

        assert th.buscar("br") is not None
        assert th.buscar("BR")["pais"] == "Brasil"
        assert th.buscar("XX") is None

    def test_chave_duplicada_nao_incrementa_tamanho(self):
        th = TabelaHash()
        th.inserir("PT", {"codigo": "PT", "pais": "Portugal"})
        th.inserir("PT", {"codigo": "PT", "pais": "Portugal"})

        assert th.tamanho == 1
        assert th.buscar("PT")["pais"] == "Portugal"

    def test_tratamento_de_colisoes(self):
        th = TabelaHash(capacidade=2)
        th.inserir("BR", {"codigo": "BR", "pais": "Brasil"})
        th.inserir("US", {"codigo": "US", "pais": "Estados Unidos"})
        th.inserir("PT", {"codigo": "PT", "pais": "Portugal"})

        assert th.tamanho == 3
        assert th.colisoes > 0
        assert th.buscar("BR")["pais"] == "Brasil"
        assert th.buscar("US")["pais"] == "Estados Unidos"
        assert th.buscar("PT")["pais"] == "Portugal"

    def test_remocao(self):
        th = TabelaHash()
        th.inserir("IT", {"codigo": "IT", "pais": "Itália"})

        assert th.remover("IT") is True
        assert th.buscar("IT") is None
        assert th.remover("IT") is False


# ==============================================================================
# SUÍTE DE TESTES: ÁRVORE B (ETAPA 2)
# ==============================================================================
class TestArvoreB:
    def test_arvore_vazia(self):
        ab = ArvoreB(ordem=3)
        assert ab.buscar(58372) is None
        assert ab.listar_ordem() == []
        assert ab.alterar(58372, {"nome": "Teste"}) is False

        stats = ab.estatisticas()
        assert stats["total_registros"] == 0
        assert stats["altura"] == 0
        assert stats["divisoes"] == 0

    def test_ordem_invalida(self):
        with pytest.raises(ValueError):
            ArvoreB(ordem=1)

    def test_insercao_e_busca(self, fabrica_cliente):
        ab = ArvoreB(ordem=3)
        ab.inserir(58372, fabrica_cliente(58372, nome="Maria Silva"))

        encontrado = ab.buscar(58372)
        assert encontrado is not None
        assert encontrado["nome"] == "Maria Silva"
        assert ab.buscar(99999) is None
        assert ab.ultima_busca["paginas_visitadas"] >= 1
        assert ab.ultima_busca["comparacoes"] >= 1

    def test_bloqueio_id_duplicado(self, fabrica_cliente):
        ab = ArvoreB(ordem=3)
        ab.inserir(58372, fabrica_cliente(58372))

        with pytest.raises(ValueError):
            ab.inserir(58372, fabrica_cliente(58372))

    def test_percurso_em_ordem(self, fabrica_cliente):
        ab = ArvoreB(ordem=3)
        ids = [58372, 10234, 89120, 34512, 12000, 77431]
        for cid in ids:
            ab.inserir(cid, fabrica_cliente(cid))

        listados = ab.listar_ordem()
        assert [c["id"] for c in listados] == sorted(ids)

    def test_insercao_ordem_decrescente(self, fabrica_cliente):
        ab = ArvoreB(ordem=3)
        ids_decrescentes = list(range(10050, 10000, -1))
        for cid in ids_decrescentes:
            ab.inserir(cid, fabrica_cliente(cid))

        assert ab.tamanho == 50
        assert [c["id"] for c in ab.listar_ordem()] == sorted(ids_decrescentes)

    def test_alteracao_de_registro(self, fabrica_cliente):
        ab = ArvoreB(ordem=3)
        ab.inserir(58372, fabrica_cliente(58372, nome="Maria Silva", pacote=102))

        sucesso = ab.alterar(
            58372,
            {"id": 11111, "nome": "Maria Souza", "pacote": 202, "status": "inativo"},
        )
        assert sucesso is True

        cliente = ab.buscar(58372)
        assert cliente["id"] == 58372
        assert cliente["nome"] == "Maria Souza"
        assert cliente["pacote"] == 202
        assert cliente["status"] == "inativo"
        assert ab.alterar(99999, {"nome": "Inexistente"}) is False

    @pytest.mark.parametrize("ordem", [2, 3, 5])
    def test_divisoes_e_crescimento_por_ordem(self, fabrica_cliente, ordem):
        ab = ArvoreB(ordem=ordem)
        for cid in range(10000, 10030):
            ab.inserir(cid, fabrica_cliente(cid))

        stats = ab.estatisticas()
        assert stats["ordem"] == ordem
        assert stats["total_registros"] == 30
        assert stats["divisoes"] > 0
        assert stats["altura"] > 1

    def test_carga_1000_clientes_e_idempotencia(self, fabrica_cliente):
        random.seed(42)
        ids_unicos = random.sample(range(10000, 99999), 1000)
        clientes = [fabrica_cliente(cid) for cid in ids_unicos]

        ab = ArvoreB(ordem=5)
        total = ab.carregar(clientes)
        assert total == 1000
        assert ab.tamanho == 1000

        # Garante que recarregar a mesma base não duplica registros
        ab.carregar(clientes)
        assert ab.tamanho == 1000

        listados = ab.listar_ordem()
        assert len(listados) == 1000
        assert [c["id"] for c in listados] == sorted(ids_unicos)

        alvo = ids_unicos[500]
        assert ab.buscar(alvo)["id"] == alvo
        assert ab.ultima_busca["paginas_visitadas"] <= ab.altura()


# ==============================================================================
# SUÍTE DE TESTES: PACOTES DE SERVIÇO (ETAPA 2)
# ==============================================================================
class TestPacotes:
    def test_pacotes_contem_codigos_obrigatorios_do_pdf(self):
        pacotes = persistencia.carregar_pacotes()
        codigos = [p["codigo"] for p in pacotes]
        assert sorted(codigos) == [101, 102, 201, 202, 301]

    def test_dados_e_validade_conforme_especificacao(self):
        mapa = persistencia.obter_mapa_pacotes()
        
        # 101 Europa Basic | 5 GB | 15 dias
        assert mapa[101]["nome"] == "Europa Basic"
        assert mapa[101]["dados"] == "5 GB"
        assert mapa[101]["validade"] == "15 dias"

        # 102 Europa Plus | 10 GB | 30 dias
        assert mapa[102]["nome"] == "Europa Plus"
        assert mapa[102]["dados"] == "10 GB"
        assert mapa[102]["validade"] == "30 dias"

        # 201 América Basic | 5 GB | 15 dias
        assert mapa[201]["nome"] == "América Basic"
        assert mapa[201]["dados"] == "5 GB"
        assert mapa[201]["validade"] == "15 dias"

        # 202 América Plus | 15 GB | 30 dias
        assert mapa[202]["nome"] == "América Plus"
        assert mapa[202]["dados"] == "15 GB"
        assert mapa[202]["validade"] == "30 dias"

        # 301 Global | 20 GB | 30 dias
        assert mapa[301]["nome"] == "Global"
        assert mapa[301]["dados"] == "20 GB"
        assert mapa[301]["validade"] == "30 dias"


# ==============================================================================
# SUÍTE DE TESTES: GERADOR DE MASSA DE CLIENTES (ETAPA 2)
# ==============================================================================
class TestGeradorClientes:
    def test_geracao_1000_clientes_com_campos_obrigatorios(self):
        clientes = gerar_clientes(quantidade=1000, seed=123)
        assert len(clientes) == 1000

        ids = set()
        for c in clientes:
            # ID único de 5 dígitos (10000 a 99999)
            cid = c["id"]
            assert isinstance(cid, int)
            assert 10000 <= cid <= 99999
            assert cid not in ids
            ids.add(cid)

            # Nome e Email
            assert isinstance(c["nome"], str) and len(c["nome"].split()) >= 2
            assert "@" in c["email"] and c["email"].endswith("@email.com")

            # eSIM formatado
            assert c["esim"].startswith("ESIM-")
            assert len(c["esim"].split("-")[1]) == 5

            # Pacote válido
            assert c["pacote"] in PACOTES_VALIDOS

            # Status válido
            assert c["status"] in STATUS_VALIDOS

        assert len(ids) == 1000

    def test_reproducibilidade_com_seed(self):
        c1 = gerar_clientes(quantidade=50, seed=99)
        c2 = gerar_clientes(quantidade=50, seed=99)
        assert c1 == c2


# ==============================================================================
# SUÍTE DE TESTES: PERSISTÊNCIA COMPLETA (ETAPA 1 + ETAPA 2)
# ==============================================================================
class TestPersistencia:
    def test_preservacao_paises_e_retrocompatibilidade(self):
        # Carregar via alias antigo e nova função
        dados_antigo = persistencia.carregar_dados()
        paises_novo = persistencia.carregar_paises()
        assert dados_antigo == paises_novo
        assert len(paises_novo) >= 7

        codigos = [p["codigo"] for p in paises_novo]
        assert "BR" in codigos
        assert "IT" in codigos

    def test_salvar_e_carregar_clientes_em_arquivo_temporario(self, tmp_path):
        caminho_teste = str(tmp_path / "clientes_teste.json")
        massa = gerar_clientes(quantidade=20, seed=77)

        persistencia.salvar_clientes(massa, caminho=caminho_teste)
        carregados = persistencia.carregar_clientes(caminho=caminho_teste, auto_gerar=False)

        assert len(carregados) == 20
        assert carregados[0]["id"] == massa[0]["id"]
        assert carregados[0]["nome"] == massa[0]["nome"]

    def test_salvar_clientes_a_partir_de_arvore_b(self, tmp_path):
        caminho_teste = str(tmp_path / "clientes_arvore.json")
        ab = ArvoreB(ordem=3)
        c1 = {"id": 20000, "nome": "Cliente B", "email": "b@email.com", "esim": "ESIM-11111", "pacote": 101, "status": "ativo"}
        c2 = {"id": 10000, "nome": "Cliente A", "email": "a@email.com", "esim": "ESIM-22222", "pacote": 102, "status": "ativo"}
        ab.inserir(20000, c1)
        ab.inserir(10000, c2)

        persistencia.salvar_clientes(ab, caminho=caminho_teste)
        carregados = persistencia.carregar_clientes(caminho=caminho_teste, auto_gerar=False)

        # Salvo pela Árvore B deve estar ordenado por ID (10000, depois 20000)
        assert len(carregados) == 2
        assert carregados[0]["id"] == 10000
        assert carregados[1]["id"] == 20000

    def test_auto_geracao_de_clientes_quando_ausente(self, tmp_path):
        caminho_inexistente = str(tmp_path / "subpasta" / "clientes_novo.json")
        assert not os.path.exists(caminho_inexistente)

        clientes = persistencia.carregar_clientes(caminho=caminho_inexistente, auto_gerar=True, quantidade=15)
        assert len(clientes) == 15
        assert os.path.exists(caminho_inexistente)


# ==============================================================================
# SUÍTE DE TESTES: CARGA IDEMPOTENTE NA INICIALIZAÇÃO DA APLICAÇÃO (APP.PY)
# ==============================================================================
class TestCargaAppArvoreB:
    def test_carga_inicial_app(self):
        import app

        # Verifica se as estruturas estão instanciadas e povoadas no app
        assert app.tabela is not None
        assert app.tabela.tamanho >= 7

        assert app.arvore_clientes is not None
        assert app.arvore_clientes.tamanho == 1000

        assert len(app.pacotes) == 5
        assert 101 in app.mapa_pacotes

    def test_idempotencia_da_carga(self):
        import app

        tamanho_original = app.arvore_clientes.tamanho
        assert tamanho_original == 1000

        # Executa recargas sucessivas
        app.carregar_clientes_na_arvore(app.arvore_clientes)
        assert app.arvore_clientes.tamanho == tamanho_original

        app.carregar_clientes_na_arvore(app.arvore_clientes)
        assert app.arvore_clientes.tamanho == tamanho_original

        # Busca um cliente arbitrário da base para confirmar integridade
        primeiro_cliente = app.arvore_clientes.listar_ordem()[0]
        cid = primeiro_cliente["id"]
        recuperado = app.arvore_clientes.buscar(cid)

        assert recuperado is not None
        assert recuperado["id"] == cid
        assert recuperado["pacote"] in PACOTES_VALIDOS
