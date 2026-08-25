from app.extensions import db
from app.models import Obito, Investigacao, InvestigacaoCampo, Anexo
from app.utils.campos import get_campos_padrao_investigacao
from app.utils.validators import ValidadorInvestigacao
from app.utils.audit import audit_log, serialize_model
from flask import request, current_app
from datetime import date, datetime
from typing import Optional, List, Tuple, Dict, Any

class InvestigacaoService:
    @staticmethod
    def criar(usuario, obito: Obito, tipo: str, dados_campos: dict = None) -> Tuple[Investigacao, List[str]]:
        """Cria nova investigação com campos padrão."""
        erros = []
        
        if tipo not in dict(Investigacao.__dict__.get('TIPOS_INVESTIGACAO', [])):
            return None, ['Tipo de investigação inválido.']
        
        inv = Investigacao(
            obito_id=obito.id,
            tipo=tipo,
            status='AGUARDANDO',
            data_abertura=date.today(),
            usuario_id=usuario.id,
        )
        db.session.add(inv)
        db.session.flush()
        
        # Cria campos padrão
        campos_padrao = get_campos_padrao_investigacao(tipo)
        for nome_campo in campos_padrao:
            valor = ''
            if dados_campos:
                valor = dados_campos.get(f'inv_{nome_campo}', '')
                # Checkbox: se presente no form = 'X'
                if valor and valor != 'X':
                    valor = 'X'
            campo = InvestigacaoCampo(
                investigacao_id=inv.id,
                nome_campo=nome_campo,
                valor=valor
            )
            db.session.add(campo)
        
        # Preenche campos do form se fornecidos
        if dados_campos:
            for key, value in dados_campos.items():
                if key.startswith('inv_'):
                    nome_campo = key[4:]
                    campo = next((c for c in inv.campos if c.nome_campo == nome_campo), None)
                    if campo:
                        campo.valor = value if value == 'X' else (value or '')
        
        db.session.commit()
        
        audit_log(usuario, 'CREATE', 'Investigacao', inv.id,
                  None, {'tipo': tipo, 'obito_id': obito.id})
        
        return inv, []

    @staticmethod
    def criar_com_obito(usuario, dados_obito: dict, tipo_investigacao: str, dados_campos: dict = None) -> Tuple[Obito, Optional[Investigacao], List[str]]:
        """
        Cria óbito e investigação em uma única transação (corrige race condition).
        """
        from app.services.obito_service import ObitoService
        
        erros = []
        
        # Valida dados do óbito
        obito, erros_obito = ObitoService.criar(usuario, dados_obito)
        erros.extend(erros_obito)
        
        inv = None
        if tipo_investigacao and not erros:
            inv, erros_inv = InvestigacaoService.criar(usuario, obito, tipo_investigacao, dados_campos)
            erros.extend(erros_inv)
        
        if erros:
            db.session.rollback()
            return None, None, erros
        
        db.session.commit()
        return obito, inv, []

    @staticmethod
    def atualizar_campos(investigacao: Investigacao, usuario, dados_form: dict) -> List[str]:
        """Atualiza valores dos campos da investigação."""
        from app.utils.campos import get_tipo_campo
        
        erros = ValidadorInvestigacao.validar(investigacao.tipo, {
            c.nome_campo: (dados_form.get(f'campo_{c.id}', '') if get_tipo_campo(c.nome_campo) == 'checkbox' 
                          else dados_form.get(f'campo_{c.id}', ''))
            for c in investigacao.campos
        })
        
        if erros:
            return erros
        
        antes = {c.nome_campo: c.valor for c in investigacao.campos}
        
        for campo in investigacao.campos:
            if get_tipo_campo(campo.nome_campo) == 'checkbox':
                campo.valor = 'X' if dados_form.get(f'campo_{campo.id}') else ''
            else:
                campo.valor = dados_form.get(f'campo_{campo.id}', '')
        
        investigacao.atualizado_em = datetime.utcnow()
        db.session.commit()
        
        depois = {c.nome_campo: c.valor for c in investigacao.campos}
        audit_log(usuario, 'UPDATE', 'InvestigacaoCampo', investigacao.id, antes, depois)
        
        return []

    @staticmethod
    def finalizar(investigacao: Investigacao, usuario, conclusao: str) -> List[str]:
        """Finaliza investigação (status = CONCLUIDA)."""
        if investigacao.status == 'CONCLUIDA':
            return ['Investigação já está concluída.']
        
        if not conclusao or not conclusao.strip():
            return ['Conclusão é obrigatória para finalizar.']
        
        antes = serialize_model(investigacao)
        
        investigacao.status = 'CONCLUIDA'
        investigacao.data_conclusao = date.today()
        investigacao.conclusao = conclusao.strip()
        investigacao.atualizado_em = datetime.utcnow()
        
        db.session.commit()
        
        depois = serialize_model(investigacao)
        audit_log(usuario, 'FINALIZAR', 'Investigacao', investigacao.id, antes, depois)
        
        return []

    @staticmethod
    def atualizar_status(investigacao: Investigacao, usuario, dados: dict) -> List[str]:
        """Atualiza status e outros metadados da investigação."""
        antes = serialize_model(investigacao)
        
        if 'status' in dados:
            investigacao.status = dados['status']
        if 'responsavel' in dados:
            investigacao.responsavel = dados['responsavel'] or None
        if 'data_abertura' in dados and dados['data_abertura']:
            from datetime import datetime
            investigacao.data_abertura = datetime.strptime(dados['data_abertura'], '%Y-%m-%d').date()
        if 'data_conclusao' in dados and dados['data_conclusao']:
            from datetime import datetime
            investigacao.data_conclusao = datetime.strptime(dados['data_conclusao'], '%Y-%m-%d').date()
        if 'conclusao' in dados:
            investigacao.conclusao = dados['conclusao'].strip() or None
        if 'observacoes' in dados:
            investigacao.observacoes = dados['observacoes'].strip() or None
        
        investigacao.atualizado_em = datetime.utcnow()
        db.session.commit()
        
        depois = serialize_model(investigacao)
        audit_log(usuario, 'UPDATE', 'Investigacao', investigacao.id, antes, depois)
        
        return []

    @staticmethod
    def excluir(investigacao: Investigacao, usuario) -> bool:
        antes = serialize_model(investigacao)
        db.session.delete(investigacao)
        audit_log(usuario, 'DELETE', 'Investigacao', investigacao.id, antes, None)
        return True

    @staticmethod
    def anexar_arquivo(investigacao: Investigacao, usuario, arquivo) -> Tuple[Optional[Anexo], str]:
        import uuid
        import os
        from werkzeug.utils import secure_filename
        from app.utils.security import validate_file_upload
        
        ok, msg = validate_file_upload(arquivo, allowed_extensions={'pdf', 'jpg', 'jpeg', 'png'})
        if not ok:
            return None, msg
        
        ext = arquivo.filename.rsplit('.', 1)[-1].lower() if '.' in arquivo.filename else ''
        nome_arquivo = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
        arquivo.save(os.path.join(current_app.config['UPLOAD_FOLDER'], nome_arquivo))
        
        anexo = Anexo(
            investigacao_id=investigacao.id,
            nome_original=secure_filename(arquivo.filename) or arquivo.filename,
            nome_arquivo=nome_arquivo,
            tipo=ext,
            tamanho=os.path.getsize(os.path.join(current_app.config['UPLOAD_FOLDER'], nome_arquivo)),
        )
        db.session.add(anexo)
        db.session.commit()
        
        audit_log(usuario, 'UPLOAD', 'Anexo', anexo.id, 
                  None, {'nome': anexo.nome_original, 'tipo': ext})
        
        return anexo, 'Arquivo anexado com sucesso!'

    @staticmethod
    def excluir_anexo(anexo: Anexo, usuario) -> bool:
        import os
        from flask import current_app
        
        caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], anexo.nome_arquivo)
        if os.path.exists(caminho):
            os.remove(caminho)
        
        audit_log(usuario, 'DELETE', 'Anexo', anexo.id, 
                  {'nome': anexo.nome_original}, None)
        
        db.session.delete(anexo)
        db.session.commit()
        return True

    @staticmethod
    def listar(tipo: str = '', status: str = '', busca: str = '', page: int = 1, per_page: int = 20):
        query = Investigacao.query
        if tipo:
            query = query.filter_by(tipo=tipo)
        if status:
            query = query.filter_by(status=status)
        if busca:
            query = query.join(Obito).filter(Obito.nome.ilike(f'%{busca}%'))
        query = query.order_by(Investigacao.criado_em.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def obter_para_impressao(investigacao: Investigacao) -> dict:
        """Prepara dados para template de impressão com mapeamento de campos legados."""
        from app.utils.campos import get_campos_padrao_investigacao
        campos_dict = {c.nome_campo: c.valor for c in investigacao.campos}
        
        # Mapeamento de campos legados (compatibilidade com dados antigos)
        mapeamentos = {
            'INFANTIL': {
                'Nome da criança / Nome da mãe': ('Nome da criança', 'Nome da mãe'),
                'Nº da DO / Nº da DN': ('Nº da DO', 'Nº da DN'),
                'Peso ao nascer (gramas)': ('Peso ao nascer (gramas)', None),
                'Idade ao óbito (meses/dias/horas)': ('Idade ao óbito', None),
                'Nº do Cartão SUS / Equipe PSF': ('Nº do Cartão SUS', 'Equipe/PACS/PSF'),
                'Pré-natal: número de consultas': ('Nº de consultas pré-natal', None),
                'Patologias na gestação': ('Patologias/fatores de risco', None),
                'Aleitamento materno exclusivo?': ('Aleitamento materno exclusivo?', None),
                'Vacinação completa para idade?': ('Vacinação completa?', None),
                'Causa do óbito registrada no prontuário': ('Causa do óbito no prontuário', None),
                'Resumo do caso / conclusão': ('O que aconteceu (investigador)', None),
            },
            'MAL_DEFINIDA': {
                'Nº da DO / Causa básica original': ('Nº da DO', 'Causa básica original'),
                'Nome da Unidade Básica de Saúde': ('Nome da Unidade Básica/USF', None),
                'Patologias que motivavam atendimentos': ('Patologias/motivos de atendimento', None),
                'Data e motivo da última consulta': ('Data da última consulta', 'Motivo da última consulta'),
                'Estabelecimento de saúde da internação': ('Nome do estabelecimento de saúde', None),
                'Data da internação / alta': ('Data da internação', 'Data da alta'),
                'Hipótese diagnóstica da alta': ('Hipótese diagnóstica da alta', None),
                'Resultados de exames relevantes': ('Resultados de exames relevantes', None),
                'Causa do óbito no prontuário': ('Causa do óbito no prontuário', None),
                'Investigação em outros locais (SINAN/IML/SVO)': ('Investigação SINAN', None),
                'Causas da morte após investigação / CID': ('Causa básica - diagnóstico', None),
            },
            'MIF': {
                'Estava grávida no momento do óbito?': ('Grávida no momento do óbito? (Sim)', None),
                'Esteve grávida nos 12 meses anteriores?': ('Esteve grávida nos 12 meses? (Sim)', None),
                'Urbano/Rural': ('Zona: Urbana', 'Zona: Rural'),
                'Resumo do caso / justificativa': ('Resumo do caso / justificativa', None),
            },
            'MATERNO': {
                'Nº da DO / Data do óbito': ('Nº da DO', 'Data do óbito'),
                'Idade gestacional na 1ª consulta': ('IG 1ª consulta (semanas)', None),
                'Número de consultas pré-natal': ('Nº consultas pré-natal', None),
                'Foi considerada gestante de alto risco?': ('Gestante alto risco? (Sim)', None),
                'Patologias/fatores de risco na gestação': ('Patologias/fatores de risco', None),
                'Foi internada durante a gestação? Motivo?': ('Internada na gestação? (Sim)', 'Motivos da internação'),
                'Causas do óbito registradas no prontuário': ('Causa do óbito no prontuário', None),
                'Resumo do caso / conclusão': ('O que aconteceu (investigador)', None),
            },
            'INFANTIL_FETAL': {
                'Nº da DO / Nº da DN': ('Nº da DO', 'Nº da DN'),
                'Idade gestacional (semanas)': ('Idade gestacional (semanas)', None),
                'Faixa etária (fetal/neonatal/pós-neonatal)': ('Faixa etária: Fetal', None),
                'Idade da mãe / Escolaridade materna': ('Idade da mãe (anos)', 'Escolaridade mãe - anos'),
                'Classificação de evitabilidade': ('Wigglesworth: W1', None),
                'Recomendações e medidas de prevenção': ('Recomendações / propostas de intervenção', None),
            },
        }
        
        tipo_map = mapeamentos.get(investigacao.tipo, {})
        for campo_antigo, (campo_novo1, campo_novo2) in tipo_map.items():
            if campo_antigo in campos_dict and campo_novo1 and campo_novo1 not in campos_dict:
                valor = campos_dict[campo_antigo]
                if campo_novo2 and ' / ' in valor:
                    partes = valor.split(' / ', 1)
                    campos_dict[campo_novo1] = partes[0].strip()
                    campos_dict[campo_novo2] = partes[1].strip() if len(partes) > 1 else ''
                elif 'Urbano/Rural' == campo_antigo:
                    v = valor.lower()
                    campos_dict['Zona: Urbana'] = 'X' if 'urbano' in v else ''
                    campos_dict['Zona: Rural'] = 'X' if 'rural' in v else ''
                elif 'Faixa et' in campo_antigo:
                    v = valor.lower()
                    for f in ['Fetal', 'Neonatal precoce', 'Neonatal tardio', 'Pós-neonatal', 'Ignorado']:
                        key = f'Faixa etária: {f}'
                        if f.lower() in v:
                            campos_dict[key] = 'X'
                elif campo_novo1:
                    campos_dict[campo_novo1] = valor
                if campo_novo2 and campo_novo2 not in campos_dict:
                    campos_dict[campo_novo2] = ''
        
        return campos_dict