import streamlit as st
import requests
import pandas as pd
import folium  # type: ignore
from streamlit_folium import st_folium  # type: ignore
from streamlit_js_eval import get_geolocation  # type: ignore

st.set_page_config(page_title="Comparador de Mercados", layout="wide")

st.title("🛒 Montador de Lista de Compras Inteligente")
st.caption("Projeto de Web Avançada - Comparação de Preços com GPS Automático")

# =========================================================================
# INICIALIZAÇÃO DA MEMÓRIA DA SESSÃO (STATE)
# =========================================================================
if "produtos" not in st.session_state:
    st.session_state.produtos = []

if "dados_busca" not in st.session_state:
    st.session_state.dados_busca = None  # Vai guardar o resultado da API para não sumir

# Interface para adicionar itens
col1, col2 = st.columns([4, 1])
with col1:
    novo_produto = st.text_input("Digite o nome do produto:", key="input_produto", placeholder="Ex: Arroz Tipo 1")
with col2:
    if st.button("Adicionar", use_container_width=True) and novo_produto:
        st.session_state.produtos.append(novo_produto)

# Exibe os produtos adicionados
if st.session_state.produtos:
    st.write("### Itens na sua Lista:")
    for i, p in enumerate(st.session_state.produtos):
        st.text(f"🔹 {p}")
    
    col_limpar, _ = st.columns([1, 4])
    with col_limpar:
        if st.button("🗑️ Limpar Lista", use_container_width=True):
            st.session_state.produtos = []
            st.session_state.dados_busca = None  # Limpa os resultados antigos também
            st.rerun()

    # Botão para disparar a busca na API Backend
    if st.button("🚀 Comparar Preços nos Mercados", type="primary"):
        with st.spinner("Os robôs estão varrendo os supermercados paralelamente... Aguarde."):
            try:
                # Dispara a requisição HTTP para o seu app.py (FastAPI) na porta 8000
                resposta = requests.post(
                    "http://127.0.0.1:8000/api/comparar", 
                    json={"produtos": st.session_state.produtos}
                )
                
                if resposta.status_code == 200:
                    # SALVA NA MEMÓRIA DA SESSÃO: Daqui ele não some mais sozinho!
                    st.session_state.dados_busca = resposta.json()
                else:
                    st.error("Erro ao processar a lista no servidor backend.")
            except Exception as e:
                st.error(f"Não foi possível conectar à API: {e}")

    # =========================================================================
    # RENDERIZAÇÃO DOS RESULTADOS (Lê direto da memória salva)
    # =========================================================================
    if st.session_state.dados_busca is not None:
        dados = st.session_state.dados_busca
        
        st.success(f"🏆 Melhor Opção de Compra: {dados['campeao_economia']}")
        
        # Mostra os cards de resumo
        resumo = dados["resumo_mercados"]
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.metric("Atacadão", f"R$ {resumo['Atacadão']['total_acumulado']}", resumo['Atacadão']['itens_encontrados'])
        with c2:
            st.metric("Carrefour", f"R$ {resumo['Carrefour']['total_acumulado']}", resumo['Carrefour']['itens_encontrados'])
        with c3:
            st.metric("ExtraBom", f"R$ {resumo['ExtraBom']['total_acumulado']}", resumo['ExtraBom']['itens_encontrados'])
            
        st.write("---")
        st.write("### 📊 Tabela Comparativa de Produtos:")
        
        # Conversão do JSON para tabela visual
        linhas_tabela = []
        for item in dados["detalhe_produtos"]:
            nome_buscado = item["produto_solicitado"].capitalize()
            linha = {"Produto Buscado": nome_buscado}
            
            for mercado in ["Atacadão", "Carrefour", "ExtraBom"]:
                info_mercado = item["mercados"].get(mercado)
                if info_mercado and "preco" in info_mercado:
                    linha[mercado] = f"{info_mercado['nome_real']} — R$ {info_mercado['preco']:.2f}"
                elif info_mercado and "erro" in info_mercado:
                    linha[mercado] = "⚠️ Indisponível"
                else:
                    linha[mercado] = "❌ Não encontrado"
                    
            linhas_tabela.append(linha)
        
        df = pd.DataFrame(linhas_tabela)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # =========================================================================
        # BLOCO DO MAPA COM GPS FIXADO CONTRA REFRESH
        # =========================================================================
        st.write("---")
        st.write("### 📍 Onde comprar (Sua Localização Atual por GPS):")
        
        # Captura a geolocalização do navegador
        localizacao_gps = get_geolocation()
        
        if localizacao_gps and 'coords' in localizacao_gps:
            coord_usuario = [localizacao_gps['coords']['latitude'], localizacao_gps['coords']['longitude']]
            texto_pino_usuario = "<b>Você está aqui (Localização Real por GPS)</b>"
        else:
            coord_usuario = [-20.3200, -40.3050]
            texto_pino_usuario = "<b>Você está aqui (Vitória)</b><br>⚠️ Permita o acesso ao GPS para ver sua casa."
        
        coordenadas_mercados = {
            "Atacadão": {
                "coords": [-20.3570, -40.3352], 
                "cor": "blue", 
                "desc": "<b>Atacadão Vila Velha</b><br>📍 Rod. Darly Santos<br>⏰ Seg a Sáb: 7h às 22h"
            },
            "Carrefour": {
                "coords": [-20.3283, -40.2936], 
                "cor": "orange", 
                "desc": "<b>Carrefour Hipermercado</b><br>📍 Shopping Vila Velha - Av. Luciano das Neves<br>⏰ Seg a Sáb: 9h às 22h"
            },
            "ExtraBom": {
                "coords": [-20.3118, -40.3009], 
                "cor": "green", 
                "desc": "<b>Extrabom Praia do Suá</b><br>📍 R. Padre Antônio Ribeiro Pinto<br>⏰ Seg a Qui: 7h às 21h | Sex e Sáb: 7h às 21:30h"
            }
        }
        
        mapa = folium.Map(location=coord_usuario, zoom_start=12, control_scale=True)
        
        folium.Marker(
            location=coord_usuario,
            popup=texto_pino_usuario,
            tooltip="Minha Posição",
            icon=folium.Icon(color="red", icon="home")
        ).add_to(mapa)
        
        campeao_string = dados['campeao_economia']
        nome_campeao = "Nenhum"
        for merc in coordenadas_mercados.keys():
            if merc in campeao_string:
                nome_campeao = merc
        
        for nome_m, info in coordenadas_mercados.items():
            if nome_m == nome_campeao:
                icone = folium.Icon(color="darkgreen", icon="trophy", prefix="fa")
                texto_popup = f"<b>🏆 {nome_m} (MELHOR PREÇO)</b><br>{info['desc']}"
            else:
                icone = folium.Icon(color=info["cor"], icon="shopping-cart")
                texto_popup = info['desc']
                
            folium.Marker(
                location=info["coords"],
                popup=texto_popup,
                tooltip=nome_m,
                icon=icone
            ).add_to(mapa)
            
        st_folium(mapa, width=1200, height=450, returned_objects=[])