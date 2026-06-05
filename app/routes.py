from flask import Blueprint, render_template, request, flash, session, url_for, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import re
from concurrent.futures import ThreadPoolExecutor
from scrapers.atacadao import buscar as buscar_atacadao
from scrapers.carrefur import buscar as buscar_carrefour 
from scrapers.extrabom import buscar as buscar_extrabom
import json
from db import db
from models.search import SearchQuery
from app.forms import BuscaForm, CadastroForm, LoginForm
from models.user import Usuario 

main_bp = Blueprint('main', __name__)

def sanitizar_texto(texto: str) -> str:
    texto_limpo = re.sub(r'[^a-zA-Z0-9áéíóúàèìòùâêîôûãõç\s]', '', texto)
    return re.sub(r'\s+', ' ', texto_limpo).strip()

def rodar_scrapers_do_mercado(nome_mercado, funcao_busca, lista_produtos):
    total_acumulado = 0.0
    itens_encontrados = 0
    detalhes = {}

    for produto in lista_produtos:
        try:
            resultado = funcao_busca(produto)
            if resultado is not None:
                total_acumulado += resultado["preco"]
                itens_encontrados += 1
                detalhes[produto] = {
                    "nome_real": resultado["nome"],
                    "preco": resultado["preco"]
                }
            else:
                detalhes[produto] = None
        except Exception:
            detalhes[produto] = {"erro": "Módulo indisponível"}
            
    return {
        "mercado": nome_mercado,
        "total": total_acumulado,
        "encontrados": itens_encontrados,
        "produtos": detalhes
    }

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        flash('Por favor, faça o login para usar o Montador de Listas.', 'warning')
        return redirect(url_for('main.login'))

    form = BuscaForm()
    dados = None
    produtos_inseridos = ""
    
    if 'historico' not in session:
        session['historico'] = []
    if 'limite_gastos' not in session:
        session['limite_gastos'] = 0.0

    # Pega o termo da URL (se existir)
    busca_historico = request.args.get('repesquisar')
    
    # 👇 A CORREÇÃO ESTÁ AQUI: 
    # Se for uma submissão de formulário (POST), ignoramos a URL!
    if request.method == 'POST' and form.validate_on_submit():
        busca_historico = None

    if busca_historico:
        produtos_inseridos = busca_historico
        
        busca_salva = SearchQuery.query.filter_by(
            user_id=session['user_id'], 
            raw_query=busca_historico
        ).order_by(SearchQuery.id.desc()).first()
        
        if busca_salva:
            dados = json.loads(busca_salva.results_json)
            return render_template('index.html', form=form, dados=dados, produtos_inseridos=produtos_inseridos)

    if form.validate_on_submit() or busca_historico:
        # Pega o texto do formulário se for POST, senão pega do histórico
        produtos_texto = form.produtos.data if request.method == 'POST' else busca_historico
        produtos_inseridos = produtos_texto
        
        lista_crua = produtos_texto.split(',')
        itens_validados = []
        for item in lista_crua:
            nome_limpo = sanitizar_texto(item)
            if len(nome_limpo) >= 3:
                itens_validados.append(nome_limpo)
                
        if not itens_validados:
            flash("Por favor, insira ao menos um produto válido com 3 letras.", "warning")
            return render_template('index.html', form=form, dados=dados, produtos_inseridos=produtos_inseridos)

        historico_atual = list(session['historico'])
        if produtos_texto not in historico_atual:
            historico_atual.insert(0, produtos_texto)
            session['historico'] = historico_atual[:5]

        mercados_mapeados = [
            ("Atacadão", buscar_atacadao),
            ("Carrefour", buscar_carrefour),
            ("ExtraBom", buscar_extrabom)
        ]

        resultados_paralelos = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futuros = [
                executor.submit(rodar_scrapers_do_mercado, nome, funcao, itens_validados)
                for nome, funcao in mercados_mapeados
            ]
            for futuro in futuros:
                resultados_paralelos.append(futuro.result())

        resumo_mercados = {}
        melhor_mercado = None
        max_itens = -1
        menor_preco_total = float('inf')

        for res in resultados_paralelos:
            nome_m = res["mercado"]
            qtd_achada = res["encontrados"]
            preco_total = res["total"]
            
            resumo_mercados[nome_m] = {
                "total_acumulado": round(preco_total, 2),
                "itens_encontrados": f"{qtd_achada}/{len(itens_validados)}"
            }

            if qtd_achada > max_itens:
                max_itens = qtd_achada
                menor_preco_total = preco_total
                melhor_mercado = nome_m
            elif qtd_achada == max_itens:
                if preco_total < menor_preco_total and qtd_achada > 0:
                    menor_preco_total = preco_total
                    melhor_mercado = nome_m

        if melhor_mercado and max_itens > 0:
            vencedor_texto = f"{melhor_mercado} (Achou {max_itens} itens - Total: R$ {menor_preco_total:.2f})"
        else:
            vencedor_texto = "Nenhum produto foi localizado nos supermercados."

        tabela_comparativa = []
        for produto in itens_validados:
            bloco_produto = {"produto_solicitado": produto, "mercados": {}, "menor_preco": float('inf')}
            for res in resultados_paralelos:
                nome_m = res["mercado"]
                prod_info = res["produtos"].get(produto)
                bloco_produto["mercados"][nome_m] = prod_info
                if prod_info and "preco" in prod_info:
                    if prod_info["preco"] < bloco_produto["menor_preco"]:
                        bloco_produto["menor_preco"] = prod_info["preco"]
            tabela_comparativa.append(bloco_produto)

        dados = {
            "campeao_economia": vencedor_texto,
            "resumo_mercados": resumo_mercados,
            "detalhe_produtos": tabela_comparativa
        }

        try:
            resumo_serializado = json.dumps(dados, ensure_ascii=False)
            busca = SearchQuery(
                raw_query=produtos_texto,
                sanitized=",".join(itens_validados),
                results_json=resumo_serializado,
                user_id=session['user_id'] 
            )
            db.session.add(busca)
            db.session.commit()
        except Exception:
            db.session.rollback()

    return render_template('index.html', form=form, dados=dados, produtos_inseridos=produtos_inseridos)

