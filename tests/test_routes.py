import pytest
from app import create_app
from app.routes import sanitizar_texto

# Cria um "cliente" falso para simular acessos ao site
@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        # Simula usuário logado
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_nome'] = 'Usuário Teste'

        yield client

def test_pagina_inicial_carrega(client):
    """Garante que a página principal responde com código 200 (OK)"""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Montador de Lista Inteligente" in response.data

def test_pagina_orcamento_carrega(client):
    """Garante que a página do gestor de orçamento está online"""
    response = client.get('/orcamento')
    assert response.status_code == 200
    assert b"Limite de" in response.data

def test_funcao_sanitizar_texto():
    """Garante que o filtro Regex remove pontuações indesejadas, mas mantém espaços e letras"""
    texto_sujo = "Café Pilão!!! @1kg..."
    texto_limpo = sanitizar_texto(texto_sujo)

    assert texto_limpo == "Café Pilão 1kg"