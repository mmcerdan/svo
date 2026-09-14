import re
from typing import List, Dict, Any

# ============================================================
# CAMPOS PADRÃO POR TIPO DE INVESTIGAÇÃO
# ============================================================

CAMPOS_PADRAO = {
    'MIF': [
        'Nome da falecida', 'Nº da DO', 'Data do óbito', 'Endereço', 'Número',
        'Complemento', 'Bairro', 'Distrito/Povoado',
        'Zona: Urbana', 'Zona: Rural',
        'Município de residência', 'UF residência', 'Cartão SUS',
        'Equipe/PACS/PSF', 'Centro Saúde/UBS', 'Distrito Sanitário',
        'Local de ocorrência', 'Nome estabelecimento', 'Código CNES',
        'Município ocorrência', 'UF ocorrência',
        'Grávida no momento do óbito? (Sim)', 'Grávida no momento do óbito? (Não)',
        'Grávida no momento do óbito? (Não sabe)',
        'Esteve grávida nos 12 meses? (Sim)', 'Esteve grávida nos 12 meses? (Não)',
        'Esteve grávida nos 12 meses? (Não sabe)',
        'Resumo do caso / justificativa', 'Data da investigação',
        'Responsável investigação - nome', 'Responsável investigação - carimbo/rubrica',
    ],
    'MATERNO': [
        'Nome da falecida', 'Nº da DO', 'Data do óbito', 'Endereço', 'Número',
        'Complemento', 'Bairro', 'Distrito/Povoado',
        'Zona: Urbana', 'Zona: Rural',
        'Tipo seguro saúde', 'Centro de Saúde/UBS',
        'Equipe/PACS/PSF - nome', 'Sem cobertura ESF', 'Distrito Sanitário',
        'Nome serviço pré-natal', 'Código CNES (pré-natal)',
        'Tipo serviço: CS SUS', 'Tipo serviço: Convênio', 'Tipo serviço: Particular',
        'Não fez pré-natal',
        'IG 1ª consulta (semanas)', 'IG 1ª consulta (meses)', 'IG 1ª consulta SR',
        'IG última consulta (semanas)', 'IG última consulta (meses)', 'IG última consulta SR',
        'Nº consultas pré-natal', 'Nº consultas SR',
        'Cadastrada no Sisprenatal? (Sim)', 'Cadastrada no Sisprenatal? (Não)',
        'Cadastrada no Sisprenatal? (SR)',
        'Já esteve grávida antes? (Sim)', 'Já esteve grávida antes? (Não)',
        'Já esteve grávida antes? (SR)',
        'Nº gestações', 'Nº partos', 'Nº abortos', 'Histórico gestações SR',
        'Partos normais', 'Partos fórceps', 'Partos cesáreos', 'Tipos parto SR',
        'Gestante alto risco? (Sim)', 'Gestante alto risco? (Não)', 'Gestante alto risco? (SR)',
        'Acompanhada PNAR? (Sim/Qual)', 'Acompanhada PNAR? (Não)', 'Acompanhada PNAR? (SR)',
        'A partir de semanas (PNAR)',
        'Acompanhamento AB mantido? (Sim)', 'Acompanhamento AB mantido? (Não)',
        'Acompanhamento AB mantido? (SR)',
        'Internada na gestação? (Sim)', 'Internada na gestação? (Não)',
        'Internada na gestação? (SR)',
        'Quantas internações?', 'Motivos da internação',
        '1ª internação (semanas)', '1ª internação (local)',
        '2ª internação (semanas)', '2ª internação (local)',
        'Patologias/fatores de risco',
        'Uso de medicação? (Sim)', 'Uso de medicação? (Não)', 'Uso de medicação? (SR)',
        'Quais medicamentos?',
        'Vacinação tétano: 1ª dose', 'Vacinação tétano: 2ª dose', 'Vacinação tétano: 3ª dose',
        'Vacinação tétano: Reforço', 'Vacinação tétano: Imune', 'Vacinação tétano: SR',
        'Visita domiciliar pré-natal? (Sim)', 'Visita domiciliar pré-natal? (Não)',
        'Visita domiciliar pré-natal? (SR)',
        'Motivo da visita domiciliar', 'Observações do pré-natal',
        'Resp. investigação PN - nome', 'Resp. investigação PN - profissão',
        'Causa do óbito no prontuário', 'Observações gerais',
        'O que aconteceu (investigador)', 'Data de encerramento',
        'Resp. investigação geral - nome', 'Resp. investigação geral - carimbo',
        'Maternidade referencia', 'Faltas no pre-natal', 'Prevencao cancer',
        'Exame 24.1 T1', 'Exame 24.1 T1 resultado', 'Exame 24.1 T2', 'Exame 24.1 T2 resultado', 'Exame 24.1 T3', 'Exame 24.1 T3 resultado', 'Exame 24.1 SR',
        'Exame 24.2 T1', 'Exame 24.2 T1 resultado', 'Exame 24.2 T2', 'Exame 24.2 T2 resultado', 'Exame 24.2 T3', 'Exame 24.2 T3 resultado', 'Exame 24.2 SR',
        'Exame 24.3 T1', 'Exame 24.3 T1 resultado', 'Exame 24.3 T2', 'Exame 24.3 T2 resultado', 'Exame 24.3 T3', 'Exame 24.3 T3 resultado', 'Exame 24.3 SR',
        'Exame 24.4 T1', 'Exame 24.4 T1 resultado', 'Exame 24.4 T2', 'Exame 24.4 T2 resultado', 'Exame 24.4 T3', 'Exame 24.4 T3 resultado', 'Exame 24.4 SR',
        'Exame 24.5 T1', 'Exame 24.5 T1 resultado', 'Exame 24.5 T2', 'Exame 24.5 T2 resultado', 'Exame 24.5 T3', 'Exame 24.5 T3 resultado', 'Exame 24.5 SR',
        'Exame 24.6 T1', 'Exame 24.6 T1 resultado', 'Exame 24.6 T2', 'Exame 24.6 T2 resultado', 'Exame 24.6 T3', 'Exame 24.6 T3 resultado', 'Exame 24.6 SR',
        'Exame 24.7 T1', 'Exame 24.7 T1 resultado', 'Exame 24.7 T2', 'Exame 24.7 T2 resultado', 'Exame 24.7 T3', 'Exame 24.7 T3 resultado', 'Exame 24.7 SR',
        'Exame 24.8 T1', 'Exame 24.8 T1 resultado', 'Exame 24.8 T2', 'Exame 24.8 T2 resultado', 'Exame 24.8 T3', 'Exame 24.8 T3 resultado', 'Exame 24.8 SR',
        'Exame 24.9 T1', 'Exame 24.9 T1 resultado', 'Exame 24.9 T2', 'Exame 24.9 T2 resultado', 'Exame 24.9 T3', 'Exame 24.9 T3 resultado', 'Exame 24.9 SR',
        'Exame 24.10 T1', 'Exame 24.10 T1 resultado', 'Exame 24.10 T2', 'Exame 24.10 T2 resultado', 'Exame 24.10 T3', 'Exame 24.10 T3 resultado', 'Exame 24.10 SR',
        'Exame 24.11 T1', 'Exame 24.11 T1 resultado', 'Exame 24.11 T2', 'Exame 24.11 T2 resultado', 'Exame 24.11 T3', 'Exame 24.11 T3 resultado', 'Exame 24.11 SR',
        'Exame 24.12 T1', 'Exame 24.12 T1 resultado', 'Exame 24.12 T2', 'Exame 24.12 T2 resultado', 'Exame 24.12 T3', 'Exame 24.12 T3 resultado', 'Exame 24.12 SR',
        'Exame 24.13 T1', 'Exame 24.13 T1 resultado', 'Exame 24.13 T2', 'Exame 24.13 T2 resultado', 'Exame 24.13 T3', 'Exame 24.13 T3 resultado', 'Exame 24.13 SR',
        'Quadro PN - data_1', 'Quadro PN - ig_1', 'Quadro PN - peso_1', 'Quadro PN - pa_1', 'Quadro PN - au_1', 'Quadro PN - bcf_1', 'Quadro PN - mf_1', 'Quadro PN - edema_1', 'Quadro PN - queixas_1', 'Quadro PN - prof_1',
        'Quadro PN - data_2', 'Quadro PN - ig_2', 'Quadro PN - peso_2', 'Quadro PN - pa_2', 'Quadro PN - au_2', 'Quadro PN - bcf_2', 'Quadro PN - mf_2', 'Quadro PN - edema_2', 'Quadro PN - queixas_2', 'Quadro PN - prof_2',
        'Quadro PN - data_3', 'Quadro PN - ig_3', 'Quadro PN - peso_3', 'Quadro PN - pa_3', 'Quadro PN - au_3', 'Quadro PN - bcf_3', 'Quadro PN - mf_3', 'Quadro PN - edema_3', 'Quadro PN - queixas_3', 'Quadro PN - prof_3',
        'Quadro PN - data_4', 'Quadro PN - ig_4', 'Quadro PN - peso_4', 'Quadro PN - pa_4', 'Quadro PN - au_4', 'Quadro PN - bcf_4', 'Quadro PN - mf_4', 'Quadro PN - edema_4', 'Quadro PN - queixas_4', 'Quadro PN - prof_4',
        'Atendimento - data_1', 'Atendimento - tipo_1', 'Atendimento - local_1', 'Atendimento - idade_1', 'Atendimento - peso_1', 'Atendimento - queixa_1', 'Atendimento - exames_1', 'Atendimento - conduta_1',
        'Atendimento - data_2', 'Atendimento - tipo_2', 'Atendimento - local_2', 'Atendimento - idade_2', 'Atendimento - peso_2', 'Atendimento - queixa_2', 'Atendimento - exames_2', 'Atendimento - conduta_2',
        'Atendimento - data_3', 'Atendimento - tipo_3', 'Atendimento - local_3', 'Atendimento - idade_3', 'Atendimento - peso_3', 'Atendimento - queixa_3', 'Atendimento - exames_3', 'Atendimento - conduta_3',
        'Atendimento - data_4', 'Atendimento - tipo_4', 'Atendimento - local_4', 'Atendimento - idade_4', 'Atendimento - peso_4', 'Atendimento - queixa_4', 'Atendimento - exames_4', 'Atendimento - conduta_4',
        'Atendimento - data_5', 'Atendimento - tipo_5', 'Atendimento - local_5', 'Atendimento - idade_5', 'Atendimento - peso_5', 'Atendimento - queixa_5', 'Atendimento - exames_5', 'Atendimento - conduta_5',
        'Encaminhamentos urgencia', 'Acomp. em programas (hiperdia)',
        'Causa do obito no prontuario (M1)', 'Observacoes gerais (M1)',
    ],
    'INFANTIL_FETAL': [
        'Nome da criança', 'Nome da mãe', 'Nº do caso', 'Data de nascimento',
        'Nº da DN', 'Nº da DO', 'Data do óbito',
        'Tipo óbito fetal: Anteparto', 'Tipo óbito fetal: Intraparto',
        'Peso ao nascer (gramas)',
        'Sexo: Masculino', 'Sexo: Feminino', 'Sexo: Ignorado',
        'Idade ao óbito', 'Idade gestacional (semanas)', 'Idade gestacional (meses)',
        'IG ignorado',
        'Faixa etária: Fetal', 'Faixa etária: Neonatal precoce',
        'Faixa etária: Neonatal tardio', 'Faixa etária: Pós-neonatal',
        'Faixa etária: Ignorado',
        'Idade da mãe (anos)',
        'Escolaridade mãe - anos', 'Escolaridade mãe - série',
        'Escolaridade mãe - grau', 'Escolaridade mãe - ignorado',
        'Município residência', 'UF residência', 'Município ocorrência', 'UF ocorrência',
        'Resumo do caso',
        'Fonte: Prontuários ambulatoriais', 'Fonte: Entrevista domiciliar',
        'Fonte: Autópsia verbal', 'Fonte: Registros urgência/emergência',
        'Fonte: Registros hospitalares', 'Fonte: SVO', 'Fonte: IML',
        'Estabelecimentos saúde pré-natal',
        'Avaliação - Assistência pré-natal: Sim', 'Avaliação - Assistência pré-natal: Não', 'Avaliação - Assistência pré-natal: SR',
        'Avaliação - Assistência ao parto: Sim', 'Avaliação - Assistência ao parto: Não', 'Avaliação - Assistência ao parto: SR',
        'Avaliação - Assistência RN sala parto: Sim', 'Avaliação - Assistência RN sala parto: Não', 'Avaliação - Assistência RN sala parto: SR',
        'Avaliação - Assistência RN alojamento: Sim', 'Avaliação - Assistência RN alojamento: Não', 'Avaliação - Assistência RN alojamento: SR',
        'Avaliação - Assistência RN UTI neonatal: Sim', 'Avaliação - Assistência RN UTI neonatal: Não', 'Avaliação - Assistência RN UTI neonatal: SR',
        'Avaliação - Assistência criança atenção básica: Sim', 'Avaliação - Assistência criança atenção básica: Não', 'Avaliação - Assistência criança atenção básica: SR',
        'Avaliação - Assistência criança urgência: Sim', 'Avaliação - Assistência criança urgência: Não', 'Avaliação - Assistência criança urgência: SR',
        'Avaliação - Assistência criança hospital: Sim', 'Avaliação - Assistência criança hospital: Não', 'Avaliação - Assistência criança hospital: SR',
        'Avaliação - Dificuldades da família: Sim', 'Avaliação - Dificuldades da família: Não', 'Avaliação - Dificuldades da família: SR',
        'Avaliação - Causas externas: Sim', 'Avaliação - Causas externas: Não', 'Avaliação - Causas externas: SR',
        'Organização - Cobertura atenção primária: Sim', 'Organização - Cobertura atenção primária: Não', 'Organização - Cobertura atenção primária: SR',
        'Organização - Referência/contrarreferência: Sim', 'Organização - Referência/contrarreferência: Não', 'Organização - Referência/contrarreferência: SR',
        'Organização - Pré-natal alto risco: Sim', 'Organização - Pré-natal alto risco: Não', 'Organização - Pré-natal alto risco: SR',
        'Organização - Leito UTI gestante: Sim', 'Organização - Leito UTI gestante: Não', 'Organização - Leito UTI gestante: SR',
        'Organização - Leitos UTI neonatal: Sim', 'Organização - Leitos UTI neonatal: Não', 'Organização - Leitos UTI neonatal: SR',
        'Organização - Central regulação: Sim', 'Organização - Central regulação: Não', 'Organização - Central regulação: SR',
        'Organização - Transporte pré/inter-hospitalar: Sim', 'Organização - Transporte pré/inter-hospitalar: Não', 'Organização - Transporte pré/inter-hospitalar: SR',
        'Organização - Bancos de sangue: Sim', 'Organização - Bancos de sangue: Não', 'Organização - Bancos de sangue: SR',
        'Organização - Outros: Sim', 'Organização - Outros: Não', 'Organização - Outros: SR',
        'Óbito evitável? (Sim)', 'Óbito evitável? (Não)', 'Óbito evitável? (Inconclusivo)',
        'Wigglesworth: W1', 'Wigglesworth: W2', 'Wigglesworth: W3',
        'Wigglesworth: W4', 'Wigglesworth: W5', 'Wigglesworth: W6',
        'Wigglesworth: W7', 'Wigglesworth: W8', 'Wigglesworth: W9',
        'SEADE: S1', 'SEADE: S2', 'SEADE: S3', 'SEADE: S4',
        'SEADE: S5', 'SEADE: S6', 'SEADE: S7',
        'Local do parto: Hospital', 'Local do parto: Domicilio', 'Local do parto: Outro',
        'Tipo estabelecimento parto',
        'Uso de partograma', 'VDRL',
        'Acompanhamento atencao basica', 'Vacinas realizadas',
        'Causa original prontuario',
        'CID Ia - diagnostico', 'CID Ia - CID',
        'CID Ib - diagnostico', 'CID Ib - CID',
        'CID Ic - diagnostico', 'CID Ic - CID',
        'CID Id - diagnostico', 'CID Id - CID',
        'CID II - diagnostico', 'CID II - CID',
        'Alteracao DO - causa basica original', 'Alteracao DO - causa basica nova',
        'Alteracao DO - CID original', 'Alteracao DO - CID novo',
        'Alteracao DO - data original', 'Alteracao DO - data nova',
        'Alteracao DO - local original', 'Alteracao DO - local nova',
        'Alteracao DO - idade original', 'Alteracao DO - idade nova',
        'Alteracao DO - peso original', 'Alteracao DO - peso novo',
        'Problemas identificados',
        'Problema 26.1 acesso - 1', 'Problema 26.1 acesso - 2', 'Problema 26.1 acesso - 3',
        'Problema 26.1 assistencia - 1', 'Problema 26.1 assistencia - 2', 'Problema 26.1 assistencia - 3',
        'Problema 26.2 acesso - 1', 'Problema 26.2 acesso - 2', 'Problema 26.2 acesso - 3',
        'Problema 26.2 assistencia - 1', 'Problema 26.2 assistencia - 2', 'Problema 26.2 assistencia - 3',
        'Problema 26.3 acesso - 1', 'Problema 26.3 acesso - 2', 'Problema 26.3 acesso - 3',
        'Problema 26.3 assistencia - 1', 'Problema 26.3 assistencia - 2', 'Problema 26.3 assistencia - 3',
        'Problema 26.4 acesso - 1', 'Problema 26.4 acesso - 2', 'Problema 26.4 acesso - 3',
        'Problema 26.4 assistencia - 1', 'Problema 26.4 assistencia - 2', 'Problema 26.4 assistencia - 3',
        'Problema 26.5 acesso - 1', 'Problema 26.5 acesso - 2', 'Problema 26.5 acesso - 3',
        'Problema 26.5 assistencia - 1', 'Problema 26.5 assistencia - 2', 'Problema 26.5 assistencia - 3',
        'Problema 26.6 acesso - 1', 'Problema 26.6 acesso - 2', 'Problema 26.6 acesso - 3',
        'Problema 26.6 assistencia - 1', 'Problema 26.6 assistencia - 2', 'Problema 26.6 assistencia - 3',
        'Problema 26.7 acesso - 1', 'Problema 26.7 acesso - 2', 'Problema 26.7 acesso - 3',
        'Problema 26.7 assistencia - 1', 'Problema 26.7 assistencia - 2', 'Problema 26.7 assistencia - 3',
        'Problema 26.8 acesso - 1', 'Problema 26.8 acesso - 2', 'Problema 26.8 acesso - 3',
        'Problema 26.8 assistencia - 1', 'Problema 26.8 assistencia - 2', 'Problema 26.8 assistencia - 3',
        'Problema 26.9 acesso - 1', 'Problema 26.9 acesso - 2', 'Problema 26.9 acesso - 3',
        'Problema 26.9 assistencia - 1', 'Problema 26.9 assistencia - 2', 'Problema 26.9 assistencia - 3',
        'Organizacao a - 1', 'Organizacao a - 2', 'Organizacao a - 3', 'Organizacao a - obs',
        'Organizacao b - 1', 'Organizacao b - 2', 'Organizacao b - 3', 'Organizacao b - obs',
        'Organizacao c - 1', 'Organizacao c - 2', 'Organizacao c - 3', 'Organizacao c - obs',
        'Organizacao d - 1', 'Organizacao d - 2', 'Organizacao d - 3', 'Organizacao d - obs',
        'Organizacao e - 1', 'Organizacao e - 2', 'Organizacao e - 3', 'Organizacao e - obs',
        'Organizacao f - 1', 'Organizacao f - 2', 'Organizacao f - 3', 'Organizacao f - obs',
        'Organizacao g - 1', 'Organizacao g - 2', 'Organizacao g - 3', 'Organizacao g - obs',
        'Organizacao h - 1', 'Organizacao h - 2', 'Organizacao h - 3', 'Organizacao h - obs',
        'Organizacao i - 1', 'Organizacao i - 2', 'Organizacao i - 3', 'Organizacao i - obs',
        'Lista Brasileira 1.1: Sim', 'Lista Brasileira 1.1: Não',
        'Lista Brasileira 1.2: Sim', 'Lista Brasileira 1.2: Não',
        'Lista Brasileira 1.3: Sim', 'Lista Brasileira 1.3: Não',
        'Lista Brasileira 1.4: Sim', 'Lista Brasileira 1.4: Não',
        'Lista Brasileira 2.1: Sim', 'Lista Brasileira 2.1: Não',
        'Lista Brasileira 2.2: Sim', 'Lista Brasileira 2.2: Não',
        'Lista Brasileira 2.3: Sim', 'Lista Brasileira 2.3: Não',
        'Lista Brasileira 3.1: Sim', 'Lista Brasileira 3.1: Não',
        'Lista Brasileira 3.2: Sim', 'Lista Brasileira 3.2: Não',
        'Lista Brasileira 3.3: Sim', 'Lista Brasileira 3.3: Não',
        'Recomendacao 1: Sim', 'Recomendacao 1: Não',
        'Recomendacao 2: Sim', 'Recomendacao 2: Não',
        'Recomendacao 3: Sim', 'Recomendacao 3: Não',
        'Recomendacao 4: Sim', 'Recomendacao 4: Não',
        'Recomendacao 5: Sim', 'Recomendacao 5: Não',
        'Recomendacao 6: Sim', 'Recomendacao 6: Não',
        'Recomendacao 7: Sim', 'Recomendacao 7: Não',
        'Recomendacao 8: Sim', 'Recomendacao 8: Não',
        'Data da conclusao',
        'Responsavel preenchimento - nome', 'Responsavel preenchimento - carimbo/rubrica',
    ],
'MAL_DEFINIDA': [
        'Nº da DO', 'Nome do falecido', 'Nome da mãe',
        'Data de nascimento', 'Data do óbito', 'Causa básica original',
        'Nome da Unidade Básica/USF', 'Nº prontuário UBS',
        'Tempo de moradia no domicílio', 'Cadastrado na USF: Sim', 'Cadastrado na USF: Nao',
        'Patologias/motivos de atendimento',
        'Data da última consulta', 'Motivo da última consulta',
        'Nome do estabelecimento de saúde', 'Nº prontuário hospitalar',
        'Data da internação', 'Data da alta',
        'Estado do paciente: Consciente', 'Estado do paciente: Inconsciente',
        'Estado do paciente: Agonizante', 'Estado do paciente: Sem vida',
        'Motivo da alta: Cura', 'Motivo da alta: Transferencia',
        'Motivo da alta: Saida solicitacao', 'Motivo da alta: Evasao', 'Motivo da alta: Obito',
        'Atendimento pré-hospitalar', 'Hipótese diagnóstica da alta',
        'Resultados de exames relevantes', 'Procedimentos realizados',
        'Causa do óbito no prontuário',
        'Investigação SINAN: Investigado', 'Investigação SINAN: Nao disponivel', 'Investigação SINAN: Nao realizado', 'Investigação SINAN - patologia',
        'Investigação IML: Investigado', 'Investigação IML: Nao disponivel', 'Investigação IML: Nao realizado', 'Investigação IML - laudo',
        'Investigação SVO: Investigado', 'Investigação SVO: Nao disponivel', 'Investigação SVO: Nao realizado', 'Investigação SVO - laudo',
        'Investigação FUNASA: Investigado', 'Investigação FUNASA: Nao disponivel', 'Investigação FUNASA: Nao realizado', 'Investigação FUNASA - descricao',
        'Investigacao jornal/internet: Consultado', 'Investigacao jornal/internet: Nao disponivel', 'Investigacao jornal/internet - descricao',
        'Formulario utilizado: Form 1', 'Formulario utilizado: Form 2', 'Formulario utilizado: Form 3', 'Formulario utilizado: Form 3.1-MIF', 'Formulario utilizado: Nao realizada', 'Formulario utilizado (detalhe)',
        'Causa direta - diagnostico', 'Causa direta - CID',
        'Antecedente (linha b) - diagnostico', 'Antecedente (linha b) - CID',
        'Antecedente (linha c) - diagnostico', 'Antecedente (linha c) - CID',
        'Causa basica - diagnostico', 'Causa basica - CID',
        'Outras condicoes significativas', 'Parte II - CID',
        'Data da conclusao', 'Responsavel pela investigacao',
        'Coordenador Vigilancia SIM',
    ],
'INFANTIL': [
        'Nome da criança', 'Nome da mãe', 'Nº da DO', 'Data do óbito',
        'Nº da DN', 'Data de nascimento',
        'Sexo', 'Sexo: Masculino', 'Sexo: Feminino', 'Sexo: Ignorado',
        'Peso ao nascer (gramas)', 'Idade ao óbito',
        'Idade óbito - meses', 'Idade óbito - dias', 'Idade óbito - horas',
        'Idade óbito - minutos', 'Idade óbito ignorado',
        'Nº do Cartão SUS', 'Equipe/PACS/PSF', 'Centro de Saude/UBS',
        'Distrito Sanitário', 'Nome do servico de pre-natal', 'Código CNES',
        'Tipo de servico',
        'Tipo servico: CS SUS', 'Tipo servico: Convenio', 'Tipo servico: Particular',
        'Não fez pré-natal',
        'IG na 1a consulta (semanas)', 'IG na 1a consulta (meses)',
        'IG 1ª consulta sem registro',
        'Nº de consultas pré-natal', 'Nº consultas sem registro',
        'Esteve grávida antes? (Sim)', 'Esteve grávida antes? (Não)',
        'Esteve grávida antes? (SR)',
        'Nº gestações', 'Nº partos', 'Nº abortos', 'Histórico gestações SR',
        'Partos normais', 'Partos fórceps', 'Partos cesáreos', 'Tipos parto SR',
        'Gestante de alto risco? (Sim)', 'Gestante de alto risco? (Não)',
        'Gestante de alto risco? (SR)', 'Detalhe do alto risco',
        'Acompanhada PNAR? (Sim/Qual)', 'Acompanhada PNAR? (Não)',
        'Acompanhada PNAR? (SR)', 'A partir de quantas semanas?',
        'Acompanhamento AB mantido? (Sim)', 'Acompanhamento AB mantido? (Não)',
        'Acompanhamento AB mantido? (SR)',
        'Internada durante a gestação? (Sim)', 'Internada durante a gestação? (Não)',
        'Internada durante a gestação? (SR)',
        'Quantas internações?', 'Motivos da internação',
        '1ª internação - semanas', '1ª internação - local',
        '2ª internação - semanas', '2ª internação - local',
        'Patologias/fatores de risco',
        'Uso de medicação na gestação? (Sim)', 'Uso de medicação na gestação? (Não)',
        'Uso de medicação na gestação? (SR)', 'Quais medicamentos?',
        'Esquema vacinacao tétano: 1ª dose', 'Esquema vacinacao tétano: 2ª dose',
        'Esquema vacinacao tétano: 3ª dose', 'Esquema vacinacao tétano: Reforço',
        'Esquema vacinacao tétano: Imune', 'Esquema vacinacao tétano: SR',
        'Visita domiciliar pré-natal? (Sim)', 'Visita domiciliar pré-natal? (Não)',
        'Visita domiciliar pré-natal? (SR)',
        'Motivo da visita domiciliar', 'Observacoes do pre-natal',
        'O que aconteceu (investigador) - PN',
        'Responsavel investigacao - nome', 'Responsavel investigacao - profissao',
        'Crianca em acompanhamento servico de saude? (Sim)',
        'Crianca em acompanhamento servico de saude? (Não)',
        'Crianca em acompanhamento servico de saude? (SR)',
        'Estabelecimento atendimento crianca', 'Codigo CNES (crianca)',
        'Tipo servico crianca: CS SUS', 'Tipo servico crianca: Convenio',
        'Tipo servico crianca: Particular',
        'Aleitamento materno? (Sim)', 'Aleitamento materno? (Não)',
        'Aleitamento exclusivo? (Sim)', 'Aleitamento exclusivo? (Não)',
        'Tempo aleitamento exclusivo - dias', 'Tempo aleitamento exclusivo - meses',
        'NSA aleitamento exclusivo',
        'Duracao aleitamento misto - dias', 'Duracao aleitamento misto - meses',
        'NSA aleitamento misto', 'Observacoes alimentacao',
        'Encaminhamento referencia? (Sim)', 'Encaminhamento referencia? (Não)',
        'Encaminhamento referencia? (SR)', 'Motivo do encaminhamento',
        'Vacinacao completa? (Sim)', 'Vacinacao completa? (Não)',
        'Vacinacao completa? (SR)', 'Vacinas em atraso',
        'Acomp. especial? (Sim)', 'Acomp. especial? (Não)',
        'Acomp. especial? (SR)',
        'Acomp. especial: Desnutricao', 'Acomp. especial: RN alto risco',
        'Acomp. especial: Prematuro', 'Acomp. especial: Asma',
        'Acomp. especial: Baixo peso', 'Acomp. especial: Outro',
        'Visitas domiciliares? (Sim)', 'Visitas domiciliares? (Não)',
        'Visitas domiciliares? (SR)',
        'Motivo da visita domiciliar (crianca)',
        'Causa do obito no prontuario', 'Observacoes gerais',
        'O que aconteceu (investigador)', 'Data da conclusao',
        'Responsavel pela investigacao', 'Responsavel - carimbo/rubrica',
        'Quadro PN - data_1', 'Quadro PN - ig_1', 'Quadro PN - peso_1', 'Quadro PN - pa_1', 'Quadro PN - au_1', 'Quadro PN - bcf_1', 'Quadro PN - mf_1', 'Quadro PN - edema_1', 'Quadro PN - queixas_1', 'Quadro PN - prof_1',
        'Quadro PN - data_2', 'Quadro PN - ig_2', 'Quadro PN - peso_2', 'Quadro PN - pa_2', 'Quadro PN - au_2', 'Quadro PN - bcf_2', 'Quadro PN - mf_2', 'Quadro PN - edema_2', 'Quadro PN - queixas_2', 'Quadro PN - prof_2',
        'Quadro PN - data_3', 'Quadro PN - ig_3', 'Quadro PN - peso_3', 'Quadro PN - pa_3', 'Quadro PN - au_3', 'Quadro PN - bcf_3', 'Quadro PN - mf_3', 'Quadro PN - edema_3', 'Quadro PN - queixas_3', 'Quadro PN - prof_3',
        'Quadro PN - data_4', 'Quadro PN - ig_4', 'Quadro PN - peso_4', 'Quadro PN - pa_4', 'Quadro PN - au_4', 'Quadro PN - bcf_4', 'Quadro PN - mf_4', 'Quadro PN - edema_4', 'Quadro PN - queixas_4', 'Quadro PN - prof_4',
        'Quadro PN - data_5', 'Quadro PN - ig_5', 'Quadro PN - peso_5', 'Quadro PN - pa_5', 'Quadro PN - au_5', 'Quadro PN - bcf_5', 'Quadro PN - mf_5', 'Quadro PN - edema_5', 'Quadro PN - queixas_5', 'Quadro PN - prof_5',
        'Atendimento - data_1', 'Atendimento - tipo_1', 'Atendimento - local_1', 'Atendimento - idade_1', 'Atendimento - peso_1', 'Atendimento - queixa_1', 'Atendimento - exames_1', 'Atendimento - conduta_1',
        'Atendimento - data_2', 'Atendimento - tipo_2', 'Atendimento - local_2', 'Atendimento - idade_2', 'Atendimento - peso_2', 'Atendimento - queixa_2', 'Atendimento - exames_2', 'Atendimento - conduta_2',
        'Atendimento - data_3', 'Atendimento - tipo_3', 'Atendimento - local_3', 'Atendimento - idade_3', 'Atendimento - peso_3', 'Atendimento - queixa_3', 'Atendimento - exames_3', 'Atendimento - conduta_3',
        'Atendimento - data_4', 'Atendimento - tipo_4', 'Atendimento - local_4', 'Atendimento - idade_4', 'Atendimento - peso_4', 'Atendimento - queixa_4', 'Atendimento - exames_4', 'Atendimento - conduta_4',
        'Atendimento - data_5', 'Atendimento - tipo_5', 'Atendimento - local_5', 'Atendimento - idade_5', 'Atendimento - peso_5', 'Atendimento - queixa_5', 'Atendimento - exames_5', 'Atendimento - conduta_5',
        'Atendimento - data_6', 'Atendimento - tipo_6', 'Atendimento - local_6', 'Atendimento - idade_6', 'Atendimento - peso_6', 'Atendimento - queixa_6', 'Atendimento - exames_6', 'Atendimento - conduta_6',
        'Exame hb_ht - 1tri', 'Exame hb_ht - 2tri', 'Exame hb_ht - 3tri', 'Exame hb_ht - resultado',
        'Exame grupo_sanguineo_abo - 1tri', 'Exame grupo_sanguineo_abo - 2tri', 'Exame grupo_sanguineo_abo - 3tri', 'Exame grupo_sanguineo_abo - resultado',
        'Exame fator_rh - 1tri', 'Exame fator_rh - 2tri', 'Exame fator_rh - 3tri', 'Exame fator_rh - resultado',
        'Exame coombs_indireto - 1tri', 'Exame coombs_indireto - 2tri', 'Exame coombs_indireto - 3tri', 'Exame coombs_indireto - resultado',
        'Exame glicemia_jejum - 1tri', 'Exame glicemia_jejum - 2tri', 'Exame glicemia_jejum - 3tri', 'Exame glicemia_jejum - resultado',
        'Exame toxoplasmose_igm - 1tri', 'Exame toxoplasmose_igm - 2tri', 'Exame toxoplasmose_igm - 3tri', 'Exame toxoplasmose_igm - resultado',
        'Exame curva_tolerancia_glicose - 1tri', 'Exame curva_tolerancia_glicose - 2tri', 'Exame curva_tolerancia_glicose - 3tri', 'Exame curva_tolerancia_glicose - resultado',
        'Exame urina_rotina - 1tri', 'Exame urina_rotina - 2tri', 'Exame urina_rotina - 3tri', 'Exame urina_rotina - resultado',
        'Exame urocultura - 1tri', 'Exame urocultura - 2tri', 'Exame urocultura - 3tri', 'Exame urocultura - resultado',
        'Exame hbsag - 1tri', 'Exame hbsag - 2tri', 'Exame hbsag - 3tri', 'Exame hbsag - resultado',
        'Exame teste_hiv - 1tri', 'Exame teste_hiv - 2tri', 'Exame teste_hiv - 3tri', 'Exame teste_hiv - resultado',
        'Exame vdrl - 1tri', 'Exame vdrl - 2tri', 'Exame vdrl - 3tri', 'Exame vdrl - resultado',
        'Exame outros_exames - 1tri', 'Exame outros_exames - 2tri', 'Exame outros_exames - 3tri', 'Exame outros_exames - resultado',
    ],
}

