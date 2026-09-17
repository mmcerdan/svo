from app import create_app
from app.extensions import db
from app.models import CID
from cid_data import CIDS

app = create_app()
with app.app_context():
    # Clear existing
    CID.query.delete()
    db.session.commit()
    
    count = 0
    for codigo, descricao in CIDS:
        # Determine chapter based on code prefix
        capitulo = ''
        prefix = codigo[0]
        if prefix == 'A' or prefix == 'B':
            capitulo = 'I - Certas doenças infecciosas e parasitárias'
        elif prefix == 'C' or prefix == 'D':
            capitulo = 'II - Neoplasias'
        elif prefix == 'E':
            capitulo = 'IV - Doenças endócrinas, nutricionais e metabólicas'
        elif prefix == 'F':
            capitulo = 'V - Transtornos mentais e comportamentais'
        elif prefix == 'G':
            capitulo = 'VI - Doenças do sistema nervoso'
        elif prefix == 'H':
            capitulo = 'VII - Doenças do olho e anexos / VIII - Doenças do ouvido'
        elif prefix == 'I':
            capitulo = 'IX - Doenças do aparelho circulatório'
        elif prefix == 'J':
            capitulo = 'X - Doenças do aparelho respiratório'
        elif prefix == 'K':
            capitulo = 'XI - Doenças do aparelho digestivo'
        elif prefix == 'L':
            capitulo = 'XII - Doenças da pele e do tecido subcutâneo'
        elif prefix == 'M':
            capitulo = 'XIII - Doenças do sistema osteomuscular e do tecido conjuntivo'
        elif prefix == 'N':
            capitulo = 'XIV - Doenças do aparelho geniturinário'
        elif prefix == 'O':
            capitulo = 'XV - Gravidez, parto e puerpério'
        elif prefix == 'P':
            capitulo = 'XVI - Certas afecções originadas no período perinatal'
        elif prefix == 'Q':
            capitulo = 'XVII - Malformações congênitas'
        elif prefix == 'R':
            capitulo = 'XVIII - Sintomas, sinais e achados anormais'
        elif prefix == 'S' or prefix == 'T':
            capitulo = 'XIX - Lesões, envenenamentos e algumas outras consequências de causas externas'
        elif prefix == 'V' or prefix == 'W' or prefix == 'X' or prefix == 'Y':
            capitulo = 'XX - Causas externas de morbidade e mortalidade'
        elif prefix == 'Z':
            capitulo = 'XXI - Fatores que influenciam o estado de saúde e contato com serviços'
        
        cid = CID(codigo=codigo, descricao=descricao, capitulo=capitulo)
        db.session.add(cid)
        count += 1
        
        if count % 500 == 0:
            db.session.commit()
            print(f"  {count} inseridos...")
    
    db.session.commit()
    print(f"Total: {count} CIDs importados!")