# GlobalSIM — Administração de Serviços de Internet por eSIM

Aplicação Web desenvolvida em **Python** e **Flask** para a disciplina de **Estruturas de Dados II** (Sistemas de Informação — DCET I / UNEB, Prof. Maria Inés Restovic). O projeto administra países atendidos, cobertura de rede, cadastro de clientes e planos de dados por eSIM, integrando estruturas de dados em memória com persistência em arquivos JSON.

## Arquitetura e Estruturas de Dados

A aplicação separa a lógica das estruturas de dados das rotas Web em Flask, utilizando arquivos JSON apenas para carga inicial e persistência em disco:

### 1. Tabela Hash (`tabela_hash.py` — Etapa 1)
* **Finalidade:** Armazenamento e consulta de cobertura dos países atendidos pela GlobalSIM (`codigo`, `pais`, `regiao`, `operadora`, `tecnologia`).
* **Chave:** Código internacional do país de 2 letras (tratamento *case-insensitive*, ex.: `BR`, `PT`, `IT`, `US`).
* **Tratamento de Colisões:** Encadeamento separado (*Separate Chaining*), mantendo listas encadeadas nos *buckets* em caso de colisão.
* **Complexidade:** $O(1)$ no caso médio para inserção, busca e remoção; $O(n)$ no pior caso, dependendo do fator de carga ($\alpha = n / m$) e da distribuição das chaves.
* **Instrumentação:** Contabilização de capacidade, total de elementos inseridos e número de colisões.

### 2. Árvore B (`b_tree.py` — Etapa 2)
* **Finalidade:** Gerenciamento escalável de clientes e eSIMs (`id`, `nome`, `email`, `esim`, `pacote`, `status`), preparada para operar com conjuntos de aproximadamente 1.000 registros.
* **Chave:** `id` numérico único do cliente.
* **Operações Implementadas:**
  * Inserção balanceada com cisão (*split*) de páginas em caso de *overflow*;
  * Busca recursiva por ID;
  * Percurso em ordem (`listar_ordem()`) para listagem crescente de clientes;
  * Alteração de dados cadastrais mantendo a integridade da chave;
  * Carga em lote idempotente (`carregar()`).
* **Complexidade:** $O(\log_t n)$ para busca e inserção.
* **Instrumentação:** Medição de altura da árvore, total de divisões de páginas, comparações realizadas e páginas visitadas por busca.

### 3. Grafos Ponderados (Etapa 3 — Escopo do Projeto)
* **Finalidade:** Representação da rede internacional da GlobalSIM, onde os países atendidos são vértices e as conexões entre pontos da infraestrutura são arestas ponderadas pela latência simulada em milissegundos ($ms$).
* **Algoritmos Previstos na Especificação:** Busca em Largura (BFS), Busca em Profundidade (DFS) e algoritmo de Dijkstra para cálculo de rotas de menor latência entre origem e destino.

## Diferencial da Equipe

### Ranking de Países por Conectividade da Rede
Identifica os países com maior e menor nível de conectividade dentro da rede internacional. A conectividade de cada país é avaliada pelo número de conexões diretas e pela latência média até os demais países, calculada com o algoritmo de **Dijkstra**, gerando um ranking que evidencia os países mais bem conectados e aqueles com maior latência média por estarem mais afastados na topologia.

## Estrutura do Projeto

(Adcicionar ao fim do projeto) 

## Como Executar

### 1. Ativar o ambiente virtual e instalar dependências

```bash
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Linux / macOS
source venv/bin/activate

# Instalação das dependências
pip install -r requirements.txt
```

*(Ou diretamente via `pip install flask pytest`)*

### 2. Iniciar a aplicação Web

```bash
python app.py
```

A aplicação ficará disponível localmente em `http://127.0.0.1:5000`.

### 3. Executar os testes automatizados

```bash
pytest -v
```