def get_campos_padrao_investigacao(tipo: str) -> List[str]:
    """Retorna lista de nomes de campos padrão para o tipo de investigação."""
    return CAMPOS_PADRAO.get(tipo, ['Observações do caso'])


# ============================================================
# CLASSIFICAÇÃO DE TIPO DE CAMPO (checkbox vs textarea)
# ============================================================

_CHECKBOX_PATTERNS = [
    r'\?\s*\(',           # "? (" — pergunta com opção: (Sim), (Não), (SR)
    r'^Fonte:\s',         # "Fonte: "
    r'^Avaliação\s*\-',   # "Avaliação -"
    r'^Organização\s*\-', # "Organização -"
    r'^Acomp\.\s*especial:', # "Acomp. especial:"
    r'^Vacinação\s+tétano',  # "Vacinação tétano:"
    r'^Esquema\s+vacinação', # "Esquema vacinação tétano:"
    r'^Cadastrada\s+no',  # "Cadastrada no Sisprenatal"
    r'^Já\s+esteve',      # "Já esteve grávida antes?"
    r'^Gestante\s+alto\s+risco',
    r'^Acompanhada\s+PNAR',
    r'^Internada\s+(na|durante)',
    r'^Uso\s+de\s+medica',
    r'^Visita\s+domiciliar',
    r'^Aleitamento',
    r'^Encaminhamento\s+referência',
    r'^Vacinação\s+completa',
    r'^Acompanhamento\s+especial',
    r'^Óbito\s+evitável',
    r'^Criança\s+em\s+acompanhamento',
    r'^Acompanhamento\s+AB',
    r'^Não\s+fez\s+pré-natal',
    r'^Sem\s+cobertura\s+ESF',
    # Padrões adicionais para novos campos
    r'^Investigacao\s',    # SINAN, IML, SVO, FUNASA, journal/internet
    r'^Lista Brasileira:', # Lista Brasileira de Causas de Obito
    r'^Recomendacao\s',    # Recomendacoes e medidas
    r'^Organizacao\s',     # campo 26.10
    r'^Problema\s',        # campo 26
    r'^Wigglesworth:',     # classificação de evitabilidade
    r'^SEADE:',
    r'^Exame\s+\S+\s+T[123]$',      # Exame 24.1 T1 (tri checkbox)
    r'^Exame\s+\S+\s+SR$',          # Exame 24.1 SR (sem resposta)
    r'^Exame\s+\S+\s+-\s*[123]tri$', # Exames INFANTIL (hb_ht - 1tri)
]

