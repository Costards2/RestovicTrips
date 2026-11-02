# GlobalSIM - Etapa 1

## Objetivo do Projeto
A GlobalSIM é uma aplicação para administrar serviços de internet por eSIM. A Etapa 1 foca no cadastro de países e verificação de cobertura.

## Arquitetura e Tabela Hash
O projeto utiliza Flask para web, JSON para persistência, e uma Tabela Hash customizada para estruturação de dados em memória.
A chave da Hash é o código do país (2 letras). Colisões são tratadas usando encadeamento separado (Linked List). O desempenho é $O(1)$ médio, mas $O(n)$ no pior caso dependendo do fator de carga e distribuição.

## Integrantes do projeto
Pedro Costard, Mirela Fernandes, Lucy Lima  e Gustavo Fernandes

## Diferenciais: Painel de Monitoramento da Tabela Hash e Ranking de Países por Conectividade da Rede
1- Painel de Monitoramento da Tabela Hash. Resolve o problema da "caixa preta" algorítmica, provendo uma visualização real do desempenho da Hash: colisões, ocupação de buckets, fator de carga e operações de busca.

2- Ranking de Países por Conectividade da Rede. O diferencial identifica os países com maior e menor nível de conectividade dentro da rede. A conectividade de cada país é medida pelo número de conexões diretas e pela latência média até os demais países, calculada com Dijkstra. O sistema gera um ranking que mostra quais países estão mais bem conectados e quais têm a maior latência média, por ficarem mais afastados na rede.

## Como Executar
1. Instale o Flask e Pytest: `pip install flask pytest`
2. Execute a aplicação: `python app.py`
3. Execute os testes: `pytest test_app.py`

