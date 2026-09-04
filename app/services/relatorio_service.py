from app.extensions import db
from app.models import Obito, Investigacao, CID
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy import func

class RelatorioService:
    @staticmethod
    def dados_geral(data_inicio: Optional[date] = None, data_fim: Optional[date] = None) -> Dict[str, Any]:
        query = Obito.query
        if data_inicio:
            query = query.filter(Obito.data_obito >= data_inicio)
        if data_fim:
            query = query.filter(Obito.data_obito <= data_fim)
        
        total = query.count()
        por_sexo = db.session.query(Obito.sexo, func.count(Obito.id)).filter(
            Obito.sexo.isnot(None)
        ).group_by(Obito.sexo).all()
        por_local = db.session.query(Obito.local_obito, func.count(Obito.id)).filter(
            Obito.local_obito.isnot(None)
        ).group_by(Obito.local_obito).all()
        
        return {
            'total': total,
            'por_sexo': [{'label': s or 'Não informado', 'value': c} for s, c in por_sexo],
            'por_local': [{'label': l or 'Não informado', 'value': c} for l, c in por_local],
        }

    @staticmethod
    def dados_investigacoes(data_inicio: Optional[date] = None, data_fim: Optional[date] = None) -> Dict[str, Any]:
        from app.models import Investigacao, TIPOS_INVESTIGACAO, STATUS_INVESTIGACAO
        
        query = Investigacao.query
        if data_inicio or data_fim:
            query = query.join(Obito)
            if data_inicio:
                query = query.filter(Obito.data_obito >= data_inicio)
            if data_fim:
                query = query.filter(Obito.data_obito <= data_fim)
        
        total = query.count()
        
        por_tipo = db.session.query(Investigacao.tipo, func.count(Investigacao.id))
        if data_inicio or data_fim:
            por_tipo = por_tipo.join(Obito)
            if data_inicio:
                por_tipo = por_tipo.filter(Obito.data_obito >= data_inicio)
            if data_fim:
                por_tipo = por_tipo.filter(Obito.data_obito <= data_fim)
        por_tipo = por_tipo.group_by(Investigacao.tipo).all()
        
        por_status = db.session.query(Investigacao.status, func.count(Investigacao.id))
        if data_inicio or data_fim:
            por_status = por_status.join(Obito)
            if data_inicio:
                por_status = por_status.filter(Obito.data_obito >= data_inicio)
            if data_fim:
                por_status = por_status.filter(Obito.data_obito <= data_fim)
        por_status = por_status.group_by(Investigacao.status).all()
        
        tipo_map = dict(TIPOS_INVESTIGACAO)
        status_map = dict(STATUS_INVESTIGACAO)
        
        return {
            'total': total,
            'por_tipo': [{'label': tipo_map.get(t, t), 'value': c} for t, c in por_tipo],
            'por_status': [{'label': status_map.get(s, s), 'value': c} for s, c in por_status],
        }

    @staticmethod
    def dados_causas(data_inicio=None, data_fim=None, limite=15):
        query = db.session.query(
            Obito.causa_morte_cid,
            CID.descricao,
            func.count(Obito.id).label('qtd')
        ).outerjoin(CID, Obito.causa_morte_cid == CID.codigo).filter(
            Obito.causa_morte_cid.isnot(None)
        )
        if data_inicio:
            query = query.filter(Obito.data_obito >= data_inicio)
        if data_fim:
            query = query.filter(Obito.data_obito <= data_fim)
        
        causas = query.group_by(Obito.causa_morte_cid, CID.descricao).order_by(
            func.count(Obito.id).desc()
        ).limit(limite).all()
        
        return {
            'causas': [{'label': c or 'Sem CID', 'descricao': d or '', 'value': v} for c, d, v in causas],
        }