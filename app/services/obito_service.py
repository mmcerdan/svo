from app.extensions import db
from app.models import Obito, Usuario
from app.utils.validators import validar_data_obito, validar_numero_dob, validar_cid10
from app.utils.audit import audit_log, serialize_model
from flask import request
from datetime import date, datetime
from typing import Optional, Tuple, List
from sqlalchemy import or_

class ObitoService:
    @staticmethod
    def criar(usuario: Usuario, dados: dict) -> Tuple[Obito, List[str]]:
        """
        Cria novo óbito com validações.
        Retorna (obito, lista_erros).
        """
        erros = []
        
        # Validações
        ok, msg = validar_numero_dob(dados.get('numero_dob', ''))
        if not ok:
            erros.append(msg)
        
        data_obito = dados.get('data_obito')
        data_nascimento = dados.get('data_nascimento')
        if isinstance(data_obito, str):
            from datetime import datetime
            data_obito = datetime.strptime(data_obito, '%Y-%m-%d').date()
        if isinstance(data_nascimento, str) and data_nascimento:
            from datetime import datetime
            data_nascimento = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
        
        ok, msg = validar_data_obito(data_obito, data_nascimento)
        if not ok:
            erros.append(msg)
        
        cid = dados.get('causa_morte_cid', '').strip().upper()
        if cid and not validar_cid10(cid):
            erros.append('CID-10 inválido. Formato esperado: A00.0 ou A00')
        
        if erros:
            return None, erros
        
        # Cria óbito
        obito = Obito(
            nome=dados['nome'].strip(),
            data_nascimento=data_nascimento,
            data_obito=data_obito,
            sexo=dados.get('sexo'),
            nome_mae=(dados.get('nome_mae') or '').strip() or None,
            nome_pai=(dados.get('nome_pai') or '').strip() or None,
            numero_dob=(dados.get('numero_dob') or '').strip(),
            causa_morte=(dados.get('causa_morte') or '').strip() or None,
            causa_morte_cid=cid or None,
            causas_morte_cids=dados.get('causas_morte_cids', []),
            local_obito=dados.get('local_obito'),
            municipio_ocorrencia=(dados.get('municipio_ocorrencia') or '').strip() or None,
            endereco=(dados.get('endereco') or '').strip() or None,
            observacoes=(dados.get('observacoes') or '').strip() or None,
            estabelecimento_id=dados.get('estabelecimento_id'),
            usuario_id=usuario.id,
        )
        
        db.session.add(obito)
        db.session.flush()
        
        # Auditoria
        audit_log(usuario, 'CREATE', 'Obito', obito.id, 
                  None, serialize_model(obito))
        
        return obito, []

    @staticmethod
    def atualizar(obito: Obito, usuario: Usuario, dados: dict) -> List[str]:
        """Atualiza óbito existente."""
        erros = []
        
        # Validações similares à criação
        numero_dob = dados.get('numero_dob', '').strip()
        if numero_dob and numero_dob != obito.numero_dob:
            ok, msg = validar_numero_dob(numero_dob, obito.id)
            if not ok:
                erros.append(msg)
        
        data_obito = dados.get('data_obito')
        data_nascimento = dados.get('data_nascimento')
        if isinstance(data_obito, str):
            from datetime import datetime
            data_obito = datetime.strptime(data_obito, '%Y-%m-%d').date()
        if isinstance(data_nascimento, str) and data_nascimento:
            from datetime import datetime
            data_nascimento = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
        
        ok, msg = validar_data_obito(data_obito, data_nascimento)
        if not ok:
            erros.append(msg)
        
        cid = dados.get('causa_morte_cid', '').strip().upper()
        if cid and not validar_cid10(cid):
            erros.append('CID-10 inválido.')
        
        if erros:
            return erros
        
        # Captura estado anterior para auditoria
        antes = serialize_model(obito)
        
        # Atualiza campos
        obito.nome = dados['nome'].strip()
        obito.data_nascimento = data_nascimento
        obito.data_obito = data_obito
        obito.sexo = dados.get('sexo')
        obito.nome_mae = (dados.get('nome_mae') or '').strip() or None
        obito.nome_pai = (dados.get('nome_pai') or '').strip() or None
        obito.numero_dob = numero_dob
        obito.causa_morte = (dados.get('causa_morte') or '').strip() or None
        obito.causa_morte_cid = cid or None
        obito.causas_morte_cids = dados.get('causas_morte_cids', [])
        obito.local_obito = dados.get('local_obito')
        obito.municipio_ocorrencia = (dados.get('municipio_ocorrencia') or '').strip() or None
        obito.endereco = (dados.get('endereco') or '').strip() or None
        obito.observacoes = (dados.get('observacoes') or '').strip() or None
        obito.estabelecimento_id = dados.get('estabelecimento_id')
        obito.atualizado_em = datetime.utcnow()
        
        # Auditoria
        depois = serialize_model(obito)
        audit_log(usuario, 'UPDATE', 'Obito', obito.id, antes, depois)
        
        return []

    @staticmethod
    def excluir(obito: Obito, usuario: Usuario) -> bool:
        """Exclui óbito (cascata remove investigações e anexos)."""
        antes = serialize_model(obito)
        db.session.delete(obito)
        audit_log(usuario, 'DELETE', 'Obito', obito.id, antes, None)
        return True

    @staticmethod
    def listar(busca: str = '', page: int = 1, per_page: int = 20):
        """Lista óbitos com paginação e busca."""
        query = Obito.query
        if busca:
            query = query.filter(
                or_(
                    Obito.nome.ilike(f'%{busca}%'),
                    Obito.numero_dob.ilike(f'%{busca}%'),
                    Obito.nome_mae.ilike(f'%{busca}%'),
                )
            )
        query = query.order_by(Obito.data_obito.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def buscar_por_id(obito_id: int) -> Optional[Obito]:
        return db.session.get(Obito, obito_id)