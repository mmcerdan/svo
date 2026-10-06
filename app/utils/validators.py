import re
from datetime import date
from typing import Optional, Tuple
from wtforms.validators import ValidationError

# CID-10 regex (simplificado - para produção use biblioteca dedicada como pyicd)
CID10_REGEX = re.compile(r'^[A-TV-Z][0-9]{2}(\.[0-9A-TV-Z]{1,4})?$')

def validar_cid10(cid: str) -> bool:
    """Valida formato básico de CID-10."""
    if not cid:
        return True  # Opcional
    return bool(CID10_REGEX.match(cid.upper()))

def validar_data_obito(data_obito: date, data_nascimento: Optional[date] = None) -> Tuple[bool, str]:
    """Valida se a data do óbito é coerente."""
    hoje = date.today()
    if data_obito > hoje:
        return False, 'Data do óbito não pode ser futura.'
    if data_nascimento and data_obito < data_nascimento:
        return False, 'Data do óbito não pode ser anterior à data de nascimento.'
    # Idade máxima razoável
    if data_nascimento and (data_obito - data_nascimento).days > 365 * 130:
        return False, 'Idade calculada excede 130 anos. Verifique as datas.'
    return True, ''

def validar_numero_dob(numero_dob: str, obito_id: Optional[int] = None) -> Tuple[bool, str]:
    """Valida o número da DO.

    Óbitos de gemelares podem compartilhar a mesma DO — por isso a
    unicidade NÃO é bloqueante. Apenas retorna aviso informativo.
    """
    if not numero_dob:
        return True, ''
    # Não bloqueia: gêmeos usam a mesma DO. Mantido por compatibilidade.
    return True, ''

