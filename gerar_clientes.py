import json
import os
import random
import unicodedata

PRIMEIROS_NOMES = [
    "Lucas", "Maria", "Gabriel", "Ana", "Matheus", "Beatriz", "Guilherme", "Julia",
    "Felipe", "Larissa", "Rafael", "Camila", "Rodrigo", "Mariana", "Gustavo", "Carolina",
    "Leonardo", "Fernanda", "Bruno", "Amanda", "Thiago", "Leticia", "Diego", "Bruna",
    "Pedro", "Juliana", "Vinicius", "Jessica", "Eduardo", "Vanessa", "Caio", "Aline",
    "Daniel", "Patricia", "Alexandre", "Renata", "Marcelo", "Natalia", "Vitor", "Isabela",
    "Andre", "Bianca", "Joao", "Luana", "Henrique", "Carla", "Arthur", "Debora",
    "Murilo", "Thais", "Carlos", "Helena", "Marcos", "Alice", "Samuel", "Manuela"
]

SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira",
    "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Lopes",
    "Soares", "Fernandes", "Vieira", "Barbosa", "Rocha", "Dias", "Nascimento", "Andrade",
    "Moreira", "Nunes", "Marques", "Machado", "Mendes", "Freitas", "Cardoso", "Ramos",
    "Goncalves", "Santana", "Teixeira", "Pinto", "Cavalcanti", "Castro", "Moura"
]

PACOTES_VALIDOS = [101, 102, 201, 202, 301]
STATUS_VALIDOS = ["ativo", "inativo"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO_CLIENTES_PADRAO = os.path.join(BASE_DIR, "arquivos", "clientes.json")


def _remover_acentos(texto: str) -> str:
    """Remove caracteres acentuados para geração de emails padronizados."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def gerar_clientes(quantidade: int = 1000, seed: int = 42) -> list:
    """
    Gera uma coleção de clientes simulados com IDs únicos de 5 dígitos (10000-99999).
    Cada registro contém: id, nome, email, esim, pacote válido e status.
    """
    if seed is not None:
        random.seed(seed)

    if quantidade > 90000:
        raise ValueError("Quantidade máxima suportada para IDs únicos de 5 dígitos é 90.000.")

    # Amostragem sem reposição para garantir IDs únicos de 5 dígitos
    ids_unicos = random.sample(range(10000, 100000), quantidade)
    clientes = []

    for cid in ids_unicos:
        primeiro_nome = random.choice(PRIMEIROS_NOMES)
        sobrenome = random.choice(SOBRENOMES)
        nome_completo = f"{primeiro_nome} {sobrenome}"

        # Email sem acentos baseado no nome e ID único para evitar duplicidades
        nome_email = _remover_acentos(primeiro_nome)
        sobrenome_email = _remover_acentos(sobrenome)
        email = f"{nome_email}.{sobrenome_email}{cid % 1000}@email.com"

        # eSIM único com formato padronizado conforme especificação
        esim_codigo = random.randint(10000, 99999)
        esim = f"ESIM-{esim_codigo}"

        # Pacote dentre os 5 válidos definidos na especificação
        pacote = random.choice(PACOTES_VALIDOS)

        # Distribuição de status (85% ativo, 15% inativo)
        status = "ativo" if random.random() < 0.85 else "inativo"

        clientes.append({
            "id": cid,
            "nome": nome_completo,
            "email": email,
            "esim": esim,
            "pacote": pacote,
            "status": status
        })

    return clientes


def salvar_clientes_em_arquivo(clientes: list, caminho: str = None) -> str:
    """Salva a lista de clientes em arquivo JSON formatado."""
    caminho_final = caminho or CAMINHO_CLIENTES_PADRAO
    diretorio = os.path.dirname(caminho_final)
    if diretorio and not os.path.exists(diretorio):
        os.makedirs(diretorio, exist_ok=True)

    with open(caminho_final, "w", encoding="utf-8") as f:
        json.dump(clientes, f, indent=4, ensure_ascii=False)

    return caminho_final


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gerador de massa de clientes para GlobalSIM/R-Mobile.")
    parser.add_argument("--qtd", type=int, default=1000, help="Quantidade de clientes a gerar (padrão: 1000)")
    parser.add_argument("--seed", type=int, default=42, help="Semente para reproducibilidade (padrão: 42)")
    parser.add_argument("--out", type=str, default=None, help="Caminho do arquivo de saída JSON")

    args = parser.parse_args()
    dados = gerar_clientes(quantidade=args.qtd, seed=args.seed)
    caminho_salvo = salvar_clientes_em_arquivo(dados, args.out)
    print(f"Sucesso: {len(dados)} clientes gerados e salvos em: {caminho_salvo}")