_CHECKBOX_RE = re.compile('|'.join(_CHECKBOX_PATTERNS))

def get_tipo_campo(nome_campo: str) -> str:
    """
    Retorna 'checkbox' ou 'textarea' conforme o nome do campo.
    """
    if _CHECKBOX_RE.search(nome_campo):
        return 'checkbox'
    # Campos com ": " seguido de opção curta
    partes = nome_campo.split(': ', 1)
    if len(partes) == 2:
        opcao = partes[1]
        palavras = opcao.split()
        if len(palavras) <= 3 and not opcao.endswith(
            ('geral', 'prontuário', 'justificativa', 'investigação')
        ):
            return 'checkbox'
    return 'textarea'


# ============================================================
# EXTRAÇÃO DE GRUPO PARA AGRUPAMENTO DE CHECKBOXES
# ============================================================

_GRUPO_RE_1 = re.compile(
    r'^(.+?)\s*[:(]\s*(?:Sim|Não|SR|Ignorado|Inconclusivo|Sim/Qual|'
    r'Anteparto|Intraparto|Urbana|Rural|Masculino|Feminino|'
    r'CS SUS|Convênio|Particular).*'
)
_GRUPO_RE_2 = re.compile(r'^(.+?\?)\s*\(')

def get_grupo_campo(nome_campo: str) -> str | None:
    """Extrai o nome do grupo de um campo checkbox, ou None se for textarea."""
    if get_tipo_campo(nome_campo) != 'checkbox':
        return None
    m = _GRUPO_RE_1.match(nome_campo)
    if m:
        return m.group(1).strip()
    m = _GRUPO_RE_2.match(nome_campo)
    if m:
        return m.group(1).strip()
    # Exames: agrupar T1/T2/T3/SR/resultado do mesmo exame sob "Exame <cod>"
    m = re.match(r'^(Exame\s+\S+)', nome_campo)
    if m:
        return m.group(1).strip()
    # Problema/Organização: agrupar sob o nome do bloco
    n2 = nome_campo.lower().replace('ç', 'c').replace('ã', 'a')
    if n2.startswith('problema'):
        return 'Problema'
    if n2.startswith('organizac'):
        return 'Organização'
    partes = nome_campo.split(': ', 1)
    if len(partes) == 2:
        return partes[0]
    return nome_campo


