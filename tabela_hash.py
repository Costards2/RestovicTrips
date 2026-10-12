class Nodo:
    def __init__(self, chave, valor):
        self.chave = chave.upper()
        self.valor = valor
        self.proximo = None

class TabelaHash:
    def __init__(self, capacidade=11):
        self.capacidade = capacidade
        self.tabela = [None] * self.capacidade
        self.tamanho = 0
        self.colisoes = 0
        self.comparacoes_buscas = 0
        self.operacoes = 0

    def _hash(self, chave):
        soma = sum(ord(c) for c in chave.upper())
        return soma % self.capacidade

    def inserir(self, chave, valor):
        self.operacoes += 1
        indice = self._hash(chave)
        novo_nodo = Nodo(chave, valor)
        
        if self.tabela[indice] is None:
            self.tabela[indice] = novo_nodo
            self.tamanho += 1
            return True
        
        atual = self.tabela[indice]
        while atual:
            if atual.chave == chave.upper():
                return False # Código duplicado
            if atual.proximo is None:
                break
            atual = atual.proximo
            
        atual.proximo = novo_nodo
        self.colisoes += 1
        self.tamanho += 1
        return True

    def buscar(self, chave):
        self.operacoes += 1
        indice = self._hash(chave)
        atual = self.tabela[indice]
        
        while atual:
            self.comparacoes_buscas += 1
            if atual.chave == chave.upper():
                return atual.valor
            atual = atual.proximo
        return None

    def alterar(self, chave, novos_dados):
        self.operacoes += 1
        indice = self._hash(chave)
        atual = self.tabela[indice]
        
        while atual:
            if atual.chave == chave.upper():
                atual.valor.update(novos_dados)
                return True
            atual = atual.proximo
        return False

    def remover(self, chave):
        self.operacoes += 1
        indice = self._hash(chave)
        atual = self.tabela[indice]
        anterior = None
        
        while atual:
            if atual.chave == chave.upper():
                if anterior is None:
                    self.tabela[indice] = atual.proximo
                else:
                    anterior.proximo = atual.proximo
                self.tamanho -= 1
                return True
            anterior = atual
            atual = atual.proximo
        return False

    def listar_todos(self):
        lista = []
        for nodo in self.tabela:
            atual = nodo
            while atual:
                lista.append(atual.valor)
                atual = atual.proximo
        return lista

    def obter_estatisticas(self):
        posicoes_ocupadas = sum(1 for nodo in self.tabela if nodo is not None)
        fator_carga = self.tamanho / self.capacidade if self.capacidade > 0 else 0
        return {
            "capacidade": self.capacidade,
            "quantidade_registros": self.tamanho,
            "posicoes_ocupadas": posicoes_ocupadas,
            "fator_carga": round(fator_carga, 2),
            "colisoes": self.colisoes,
            "comparacoes": self.comparacoes_buscas,
            "operacoes": self.operacoes
        }