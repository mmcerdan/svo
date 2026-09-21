from app.extensions import db
from app.models import Obito, Investigacao, CID
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy import func, extract, case

class RelatorioService:

    @staticmethod
    def _aplicar_filtros_base(query, nome=None, data_inicio=None, data_fim=None,
                              idade_min=None,idade_max=None, model=None):
        if model is None:
            model = Obito

        if nome:
            query = query.filter(Obito.nome.ilike(f'%{nome}%'))

        if data_inicio:
            query = query.filter(Obito.data_obito >= data_inicio)
        if data_fim:
            query = query.filter(Obito.data_obito <= data_fim)

        if idade_min is not None or idade_max is not None:
            hoje = date.today()
            if idade_min is not None:
                data_max_nasc = date(hoje.year - int(idade_min), hoje.month, hoje.day)
                query = query.filter(Obito.data_nascimento <= data_max_nasc)
            if idade_max is not None:
                data_min_nasc = date(hoje.year - int(idade_max) - 1, hoje.month, hoje.day)
                query = query.filter(Obito.data_nascimento > data_min_nasc)

        return query

    @staticmethod
    def dados_geral(data_inicio=None, data_fim=None, nome=None,
                    idade_min=None, idade_max=None) -> Dict[str, Any]:
        query = RelatorioService._aplicar_filtros_base(
            Obito.query, nome=nome, data_inicio=data_inicio, data_fim=data_fim,
            idade_min=idade_min, idade_max=idade_max
        )

        total = query.count()

        query_sexo = RelatorioService._aplicar_filtros_base(
            Obito.query, nome=nome, data_inicio=data_inicio, data_fim=data_fim,
            idade_min=idade_min, idade_max=idade_max
        )
        por_sexo = query_sexo.with_entities(
            Obito.sexo, func.count(Obito.id)
        ).filter(Obito.sexo.isnot(None)).group_by(Obito.sexo).all()

        query_local = RelatorioService._aplicar_filtros_base(
            Obito.query, nome=nome, data_inicio=data_inicio, data_fim=data_fim,
            idade_min=idade_min, idade_max=idade_max
        )
        por_local = query_local.with_entities(
            Obito.local_obito, func.count(Obito.id)
        ).filter(Obito.local_obito.isnot(None)).group_by(Obito.local_obito).all()

        query_cid = RelatorioService._aplicar_filtros_base(
            Obito.query, nome=nome, data_inicio=data_inicio, data_fim=data_fim,
            idade_min=idade_min, idade_max=idade_max
        )
        por_cid = query_cid.with_entities(
            Obito.causa_morte_cid, func.count(Obito.id)
        ).filter(Obito.causa_morte_cid.isnot(None)).group_by(Obito.causa_morte_cid).order_by(
            func.count(Obito.id).desc()
        ).all()

        base = RelatorioService._aplicar_filtros_base(
            Obito.query, nome=nome, data_inicio=data_inicio, data_fim=data_fim,
            idade_min=idade_min, idade_max=idade_max
        ).subquery()
        por_tipo_ficha = db.session.query(
            Investigacao.tipo, func.count(Investigacao.id)
        ).join(base, Investigacao.obito_id == base.c.id).group_by(Investigacao.tipo).all()

        return {
            'total': total,
            'por_sexo': [{'label': s or 'Não informado', 'value': c} for s, c in por_sexo],
            'por_local': [{'label': l or 'Não informado', 'value': c} for l, c in por_local],
            'por_cid': [{'label': c or 'Sem CID', 'value': v} for c, v in por_cid],
            'por_tipo_ficha': [{'label': t or 'Sem investigação', 'value': v} for t, v in por_tipo_ficha],
        }

    @staticmethod
    def dados_investigacoes(data_inicio=None, data_fim=None, nome=None,
                            idade_min=None, idade_max=None) -> Dict[str, Any]:
        from app.models import TIPOS_INVESTIGACAO, STATUS_INVESTIGACAO

        base = RelatorioService._aplicar_filtros_base(
            Obito.query, nome=nome, data_inicio=data_inicio, data_fim=data_fim,
            idade_min=idade_min, idade_max=idade_max
        ).subquery()

        query = Investigacao.query.join(base, Investigacao.obito_id == base.c.id)

        total = query.count()

        por_tipo = query.with_entities(
            Investigacao.tipo, func.count(Investigacao.id)
        ).group_by(Investigacao.tipo).all()

        por_status = query.with_entities(
            Investigacao.status, func.count(Investigacao.id)
        ).group_by(Investigacao.status).all()

        tipo_map = dict(TIPOS_INVESTIGACAO)
        status_map = dict(STATUS_INVESTIGACAO)

        return {
            'total': total,
            'por_tipo': [{'label': tipo_map.get(t, t), 'value': c} for t, c in por_tipo],
            'por_status': [{'label': status_map.get(s, s), 'value': c} for s, c in por_status],
        }

    @staticmethod
    def dados_causas(data_inicio=None, data_fim=None, nome=None,
                     idade_min=None, idade_max=None, limite=15):
        query = RelatorioService._aplicar_filtros_base(
            Obito.query, nome=nome, data_inicio=data_inicio, data_fim=data_fim,
            idade_min=idade_min, idade_max=idade_max
        )

        query = db.session.query(
            Obito.causa_morte_cid,
            CID.descricao,
            func.count(Obito.id).label('qtd')
        ).outerjoin(CID, Obito.causa_morte_cid == CID.codigo).filter(
            Obito.causa_morte_cid.isnot(None)
        )

        if nome:
            query = query.filter(Obito.nome.ilike(f'%{nome}%'))
        if data_inicio:
            query = query.filter(Obito.data_obito >= data_inicio)
        if data_fim:
            query = query.filter(Obito.data_obito <= data_fim)
        if idade_min is not None or idade_max is not None:
            hoje = date.today()
            if idade_min is not None:
                data_max_nasc = date(hoje.year - int(idade_min), hoje.month, hoje.day)
                query = query.filter(Obito.data_nascimento <= data_max_nasc)
            if idade_max is not None:
                data_min_nasc = date(hoje.year - int(idade_max) - 1, hoje.month, hoje.day)
                query = query.filter(Obito.data_nascimento > data_min_nasc)

        causas = query.group_by(Obito.causa_morte_cid, CID.descricao).order_by(
            func.count(Obito.id).desc()
        ).limit(limite).all()

        return {
            'causas': [{'label': c or 'Sem CID', 'descricao': d or '', 'value': v} for c, d, v in causas],
        }