@main_bp.route('/orcamento')
def orcamento():
    if 'user_id' not in session:
        flash('Por favor, faça o login para acessar o orçamento.', 'warning')
        return redirect(url_for('main.login'))

    return render_template('orcamento.html')

@main_bp.route('/salvar-orcamento', methods=['POST'])
def salvar_orcamento():
    limite = float(request.form.get('limite', 0.0))
    session['limite_gastos'] = limite
    flash(f"🎯 Limite de orçamento definido para R$ {limite:.2f}!", "success")
    return render_template('orcamento.html')

@main_bp.route('/registo', methods=['GET', 'POST'])
def registo():
    form = CadastroForm()
    if form.validate_on_submit():
        user_existente = Usuario.query.filter_by(email=form.email.data).first()
        if user_existente:
            flash('Este e-mail já está registado.', 'danger')
            return render_template('registo.html', form=form)
        
        hashed_senha = generate_password_hash(form.senha.data)
        novo_usuario = Usuario(nome=form.nome.data, email=form.email.data, senha=hashed_senha)
        db.session.add(novo_usuario)
        db.session.commit()
        
        flash('Conta criada com sucesso! Por favor, inicie sessão.', 'success')
        return redirect(url_for('main.login'))
        
    return render_template('registo.html', form=form)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.senha, form.senha.data):
            session['user_id'] = user.id
            session['user_nome'] = user.nome
            flash(f'Bem-vindo(a) de volta, {user.nome}!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('E-mail ou palavra-passe incorretos.', 'danger')
            
    return render_template('login.html', form=form)

@main_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_nome', None)
    flash('Sessão terminada com sucesso.', 'info')
    return redirect(url_for('main.login'))