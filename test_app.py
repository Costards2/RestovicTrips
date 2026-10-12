import pytest
from tabela_hash import TabelaHash

def test_insercao_e_busca():
    th = TabelaHash()
    th.inserir("BR", {"codigo": "BR", "pais": "Brasil"})
    assert th.buscar("br") is not None # Testa case-insensitive
    assert th.buscar("BR")["pais"] == "Brasil"

def test_colisoes():
    th = TabelaHash(capacidade=2) # Força colisão
    th.inserir("BR", {"codigo": "BR"})
    th.inserir("US", {"codigo": "US"})
    th.inserir("PT", {"codigo": "PT"})
    assert th.tamanho == 3
    assert th.colisoes > 0

def test_remocao():
    th = TabelaHash()
    th.inserir("IT", {"codigo": "IT"})
    assert th.remover("IT") == True
    assert th.buscar("IT") is None