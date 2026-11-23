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

def _comparar_graus_arvore_b(ordens=(2, 3, 5)):
    """Compara altura, divisões e custo de busca da Árvore B para diferentes ordens."""
    clientes = arvore_clientes.listar_ordem()
    id_amostra = clientes[len(clientes) // 2]["id"] if clientes else None
    comparacao = []

    for ordem in ordens:
        arv = ArvoreB(ordem=ordem)
        arv.carregar(clientes)
        if id_amostra is not None:
            arv.buscar(id_amostra)
        est = arv.estatisticas()
        comparacao.append({
            "ordem": ordem,
            "total_registros": est["total_registros"],
            "altura": est["altura"],
            "divisoes": est["divisoes"],
            "comparacoes_busca": est["ultima_busca"]["comparacoes"],
            "paginas_visitadas": est["ultima_busca"]["paginas_visitadas"],
        })

    return comparacao


@app.route('/estatisticas')
def estatisticas():
    stats = tabela.obter_estatisticas()
    b_stats = arvore_clientes.estatisticas()
    comparacao_graus = _comparar_graus_arvore_b()
    return render_template(
        'estatisticas.html',
        stats=stats,
        tabela=tabela.tabela,
        b_stats=b_stats,
        comparacao_graus=comparacao_graus,
    )


@app.route('/clientes')
def clientes():
    lista = arvore_clientes.listar_ordem()
    return render_template('clientes.html', clientes=lista)


STATUS_VALIDOS = ("ativo", "inativo")


def _validar_dados_cliente(form):
    """Valida nome, e-mail e status do formulário de cliente e devolve a lista de erros."""
    erros = []
    nome = form.get("nome", "").strip()
    email = form.get("email", "").strip()
    status = form.get("status", "ativo").strip().lower()

    if not nome:
        erros.append("Erro: Informe o nome do cliente.")
    if "@" not in email or "." not in email.split("@")[-1]:
        erros.append("Erro: Informe um e-mail válido.")
    if status not in STATUS_VALIDOS:
        erros.append("Erro: Status inválido.")
    return erros


@app.route('/clientes/cadastrar', methods=['GET', 'POST'])
def cadastro_cliente():
    if request.method == 'POST':
        id_raw = request.form.get('id', '').strip()
        pacote_raw = request.form.get('pacote', '').strip()

        if not id_raw.isdigit() or not (10000 <= int(id_raw) <= 99999):
            flash('Erro: O ID do cliente deve ser um número inteiro de 5 dígitos (10000 a 99999).', 'danger')
            return render_template('cadastro_cliente.html', pacotes=pacotes)

        id_cliente = int(id_raw)
        if arvore_clientes.buscar(id_cliente) is not None:
            flash('Erro: Já existe um cliente cadastrado com esse ID.', 'danger')
            return render_template('cadastro_cliente.html', pacotes=pacotes)

        if not pacote_raw.isdigit() or int(pacote_raw) not in mapa_pacotes:
            flash('Erro: Pacote selecionado é inválido.', 'danger')
            return render_template('cadastro_cliente.html', pacotes=pacotes)

        erros = _validar_dados_cliente(request.form)
        if erros:
            for erro in erros:
                flash(erro, "danger")
            return render_template("cadastro_cliente.html", pacotes=pacotes)

        novo_cliente = {
            "id": id_cliente,
            "nome": request.form.get('nome', '').strip(),
            "email": request.form.get('email', '').strip(),
            "esim": request.form.get("esim", "").strip().upper() or f"ESIM-{id_cliente:05d}",
            "pacote": int(pacote_raw),
            "status": request.form.get('status', 'ativo').strip().lower(),
        }
        arvore_clientes.inserir(id_cliente, novo_cliente)
        persistencia.salvar_clientes(arvore_clientes)
        flash('Cliente cadastrado com sucesso!', 'success')
        return redirect(url_for('clientes'))

    return render_template('cadastro_cliente.html', pacotes=pacotes)


@app.route('/clientes/editar/<int:id_cliente>', methods=['GET', 'POST'])
def editar_cliente(id_cliente):
    cliente = arvore_clientes.buscar(id_cliente)
    if not cliente:
        flash('Cliente não encontrado.', 'danger')
        return redirect(url_for('clientes'))

    if request.method == 'POST':
        pacote_raw = request.form.get('pacote', '').strip()
        if not pacote_raw.isdigit() or int(pacote_raw) not in mapa_pacotes:
            flash('Erro: Pacote selecionado é inválido.', 'danger')
            return render_template('editar_cliente.html', cliente=cliente, pacotes=pacotes)

        erros = _validar_dados_cliente(request.form)
        if erros:
            for erro in erros:
                flash(erro, "danger")
            return render_template("editar_cliente.html", cliente=cliente, pacotes=pacotes)

        novos_dados = {
            "nome": request.form.get('nome', '').strip(),
            "email": request.form.get('email', '').strip(),
            "esim": request.form.get("esim", "").strip().upper() or None,  # em branco mantém o atual
            "pacote": int(pacote_raw),
            "status": request.form.get('status', 'ativo').strip().lower(),
        }
        if arvore_clientes.alterar(id_cliente, novos_dados):
            persistencia.salvar_clientes(arvore_clientes)
            flash('Dados do cliente atualizados com sucesso!', 'success')
        else:
            flash('Erro ao atualizar o cliente.', 'danger')
        return redirect(url_for('clientes'))

    return render_template('editar_cliente.html', cliente=cliente, pacotes=pacotes)


@app.route('/clientes/consultar', methods=['GET', 'POST'])
def consulta_cliente():
    cliente = None
    pacote = None
    pais = None
    busca_metricas = None

    id_raw = (
        request.form.get('id_cliente', '').strip()
        if request.method == 'POST'
        else request.args.get('id', '').strip()
    )
    codigo_pais = request.form.get('codigo_pais', '').strip().upper() if request.method == 'POST' else ''

    if id_raw:
        if not id_raw.isdigit():
            flash('Informe um ID numérico válido para consultar o cliente.', 'danger')
        else:
            cliente = arvore_clientes.buscar(int(id_raw))
            busca_metricas = dict(arvore_clientes.ultima_busca)
            if not cliente:
                flash('Cliente não encontrado na Árvore B.', 'danger')
            else:
                pacote = mapa_pacotes.get(int(cliente['pacote']))
                if codigo_pais:
                    pais = tabela.buscar(codigo_pais)
                    if not pais:
                        flash('País de destino não encontrado ou sem cobertura.', 'warning')

    return render_template(
        'consulta_cliente.html',
        cliente=cliente,
        pacote=pacote,
        pais=pais,
        busca_metricas=busca_metricas,
    )

if __name__ == '__main__':
    app.run(debug=True)