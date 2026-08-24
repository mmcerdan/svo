"""
Testes E2E com Playwright.
Execute com: pytest tests/e2e/ -v --headed
Requer: playwright install chromium
"""
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:5000"

@pytest.fixture(scope="session")
def base_url():
    return BASE_URL

class TestFluxoCompleto:
    """Testes do fluxo completo: login -> criar óbito -> investigação -> finalizar -> imprimir."""
    
    def test_login_logout(self, page: Page):
        """Testa login e logout."""
        page.goto(f"{BASE_URL}/auth/login")
        
        # Login
        page.fill('input[name="usuario"]', "admin")
        page.fill('input[name="senha"]', "admin123")
        page.click('button[type="submit"]')
        
        # Verifica redirecionamento para dashboard
        expect(page).to_have_url(f"{BASE_URL}/")
        expect(page.locator("text=Bem-vindo")).to_be_visible()
        
        # Logout
        page.click('a:has-text("Sair")')
        expect(page).to_have_url(f"{BASE_URL}/auth/login")
    
    def test_criar_obito_com_investigacao_mif(self, page: Page):
        """Fluxo completo: cria óbito com investigação MIF."""
        # Login
        page.goto(f"{BASE_URL}/auth/login")
        page.fill('input[name="usuario"]', "admin")
        page.fill('input[name="senha"]', "admin123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/")
        
        # Navega para novo óbito
        page.click('a:has-text("Óbitos")')
        page.click('a:has-text("Novo")')
        page.wait_for_url(f"{BASE_URL}/obitos/novo")
        
        # Preenche dados do óbito
        page.fill('input[name="nome"]', "E2E Teste Maria")
        page.fill('input[name="data_nascimento"]', "1960-05-10")
        page.fill('input[name="data_obito"]', "2024-06-15")
        page.select_option('select[name="sexo"]', "F")
        page.fill('input[name="nome_mae"]', "Mãe Teste")
        page.fill('input[name="numero_dob"]', "DO-E2E-001")
        page.fill('input[name="causa_morte"]', "Eclampsia")
        page.fill('input[name="causa_morte_cid"]', "O15.0")
        page.select_option('select[name="local_obito"]', "HOSPITAL")
        page.fill('input[name="municipio_ocorrencia"]', "Goianira")
        page.fill('textarea[name="endereco"]', "Rua Teste, 123")
        
        # Seleciona investigação MIF
        page.select_option('select[name="criar_investigacao"]', "MIF")
        
        # Aguarda carregar campos dinâmicos
        page.wait_for_selector('#campos-investigacao-container:not([style*="display: none"])')
        
        # Preenche campos da investigação MIF
        # Zona
        page.check('input[name="inv_Zona: Urbana"]')
        
        # Grávida no momento
        page.check('input[name="inv_Grávida no momento do óbito? (Sim)"]')
        
        # Esteve grávida nos 12 meses
        page.check('input[name="inv_Esteve grávida nos 12 meses? (Sim)"]')
        
        # Resumo
        page.fill('textarea[name="inv_Resumo do caso / justificativa"]', "Caso de teste E2E")
        
        # Data investigação
        page.fill('input[name="inv_Data da investigação"]', "2024-06-16")
        
        # Responsável
        page.fill('input[name="inv_Responsável investigação - nome"]', "Dr. Teste")
        
        # Submete
        page.click('button:has-text("Salvar")')
        
        # Verifica redirecionamento para detalhe da investigação
        page.wait_for_url("**/investigacoes/**")
        expect(page.locator("text=MIF")).to_be_visible()
        expect(page.locator("text=E2E Teste Maria")).to_be_visible()
    
    def test_finalizar_investigacao(self, page: Page):
        """Testa finalização de investigação via modal."""
        # Assume que existe investigação com status AGUARDANDO
        # Primeiro cria uma investigação MIF via API
        page.goto(f"{BASE_URL}/auth/login")
        page.fill('input[name="usuario"]', "admin")
        page.fill('input[name="senha"]', "admin123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/")
        
        # Cria óbito + investigação via API para garantir estado
        # (Em teste real, usaria a UI; aqui usa API para velocidade)
        response = page.request.post(f"{BASE_URL}/obitos/novo", data={
            "nome": "E2E Finalizar Teste",
            "data_nascimento": "1970-01-01",
            "data_obito": "2024-07-01",
            "sexo": "M",
            "nome_mae": "Mãe Teste",
            "numero_dob": "DO-E2E-FIN-001",
            "causa_morte": "Teste",
            "causa_morte_cid": "I21.9",
            "local_obito": "HOSPITAL",
            "criar_investigacao": "MIF",
            # Campos MIF obrigatórios
            "inv_Zona: Urbana": "X",
            "inv_Grávida no momento do óbito? (Sim)": "X",
            "inv_Esteve grávida nos 12 meses? (Sim)": "X",
        })
        
        # Extrai ID da investigação criada (página de detalhe)
        # Navega para lista de investigações
        page.goto(f"{BASE_URL}/investigacoes/")
        
        # Clica na primeira investigação AGUARDANDO
        page.click('table tbody tr:has-text("AGUARDANDO") a')
        
        # Clica em Finalizar
        page.click('button:has-text("Finalizar")')
        
        # Modal abre
        expect(page.locator('#modalFinalizar')).to_be_visible()
        
        # Preenche conclusão
        page.fill('textarea[name="conclusao"]', "Conclusão do teste E2E - Caso encerrado.")
        
        # Confirma
        page.click('button:has-text("Confirmar Finalização")')
        
        # Verifica sucesso
        expect(page.locator("text=Concluída")).to_be_visible()
        expect(page.locator("text=Conclusão do teste E2E")).to_be_visible()
    
    def test_imprimir_investigacao(self, page: Page):
        """Testa abertura da impressão."""
        page.goto(f"{BASE_URL}/auth/login")
        page.fill('input[name="usuario"]', "admin")
        page.fill('input[name="senha"]', "admin123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/")
        
        page.goto(f"{BASE_URL}/investigacoes/")
        
        # Clica em imprimir da primeira investigação
        with page.expect_popup() as popup_info:
            page.click('table tbody tr:first-child a:has-text("Imprimir")')
        imprimir_page = popup_info.value
        
        # Verifica que abriu página de impressão
        expect(imprimir_page.locator("text=MINISTÉRIO")).to_be_visible()
        expect(imprimir_page.locator("text=Goianira")).to_be_visible()
        
        imprimir_page.close()

class TestRelatorios:
    """Testes dos relatórios."""
    
    def test_acesso_relatorios(self, page: Page):
        page.goto(f"{BASE_URL}/auth/login")
        page.fill('input[name="usuario"]', "admin")
        page.fill('input[name="senha"]', "admin123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/")
        
        page.click('a:has-text("Relatórios")')
        page.wait_for_url(f"{BASE_URL}/relatorios/")
        
        expect(page.locator("text=Relatórios")).to_be_visible()
        expect(page.locator('#graficoPrincipal')).to_be_visible()
    
    def test_filtro_periodo(self, page: Page):
        page.goto(f"{BASE_URL}/auth/login")
        page.fill('input[name="usuario"]', "admin")
        page.fill('input[name="senha"]', "admin123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/")
        
        page.goto(f"{BASE_URL}/relatorios/")
        
        # Preenche datas
        page.fill('#data_inicio', "2024-01-01")
        page.fill('#data_fim', "2024-12-31")
        
        # Clica em Investigacoes
        page.click('button:has-text("Investigações")')
        
        # Verifica que carregou dados
        expect(page.locator('#resumo-dados')).not_to_be_empty()