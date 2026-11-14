import random
import pytest
from tabela_hash import TabelaHash
from b_tree import ArvoreB


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