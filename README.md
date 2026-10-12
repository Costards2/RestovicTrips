# GlobalSIM - Etapa 1

## Objetivo do Projeto
A GlobalSIM é uma aplicação para administrar serviços de internet por eSIM[cite: 1]. A Etapa 1 foca no cadastro de países e verificação de cobertura[cite: 3].

## Arquitetura e Tabela Hash
O projeto utiliza Flask para web, JSON para persistência, e uma Tabela Hash customizada para estruturação de dados em memória.
A chave da Hash é o código do país (2 letras)[cite: 3]. Colisões são tratadas usando encadeamento separado (Linked List). O desempenho é $O(1)$ médio, mas $O(n)$ no pior caso dependendo do fator de carga e distribuição.

## Diferencial: Painel de Monitoramento da Tabela Hash
Resolve o problema da "caixa preta" algorítmica, provendo uma visualização real do desempenho da Hash: colisões, ocupação de buckets, fator de carga e operações de busca.

## Como Executar
1. Instale o Flask e Pytest: `pip install flask pytest`
2. Execute a aplicação: `python app.py`
3. Execute os testes: `pytest test_app.py`
