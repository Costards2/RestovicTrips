from flask import Flask, render_template, request, redirect, url_for, flash
from tabela_hash import TabelaHash
from b_tree import ArvoreB
import persistencia
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'chave_secreta_padrao_segura')

# ==============================================================================
# INICIALIZAÇÃO DAS ESTRUTURAS DE DADOS
# ==============================================================================
# 1. Tabela Hash (Países e Cobertura - Etapa 1)
tabela = TabelaHash()
dados_iniciais = persistencia.carregar_dados()
for p in dados_iniciais:
    tabela.inserir(p['codigo'], p)

# 2. Árvore B (Clientes e eSIMs - Etapa 2)
arvore_clientes = ArvoreB(ordem=5)


def carregar_clientes_na_arvore(arvore: ArvoreB = None) -> ArvoreB:
    """Carrega os clientes a partir do arquivo JSON na Árvore B de forma idempotente."""
    alvo = arvore if arvore is not None else arvore_clientes
    clientes = persistencia.carregar_clientes()
    alvo.carregar(clientes)
    return alvo


# Carga idempotente na Árvore B ao subir a aplicação
carregar_clientes_na_arvore(arvore_clientes)

# 3. Pacotes de Serviço (Etapa 2)
pacotes = persistencia.carregar_pacotes()
mapa_pacotes = persistencia.obter_mapa_pacotes()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        codigo = request.form.get('codigo').strip().upper()
        dados = {
            "codigo": codigo,
            "pais": request.form.get('pais').strip(),
            "regiao": request.form.get('regiao').strip(),
            "operadora": request.form.get('operadora').strip(),
            "tecnologia": request.form.get('tecnologia').strip()
        }
        if tabela.inserir(codigo, dados):
            persistencia.salvar_dados(tabela)
            flash('País cadastrado com sucesso!', 'success')
            return redirect(url_for('paises'))
        else:
            flash('Erro: Código já cadastrado.', 'danger')
    return render_template('cadastro.html')

@app.route('/consulta', methods=['GET', 'POST'])
def consulta():
    resultado = None
    if request.method == 'POST':
        codigo = request.form.get('codigo').strip()
        resultado = tabela.buscar(codigo)
        if not resultado:
            flash('País não encontrado ou sem cobertura.', 'danger')
    return render_template('consulta.html', resultado=resultado)

@app.route('/paises')
def paises():
    lista = tabela.listar_todos()
    return render_template('paises.html', paises=lista)

@app.route('/editar/<codigo>', methods=['GET', 'POST'])
def editar(codigo):
    pais = tabela.buscar(codigo)
    if not pais:
        flash('País não encontrado.', 'danger')
        return redirect(url_for('paises'))
        
    if request.method == 'POST':
        novos_dados = {
            "pais": request.form.get('pais').strip(),
            "regiao": request.form.get('regiao').strip(),
            "operadora": request.form.get('operadora').strip(),
            "tecnologia": request.form.get('tecnologia').strip()
        }
        if tabela.alterar(codigo, novos_dados):
            persistencia.salvar_dados(tabela)
            flash('Dados atualizados com sucesso!', 'success')
        else:
            flash('Erro ao atualizar.', 'danger')
        return redirect(url_for('paises'))
        
    return render_template('editar.html', pais=pais)

@app.route('/remover/<codigo>', methods=['POST'])
def remover(codigo):
    if tabela.remover(codigo):
        persistencia.salvar_dados(tabela)
        flash('País removido com sucesso!', 'success')
    else:
        flash('Erro ao remover o país.', 'danger')
    return redirect(url_for('paises'))

@app.route('/estatisticas')
def estatisticas():
    stats = tabela.obter_estatisticas()
    return render_template('estatisticas.html', stats=stats, tabela=tabela.tabela,
                           stats_arvore=arvore_clientes.estatisticas())

# ==============================================================================
# ETAPA 2 — CLIENTES (ÁRVORE B) E INTEGRAÇÃO COM A TABELA HASH
# ==============================================================================
POR_PAGINA = 50
STATUS_VALIDOS = ('ativo', 'inativo')
 
def _parse_id(texto):
    # Converte o ID digitado em inteiro positivo (None se for inválido)
    texto = (texto or '').strip()
    if not (texto.isascii() and texto.isdigit()) or int(texto) <= 0:
        return None
    return int(texto)
 
def _ler_formulario_cliente(form):
    # Lê e valida os campos do cliente: devolve (dados, erros)
    nome = (form.get('nome') or '').strip()
    email = (form.get('email') or '').strip()
    esim = (form.get('esim') or '').strip().upper()
    status = (form.get('status') or 'ativo').strip().lower()
    pacote = _parse_id(form.get('pacote'))
 
    erros = []
    if not nome:
        erros.append('Informe o nome do cliente.')
    if '@' not in email or '.' not in email.split('@')[-1]:
        erros.append('Informe um e-mail válido.')
    if pacote not in mapa_pacotes:
        erros.append('Pacote inválido. Escolha um pacote do catálogo.')
    if status not in STATUS_VALIDOS:
        erros.append('Status inválido.')
 
    dados = {
        "nome": nome,
        "email": email,
        "esim": esim,
        "pacote": pacote,
        "status": status
    }
    return dados, erros
 
def _avisos_integracao(cliente, pacote, pais):
    # Avisos (não bloqueantes) sobre a combinação cliente x pacote x destino
    avisos = []
    if cliente.get('status') != 'ativo':
        avisos.append('O eSIM deste cliente está inativo.')
    if pacote is None:
        avisos.append('O pacote do cliente não existe no catálogo.')
    elif pais is not None:
        nome = pacote['nome']
        regiao = pais.get('regiao', '')
        if nome.startswith('Europa') and regiao != 'Europa':
            avisos.append(f'O pacote {nome} não cobre a região {regiao}.')
        elif nome.startswith('América') and not regiao.startswith('América'):
            avisos.append(f'O pacote {nome} não cobre a região {regiao}.')
    return avisos
 
