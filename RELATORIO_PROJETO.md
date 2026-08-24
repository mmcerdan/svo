# Relatório do Projeto — Sistema de Informações de Óbito (Goianira)

---

## 1. Visão Geral

Sistema web local (Flask + SQLite) para registro, investigação e impressão de óbitos do município de Goianira/GO, seguindo os formulários oficiais do SIM (Sistema de Informação sobre Mortalidade) do Ministério da Saúde.

**Stack:** Python 3.11 • Flask 3 • SQLAlchemy • SQLite • Bootstrap 5 • Chart.js  
**Autenticação:** Flask-Login (Admin / Supervisor / Usuário) + CSRF obrigatório  
**Porta:** 5000 (acessível na rede em `192.168.0.250:5000`)

---

## 2. Fluxos Principais

| Rota | Descrição |
|------|-----------|
| `/` | Dashboard com gráficos (Chart.js): óbitos por sexo, local, investigações por tipo/status, principais CID |
| `/obitos` | Lista paginada + busca de óbitos cadastrados |
| `/obitos/novo` | **Cadastro combinado**: dados do óbito + escolha do tipo de investigação (MIF, Materno, Infantil/Fetal, Mal Definida, Infantil) → carrega dinamicamente os campos específicos da ficha (checkboxes agrupados + textareas) → salva Óbito + Investigação em um POST |
| `/obitos/<id>` | Detalhe do óbito + lista de investigações vinculadas |
| `/investigacoes/<id>` | **Preenchimento da ficha**: campos agrupados por tipo (checkboxes inline-flex, textareas), botão **Salvar Campos** + botão **Finalizar** (modal que muda status→Concluída, data→hoje, salva conclusão) |
| `/investigacoes/<id>/imprimir` | **Impressão em CSS Grid puro (A4, sem fundo PDF)**: Helvetica/Arial, layout responsivo, quebra de linha automática (`word-break: break-word`), checkboxes alinhados via `inline-flex`, tabelas (Quadro PN, Exames, Atendimentos) com colunas proporcionais |
| `/relatorios` | Dashboard com filtros de período e 3 abas: Geral, Investigações, Causas (CID) |

---

## 3. Tipos de Investigação Suportados (5 fichas SIM)

| Código | Nome | Campos | Páginas (PDF) | Observação |
|--------|------|--------|---------------|------------|
| **MIF** | Mulher em Idade Fértil | 31 | 1 | Foco em óbito materno possível |
| **MATERNO** | Materno | 86 | 3 | Pré-natal, parto, exames, vacinação, atendimentos |
| **INFANTIL_FETAL** | Infantil / Fetal (IF5) | 87 | 4 | Wigglesworth (W1-W9), SEADE (S1-S7), Avaliação/Organização |
| **MAL_DEFINIDA** | Causa Mal Definida (IOCMD) | 42 | 2 | Tabela de causas DO (linhas a/b/c/d + Parte II) |
| **INFANTIL** | Infantil (I1) | 129 | 5 | Pré-natal da mãe + assistência à criança (aleitamento, vacinação, acompanhamento especial) |

**Total de campos definidos:** ~375 entre todos os tipos.

---

## 4. Modelo de Dados

```
Usuario (1) ──< Obito (1) ──< Investigacao (1) ──< InvestigacaoCampo (N)
                                           └─< Anexo (N)
```

- `InvestigacaoCampo`: chave-valor (`nome_campo`, `valor`). Checkboxes guardam `'X'` ou `''`.
- Campos dinâmicos criados via `get_campos_padrao_investigacao(tipo)` na criação da investigação.

---

## 5. Principais Entregas Técnicas

### 5.1 Impressão sem fundo PDF (CSS Grid)
- 5 templates `imprimir_*.html` com **CSS Grid** nativo
- `height: auto` em todas as `<tr>`; sem `overflow:hidden` nem `min-height` fixo
- Checkboxes: `display:inline-flex; align-items:center` + `<span class="box">X</span>`
- Wigglesworth/SEADE: `gap: 0.5em 1.2em` (unidades relativas `em`)
- Tabelas clínicas: coluna "Queixas" `width:35%`, trimestres `width:40px`
- `page-break-inside:auto` em textos longos; `page-break-inside:avoid` em assinaturas
- Header institucional (MS + Goianira) em todas as fichas

