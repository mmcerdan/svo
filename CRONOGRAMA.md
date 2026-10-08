# Cronograma de Pendências — Sistema de Óbito

> Versão base: **v1.1** (08/10/2026) · Documento vivo · Revisar a cada etapa concluída

## 🎯 Objetivo

Resolver as pendências mapeadas na auditoria da v1.1 **sem quebrar o que já funciona em produção** (192.168.0.225:9010), em ordem de dependência e risco crescente.

## 🛡️ Regras de ouro (valem para TODA etapa)

1. **Auditoria read-only antes** — cada etapa começa com análise do estado atual + suíte de testes verde
2. **Backup antes de mudar** — `pg_dump` + `git tag` antes de qualquer alteração em produção
3. **Testes verdes como gate** — nada sobe com teste vermelho novo (baseline Etapa 0: **81 ✅ / 0 ❌ / 0 erros**)
4. **Rollback documentado** — cada etapa tem caminho de volta testado
5. **Deploy em janela** — preferencialmente horário comercial, com aviso aos usuários
6. **Uma etapa por vez** — só iniciar a próxima após validação da anterior

---

## 📅 Cronograma

| Etapa | Prazo sugerido | Duração | Risco | Entregável principal |
|-------|----------------|---------|-------|----------------------|
| **0. Fundação verde** | 13–16/10/2026 | 4 dias | 🟢 Baixo | Testes 100% verdes + Alembic ativo |
| **1. Validações de negócio** | 19–23/10/2026 | 1 semana | 🟢 Baixo-médio | Ficha validada na criação/finalização |
| **2. HTTPS + Perfis** | 26/10–06/11/2026 | 2 semanas | 🟡 Médio | 443 ativo + permissões reais |
| **3. Admin CID/Estabelecimento** | 09–13/11/2026 | 1 semana | 🟢 Baixo | CRUD completo com UI |
| **4. Tabelas repetíveis** | 16–27/11/2026 | 2 semanas | 🔴 Alto | Modelo de linhas + UI + impressão |
| **5. Testes E2E** | 30/11–04/12/2026 | 1 semana | 🟢 Baixo | Playwright rodando em staging |

> Datas são sugestões — ajustar conforme disponibilidade. Etapa 5 pode avançar em paralelo a partir da Etapa 2.

---

## 📋 Detalhamento por etapa

### Etapa 0 — Fundação verde (13–16/10)
**Por quê:** sem baseline verde e sem migrações versionadas, cada mudança seguinte é um risco desnecessário.

- [x] Corrigir testes desatualizados de DO duplicada (`tests/test_obitos.py:39-44,88-99`, `test_validators.py:38-42`) — alinhar à regra de gêmeos da v1.1
- [x] Resolver erros JSONB/SQLite nos testes (23 errors) — `JSON().with_variant(JSONB, 'postgresql')` no model
- [x] Investigar/decidir sobre o teste `test_infantil_fetal_wigglesworth_exato_um` (1 failed) — teste incompleto (faltava SEADE); validador correto, teste ajustado
- [x] Ativar **Flask-Migrate/Alembic** (já no requirements): `flask db init` + baseline `4f239821b7c0` ("baseline v1.1") + stamp no dev local
- [x] Script `deploy.sh` passa a rodar `flask db upgrade` em vez de `db.create_all()` (stamp automático para banco pré-Alembic)
- [x] CI local: comando único `make test` (Makefile) rodando suíte completa

**Critério de aceite:** `pytest` 100% verde; `flask db current` mostra revisão ativa; produção inalterada.

### Etapa 1 — Validações de negócio (19–23/10)
**Por quê:** hoje a validação só roda ao salvar campos — dá para criar e finalizar ficha vazia (`investigacao_service.py:91-141,198-219`).

- [ ] Validar `ValidadorInvestigacao` na **criação** da investigação (modo aviso)
- [ ] Validar na **finalização** — exigir campos obrigatórios (modo aviso → bloqueio após validação com usuários)
- [ ] Consistência ficha × óbito (DO, datas, nome divergentes → alerta)
- [ ] Validar CID-10 em `causas_morte_cids` (`obito_service.py:53`)
- [ ] Testes unitários para cada nova regra

**Critério de aceite:** ficha vazia não finaliza (com aviso claro na UI); testes verdes; rollback = flag de config.

### Etapa 2 — HTTPS + Perfis (26/10–06/11)
**Por quê:** sistema em uso — segurança operacional (2a semana: permissões).

