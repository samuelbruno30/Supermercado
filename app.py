from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
import re
from concurrent.futures import ThreadPoolExecutor

# Importa as funções de busca de dentro da sua pasta 'scrapers'
from scrapers.atacadao import buscar as buscar_atacadao
from scrapers.carrefur import buscar as buscar_carrefour 
from scrapers.extrabom import buscar as buscar_extrabom

app = FastAPI(
    title="API de Comparação de Preços Paralela",
    description="Backend de alta performance com processamento multi-thread."
)

class PayloadLista(BaseModel):
    produtos: List[str] = Field(..., min_items=1, max_items=15)

def sanitizar_texto(texto: str) -> str:
    # REGRA DE SEGURANÇA: Limpa contra caracteres maliciosos e injeções
    texto_limpo = re.sub(r'[^a-zA-Z0-9áéíóúàèìòùâêîôûãõç\s]', '', texto)
    return re.sub(r'\s+', ' ', texto_limpo).strip()

# Função auxiliar que o Worker paralelo vai usar para processar um único mercado inteiro
def rodar_scrapers_do_mercado(nome_mercado, funcao_busca, lista_produtos):
    """
    Esta função roda dentro de uma thread isolada para cada mercado.
    Ela busca todos os produtos da lista naquele supermercado específico.
    """
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
            # Fallback seguro caso o robô falhe ou o site caia
            detalhes[produto] = {"erro": "Módulo indisponível"}
            
    return {
        "mercado": nome_mercado,
        "total": total_acumulado,
        "encontrados": itens_encontrados,
        "produtos": detalhes
    }

@app.post("/api/comparar")
async def comparar_lista(payload: PayloadLista):
    itens_validados = []
    for item in payload.produtos:
        nome_limpo = sanitizar_texto(item)
        if len(nome_limpo) >= 3:
            itens_validados.append(nome_limpo)
            
    if not itens_validados:
        raise HTTPException(status_code=400, detail="Nenhum termo válido enviado.")

    mercados_mapeados = [
        ("Atacadão", buscar_atacadao),
        ("Carrefour", buscar_carrefour),
        ("ExtraBom", buscar_extrabom)
    ]

    # =========================================================================
    # O MOTOR DE PARALELISMO (THREADS ASYNC)
    # =========================================================================
    resultados_paralelos = []
    
    # Abrimos um pool com no máximo 3 trabalhadores (um para cada mercado)
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Dispara as 3 buscas simultaneamente em background
        futuros = [
            executor.submit(rodar_scrapers_do_mercado, nome, funcao, itens_validados)
            for nome, funcao in mercados_mapeados  # <-- CORRIGIDO AQUI!
        ]
        
        # Coleta as respostas à medida que forem terminando
        for futuro in futuros:
            resultados_paralelos.append(futuro.result())

    # =========================================================================
    # REESTRUTURAÇÃO DOS DADOS PARA O FRONT-END
    # =========================================================================
    totais = {}
    encontrados = {}
    resumo_mercados = {}
    
    # Prepara dicionários de apoio baseados no retorno das threads
    for res in resultados_paralelos:
        nome_m = res["mercado"]
        totais[nome_m] = res["total"]
        encontrados[nome_m] = res["encontrados"]
        
        resumo_mercados[nome_m] = {
            "total_acumulado": round(res["total"], 2),
            "itens_encontrados": f"{res['encontrados']}/{len(itens_validados)}",
            "lista_completa": res["encontrados"] == len(itens_validados)
        }

    # Monta a tabela comparativa item por item
    tabela_comparativa = []
    for produto in itens_validados:
        bloco_produto = {"produto_solicitado": produto, "mercados": {}}
        for res in resultados_paralelos:
            nome_m = res["mercado"]
            bloco_produto["mercados"][nome_m] = res["produtos"].get(produto)
        tabela_comparativa.append(bloco_produto)

    # Lógica do campeão de economia (desconsidera listas incompletas)
    totais_validos = {}
    for mercado, valor_total in totais.items():
        if encontrados[mercado] == len(itens_validados):
            totais_validos[mercado] = round(valor_total, 2)

    if totais_validos:
        vencedor = min(totais_validos, key=totais_validos.get)
        vencedor_texto = f"{vencedor} (R$ {totais_validos[vencedor]:.2f})"
    else:
        vencedor_texto = "Nenhum mercado possui todos os itens da lista simultaneamente"

    return {
        "status": "sucesso",
        "total_itens_buscados": len(itens_validados),
        "campeao_economia": vencedor_texto,
        "resumo_mercados": resumo_mercados,
        "detalhe_produtos": tabela_comparativa
    }