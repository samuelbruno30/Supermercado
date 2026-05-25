from flask import Blueprint, render_template, request, flash, session, url_for
import re
from concurrent.futures import ThreadPoolExecutor
from scrapers.atacadao import buscar as buscar_atacadao
from scrapers.carrefur import buscar as buscar_carrefour 
from scrapers.extrabom import buscar as buscar_extrabom

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
    dados = None
    produtos_inseridos = ""
    
    if 'historico' not in session:
        session['historico'] = []
    if 'limite_gastos' not in session:
        session['limite_gastos'] = 0.0

    busca_historico = request.args.get('repesquisar')
    if busca_historico:
        produtos_inseridos = busca_historico
        request.method = 'POST'

    if request.method == 'POST' or busca_historico:
        produtos_texto = produtos_inseridos if busca_historico else request.form.get('produtos', '')
        produtos_inseridos = produtos_texto
        
        lista_crua = produtos_texto.split(',')
        itens_validados = []
        for item in lista_crua:
            nome_limpo = sanitizar_texto(item)
            if len(nome_limpo) >= 3:
                itens_validados.append(nome_limpo)
                
        if not itens_validados:
            flash("Por favor, insira ao menos um produto válido com 3 letras.", "warning")
            return render_template('index.html', dados=dados, produtos_inseridos=produtos_inseridos)

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
        
        # BLINDAGEM DA LÓGICA DO CAMPEÃO: Critério de Desempate Robusto
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

            # Regra 1: Ganha quem achou mais itens da lista do usuário
            if qtd_achada > max_itens:
                max_itens = qtd_achada
                menor_preco_total = preco_total
                melhor_mercado = nome_m
            # Regra 2: Se empatar na quantidade de itens, ganha quem tiver o menor preço acumulado
            elif qtd_achada == max_itens:
                if preco_total < menor_preco_total and qtd_achada > 0:
                    menor_preco_total = preco_total
                    melhor_mercado = nome_m

        if melhor_mercado and max_itens > 0:
            vencedor_texto = f"{melhor_mercado} (Achou {max_itens} itens - Total: R$ {menor_preco_total:.2f})"
        else:
            vencedor_texto = "Nenhum produto foi localizado nos supermercados."

        # Montagem da tabela comparativa
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

    return render_template('index.html', dados=dados, produtos_inseridos=produtos_inseridos)

# =========================================================================
# GESTOR DE ORÇAMENTO
# =========================================================================
@main_bp.route('/orcamento')
def orcamento():
    return render_template('orcamento.html')

@main_bp.route('/salvar-orcamento', methods=['POST'])
def salvar_orcamento():
    limite = float(request.form.get('limite', 0.0))
    session['limite_gastos'] = limite
    flash(f"🎯 Limite de orçamento definido para R$ {limite:.2f}!", "success")
    return render_template('orcamento.html')