**2a. HTTPS**
- [ ] Auditoria read-only da config nginx atual (`deploy.sh:161-244`)
- [ ] Certbot real: porta 443 + redirect 80/9010→443 + renewal automático
- [ ] `SESSION_COOKIE_SECURE=True` (`config.py:40`) + HSTS
- [ ] Firewall: abrir 443/tcp

**2b. Perfis com permissão real**
- [ ] Distinguir Admin × Supervisor (hoje idênticos, `security.py:6-20`)
- [ ] Dar efeito aos cargos Investigador/Enfermeira (hoje decorativos)
- [ ] Regra de dono: edita/exclui só próprio registro (ou por perfil)
- [ ] Migrar checks avulsos `current_user.is_admin()` para decoradores

**Critério de aceite:** HTTPS com certificado válido; teste de permissão automatizado por cargo; rollback = tag git + conf nginx versionada.

### Etapa 3 — Admin CID/Estabelecimento (09–13/11)
**Por quê:** hoje CID é só busca GET e Estabelecimento não tem DELETE nem UI.

- [ ] CRUD de CIDs (listar, editar, ativar/desativar) com UI + busca/paginação
- [ ] CRUD de Estabelecimentos com UI + DELETE lógico (`ativo=False`)
- [ ] Links no menu admin (`base.html:45-52`)
- [ ] Aplicar `admin_required` nos endpoints (hoje importado e não usado, `obitos.py:223,250`)

**Critério de aceite:** UI completa de cadastro; rotas antigas inalteradas; testes de rota novos.

### Etapa 4 — Tabelas repetíveis (16–27/11) ⚠️ mais arriscada
**Por quê:** schema chave-valor não tem linhas (`investigacao.py:56-67`); repetição é fake por nome de campo.

- [ ] Decisão de modelo: tabela `investigacao_rows` (linhas + colunas JSON) vs sub-formulários
- [ ] Migração Alembic **de dados** existentes (MATERNO Quadro PN, Atendimentos; INFANTIL Atendimentos)
- [ ] UI "adicionar/remover linha" no detalhe da ficha
- [ ] Adaptar templates de impressão (`imprimir_materno`, `imprimir_infantil`)
- [ ] Contactantes DENGUE múltiplos (hoje 1 conjunto, `campos_dengue.py:394-419`)
- [ ] Deploy com janela + backup + conferência ficha a ficha após migração

**Critério de aceite:** dados migrados conferidos (antes/depois); impressão idêntica para dados antigos; rollback = `pg_dump` pré-migração.

### Etapa 5 — Testes E2E (30/11–04/12)
**Por quê:** 6 testes escritos mas Playwright não está no requirements e não há fixture `page`.

- [ ] `pytest-playwright` + `playwright install chromium` no requirements
- [ ] Fixture `page` + `tests/e2e/conftest.py`
- [ ] Remover credencial hardcoded (`test_fluxo_completo.py:23-24`) — usar fixture
- [ ] Rodar contra **staging** (banco de teste), nunca contra produção
- [ ] Hook: rodar e2e antes de deploy em produção

**Critério de aceite:** 6 testes e2e verdes em ambiente limpo.

---

## 🧪 Protocolo de testes funcionais (read-only)

Executado antes de cada etapa e após cada deploy:

1. **Suíte local:** `make test` (ou `python -m pytest tests/ -q --ignore=tests/e2e`) → deve bater com a baseline (81/0/0)
2. **Saúde em produção:** `GET /health`, todas as rotas principais HTTP 200
3. **Integridade do banco:** contagens (obitos, investigacoes, campos), FKs órfãs, índices
4. **Smoke autenticado:** login, lista, detalhe, impressão de fichas, busca CID
5. **Sem erros:** `journalctl -u sistema-obito -p err` vazio nos últimos 5 min

---

## 📌 Fora de escopo (decisão registrada)

| Item | Motivo |
|------|--------|
| Importação em lote SIM/SIH | CSV do SIM traz só dados básicos (nome, nº DO, cidade); ficha é preenchida por link na página do SIM — sem viabilidade de importação para alimentar investigações |

---

## 🔄 Histórico de revisões

| Data | Alteração |
|------|-----------|
| 08/10/2026 | Criação do cronograma (pós-auditoria v1.1) |
| 08/10/2026 | Etapa 0 local concluída: suíte 81/0/0, Alembic baseline `4f239821b7c0`, deploy.sh em `flask db upgrade`, Makefile |
| 08/10/2026 | Etapa 0 validada em produção: pull `04053d5`, `flask db current` = `4f239821b7c0 (head)` (PG), suíte 81/0/0 no servidor, smoke 200, journal limpo (backup `obito_db_pre_etapa0_20261008_110337.sql`) |