### 5.2 Formulário de Preenchimento Inteligente (`detalhe.html`)
- `get_tipo_campo(nome)` classifica cada campo como `checkbox` ou `textarea`
- `agrupar_campos(campos)` agrupa checkboxes consecutivos do mesmo prefixo (ex.: "Wigglesworth: W1…W9", "Sexo: Masculino/Feminino/Ignorado")
- Renderização: grupos em `div.campo-grupo` com `grupo-opcoes` em `flex-wrap`; textareas isolados
- Salvamento: checkboxes não marcados → `valor=''`

### 5.3 Cadastro Unificado (`/obitos/novo`)
- Dropdown "Criar Investigação" no final do formulário de óbito
- JS carrega `/investigacoes/campos-por-tipo/<tipo>` (JSON com `grupos`) e monta os campos dinamicamente
- POST cria `Obito` + `Investigacao` + todos os `InvestigacaoCampo` de uma vez

### 5.4 Finalização Rápida
- Botão "Finalizar" no detalhe da investigação (só aparece se status ≠ CONCLUIDA)
- Modal com textarea para conclusão → POST `/investigacoes/<id>/finalizar` → status=CONCLUIDA, data=hoje, conclusão salva

### 5.5 Relatórios em Tempo Real
- Consulta SQL direta (sem cache) em `/relatorios/dados`
- 3 visualizações: Geral (sexo/local), Investigações (tipo/status), Causas (top 15 CID)
- Gráficos Chart.js (bar) + tabelas resumo

---

## 6. Estado Atual (Maio 2026)

| Item | Status |
|------|--------|
| Cadastro de óbitos | ✅ Completo |
| 5 tipos de investigação | ✅ Campos definidos + impressão |
| Formulário dinâmico (checkboxes/textarea) | ✅ Funcionando |
| Cadastro combinado óbito + investigação | ✅ Funcionando |
| Finalização em 1 clique | ✅ Implementada |
| Impressão CSS Grid (sem PDF) | ✅ 5 templates testados (HTTP 200) |
| Tabelas estruturadas (Quadro PN, Exames, Atendimentos) | ⚠️ Layout pronto; dados vêm vazios (schema chave-valor não suporta linhas repetidas) |
| Migração de dados legados | ✅ Script rodado (campos antigos mantidos, novos criados vazios) |

---

## 7. Próximos Passos Sugeridos

1. **Tabelas repetíveis** (Quadro PN, Exames, Atendimentos)  
   → Nova tabela `investigacao_tabela` (investigacao_id, tabela, linha, colunas JSON) ou sub-formulários no detalhe.

2. **Importação/Exportação**  
   → CSV/SIH/SIM para preenchimento em lote.

3. **Validações de negócio**  
   → Obrigatoriedade por tipo (ex.: Wigglesworth obrigatório no IF5), CID válido, datas coerentes.

4. **Logs de auditoria**  
   → Tabela `auditoria` (usuario, acao, entidade_id, antes/depois, timestamp).

5. **Deploy em produção**  
   → Gunicorn + Nginx + systemd service + HTTPS (Let's Encrypt) + backup automático do SQLite.

---

## 8. Como Rodar

```bash
cd D:\Óbito\SistemaObito
python app.py
# → http://127.0.0.1:5000  ou  http://192.168.0.250:5000
# Login: admin / admin123
```

**Banco:** `instance/obito.db` (SQLite)  
**Arquivos estáticos:** `static/` (CSS, logos, PDF fundos legados)  
**Templates:** `templates/` (base, obitos/, investigacoes/, relatorios/)

---

## 9. Credenciais de Teste

| Perfil | Usuário | Senha | Permissões |
|--------|---------|-------|------------|
| Admin | `admin` | `admin123` | Total (usuários, exclusão, tudo) |
| Supervisor | (criar via painel) | — | Usuários + relatórios |
| Usuário | `usuario` | `123456` | CRUD óbitos/investigações próprio |

---

*Documento gerado automaticamente a partir da base de código em 24/08/2026.*