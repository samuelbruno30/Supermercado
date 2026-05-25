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
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--ignore-certificate-errors")
    
    driver = webdriver.Chrome(options=options)
    url = f"https://mercado.carrefour.com.br/busca/{produto_url}"
    
    lista_produtos = []

    try:
        driver.get(url)

        # Aguarda os links de produto reais carregarem na interface
        WebDriverWait(driver, 12).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/produto/']"))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")
        produtos = soup.select("a[href*='/produto/']")

        for item in produtos:
            try:
                texto = item.get_text(" ", strip=True)
                texto = re.sub(r"\s+", " ", texto)

                precos = re.findall(r'R\$\s*\d+[\.,]\d{2}', texto)
                if not precos:
                    continue

                # Evita pegar o preço antigo do "De / Por" pegando o último valor encontrado
                preco_texto = precos[-1]

                # Limpa os preços do bloco de texto para isolar o nome
                nome = texto
                for p in precos:
                    nome = nome.replace(p, "")

                # BLINDAGEM DE HIGIENIZAÇÃO: Remove termos de botões sem quebrar nomes como "Molho DE tomate"
                termos_lixo = ["adicionar", "retirar", "ver produto", "esgotado"]
                for termo in termos_lixo:
                    nome = re.sub(r'\b' + termo + r'\b', '', nome, flags=re.IGNORECASE)

                nome = re.sub(r"\s+", " ", nome).strip()

                if len(nome) < 3:
                    continue

                # BLINDAGEM CONTRA FALSO NEGATIVO (Validação flexível por relevância de palavras)
                nome_sem_acento = remover_acentos(nome.lower())
                produto_palavras = produto_busca.split()

                # Conta quantas palavras da busca batem com o título do site
                palavras_batidas = sum(1 for palavra in produto_palavras if palavra in nome_sem_acento)
                
                # Se não bater nenhuma palavra fundamental, descarta
                if palavras_batidas == 0:
                    continue
                
                # Se for busca composta (ex: "arroz integral"), exige que pelo menos metade das palavras bata
                if len(produto_palavras) > 1 and palavras_batidas < (len(produto_palavras) / 2):
                    continue

                preco_numero = float(
                    preco_texto
                    .replace("R$", "")
                    .replace(".", "")
                    .replace(",", ".")
                    .strip()
                )

                lista_produtos.append({
                    "mercado": "Carrefour",
                    "nome": nome,
                    "preco": preco_numero
                })

            except Exception:
                pass

    except Exception:
        pass
    finally:
        driver.quit()

    # Filtro de unicidade fina por nome do produto
    unicos = {item["nome"]: item for item in lista_produtos}.values()
    lista_produtos = list(unicos)

    if not lista_produtos:
        return None

    # Retorna o item mais barato da lista refinada
    return min(lista_produtos, key=lambda x: x["preco"])