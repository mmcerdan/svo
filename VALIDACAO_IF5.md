# VALIDAÇÃO OFICIAL IF5 - Ficha de Investigação de Óbito Infantil e Fetal

## Estrutura Oficial Confirmada (Base: Fichas PDF oficiais do Ministério da Saúde)

### PÁGINA 1 - IDENTIFICAÇÃO (Campos 1-15)
1. **Nome da criança** - Texto
2. **Nome da mãe** - Texto
3. **Nº do caso** - Texto
4. **Data de nascimento** - Data (DD/MM/AAAA)
5. **Nº da DN** - Texto
6. **Nº da DO** - Texto
7. **Data do óbito** - Data (DD/MM/AAAA)
8. **Tipo óbito fetal** - Checkboxes: Anteparto / Intraparto
9. **Peso ao nascer (g)** - Numérico
10. **Sexo** - Checkboxes: Masculino / Feminino / Ignorado
11. **Idade ao óbito** + **IG (semanas/meses)** - Texto
12. **Faixa etária** - Checkboxes: Fetal / Neonatal precoce / Neonatal tardio / Pós-neonatal / Ignorado
13. **Idade da mãe (anos)** - Numérico
14. **Escolaridade materna** - **Linha horizontal**: Anos / Série / Grau / **Ignorado (checkbox)**
15. **Município residência / UF** + **Município ocorrência / UF** - Texto

### PÁGINA 1 - CONTINUAÇÃO
- **Resumo do caso** - Textarea
- **Fontes de informação (16-17)** - Checkboxes múltiplas + **Estabelecimento pré-natal (Nome, CNES, Tipo)**

### PÁGINA 2 - ASSISTÊNCIA AO PARTO E ATENÇÃO BÁSICA (Campos 18-19)
18. **Local do parto** - Checkboxes: Hospital / Domicílio / Outro
    **Estabelecimento parto** - **Nome, CNES, Tipo (Público/Privado/Convênio/Outros)**
19. **Acompanhamento atenção básica** - **Estabelecimento AB** - **Nome, CNES, Tipo**
    **Vacinas realizadas** - Texto

### PÁGINA 2 - CID / CORREÇÃO DE CAUSAS (Campos 20-24)
20. **Causa original prontuário** - Textarea
21. **Causa do óbito - CID (Pós investigação)** - Tabela: Parte I (a,b,c,d) + Parte II - Diagnóstico + CID
22-24. **Alterações DO/DN** - Tabela: Causa básica, CID, Data, Local, Idade, Peso (Original vs Nova)

### PÁGINA 3 - MATRIZ DE PROBLEMAS (Campos 25-26)
25. **Problemas identificados** - Textarea
26. **Análise da assistência (26.1 a 26.9)** - **MATRIZ/TABELA**:
    - Linhas: 26.1 Planejamento familiar, 26.2 Pré-natal, 26.3 Assistência ao parto, 26.4 RN sala parto, 26.5 Alojamento, 26.6 UTI neonatal, 26.7 Atenção básica/ESF, 26.8 Urgência/emergência, 26.9 Hospital
    - Colunas: **Falha no acesso (1=Sim, 2=Não, 3=Inconclusivo)** + **Falha na assistência (1=Sim, 2=Não, 3=Inconclusivo)**
26.10 **Organização do sistema (a-i)** - **MATRIZ/TABELA**:
    - Itens: a) Cobertura AB, b) Referência/contrarreferência, c) Pré-natal alto risco, d) Leito UTI gestante, e) Leitos UTI neonatal, f) Central regulação, g) Transporte, h) Bancos sangue, i) Outros
    - Colunas: **1-Adequado, 2-Parcial, 3-Inadequado** + **Observação**

### PÁGINA 4 - EVITABILIDADE E RECOMENDAÇÕES (Campos 27-29)
27. **Óbito evitável?** - Checkboxes: Sim / Não / Inconclusivo
28. **Classificações**:
    - **Wigglesworth** - W1 a W9 (radio/checkbox - exatamente 1)
    - **SEADE** - S1 a S7 (checkbox - pelo menos 1)
    - **Lista Brasileira** - **Oficial: 1.1, 1.2.1, 1.2.2, 1.2.3, 1.3, 1.4, 2, 3** (checkbox Sim/Não cada)
29. **Recomendações** - **8 textareas livres** (Recomendação 1 a 8)
30. **Data da conclusão** - Data
31. **Responsável** - Nome + Carimbo/Rubrica

---

## RESUMO DAS CORREÇÕES APLICADAS

| Item | Status | Detalhes |
|------|--------|----------|
| Lista Brasileira (28) | ✅ CORRIGIDO | Oficial: 1.1, 1.2.1, 1.2.2, 1.2.3, 1.3, 1.4, 2, 3 (Sim/Não cada) |
| Estabelecimentos (17,18,19) | ✅ ADICIONADO | 3 momentos × (Nome, CNES, Tipo: Público/Privado/Convênio/Outros) |
| Matriz 26 (Frontend) | ✅ REFAATORADO | Renderização em tabela/grade igual ao PDF |
| Matriz 26.10 (Frontend) | ✅ REFAATORADO | Tabela com 1-Adequado/2-Parcial/3-Inadequado + Obs |
| Escolaridade (13) | ✅ CORRIGIDO | Linha horizontal: Anos / Série / Grau / Ignorado(checkbox) |
| Recomendações (29) | ✅ CORRIGIDO | 8 textareas livres (não checkboxes) |
| Escolaridade - Ignorado | ✅ ADICIONADO | Checkbox "Ignorado" na linha horizontal |
| Local do Parto (18) | ✅ ATUALIZADO | Estabelecimento: Nome, CNES, Tipo |

---

## ARQUIVOS MODIFICADOS

1. `app/utils/campos.py` - Campos INFANTIL_FETAL atualizados
2. `templates/investigacoes/imprimir_infantil_fetal.html` - PDF template
3. `templates/investigacoes/detalhe.html` - Frontend com templates específicos por seção
4. CSS adicionado para tabelas Matriz 26, 26.10, Lista Brasileira, Escolaridade, Estabelecimentos

---

## PENDÊNCIAS PARA VALIDAÇÃO FINAL

- [ ] Confirmar número exato de Recomendações (oficial = 8?)
- [ ] Validar se Matriz 26 legenda "1=Sim, 2=Não, 3=Inconclusivo" está correta
- [ ] Verificar se Wigglesworth deve ser radio (exatamente 1) vs checkbox
- [ ] Confirmar se SEADE exige pelo menos 1 marcado
- [ ] Testar geração PDF completo com todos os novos campos
- [ ] Verificar migração de dados em investigações existentes