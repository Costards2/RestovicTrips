import json
import os

CAMINHO_ARQUIVO = 'arquivos/paises.json'

def carregar_dados():
    if not os.path.exists('arquivos'):
        os.makedirs('arquivos')
    if not os.path.exists(CAMINHO_ARQUIVO):
        return []
    with open(CAMINHO_ARQUIVO, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            return []

def salvar_dados(tabela_hash):
    dados = tabela_hash.listar_todos()
    with open(CAMINHO_ARQUIVO, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)