class Registro:
    """Elemento armazenado nas páginas da Árvore B."""

    def __init__(self, chave=None, elemento=None):
        self.Chave = chave
        self.Elemento = elemento

class Pagina:
    """Nó da Árvore B com capacidade para 'ordem' chaves e 'ordem + 1' ponteiros."""

    def __init__(self, ordem):
        self.n = 0
        self.r = [None for _ in range(ordem)]
        self.p = [None for _ in range(ordem + 1)]

class ArvoreB:
    """Árvore B indexada pelo ID único do cliente com instrumentação de desempenho."""

    def __init__(self, ordem=5):
        if ordem < 2:
            raise ValueError("A ordem da Árvore B deve ser maior ou igual a 2.")
        self.ordem = ordem
        self.raiz = None
        self.tamanho = 0
        self.divisoes = 0
        self.comparacoes = 0
        self.paginas_visitadas = 0
        self.ultima_busca = {
            "comparacoes": 0,
            "paginas_visitadas": 0,
        }

    def _pesquisar(self, chave, ap, metricas):
        """Busca recursiva por chave a partir da página ap."""
        if ap is None:
            return None

        metricas["paginas_visitadas"] += 1
        i = 1
        while i < ap.n and chave > ap.r[i - 1].Chave:
            metricas["comparacoes"] += 1
            i += 1

        if i <= ap.n:
            metricas["comparacoes"] += 1
            if chave == ap.r[i - 1].Chave:
                return ap.r[i - 1]

        if chave < ap.r[i - 1].Chave:
            return self._pesquisar(chave, ap.p[i - 1], metricas)
        return self._pesquisar(chave, ap.p[i], metricas)

    def _insere_na_pagina(self, ap, reg, ap_dir):
        """Desloca registros e ponteiros para inserir ordenadamente na página."""
        k = ap.n
        nao_achou_posicao = k > 0
        while nao_achou_posicao:
            self.comparacoes += 1
            if reg.Chave >= ap.r[k - 1].Chave:
                nao_achou_posicao = False
                break
            ap.r[k] = ap.r[k - 1]
            ap.p[k + 1] = ap.p[k]
            k -= 1
            if k < 1:
                nao_achou_posicao = False

        ap.r[k] = reg
        ap.p[k + 1] = ap_dir
        ap.n += 1

    def _ins(self, reg, ap, cresceu, reg_retorno, ap_retorno):
        """Executa a descida recursiva e realiza a cisão da página em caso de overflow."""
        i = 1
        if ap is None:
            return True, reg, None

        while i < ap.n and reg.Chave > ap.r[i - 1].Chave:
            self.comparacoes += 1
            i += 1

        self.comparacoes += 1
        if reg.Chave == ap.r[i - 1].Chave:
            raise ValueError(f"Registro com ID {reg.Chave} já existe na Árvore B.")

        if reg.Chave < ap.r[i - 1].Chave:
            i -= 1

        cresceu, reg_retorno, ap_retorno = self._ins(
            reg, ap.p[i], cresceu, reg_retorno, ap_retorno
        )

        if not cresceu:
            return cresceu, reg_retorno, ap_retorno

        if ap.n < self.ordem:
            self._insere_na_pagina(ap, reg_retorno, ap_retorno)
            return False, reg_retorno, ap_retorno

        self.divisoes += 1
        ap_temp = Pagina(self.ordem)
        ap_temp.n = 0
        ap_temp.p[0] = None

        meio = self.ordem // 2
        if i < meio + 1:
            self._insere_na_pagina(ap_temp, ap.r[self.ordem - 1], ap.p[self.ordem])
            ap.n -= 1
            self._insere_na_pagina(ap, reg_retorno, ap_retorno)
        else:
            self._insere_na_pagina(ap_temp, reg_retorno, ap_retorno)

        for j in range(meio + 2, self.ordem + 1):
            self._insere_na_pagina(ap_temp, ap.r[j - 1], ap.p[j])

        ap.n = meio
        ap_temp.p[0] = ap.p[meio + 1]
        reg_retorno = ap.r[meio]
        ap_retorno = ap_temp
        return cresceu, reg_retorno, ap_retorno

    def inserir(self, id_cliente, cliente):
        """Insere um novo cliente na Árvore B usando o ID inteiro como chave."""
        chave = int(id_cliente)
        reg = Registro(chave=chave, elemento=cliente)

        cresceu, reg_retorno, ap_retorno = self._ins(
            reg, self.raiz, False, Registro(), Pagina(self.ordem)
        )
        if cresceu:
            ap_temp = Pagina(self.ordem)
            ap_temp.n = 1
            ap_temp.r[0] = reg_retorno
            ap_temp.p[1] = ap_retorno
            ap_temp.p[0] = self.raiz
            self.raiz = ap_temp

        self.tamanho += 1

    def buscar(self, id_cliente):
        """Busca um cliente pelo ID e registra métricas de páginas visitadas e comparações."""
        metricas = {"comparacoes": 0, "paginas_visitadas": 0}
        registro = self._pesquisar(int(id_cliente), self.raiz, metricas)

        self.ultima_busca = metricas
        self.comparacoes += metricas["comparacoes"]
        self.paginas_visitadas += metricas["paginas_visitadas"]

        return registro.Elemento if registro is not None else None

    def alterar(self, id_cliente, dados):
        """Atualiza os campos de um cliente existente sem alterar sua chave na árvore."""
        metricas = {"comparacoes": 0, "paginas_visitadas": 0}
        registro = self._pesquisar(int(id_cliente), self.raiz, metricas)

        self.ultima_busca = metricas
        self.comparacoes += metricas["comparacoes"]
        self.paginas_visitadas += metricas["paginas_visitadas"]

        if registro is None:
            return False

        for campo, valor in dados.items():
            if campo != "id" and valor is not None:
                registro.Elemento[campo] = valor
        return True

    def _percurso_em_ordem(self, ap, lista):
        """Percorre a árvore em ordem crescente de ID."""
        if ap is not None:
            i = 0
            while i < ap.n:
                self._percurso_em_ordem(ap.p[i], lista)
                lista.append(ap.r[i].Elemento)
                i += 1
            self._percurso_em_ordem(ap.p[i], lista)

    def listar_ordem(self):
        """Retorna todos os clientes ordenados de forma crescente pelo ID."""
        resultado = []
        self._percurso_em_ordem(self.raiz, resultado)
        return resultado

    def carregar(self, clientes):
        """Reinicializa a árvore e carrega uma coleção de clientes de forma idempotente."""
        self.raiz = None
        self.tamanho = 0
        self.divisoes = 0
        self.comparacoes = 0
        self.paginas_visitadas = 0
        self.ultima_busca = {"comparacoes": 0, "paginas_visitadas": 0}

        for cliente in clientes:
            self.inserir(cliente["id"], cliente)
        return self.tamanho

    def altura(self):
        """Calcula a altura atual da Árvore B em níveis."""
        nivel = 0
        atual = self.raiz
        while atual is not None:
            nivel += 1
            atual = atual.p[0]
        return nivel

    def estatisticas(self):
        """Retorna os indicadores estruturais e de instrumentação da Árvore B."""
        return {
            "ordem": self.ordem,
            "total_registros": self.tamanho,
            "altura": self.altura(),
            "divisoes": self.divisoes,
            "comparacoes_totais": self.comparacoes,
            "paginas_visitadas_totais": self.paginas_visitadas,
            "ultima_busca": dict(self.ultima_busca),
        }