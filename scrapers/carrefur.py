from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
from urllib.parse import quote

def buscar(produto):
    produto_original = produto.lower().strip()
    produto_url = quote(produto_original)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(options=options)
    url = f"https://mercado.carrefour.com.br/busca/{produto_url}"
    
    lista_produtos = []

    try:
        driver.get(url)

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

                nome = texto
                for p in precos:
                    nome = nome.replace(p, "")

                termos_lixo = ["de", "por", "adicionar", "retirar", "ver produto"]
                for termo in termos_lixo:
                    nome = re.sub(r'\b' + termo + r'\b', '', nome, flags=re.IGNORECASE)

                nome = re.sub(r"\s+", " ", nome).strip()

                if len(nome) < 3:
                    continue

                if produto_original not in nome.lower():
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

    unicos = {item["nome"]: item for item in lista_produtos}.values()
    lista_produtos = list(unicos)

    if not lista_produtos:
        return None

    return min(lista_produtos, key=lambda x: x["preco"])