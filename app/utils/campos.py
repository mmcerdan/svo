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
        'Avaliação - Assistência pré-natal', 'Avaliação - Assistência ao parto',
        'Avaliação - Assistência RN sala parto', 'Avaliação - Assistência RN alojamento',
        'Avaliação - Assistência RN UTI neonatal',
        'Avaliação - Assistência criança atenção básica',
        'Avaliação - Assistência criança urgência', 'Avaliação - Assistência criança hospital',
        'Avaliação - Dificuldades da família', 'Avaliação - Causas externas',
        'Organização - Cobertura atenção primária',
        'Organização - Referência/contrarreferência',
        'Organização - Pré-natal alto risco', 'Organização - Leito UTI gestante',
        'Organização - Leitos UTI neonatal', 'Organização - Central regulação',
        'Organização - Transporte pré/inter-hospitalar',
        'Organização - Bancos de sangue', 'Organização - Outros',
        'Óbito evitável? (Sim)', 'Óbito evitável? (Não)', 'Óbito evitável? (Inconclusivo)',
        'Wigglesworth: W1', 'Wigglesworth: W2', 'Wigglesworth: W3',
        'Wigglesworth: W4', 'Wigglesworth: W5', 'Wigglesworth: W6',
        'Wigglesworth: W7', 'Wigglesworth: W8', 'Wigglesworth: W9',
        'SEADE: S1', 'SEADE: S2', 'SEADE: S3', 'SEADE: S4',
        'SEADE: S5', 'SEADE: S6', 'SEADE: S7',
        'Fatores determinantes / comentários',
        'Recomendações / propostas de intervenção', 'Data da conclusão',
        'Comitê: Municipal', 'Comitê: Hospitalar', 'Comitê: Regional', 'Comitê: Estadual',
        'Responsável preenchimento - nome', 'Responsável preenchimento - carimbo/rubrica',
    ],
    'MAL_DEFINIDA': [
        'Nº da DO', 'Nome do falecido', 'Nome da mãe',
        'Data de nascimento', 'Data do óbito', 'Causa básica original',
        'Nome da Unidade Básica/USF', 'Nº prontuário UBS',
        'Tempo de moradia no domicílio', 'Cadastrado na USF',
        'Patologias/motivos de atendimento',
        'Data da última consulta', 'Motivo da última consulta',
        'Nome do estabelecimento de saúde', 'Nº prontuário hospitalar',
        'Data da internação', 'Data da alta',
        'Estado do paciente na hospitalização', 'Motivo da alta',
        'Atendimento pré-hospitalar', 'Hipótese diagnóstica da alta',
        'Resultados de exames relevantes', 'Procedimentos realizados',
        'Causa do óbito no prontuário',
        'Investigação SINAN', 'Investigação IML', 'Investigação SVO',
        'Investigação FUNASA', 'Investigação jornal/internet',
        'Formulário utilizado (autópsia verbal)',
        'Causa direta - diagnóstico', 'Causa direta - CID',
        'Antecedente (linha b) - diagnóstico', 'Antecedente (linha b) - CID',
        'Antecedente (linha c) - diagnóstico', 'Antecedente (linha c) - CID',
        'Causa básica - diagnóstico', 'Causa básica - CID',
        'Outras condições significativas',
        'Data da conclusão', 'Responsável pela investigação',
        'Coordenador Vigilância SIM',
    ],
    'INFANTIL': [
        'Nome da criança', 'Nome da mãe', 'Nº da DO', 'Data do óbito',
        'Nº da DN', 'Data de nascimento',
        'Sexo', 'Sexo: Masculino', 'Sexo: Feminino', 'Sexo: Ignorado',
        'Peso ao nascer (gramas)', 'Idade ao óbito',
        'Idade óbito - meses', 'Idade óbito - dias', 'Idade óbito - horas',
        'Idade óbito - minutos', 'Idade óbito ignorado',
        'Nº do Cartão SUS', 'Equipe/PACS/PSF', 'Centro de Saúde/UBS',
        'Distrito Sanitário', 'Nome do serviço de pré-natal', 'Código CNES',
        'Tipo de serviço',
        'Tipo serviço: CS SUS', 'Tipo serviço: Convênio', 'Tipo serviço: Particular',
        'Não fez pré-natal',
        'IG na 1ª consulta (semanas)', 'IG na 1ª consulta (meses)',
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
        'Esquema vacinação tétano: 1ª dose', 'Esquema vacinação tétano: 2ª dose',
        'Esquema vacinação tétano: 3ª dose', 'Esquema vacinação tétano: Reforço',
        'Esquema vacinação tétano: Imune', 'Esquema vacinação tétano: SR',
        'Visita domiciliar pré-natal? (Sim)', 'Visita domiciliar pré-natal? (Não)',
        'Visita domiciliar pré-natal? (SR)',
        'Motivo da visita domiciliar', 'Observações do pré-natal',
        'O que aconteceu (investigador) - PN',
        'Responsável investigação - nome', 'Responsável investigação - profissão',
        'Criança em acompanhamento serviço saúde? (Sim)',
        'Criança em acompanhamento serviço saúde? (Não)',
        'Criança em acompanhamento serviço saúde? (SR)',
        'Estabelecimento atendimento criança', 'Código CNES (criança)',
        'Tipo serviço criança: CS SUS', 'Tipo serviço criança: Convênio',
        'Tipo serviço criança: Particular',
        'Aleitamento materno? (Sim)', 'Aleitamento materno? (Não)',
        'Aleitamento exclusivo? (Sim)', 'Aleitamento exclusivo? (Não)',
        'Tempo aleitamento exclusivo - dias', 'Tempo aleitamento exclusivo - meses',
        'NSA aleitamento exclusivo',
        'Duração aleitamento misto - dias', 'Duração aleitamento misto - meses',
        'NSA aleitamento misto', 'Observações alimentação',
        'Encaminhamento referência? (Sim)', 'Encaminhamento referência? (Não)',
        'Encaminhamento referência? (SR)', 'Motivo do encaminhamento',
        'Vacinação completa? (Sim)', 'Vacinação completa? (Não)',
        'Vacinação completa? (SR)', 'Vacinas em atraso',
        'Acompanhamento especial? (Sim)', 'Acompanhamento especial? (Não)',
        'Acompanhamento especial? (SR)',
        'Acomp. especial: Desnutrição', 'Acomp. especial: RN alto risco',
        'Acomp. especial: Prematuro', 'Acomp. especial: Asma',
        'Acomp. especial: Baixo peso', 'Acomp. especial: Outro',
        'Visitas domiciliares? (Sim)', 'Visitas domiciliares? (Não)',
        'Visitas domiciliares? (SR)',
        'Motivo da visita domiciliar (criança)',
        'Causa do óbito no prontuário', 'Observações gerais',
        'O que aconteceu (investigador)', 'Data da conclusão',
        'Responsável pela investigação', 'Responsável - carimbo/rubrica',
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