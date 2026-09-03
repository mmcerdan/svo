from app import create_app
from app.extensions import db
from app.models import CID

app = create_app()
with app.app_context():
    # CIDs comuns para óbitos (perinatal, infecciosas, etc.)
    cids_comuns = [
        # Capítulo XVI - Perinatal
        ("P968", "Outras afecções especificadas do período perinatal", "XVI - Certas afecções originadas no período perinatal", "Outras afecções perinatais"),
        ("P969", "Afeção perinatal, não especificada", "XVI - Certas afecções originadas no período perinatal", "Outras afecções perinatais"),
        ("P95", "Morte fetal de causa não especificada", "XVI - Certas afecções originadas no período perinatal", "Morte fetal"),
        ("P369", "Sepse bacteriana do recém-nascido, não especificada", "XVI - Certas afecções originadas no período perinatal", "Infecções perinatais"),
        ("P360", "Sepse do recém-nascido devida a estreptococo do grupo B", "XVI - Certas afecções originadas no período perinatal", "Infecções perinatais"),
        ("P361", "Sepse do recém-nascido devida a outros estreptococos", "XVI - Certas afecções originadas no período perinatal", "Infecções perinatais"),
        ("P362", "Sepse do recém-nascido devida a Staphylococcus aureus", "XVI - Certas afecções originadas no período perinatal", "Infecções perinatais"),
        ("P363", "Sepse do recém-nascido devida a outros estafilococos", "XVI - Certas afecções originadas no período perinatal", "Infecções perinatais"),
        ("P364", "Sepse do recém-nascido devida a Escherichia coli", "XVI - Certas afecções originadas no período perinatal", "Infecções perinatais"),
        ("P365", "Sepse do recém-nascido devida a anaeróbios", "XVI - Certas afecções originadas no período perinatal", "Infecções perinatais"),
        ("P366", "Sepse do recém-nascido devida a outros agentes bacterianos", "XVI - Certas afecções originadas no período perinatal", "Infecções perinatais"),
        ("P368", "Outras sepse bacterianas do recém-nascido", "XVI - Certas afecções originadas no período perinatal", "Infecções perinatais"),
        ("P209", "Membrana hialina do recém-nascido, não especificada", "XVI - Certas afecções originadas no período perinatal", "Distress respiratório"),
        ("P220", "Síndrome do desconforto respiratório do recém-nascido", "XVI - Certas afecções originadas no período perinatal", "Distress respiratório"),
        ("P280", "Apneia do recém-nascido", "XVI - Certas afecções originadas no período perinatal", "Distress respiratório"),
        ("P072", "Extrema imaturidade", "XVI - Certas afecções originadas no período perinatal", "Prematuridade"),
        ("P073", "Outra prematuridade", "XVI - Certas afecções originadas no período perinatal", "Prematuridade"),
        ("P059", "Crescimento intrauterino retardado, não especificado", "XVI - Certas afecções originadas no período perinatal", "Restrição de crescimento"),
        ("P082", "Outros recém-nascidos pesados para a idade gestacional", "XVI - Certas afecções originadas no período perinatal", "Macrossomia"),
        
        # Capítulo I - Infecciosas
        ("A419", "Sepse, não especificada", "I - Certas doenças infecciosas e parasitárias", "Sepse"),
        ("A410", "Sepse devida a Staphylococcus aureus", "I - Certas doenças infecciosas e parasitárias", "Sepse"),
        ("A411", "Sepse devida a outros estafilococos", "I - Certas doenças infecciosas e parasitárias", "Sepse"),
        ("A412", "Sepse devida a estreptococo não especificado", "I - Certas doenças infecciosas e parasitárias", "Sepse"),
        ("A413", "Sepse devida a Hemophilus influenzae", "I - Certas doenças infecciosas e parasitárias", "Sepse"),
        ("A414", "Sepse devida a anaeróbios", "I - Certas doenças infecciosas e parasitárias", "Sepse"),
        ("A415", "Sepse devida a outros bacilos Gram-negativos", "I - Certas doenças infecciosas e parasitárias", "Sepse"),
        ("A418", "Outras sepse especificadas", "I - Certas doenças infecciosas e parasitárias", "Sepse"),
        ("B349", "Infecção viral, não especificada", "I - Certas doenças infecciosas e parasitárias", "Infecção viral"),
        
        # Capítulo IX - Circulatórias
        ("I219", "Infarto agudo do miocárdio, não especificado", "IX - Doenças do aparelho circulatório", "Doenças isquêmicas"),
        ("I259", "Doença isquêmica crônica do coração, não especificada", "IX - Doenças do aparelho circulatório", "Doenças isquêmicas"),
        ("I509", "Insuficiência cardíaca, não especificada", "IX - Doenças do aparelho circulatório", "Insuficiência cardíaca"),
        ("I619", "Hemorragia intracerebral, não especificada", "IX - Doenças do aparelho circulatório", "Doenças cerebrovasculares"),
        ("I639", "Infarto cerebral, não especificado", "IX - Doenças do aparelho circulatório", "Doenças cerebrovasculares"),
        ("I64", "Acidente vascular cerebral, não especificado", "IX - Doenças do aparelho circulatório", "AVC"),
        
        # Capítulo X - Respiratórias
        ("J189", "Pneumonia, não especificada", "X - Doenças do aparelho respiratório", "Pneumonia"),
        ("J449", "Doença pulmonar obstrutiva crônica, não especificada", "X - Doenças do aparelho respiratório", "DPOC"),
        ("J690", "Pneumonite devida a inalação de alimentos e vômito", "X - Doenças do aparelho respiratório", "Pneumonite por aspiração"),
        
        # Capítulo XI - Digestivas
        ("K729", "Insuficiência hepática, não especificada", "XI - Doenças do aparelho digestivo", "Insuficiência hepática"),
        ("K746", "Outras cirroses do fígado", "XI - Doenças do aparelho digestivo", "Cirrose"),
        
        # Capítulo XIV - Geniturinárias
        ("N179", "Insuficiência renal aguda, não especificada", "XIV - Doenças do aparelho geniturinário", "Insuficiência renal aguda"),
        ("N189", "Doença renal crônica, não especificada", "XIV - Doenças do aparelho geniturinário", "Doença renal crônica"),
        
        # Capítulo XVII - Malformações
        ("Q899", "Malformação congênita, não especificada", "XVII - Malformações congênitas", "Malformações"),
        ("Q799", "Malformação congênita do sistema musculoesquelético, não especificada", "XVII - Malformações congênitas", "Malformações"),
        
        # Capítulo XVIII - Sintomas
        ("R99", "Outras causas mal definidas e não especificadas de mortalidade", "XVIII - Sintomas, sinais e achados anormais", "Causas mal definidas"),
        ("R960", "Morte súbita, causa desconhecida", "XVIII - Sintomas, sinais e achados anormais", "Morte súbita"),
        ("R961", "Morte instantânea, causa desconhecida", "XVIII - Sintomas, sinais e achados anormais", "Morte súbita"),
    ]
    
    count = 0
    for codigo, descricao, capitulo, subcategoria in cids_comuns:
        if not CID.query.filter_by(codigo=codigo).first():
            cid = CID(codigo=codigo, descricao=descricao, capitulo=capitulo, subcategoria=subcategoria)
            db.session.add(cid)
            count += 1
    
    db.session.commit()
    print(f'{count} CIDs inseridos!')