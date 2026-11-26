import json
import os
from typing import Any, Dict, List, Union

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIR_ARQUIVOS = os.path.join(BASE_DIR, "arquivos")

CAMINHO_PAISES = os.path.join(DIR_ARQUIVOS, "paises.json")
CAMINHO_CLIENTES = os.path.join(DIR_ARQUIVOS, "clientes.json")
CAMINHO_PACOTES = os.path.join(DIR_ARQUIVOS, "pacotes.json")

CAMINHO_ARQUIVO = CAMINHO_PAISES

PACOTES_PADRAO: List[Dict[str, Any]] = [
    {
        "codigo": 101,
        "nome": "Europa Basic",
        "pacote": "Europa Basic",
        "dados": "5 GB",
        "validade": "15 dias",
    },
    {
        "codigo": 102,
        "nome": "Europa Plus",
        "pacote": "Europa Plus",
        "dados": "10 GB",
        "validade": "30 dias",
    },
    {
        "codigo": 201,
        "nome": "América Basic",
        "pacote": "América Basic",
        "dados": "5 GB",
        "validade": "15 dias",
    },
    {
        "codigo": 202,
        "nome": "América Plus",
        "pacote": "América Plus",
        "dados": "15 GB",
        "validade": "30 dias",
    },
    {
        "codigo": 301,
        "nome": "Global",
        "pacote": "Global",
        "dados": "20 GB",
        "validade": "30 dias",
    },
]

def _resolver_caminho(caminho: Union[str, None], caminho_padrao: str) -> str:
    """Resolve o caminho absoluto garantindo compatibilidade com caminhos relativos."""
    if not caminho:
        return caminho_padrao
    if os.path.isabs(caminho):
        return caminho
    return os.path.join(BASE_DIR, caminho)

def _garantir_diretorio(caminho: str) -> None:
    """Cria os diretórios pais caso ainda não existam."""
    diretorio = os.path.dirname(caminho)
    if diretorio and not os.path.exists(diretorio):
        os.makedirs(diretorio, exist_ok=True)

def _ler_json(caminho: str, default: Any = None) -> Any:
    """Lê um arquivo JSON de forma segura com encoding UTF-8."""
    if not os.path.exists(caminho):
        return default if default is not None else []
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default if default is not None else []

def _gravar_json(caminho: str, dados: Any) -> None:
    """Grava dados em arquivo JSON com formatação legível e encoding UTF-8."""
    _garantir_diretorio(caminho)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def carregar_paises(caminho: str = None) -> List[Dict[str, Any]]:
    """Carrega a lista de países cadastrados."""
    caminho_final = _resolver_caminho(caminho, CAMINHO_PAISES)
    return _ler_json(caminho_final, default=[])

def salvar_paises(origem: Any, caminho: str = None) -> None:
    """
    Persiste os países no arquivo JSON.
    Aceita uma instância da TabelaHash (com método listar_todos) ou uma lista de dicionários.
    """
    caminho_final = _resolver_caminho(caminho, CAMINHO_PAISES)
    if hasattr(origem, "listar_todos"):
        dados = origem.listar_todos()
    elif isinstance(origem, list):
        dados = origem
    else:
        dados = list(origem)
    _gravar_json(caminho_final, dados)

def carregar_dados() -> List[Dict[str, Any]]:
    return carregar_paises()

def salvar_dados(tabela_hash: Any) -> None:
    salvar_paises(tabela_hash)

def carregar_pacotes(caminho: str = None) -> List[Dict[str, Any]]:
    """
    Carrega o catálogo de pacotes de dados.
    Caso o arquivo não exista ou esteja corrompido, cria e persiste os pacotes padrão.
    """
    caminho_final = _resolver_caminho(caminho, CAMINHO_PACOTES)
    if not os.path.exists(caminho_final):
        _gravar_json(caminho_final, PACOTES_PADRAO)
        return list(PACOTES_PADRAO)

    dados = _ler_json(caminho_final, default=None)
    if not dados:
        _gravar_json(caminho_final, PACOTES_PADRAO)
        return list(PACOTES_PADRAO)
    return dados

def salvar_pacotes(origem: Any, caminho: str = None) -> None:
    """Salva a lista ou dicionário de pacotes no arquivo JSON."""
    caminho_final = _resolver_caminho(caminho, CAMINHO_PACOTES)
    if isinstance(origem, dict):
        dados = list(origem.values())
    elif isinstance(origem, list):
        dados = origem
    else:
        dados = list(origem)
    _gravar_json(caminho_final, dados)

def obter_mapa_pacotes(caminho: str = None) -> Dict[int, Dict[str, Any]]:
    """Retorna os pacotes indexados pelo código numérico para consulta rápida O(1)."""
    pacotes = carregar_pacotes(caminho)
    return {int(p["codigo"]): p for p in pacotes}

def carregar_clientes(
    caminho: str = None, auto_gerar: bool = True, quantidade: int = 1000
) -> List[Dict[str, Any]]:
    """
    Carrega o conjunto de clientes a partir do arquivo JSON.
    Se o arquivo não existir e auto_gerar for True, invoca o gerador de clientes automaticamente.
    """
    caminho_final = _resolver_caminho(caminho, CAMINHO_CLIENTES)
    if not os.path.exists(caminho_final) and auto_gerar:
        from gerar_clientes import gerar_clientes as _gerar

        clientes = _gerar(quantidade=quantidade)
        salvar_clientes(clientes, caminho=caminho_final)
        return clientes

    dados = _ler_json(caminho_final, default=[])
    if not dados and auto_gerar:
        from gerar_clientes import gerar_clientes as _gerar

        clientes = _gerar(quantidade=quantidade)
        salvar_clientes(clientes, caminho=caminho_final)
        return clientes

    return dados

def salvar_clientes(origem: Any, caminho: str = None) -> None:
    """
    Persiste os clientes no arquivo JSON.
    Aceita uma instância da Árvore B (com método listar_ordem) ou uma lista de dicionários.
    """
    caminho_final = _resolver_caminho(caminho, CAMINHO_CLIENTES)
    if hasattr(origem, "listar_ordem"):
        dados = origem.listar_ordem()
    elif hasattr(origem, "listar_todos"):
        dados = origem.listar_todos()
    elif isinstance(origem, list):
        dados = origem
    else:
        dados = list(origem)
    _gravar_json(caminho_final, dados)
