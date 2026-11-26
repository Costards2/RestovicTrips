import json
from typing import Any, Dict, Iterator, List, Optional, Tuple

from b_tree import ArvoreB

def _iterar_objetos_json_bytes(conteudo: bytes) -> Iterator[Tuple[int, int]]:
    """Localiza (inicio, tamanho) em bytes de cada objeto JSON dentro de um array."""
    em_string = False
    escapando = False
    profundidade = 0
    inicio_objeto: Optional[int] = None

    for pos, byte in enumerate(conteudo):
        if escapando:
            escapando = False
            continue

        if byte == 92 and em_string:
            escapando = True
            continue

        if byte == 34:
            em_string = not em_string
            continue

        if em_string:
            continue

        if byte == 123:
            if profundidade == 0:
                inicio_objeto = pos
            profundidade += 1
        elif byte == 125 and profundidade > 0:
            profundidade -= 1
            if profundidade == 0 and inicio_objeto is not None:
                yield inicio_objeto, (pos - inicio_objeto + 1)
                inicio_objeto = None

class IndiceClientesArquivo:
    """Versão 1: Árvore B guarda (id -> (inicio_byte, tamanho_bytes)) e consulta no JSON em disco."""

    def __init__(self, caminho_json: str, ordem: int = 5):
        self.caminho_json = caminho_json
        self.arvore = ArvoreB(ordem=ordem)

    def indexar(self) -> int:
        """Varre o arquivo JSON em modo binário e indexa IDs e offsets na Árvore B."""
        self.arvore = ArvoreB(ordem=self.arvore.ordem)

        with open(self.caminho_json, "rb") as arquivo:
            conteudo = arquivo.read()

        for inicio, tamanho in _iterar_objetos_json_bytes(conteudo):
            trecho = conteudo[inicio : inicio + tamanho].decode("utf-8")
            cliente = json.loads(trecho)
            self.arvore.inserir(cliente["id"], (inicio, tamanho))

        return self.arvore.tamanho

    def buscar(self, id_cliente: int) -> Optional[Dict[str, Any]]:
        """Busca a localização na Árvore B e lê apenas os bytes do cliente no arquivo JSON."""
        localizacao = self.arvore.buscar(id_cliente)
        if localizacao is None:
            return None

        inicio, tamanho = localizacao
        with open(self.caminho_json, "rb") as arquivo:
            arquivo.seek(inicio)
            dados_bytes = arquivo.read(tamanho)

        return json.loads(dados_bytes.decode("utf-8"))

def _importar_pandas(origem: str):
    """Importa pandas sob demanda com mensagem clara caso não esteja instalado."""
    try:
        import pandas as pd
    except ImportError as exc:
        raise ImportError(
            f"O pacote 'pandas' é necessário para {origem}. "
            "Instale com: pip install pandas"
        ) from exc
    return pd

class IndiceClientesPandas:
    """Versão 2: Árvore B guarda (id -> índice da linha) e consulta em um DataFrame Pandas."""

    def __init__(self, caminho_json: str, ordem: int = 5):
        self.caminho_json = caminho_json
        self.arvore = ArvoreB(ordem=ordem)
        self.df = None

    def indexar(self) -> int:
        """Carrega o JSON em um DataFrame e indexa IDs e posições (iloc) na Árvore B."""
        pd = _importar_pandas("IndiceClientesPandas")

        self.arvore = ArvoreB(ordem=self.arvore.ordem)
        self.df = pd.read_json(self.caminho_json)

        for idx, id_cliente in enumerate(self.df["id"]):
            self.arvore.inserir(int(id_cliente), idx)

        return self.arvore.tamanho

    def buscar(self, id_cliente: int) -> Optional[Dict[str, Any]]:
        """Busca o índice da linha na Árvore B e retorna o registro via df.iloc."""
        if self.df is None:
            raise RuntimeError("O índice ainda não foi carregado. Chame indexar() primeiro.")

        idx = self.arvore.buscar(id_cliente)
        if idx is None:
            return None

        return self.df.iloc[idx].to_dict()

class IndiceClientesHibrido(IndiceClientesArquivo):
    """Versão híbrida: consulta 1 cliente por byte offset (disco) e todos os clientes via DataFrame."""

    def listar_dataframe(self, ordenar_por_id: bool = True):
        """Carrega todos os clientes do JSON em um DataFrame Pandas."""
        pd = _importar_pandas("IndiceClientesHibrido.listar_dataframe")
        df = pd.read_json(self.caminho_json)
        if ordenar_por_id and "id" in df.columns:
            df = df.sort_values("id", kind="mergesort").reset_index(drop=True)
        return df

    def listar_todos(self, ordenar_por_id: bool = True) -> List[Dict[str, Any]]:
        """Retorna todos os clientes como lista de dicionários usando o DataFrame Pandas."""
        df = self.listar_dataframe(ordenar_por_id=ordenar_por_id)
        return df.to_dict(orient="records")

