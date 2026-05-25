# 🛒 Montador de Lista Inteligente & Comparador de Preços

O **Montador de Lista Inteligente** é uma aplicação web robusta desenvolvida em Python com o ecossistema Flask. O principal objetivo do sistema é automatizar a pesquisa de mercado de listas de compras de forma simultânea e em tempo real em grandes redes de supermercados da Grande Vitória (Atacadão, Carrefour e ExtraBom).

O projeto foi concebido sob os critérios de avaliação da disciplina de **Programação Web Avançada** da **Universidade Vila Velha (UVV)**.

---

## 🚀 Funcionalidades Principais

* **Busca Paralela de Alta Performance:** Utiliza concorrência nativa em Python (`ThreadPoolExecutor`) para disparar múltiplos Web Scrapers simultaneamente, reduzindo drasticamente o tempo de resposta do usuário.
* **Algoritmo de Relevância Balanceado:** Blindagem contra falsos negativos através de uma lógica de aproximação por peso de termos, ignorando acentuações e diferenças sutis de escrita nos e-commerces.
* **Gestor de Orçamento Contextual:** Permite estipular um teto de gastos. O sistema sinaliza visualmente se o total acumulado em determinado mercado ultrapassa ou se encaixa no orçamento disponível.
* **Cálculo Inteligente do Campeão:** O algoritmo prioriza o estabelecimento que encontrou a maior quantidade de itens da lista do usuário. Em caso de empate na quantidade, o critério de desempate é o menor valor total.
* **Geolocalização Integrada:** Renderização de um mapa híbrido estilizado do Google Maps via Leaflet.js, plotando as coordenadas reais das unidades físicas mais próximas e a geolocalização em tempo real do usuário.
* **Exportação para o WhatsApp:** Integração nativa via JavaScript que converte a tabela comparativa de preços em texto formatado para envio instantâneo via WhatsApp API.

---

## 📁 Estrutura Estrutural do Projeto

O projeto adota uma arquitetura modular focada na separação de conceitos de software (Separation of Concerns):

```text
Supermercado/
├── app/
│   ├── templates/          # Interfaces em HTML5 estruturadas com Bulma CSS
│   │   ├── base.html       # Layout base estrutural do sistema
│   │   ├── index.html      # Tela principal do buscador e resultados
│   │   └── orcamento.html  # Painel de controle do teto de gastos
│   ├── __init__.py         # Inicializador e configurador do Application Factory
│   └── routes.py           # Core do roteamento web, controle de sessões e lógica de negócio
├── scrapers/               # Módulos isolados de mineração de dados (Web Scraping)
│   ├── atacadao.py         # Robô automatizado Selenium para a rede Atacadão
│   ├── carrefur.py         # Robô automatizado Selenium para a rede Carrefour
│   └── extrabom.py         # Robô automatizado Selenium para a rede ExtraBom
├── venv/                   # Ambiente virtual com isolamento de dependências
├── .gitignore              # Filtros de arquivos locais para versionamento via Git
└── run.py                  # Ponto único de entrada (Single-point entry) do servidor web