class ValidadorInvestigacao:
    """Validadores específicos por tipo de investigação."""
    
    CAMPOS_OBRIGATORIOS = {
        'MIF': ['Nome da falecida', 'Nº da DO', 'Data do óbito',
                'Grávida no momento do óbito? (Sim)', 'Grávida no momento do óbito? (Não)',
                'Grávida no momento do óbito? (Não sabe)'],
        'MATERNO': ['Nome da falecida', 'Nº da DO', 'Data do óbito',
                    'IG 1ª consulta (semanas)', 'Nº consultas pré-natal'],
        'INFANTIL_FETAL': ['Nome da criança', 'Nome da mãe', 'Nº do caso',
                           'Data de nascimento', 'Nº da DN', 'Nº da DO',
                           'Data do óbito', 'Peso ao nascer (gramas)',
                           'Sexo: Masculino', 'Sexo: Feminino', 'Sexo: Ignorado',
                           'Wigglesworth: W1'],  # Pelo menos um Wigglesworth
        'MAL_DEFINIDA': ['Nº da DO', 'Nome do falecido', 'Nome da mãe',
                         'Data de nascimento', 'Data do óbito',
                         'Causa básica original'],
        'INFANTIL': ['Nome da criança', 'Nome da mãe', 'Nº da DO',
                     'Data do óbito', 'Nº da DN', 'Data de nascimento',
                     'Peso ao nascer (gramas)', 'Idade ao óbito'],
        'DENGUE': ['DI03. Nome do paciente', 'DI04. Data de nascimento',
                   'DI06. Sexo: Masculino', 'DI06. Sexo: Feminino'],
    }

    # Grupos mutuamente exclusivos (máx. 1 marcado) — DENGUE
    GRUPOS_EXCLUSIVOS_DENGUE = {
        'DI05. Unidade idade': [
            'DI05. Unidade idade: Dias', 'DI05. Unidade idade: Meses', 'DI05. Unidade idade: Anos',
        ],
        'DI06. Sexo': [
            'DI06. Sexo: Masculino', 'DI06. Sexo: Feminino',
        ],
        'IT04. Unidade': [
            'IT04. Unidade: PS', 'IT04. Unidade: Clínica',
            'IT04. Unidade: UTI', 'IT04. Unidade: Outro',
        ],
        'IT05. Estadiamento': [
            'IT05. Estadiamento: A', 'IT05. Estadiamento: B',
            'IT05. Estadiamento: C', 'IT05. Estadiamento: D',
            'IT05. Estadiamento: Não realizado',
        ],
        'DC01. Sinais/sintomas antes da internação': [
            'DC01. Sinais/sintomas antes da internação: Sim',
            'DC01. Sinais/sintomas antes da internação: Não',
        ],
        'DC04. Comorbidades': [
            'DC04. Comorbidades: Sim', 'DC04. Comorbidades: Não',
        ],
        'DC05. Doença que afete resposta imunológica': [
            'DC05. Doença que afete resposta imunológica: Sim',
            'DC05. Doença que afete resposta imunológica: Não',
            'DC05. Doença que afete resposta imunológica: Não informado',
        ],
        'DC06. Descompensação de enfermidade crônica': [
            'DC06. Descompensação de enfermidade crônica: Sim',
            'DC06. Descompensação de enfermidade crônica: Não',
            'DC06. Descompensação de enfermidade crônica: Não informado',
        ],
        'DC07. Outras manifestações após quadro agudo': [
            'DC07. Outras manifestações após quadro agudo: Sim',
            'DC07. Outras manifestações após quadro agudo: Não',
            'DC07. Outras manifestações após quadro agudo: Não informado',
        ],
        'DC08. Manifestações neurológicas': [
            'DC08. Manifestações neurológicas: Sim',
            'DC08. Manifestações neurológicas: Não',
        ],
        'DC09. Manifestações oculares': [
            'DC09. Manifestações oculares: Sim',
            'DC09. Manifestações oculares: Não',
        ],
        'DC10. Manifestações dermatológicas': [
            'DC10. Manifestações dermatológicas: Sim',
            'DC10. Manifestações dermatológicas: Não',
        ],
        'DC11. Quadro renal': [
            'DC11. Quadro renal: Sim', 'DC11. Quadro renal: Não',
        ],
        'DC12. Quadro hemorrágico': [
            'DC12. Quadro hemorrágico: Sim', 'DC12. Quadro hemorrágico: Não',
        ],
        'DC13. Evoluiu para choque': [
            'DC13. Evoluiu para choque: Sim', 'DC13. Evoluiu para choque: Não',
        ],
        'DC14. Outras complicações': [
            'DC14. Outras complicações: Sim', 'DC14. Outras complicações: Não',
        ],
        'EC1. Remoção para UTI': [
            'EC1. Remoção para UTI: Sim', 'EC1. Remoção para UTI: Não',
        ],
        'EC2. Evolução': [
            'EC2. Evolução: Transferência', 'EC2. Evolução: Alta', 'EC2. Evolução: Óbito',
        ],
        'EC4. Corpo encaminhado para necropsia': [
            'EC4. Corpo encaminhado para necropsia: Sim',
            'EC4. Corpo encaminhado para necropsia: Não',
        ],
        'EC5. Óbito fetal/<1 ano em relação ao parto': [
            'EC5. Óbito fetal/<1 ano em relação ao parto: Antes',
            'EC5. Óbito fetal/<1 ano em relação ao parto: Durante',
            'EC5. Óbito fetal/<1 ano em relação ao parto: Após',
            'EC5. Óbito fetal/<1 ano em relação ao parto: Ignorado',
        ],
        'MC01. Soroterapia intravenosa': [
            'MC01. Soroterapia intravenosa: Sim',
            'MC01. Soroterapia intravenosa: Não',
        ],
        'LI01. Exame de sangue': [
            'LI01. Exame de sangue: Sim', 'LI01. Exame de sangue: Não',
        ],
        'LI02. Punção liquórica': [
            'LI02. Punção liquórica: Sim', 'LI02. Punção liquórica: Não',
        ],
        'LI02.2. Aspecto': [
            'LI02.2. Aspecto: Límpido', 'LI02.2. Aspecto: Turvo',
            'LI02.2. Aspecto: Hemorrágico', 'LI02.2. Aspecto: Outro',
        ],
        'LI03. Exame de imagem': [
            'LI03. Exame de imagem: Sim', 'LI03. Exame de imagem: Não',
        ],
        'LE01. Exame etiológico': [
            'LE01. Exame etiológico: Sim', 'LE01. Exame etiológico: Não',
        ],
        'LE02. Isolamento por cultura': [
            'LE02. Isolamento por cultura: Sim', 'LE02. Isolamento por cultura: Não',
        ],
        'LE03. Alíquota guardada em laboratório': [
            'LE03. Alíquota guardada em laboratório: Sim',
            'LE03. Alíquota guardada em laboratório: Não',
        ],
        'EN01. Caso encerrado': [
            'EN01. Caso encerrado: Sim', 'EN01. Caso encerrado: Não',
        ],
        'EN02. Critério': [
            'EN02. Critério: Laboratorial', 'EN02. Critério: Clínico-epidemiológico',
        ],
        'EN03. Classificação': [
            'EN03. Classificação: 10 — Dengue',
            'EN03. Classificação: 11 — Dengue com sinais de alarme',
            'EN03. Classificação: 12 — Dengue grave',
            'EN03. Classificação: Descartado',
            'EN03. Classificação: Óbito por outras causas',
            'EN03. Classificação: Em investigação',
        ],
        'EDI04. Unidade idade': [
            'EDI04. Unidade idade: Dias', 'EDI04. Unidade idade: Meses', 'EDI04. Unidade idade: Anos',
        ],
        'EDI05. Sexo': [
            'EDI05. Sexo: Masculino', 'EDI05. Sexo: Feminino',
        ],
        'AS01. Ficou doente antes do óbito': [
            'AS01. Ficou doente antes do óbito: Sim',
            'AS01. Ficou doente antes do óbito: Não',
            'AS01. Ficou doente antes do óbito: Não sei',
        ],
        'AS03. Medicação sem prescrição': [
            'AS03. Medicação sem prescrição: Sim',
            'AS03. Medicação sem prescrição: Não',
        ],
        'AS04. Procurou atendimento médico': [
            'AS04. Procurou atendimento médico: Sim',
            'AS04. Procurou atendimento médico: Não',
        ],
        'C01. Alguém que morava com o caso adoeceu': [
            'C01. Alguém que morava com o caso adoeceu: Sim',
            'C01. Alguém que morava com o caso adoeceu: Não',
        ],
    }

    # Grupos Sim/Não (máx. 1) — se algum item do grupo estiver marcado, ok;
    # se nenhum estiver marcado, também ok (campo opcional).
    GRUPOS_SIM_NAO_DENGUE = [
        'DC01. Sinais/sintomas antes da internação',
        'DC04. Comorbidades',
        'DC05. Doença que afete resposta imunológica',
        'DC06. Descompensação de enfermidade crônica',
        'DC07. Outras manifestações após quadro agudo',
        'DC08. Manifestações neurológicas',
        'DC09. Manifestações oculares',
        'DC10. Manifestações dermatológicas',
        'DC11. Quadro renal',
        'DC12. Quadro hemorrágico',
        'DC13. Evoluiu para choque',
        'DC14. Outras complicações',
        'EC1. Remoção para UTI',
        'EC4. Corpo encaminhado para necropsia',
        'MC01. Soroterapia intravenosa',
        'LI01. Exame de sangue',
        'LI02. Punção liquórica',
        'LI03. Exame de imagem',
        'LE01. Exame etiológico',
        'LE02. Isolamento por cultura',
        'LE03. Alíquota guardada em laboratório',
        'EN01. Caso encerrado',
        'AS01. Ficou doente antes do óbito',
        'AS03. Medicação sem prescrição',
        'AS04. Procurou atendimento médico',
        'C01. Alguém que morava com o caso adoeceu',
    ]
    
    @classmethod
    def validar(cls, tipo: str, campos: dict) -> list[str]:
        """Retorna lista de erros de validação."""
        erros = []
        obrigatorios = cls.CAMPOS_OBRIGATORIOS.get(tipo, [])
        
        for campo in obrigatorios:
            valor = campos.get(campo)
            if not valor or (isinstance(valor, str) and not valor.strip()):
                # Para checkboxes obrigatórios (ex: Wigglesworth), verifica se algum foi marcado
                if '?' in campo or ':' in campo:
                    # É um grupo de checkboxes - verifica se algum do grupo foi marcado
                    prefixo = campo.split(':')[0] if ':' in campo else campo.split('?')[0]
                    algum_marcado = any(
                        k.startswith(prefixo) and v == 'X' 
                        for k, v in campos.items()
                    )
                    if algum_marcado:
                        continue
                erros.append(f'Campo obrigatório não preenchido: {campo}')
        
        # Validações específicas por tipo
        if tipo == 'INFANTIL_FETAL':
            # Wigglesworth: exatamente um deve ser marcado
            wigglesworth = [k for k in campos if k.startswith('Wigglesworth:') and campos[k] == 'X']
            if len(wigglesworth) != 1:
                erros.append('Classificação de Wigglesworth: selecione exatamente uma categoria (W1-W9).')
            
            # SEADE: pelo menos um
            seade = [k for k in campos if k.startswith('SEADE:') and campos[k] == 'X']
            if not seade:
                erros.append('Classificação SEADE: selecione pelo menos uma categoria (S1-S7).')
        
        if tipo == 'MIF':
            # Zona: exatamente um
            zona = [k for k in ['Zona: Urbana', 'Zona: Rural'] if campos.get(k) == 'X']
            if len(zona) != 1:
                erros.append('Zona: selecione Urbana ou Rural.')

            # Grávida: exatamente um
            gravida = [k for k in campos if k.startswith('Grávida no momento') and campos.get(k) == 'X']
            if len(gravida) != 1:
                erros.append('Grávida no momento do óbito: selecione Sim, Não ou Não sabe.')

        if tipo == 'DENGUE':
            # Sexo: obrigatório e exatamente 1
            sexo = [k for k in cls.GRUPOS_EXCLUSIVOS_DENGUE['DI06. Sexo'] if campos.get(k) == 'X']
            if len(sexo) != 1:
                erros.append('DI06. Sexo: marque exatamente uma opção (Masculino ou Feminino).')

            # Demais grupos exclusivos: no máximo 1
            for grupo_nome, chaves in cls.GRUPOS_EXCLUSIVOS_DENGUE.items():
                if grupo_nome == 'DI06. Sexo':
                    continue  # já validado acima (obrigatório)
                marcados = [k for k in chaves if campos.get(k) == 'X']
                if len(marcados) > 1:
                    erros.append(f'{grupo_nome}: selecione no máximo uma opção.')

            # Grupos Sim/Não: se algum marcado, no máximo 1 (já coberto acima);
            # validação adicional: EN02/EN03 obrigatórios se EN01 = Sim
            if campos.get('EN01. Caso encerrado: Sim') == 'X':
                en02 = [k for k in cls.GRUPOS_EXCLUSIVOS_DENGUE['EN02. Critério'] if campos.get(k) == 'X']
                if len(en02) != 1:
                    erros.append('EN02. Critério: selecione Laboratorial ou Clínico-epidemiológico.')
                en03 = [k for k in cls.GRUPOS_EXCLUSIVOS_DENGUE['EN03. Classificação'] if campos.get(k) == 'X']
                if len(en03) != 1:
                    erros.append('EN03. Classificação: selecione uma opção.')

        return erros