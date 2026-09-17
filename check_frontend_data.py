from app import create_app
from app.extensions import db
from app.models import Investigacao

app = create_app()
with app.app_context():
    inv = db.session.query(Investigacao).filter_by(tipo='INFANTIL_FETAL').first()
    if inv:
        print(f'Inv ID: {inv.id}')
        for campo in inv.campos:
            if 'Lista Brasileira' in campo.nome_campo:
                print(f'  LB: {campo.nome_campo} = {campo.valor}')
            if 'Problema 26.1' in campo.nome_campo:
                print(f'  P26: {campo.nome_campo} = {campo.valor}')
            if 'Organizacao' in campo.nome_campo:
                print(f'  Org: {campo.nome_campo} = {campo.valor}')
            if 'Escolaridade' in campo.nome_campo:
                print(f'  Esc: {campo.nome_campo} = {campo.valor}')