# ============================================================
# AGRUPAMENTO DE CAMPOS PARA TEMPLATE
# ============================================================

def agrupar_campos_list(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa items (dicts com 'nome', 'tipo', 'grupo') consecutivos pelo mesmo grupo."""
    if not items:
        return []
    grupos = []
    grupo_atual = None
    for item in items:
        if item['tipo'] == 'checkbox':
            grp = item['grupo']
            if grupo_atual and grupo_atual['titulo'] == grp:
                grupo_atual['campos'].append(item)
            else:
                grupo_atual = {'tipo': 'grupo', 'titulo': grp, 'campos': [item]}
                grupos.append(grupo_atual)
        else:
            grupo_atual = None
            grupos.append({'tipo': 'campo', 'campo': item})
    return grupos


def agrupar_campos(campos_list):
    """Agrupa objetos InvestigacaoCampo consecutivos pelo mesmo grupo."""
    if not campos_list:
        return []
    grupos = []
    grupo_atual = None
    for campo in campos_list:
        nome = campo.nome_campo
        tipo = get_tipo_campo(nome)
        if tipo == 'checkbox':
            grp = get_grupo_campo(nome)
            if grupo_atual and grupo_atual['titulo'] == grp:
                grupo_atual['campos'].append(campo)
            else:
                grupo_atual = {'tipo': 'grupo', 'titulo': grp, 'campos': [campo]}
                grupos.append(grupo_atual)
        else:
            grupo_atual = None
            grupos.append({'tipo': 'campo', 'campo': campo})
    return grupos


# ============================================================
# EXTRAÇÃO DE OPÇÃO PARA LABEL DE CHECKBOX
# ============================================================

def extrair_opcao(nome: str) -> str:
    """Extrai apenas a opção do nome do campo para exibição no label."""
    if ': ' in nome:
        return nome.split(': ', 1)[-1]
    if '? (' in nome:
        m = re.search(r'\? \(([^)]+)\)', nome)
        if m:
            return m.group(1)
    return nome