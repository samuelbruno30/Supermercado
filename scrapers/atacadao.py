from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import unicodedata
from urllib.parse import quote

def remover_acentos(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def buscar(produto):
    produto_original = produto.lower().strip()
    produto_busca = remover_acentos(produto_original)
    produto_url = quote(produto_busca)

    options = Options()
    options.add_argument("--headless=new") 
    options.add_argument("--window-size=1920,1080")
    
    # Camuflagem padrão contra detecção de robôs
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--ignore-certificate-errors")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=options)
    
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    url = f"https://www.atacadao.com.br/s?q={produto_url}&sort=score_desc&page=0"
    lista_produtos = []
    
    try:
        driver.get(url)

        # Espera carregar os títulos dos produtos (h3)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "h3"))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")
        titulos = soup.find_all("h3")

        for h3 in titulos:
            nome_produto = h3.get_text(" ", strip=True)
            nome_produto = re.sub(r'\s+', ' ', nome_produto)

            if len(nome_produto) < 4:
                continue

            nome_sem_acento = remover_acentos(nome_produto.lower())
            produto_palavras = produto_busca.split()
            
            # BLINDAGEM DA RELEVÂNCIA: Nem tanto ao mar (any), nem tanto à terra (all)
            palavras_batidas = sum(1 for palavra in produto_palavras if palavra in nome_sem_acento)
            
            # Tratamento especial para o sinônimo que você criou de biscoito/bolacha
            if palavras_batidas == 0:
                if "biscoito" in produto_palavras and "bolacha" in nome_sem_acento:
                    palavras_batidas = 1
                else:
                    continue
            
            # Para buscas compostas (ex: "feijao preto"), exige que pelo menos metade das palavras bata
            if len(produto_palavras) > 1 and palavras_batidas < (len(produto_palavras) / 2):
                continue

            # Isolamento seguro do preço dentro do Card do Produto
            card = h3.parent
            precos_no_card = []
            
            # Sobe no máximo 4 níveis, garantindo que não saia do container do produto específico
            for _ in range(4): 
                if card is None or card.name in ['body', 'html']:
                    break
                
                # Se encontrarmos uma classe comum de grid/box de produto, inspecionamos ela
                texto_card = card.get_text(" ", strip=True)
                precos_no_card = re.findall(r'R\$\s*\d+[.,]\d{2}', texto_card)
                
                if precos_no_card:
                    break
                card = card.parent

            if precos_no_card:
                # Pega o último preço encontrado (evita valor antigo atacado/varejo invertido)
                preco_texto = precos_no_card[-1]
                preco_numero = float(
                    preco_texto
                    .replace("R$", "")
                    .replace(".", "")
                    .replace(",", ".")
                    .strip()
                )

                lista_produtos.append({
                    "mercado": "Atacadão",
                    "nome": nome_produto,
                    "preco": preco_numero
                })

    except Exception:
        pass
    finally:
        driver.quit()

    # Garante a unicidade dos itens capturados
    unicos = {item["nome"]: item for item in lista_produtos}.values()
    lista_produtos = list(unicos)

    if not lista_produtos:
        return None

    # Retorna o menor preço da lista filtrada por relevância pura
    return min(lista_produtos, key=lambda x: x["preco"])