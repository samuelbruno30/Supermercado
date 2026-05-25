from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import re
import unicodedata
from urllib.parse import quote
import time

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
    
    # Camuflagem padrão contra o sistema de segurança do Extrabom
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
    
    lista_produtos = []

    try:
        # Acessa a página principal para validar sessão e cookies legítimos
        driver.get("https://www.extrabom.com.br/")
        time.sleep(1)

        # Executa a busca real
        url_busca = f"https://www.extrabom.com.br/busca/?q={produto_url}"
        driver.get(url_busca)

        # BLINDAGEM: Aguarda os itens com preço realmente aparecerem na tela
        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-price]"))
            )
        except TimeoutException:
            # Se não achar os blocos por atributo, aguarda o corpo padrão
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
            )
        
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # =========================================================================
        # ESTRATÉGIA SUPREMA: Capturar chaves por Atributos de Dados (data-price / data-name)
        # =========================================================================
        blocos_produtos = soup.find_all(attrs={"data-price": True})

        for bloco in blocos_produtos:
            try:
                nome = bloco.get("data-name", "").strip()
                preco_raw = bloco.get("data-price", "").strip()

                if not nome or not preco_raw:
                    continue

                # Normalização para comparação de palavras
                nome_sem_acento = remover_acentos(nome.lower())
                produto_palavras = produto_busca.split()

                # BLINDAGEM CONTRA FALSO NEGATIVO (Validação flexível por relevância de palavras)
                # Conta quantas palavras digitadas pelo usuário batem com o título do site
                palavras_batidas = sum(1 for palavra in produto_palavras if palavra in nome_sem_acento)
                
                # Se não bater quase nenhuma palavra principal, descarta (evita trazer itens aleatórios)
                if palavras_batidas == 0:
                    continue
                
                # Se o usuário digitou mais de uma palavra (ex: "feijao preto"), exige que pelo menos
                # metade das palavras digitadas existam no produto real encontrado
                if len(produto_palavras) > 1 and palavras_batidas < (len(produto_palavras) / 2):
                    continue

                preco_numero = float(preco_raw)

                lista_produtos.append({
                    "mercado": "ExtraBom",
                    "nome": nome,
                    "preco": preco_numero
                })
            except Exception:
                pass

        # =========================================================================
        # CASO DE CONTINGÊNCIA: Se cair na página única de um produto específico
        # =========================================================================
        if not lista_produtos:
            tag_nome_direto = soup.find(class_="nome-produto")
            div_valor_direta = soup.find("div", class_="valor")

            if tag_nome_direto and div_valor_direta:
                nome = tag_nome_direto.get_text(" ", strip=True)
                preco_bruto = div_valor_direta.get_text(" ", strip=True)
                
                match_preco = re.search(r'R\$\s*\d+\s*[\.,]\s*\d{2}', preco_bruto)
                if match_preco:
                    preco_texto = match_preco.group()
                    preco_limpo = re.sub(r'\s+', '', preco_texto)
                    preco_numero = float(preco_limpo.replace("R$", "").replace(".", "").replace(",", ".").strip())

                    nome_sem_acento = remover_acentos(nome.lower())
                    produto_palavras = produto_busca.split()

                    palavras_batidas = sum(1 for palavra in produto_palavras if palavra in nome_sem_acento)
                    if palavras_batidas > 0:
                        driver.quit()
                        return {"mercado": "ExtraBom", "nome": nome, "preco": preco_numero}

    except Exception:
        pass
    finally:
        driver.quit()

    # Filtro de unicidade fina
    unicos = {item["nome"]: item for item in lista_produtos}.values()
    lista_produtos = list(unicos)

    if not lista_produtos:
        return None

    # Retorna o mais barato dentre os que passaram no filtro de relevância
    return min(lista_produtos, key=lambda x: x["preco"])