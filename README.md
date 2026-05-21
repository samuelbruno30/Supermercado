O sistema utiliza robôs de Web Scraping operando de forma assíncrona e paralela para entregar os melhores preços com geolocalização automática.

🚀 Tecnologias Utilizadas
Front-End: Streamlit (reunindo mapas interativos e gerenciamento de estado de sessão).

Back-End: FastAPI + Uvicorn (API REST de alta performance).

Paralelismo: ThreadPoolExecutor (Multi-threading nativo para rodar os scrapers simultaneamente).

Automação/Scraping: Selenium WebDriver / Requests.

Geolocalização: HTML5 Geolocation API via JavaScript integrado com Folium.

🛠️ Como Configurar e Executar o Projeto
Para rodar este projeto localmente, você precisará ter o Python instalado (versão 3.10 ou superior recomendada).

1. Clonar o Repositório
Bash
git clone https://github.com/samuelbruno30/Supermercado.git
cd Supermercado
2. Criar e Ativar o Ambiente Virtual (venv)
No terminal do seu sistema, execute:

PowerShell
# Criando a venv
python -m venv venv

# Ativando no Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Ou Ativando no Windows (CMD)
.\venv\Scripts\activate.bat
3. Instalar as Dependências Obrigatórias
Com a venv ativa, instale todos os pacotes necessários rodando o comando abaixo:

Bash
pip install fastapi uvicorn pydantic selenium requests pandas folium streamlit-folium streamlit-js-eval
🏃‍♂️ Inicializando o Sistema
Como o projeto é dividido em duas camadas (Cliente/Servidor), você precisará abrir dois terminais diferentes com a venv ativa para ligar o sistema.

Passo 1: Ligar o Back-End (API)
No primeiro terminal, execute o servidor Uvicorn:

Bash
python -m uvicorn app:app --reload
A API estará rodando no endereço: http://127.0.0.1:8000

Passo 2: Ligar o Front-End (Interface Visual)
No segundo terminal, inicialize a interface do Streamlit:

Bash
.\venv\Scripts\streamlit.exe run lista.py
O navegador abrirá automaticamente a interface do usuário em: http://localhost:8501

💡 Destaques Técnicos do Projeto
Paralelismo Real (Multi-threads): O backend dispara threads simultâneas para pesquisar os produtos ao mesmo tempo em todos os mercados, reduzindo o tempo total de resposta da consulta.

Resiliência de Interface (st.session_state): Utiliza memória de sessão local para que os dados pesquisados e o mapa não sumam da tela quando o navegador atualizar a geolocalização em segundo plano.

Segurança de Dados: Limpeza de strings e sanitização contra caracteres maliciosos nas requisições da API.

GPS Automático: O sistema solicita permissão de localização ao navegador do usuário para plotar o pino dinamicamente no mapa de rotas ao lado do supermercado campeão de economia.