@app.route('/clientes')
def clientes():
    # Listagem paginada em ordem crescente de ID (percurso em ordem da Árvore B)
    todos = arvore_clientes.listar_ordem()
    total = len(todos)
    total_paginas = max(1, -(-total // POR_PAGINA))
    pagina = request.args.get('pagina', 1, type=int)
    pagina = min(max(pagina, 1), total_paginas)
    inicio = (pagina - 1) * POR_PAGINA
    return render_template('clientes.html',
                           clientes=todos[inicio:inicio + POR_PAGINA],
                           pagina=pagina,
                           total_paginas=total_paginas,
                           total=total,
                           mapa_pacotes=mapa_pacotes,
                           stats_arvore=arvore_clientes.estatisticas())
 
@app.route('/clientes/cadastrar', methods=['GET', 'POST'])
def cadastrar_cliente():
    if request.method == 'POST':
        id_cliente = _parse_id(request.form.get('id'))
        dados, erros = _ler_formulario_cliente(request.form)
        if id_cliente is None:
            erros.insert(0, 'O ID deve ser um número inteiro positivo.')
 
        if not erros:
            cliente = {"id": id_cliente, **dados}
            if not cliente["esim"]:
                cliente["esim"] = f'ESIM-{id_cliente:05d}'
            try:
                arvore_clientes.inserir(id_cliente, cliente)
            except ValueError:
                erros.append(f'Já existe um cliente com o ID {id_cliente}.')
            else:
                persistencia.salvar_clientes(arvore_clientes)
                flash('Cliente cadastrado com sucesso!', 'success')
                return redirect(url_for('consultar_cliente', id=id_cliente))
 
        for erro in erros:
            flash(erro, 'danger')
    return render_template('cadastro_cliente.html', pacotes=pacotes,
                           statuses=STATUS_VALIDOS, valores=request.form)
 
@app.route('/clientes/consultar', methods=['GET', 'POST'])
def consultar_cliente():
    # Aceita POST (formulário) e GET ?id= (usado após cadastro/edição)
    if request.method == 'POST':
        texto = request.form.get('id')
    else:
        texto = request.args.get('id')
    cliente = None
    pacote = None
    busca = None
 
    if texto is not None and texto.strip():
        id_cliente = _parse_id(texto)
        if id_cliente is None:
            flash('ID inválido. Digite apenas números.', 'danger')
        else:
            cliente = arvore_clientes.buscar(id_cliente)
            busca = dict(arvore_clientes.ultima_busca)
            if cliente is None:
                flash(f'Cliente {id_cliente} não encontrado.', 'danger')
            else:
                pacote = mapa_pacotes.get(cliente.get('pacote'))
    return render_template('consulta_cliente.html', cliente=cliente, pacote=pacote,
                           busca=busca, id_digitado=(texto or '').strip())
 
@app.route('/clientes/editar/<id_cliente>', methods=['GET', 'POST'])
def editar_cliente(id_cliente):
    id_num = _parse_id(id_cliente)
    cliente = None
    if id_num is not None:
        cliente = arvore_clientes.buscar(id_num)
    if cliente is None:
        flash('Cliente não encontrado.', 'danger')
        return redirect(url_for('clientes'))
 
    if request.method == 'POST':
        dados, erros = _ler_formulario_cliente(request.form)
        if not erros:
            if not dados["esim"]:
                dados["esim"] = None  # mantém o eSIM atual
            arvore_clientes.alterar(id_num, dados)
            persistencia.salvar_clientes(arvore_clientes)
            flash('Dados do cliente atualizados com sucesso!', 'success')
            return redirect(url_for('consultar_cliente', id=id_num))
        for erro in erros:
            flash(erro, 'danger')
    return render_template('editar_cliente.html', cliente=cliente,
                           pacotes=pacotes, statuses=STATUS_VALIDOS)
 
@app.route('/clientes/integrada', methods=['GET', 'POST'])
def consulta_integrada():
    # Integração Árvore B x Tabela Hash: cliente + pacote + país de destino
    ficha = None
    if request.method == 'POST':
        id_cliente = _parse_id(request.form.get('cliente'))
        destino = (request.form.get('destino') or '').strip().upper()
 
        if id_cliente is None:
            flash('Informe um ID de cliente válido (apenas números).', 'danger')
        elif not destino:
            flash('Informe o código do país de destino (ex.: IT).', 'danger')
        else:
            cliente = arvore_clientes.buscar(id_cliente)  # 1. Árvore B
            busca_arvore = dict(arvore_clientes.ultima_busca)
            if cliente is None:
                flash(f'Cliente {id_cliente} não encontrado.', 'danger')
            else:
                pais = tabela.buscar(destino)  # 2. Tabela Hash
                pacote = mapa_pacotes.get(cliente.get('pacote'))
                if pais is None:
                    flash(f'País {destino} não encontrado ou sem cobertura.', 'warning')
                ficha = {
                    "cliente": cliente,
                    "pacote": pacote,
                    "destino": destino,
                    "pais": pais,
                    "cobertura": pais is not None,
                    "avisos": _avisos_integracao(cliente, pacote, pais),
                    "busca_arvore": busca_arvore
                }
    return render_template('consulta_integrada.html', ficha=ficha)
 
if __name__ == '__main__':
    app.run(debug=True)
 

