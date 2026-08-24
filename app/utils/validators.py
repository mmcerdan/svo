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
    """Valida unicidade do número da DO."""
    from app.models import Obito
    if not numero_dob:
        return True, ''
    query = Obito.query.filter_by(numero_dob=numero_dob)
    if obito_id:
        query = query.filter(Obito.id != obito_id)
    if query.first():
        return False, 'Número de DO já cadastrado.'
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
    }
    
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
            gravida = [k for k in campos if k.startswith('Grávida no momento') and campos[k] == 'X']
            if len(gravida) != 1:
                erros.append('Grávida no momento do óbito: selecione Sim, Não ou Não sabe.')
        
        return erros