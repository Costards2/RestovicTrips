import json
import os
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

    @property
    def tamanho(self) -> int:
        return self.arvore.tamanho

    @property
    def ultima_busca(self) -> Dict[str, int]:
        return self.arvore.ultima_busca

    @property
    def ultimo_caminho(self) -> List[List[int]]:
        return self.arvore.ultimo_caminho

    def inspecionar_niveis(self, limite_por_nivel: int = 8) -> List[Dict[str, Any]]:
        """Retorna os níveis da Árvore B com os offsets (inicio, tamanho) para visualização."""
        return self.arvore.inspecionar_niveis(limite_por_nivel=limite_por_nivel)

    def estatisticas(self) -> Dict[str, Any]:
        """Retorna os indicadores estruturais e de instrumentação da Árvore B."""
        return self.arvore.estatisticas()

    def indexar(self) -> int:
        """Varre o arquivo JSON em modo binário e indexa IDs e offsets na Árvore B."""
        self.arvore = ArvoreB(ordem=self.arvore.ordem)

        if not os.path.exists(self.caminho_json):
            diretorio = os.path.dirname(self.caminho_json)
            if diretorio:
                os.makedirs(diretorio, exist_ok=True)
            with open(self.caminho_json, "wb") as arquivo:
                arquivo.write(b"[]\n")
            return 0

        with open(self.caminho_json, "rb") as arquivo:
            conteudo = arquivo.read()

        for inicio, tamanho in _iterar_objetos_json_bytes(conteudo):
            trecho = conteudo[inicio : inicio + tamanho].decode("utf-8")
            cliente = json.loads(trecho)
            self.arvore.inserir(cliente["id"], (inicio, tamanho))

        return self.arvore.tamanho

    def inserir(self, id_cliente: int, novo_cliente: Dict[str, Any]) -> Tuple[int, int]:
        """Anexa o novo cliente ao array JSON em disco e indexa seu offset na Árvore B."""
        chave = int(id_cliente)
        if self.arvore.buscar(chave) is not None:
            raise ValueError(f"Registro com ID {chave} já existe na Árvore B.")

        novo_bytes = json.dumps(novo_cliente, indent=4, ensure_ascii=False).encode("utf-8")

        if not os.path.exists(self.caminho_json) or os.path.getsize(self.caminho_json) == 0:
            diretorio = os.path.dirname(self.caminho_json)
            if diretorio:
                os.makedirs(diretorio, exist_ok=True)
            with open(self.caminho_json, "wb") as arquivo:
                arquivo.write(b"[\n")
                inicio = arquivo.tell()
                arquivo.write(novo_bytes)
                arquivo.write(b"\n]\n")
        else:
            with open(self.caminho_json, "r+b") as arquivo:
                arquivo.seek(0, os.SEEK_END)
                pos = arquivo.tell() - 1
                while pos >= 0:
                    arquivo.seek(pos)
                    if arquivo.read(1) == b"]":
                        break
                    pos -= 1
                if pos < 0:
                    raise ValueError("Arquivo JSON de clientes inválido: ']' final não encontrado.")

                pos_anterior = pos - 1
                ultimo_byte = b""
                while pos_anterior >= 0:
                    arquivo.seek(pos_anterior)
                    b = arquivo.read(1)
                    if b not in (b" ", b"\t", b"\r", b"\n"):
                        ultimo_byte = b
                        break
                    pos_anterior -= 1

                prefixo = b"\n" if ultimo_byte == b"[" else b",\n"
                arquivo.seek(pos_anterior + 1)
                arquivo.write(prefixo)
                inicio = arquivo.tell()
                arquivo.write(novo_bytes)
                arquivo.write(b"\n]\n")
                arquivo.truncate()

        localizacao = (inicio, len(novo_bytes))
        self.arvore.inserir(chave, localizacao)
        return localizacao

    def alterar(self, id_cliente: int, dados: Dict[str, Any]) -> bool:
        """Atualiza um cliente no JSON em disco e reindexa os offsets na Árvore B."""
        chave = int(id_cliente)
        if self.arvore.buscar(chave) is None:
            return False

        with open(self.caminho_json, "r", encoding="utf-8") as arquivo:
            clientes = json.load(arquivo)

        encontrado = False
        for cliente in clientes:
            if int(cliente["id"]) == chave:
                for campo, valor in dados.items():
                    if campo != "id" and valor is not None:
                        cliente[campo] = valor
                encontrado = True
                break

        if not encontrado:
            return False

        with open(self.caminho_json, "w", encoding="utf-8") as arquivo:
            json.dump(clientes, arquivo, indent=4, ensure_ascii=False)

        self.indexar()
        return True

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
        if not os.path.exists(self.caminho_json) or os.path.getsize(self.caminho_json) == 0:
            return pd.DataFrame()
        df = pd.read_json(self.caminho_json)
        if ordenar_por_id and "id" in df.columns:
            df = df.sort_values("id", kind="mergesort").reset_index(drop=True)
        return df

    def listar_todos(self, ordenar_por_id: bool = True) -> List[Dict[str, Any]]:
        """Retorna todos os clientes como lista de dicionários usando o DataFrame Pandas."""
        df = self.listar_dataframe(ordenar_por_id=ordenar_por_id)
        return df.to_dict(orient="records")

    def listar_ordem(self, ordenar_por_id: bool = True) -> List[Dict[str, Any]]:
        """Alias compatível com a interface da Árvore B para listar clientes ordenados por ID."""
        return self.listar_todos(ordenar_por_id=ordenar_por_id)

