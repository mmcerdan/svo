from app import app, db, Obito, Investigacao, InvestigacaoCampo, Anexo, Usuario
from datetime import date, datetime
import os

with app.app_context():
    admin = Usuario.query.filter_by(usuario='admin').first()
    if not admin:
        print("Admin nao encontrado")
        exit()

    # Limpa dados de teste anteriores
    for o in Obito.query.filter(Obito.nome.like('%TESTE%')).all():
        db.session.delete(o)
    db.session.commit()

    # ============ PACIENTE 1: INFANTIL ============
    obito1 = Obito(
        nome='PEDRO HENRIQUE SILVA TESTE',
        data_nascimento=date(2025, 12, 10),
        data_obito=date(2026, 3, 15),
        sexo='M',
        nome_mae='MARIA APARECIDA SILVA',
        nome_pai='JOAO PEDRO SILVA',
        numero_dob='DO-2026-005432',
        causa_morte='Pneumonia bacteriana nao especificada',
        causa_morte_cid='J15.9',
        local_obito='HOSPITAL',
        municipio_ocorrencia='Goianira',
        endereco='Rua das Flores, 123, Centro',
        observacoes='Crianca de 3 meses, prematura, com historico de infeccoes respiratorias',
        usuario_id=admin.id
    )
    db.session.add(obito1)
    db.session.commit()

    inv1 = Investigacao(
        obito_id=obito1.id, tipo='INFANTIL', status='CONCLUIDA',
        responsavel='Dra. Ana Lucia Medeiros', data_abertura=date(2026, 3, 18),
        data_conclusao=date(2026, 4, 5),
        conclusao='Obito infantil por pneumonia em crianca prematura. Identificou-se falha no acompanhamento pos-alta da UTI neonatal. A crianca nao completou o esquema vacinal para idade. Recomendado fortalecimento da busca ativa de recem-nascidos de risco.',
        observacoes='Caso discutido no comite de obito infantil. Classificacao de evitabilidade: Wigglesworth W4.',
        usuario_id=admin.id
    )
    db.session.add(inv1)
    db.session.commit()

    for nome, valor in [
        ('Nome da crianca / Nome da mae', 'PEDRO HENRIQUE SILVA / MARIA APARECIDA SILVA'),
        ('Nº da DO / Nº da DN', 'DO-2026-005432 / DN-2026-008877'),
        ('Peso ao nascer (gramas)', '2150g (baixo peso)'),
        ('Idade ao obito (meses/dias/horas)', '3 meses e 5 dias'),
        ('Nº do Cartao SUS / Equipe PSF', '123.4567.8901-00 / ESF Goianira II'),
        ('Pre-natal: numero de consultas', '6 consultas (iniciou com 12 semanas)'),
        ('Patologias na gestacao', 'Infeccao urinaria no 2o trimestre, amniorrexe prematura'),
        ('Aleitamento materno exclusivo?', 'Nao. Leite artificial desde o 1o mes'),
        ('Vacinacao completa para idade?', 'Nao. Atraso na vacina pentavalente e pneumococica'),
        ('Causa do obito registrada no prontuario', 'Pneumonia bacteriana. Insuficiencia respiratoria aguda'),
        ('Resumo do caso / conclusao', 'Prematuro (35 semanas), baixo peso, mae com infeccao urinaria na gestacao. Crianca teve alta da maternidade com 3 dias, mas nao retornou para consultas de puericultura. Deu entrada no PS com desconforto respiratorio grave, evoluiu para obito em 48h. Causa basica: Pneumonia. Fatores contribuintes: prematuridade, baixo peso, falha no acompanhamento pos-alta.')
    ]:
        c = InvestigacaoCampo(investigacao_id=inv1.id, nome_campo=nome, valor=valor)
        db.session.add(c)
    db.session.commit()

    # ============ PACIENTE 2: MIF ============
    obito2 = Obito(
        nome='FERNANDA COSTA OLIVEIRA TESTE',
        data_nascimento=date(1990, 7, 22),
        data_obito=date(2026, 5, 10),
        sexo='F',
        nome_mae='RAIMUNDA COSTA',
        nome_pai='JOSE OLIVEIRA',
        numero_dob='DO-2026-008901',
        causa_morte='Embolia pulmonar',
        causa_morte_cid='I26.9',
        local_obito='HOSPITAL',
        municipio_ocorrencia='Goianira',
        endereco='Av. Central, 456, Setor Bela Vista',
        observacoes='Mulher 35 anos, obito pos-operatorio de cesariana. Investigar possivel obito materno.',
        usuario_id=admin.id
    )
    db.session.add(obito2)
    db.session.commit()

    inv2 = Investigacao(
        obito_id=obito2.id, tipo='MIF', status='EM_ANDAMENTO',
        responsavel='Dr. Carlos Santos', data_abertura=date(2026, 5, 12),
        observacoes='Aguardando resultados de exames complementares e entrevista domiciliar.',
        usuario_id=admin.id
    )
    db.session.add(inv2)
    db.session.commit()

    for nome, valor in [
        ('Nº da DO', 'DO-2026-008901'),
        ('Data do obito', '10/05/2026'),
        ('Local de ocorrencia', 'Hospital Municipal de Goianira'),
        ('Estava gravida no momento do obito?', 'Sim. 38 semanas de gestacao. Cesarea de urgencia.'),
        ('Esteve gravida nos 12 meses anteriores?', 'Sim (gestacao atual)'),
        ('Resumo do caso / justificativa', 'Paciente internada para cesarea eletiva (apresentacao pelvica). No pos-operatorio imediato (6h apos cirurgia) apresentou dispneia subita, dor toracica e hipotensao. Parada cardiorrespiratoria nao responsiva a reanimacao. Suspeita de embolia pulmonar macica. Investigacao em andamento para confirmar obito materno.'),
        ('Data da investigacao', '12/05/2026')
    ]:
        c = InvestigacaoCampo(investigacao_id=inv2.id, nome_campo=nome, valor=valor)
        db.session.add(c)
    db.session.commit()

    # ============ PACIENTE 3: CAUSA MAL DEFINIDA ============
    obito3 = Obito(
        nome='JOAO BATISTA DOS SANTOS TESTE',
        data_nascimento=date(1945, 3, 8),
        data_obito=date(2026, 4, 28),
        sexo='M',
        nome_mae='MARIA DOS SANTOS',
        numero_dob='DO-2026-007654',
        causa_morte='Parada cardiorrespiratoria',
        causa_morte_cid='I46.9',
        local_obito='DOMICILIO',
        municipio_ocorrencia='Goianira',
        endereco='Rua 14, s/n, Zona Rural',
        observacoes='Causa mal definida. CID I46.9 (parada cardiaca). Necessario investigar causa basica.',
        usuario_id=admin.id
    )
    db.session.add(obito3)
    db.session.commit()

    inv3 = Investigacao(
        obito_id=obito3.id, tipo='MAL_DEFINIDA', status='EM_ANDAMENTO',
        responsavel='Dr. Carlos Santos', data_abertura=date(2026, 5, 2),
        observacoes='Entrevista domiciliar agendada. Aguardando prontuario da USF.',
        usuario_id=admin.id
    )
    db.session.add(inv3)
    db.session.commit()

    for nome, valor in [
        ('Nº da DO / Causa basica original', 'DO-2026-007654 / I46.9 - Parada cardiorrespiratoria'),
        ('Nome da Unidade Basica de Saude', 'USF Goianira Rural'),
        ('Patologias que motivavam atendimentos', 'Hipertensao arterial, diabetes tipo II, cardiopatia cronica'),
        ('Data e motivo da ultima consulta', '10/04/2026 - Queixa de falta de ar e inchaco nos pes'),
        ('Estabelecimento de saude da internacao', 'Nao houve internacao. Obito em domicilio.'),
        ('Data da internacao / alta', 'Nao se aplica'),
        ('Hipotese diagnostica da alta', 'Nao se aplica'),
        ('Resultados de exames relevantes', 'ECG de 10/04: sobrecarga ventricular esquerda. Glicemia: 210. Creatinina: 1.8'),
        ('Causa do obito no prontuario', 'Nao localizado. Paciente nao tinha consulta ha 18 dias.'),
        ('Investigacao em outros locais (SINAN/IML/SVO)', 'SVO: necropsia realizada. Resultado pendente.'),
        ('Causas da morte apos investigacao / CID', 'Aguardando resultado da necropsia do SVO.')
    ]:
        c = InvestigacaoCampo(investigacao_id=inv3.id, nome_campo=nome, valor=valor)
        db.session.add(c)
    db.session.commit()

    # ============ PACIENTE 4: MATERNO ============
    obito4 = Obito(
        nome='CAMILA RIBEIRO NOGUEIRA TESTE',
        data_nascimento=date(1998, 11, 30),
        data_obito=date(2026, 6, 1),
        sexo='F',
        nome_mae='TEREZINHA RIBEIRO',
        numero_dob='DO-2026-009123',
        causa_morte='Hemorragia pos-parto',
        causa_morte_cid='O72.1',
        local_obito='HOSPITAL',
        municipio_ocorrencia='Goianira',
        observacoes='Obito materno por hemorragia pos-parto imediata.',
        usuario_id=admin.id
    )
    db.session.add(obito4)
    db.session.commit()

    inv4 = Investigacao(
        obito_id=obito4.id, tipo='MATERNO', status='AGUARDANDO',
        responsavel='', data_abertura=date(2026, 6, 3),
        observacoes='Aguardando designacao de responsavel pela investigacao.',
        usuario_id=admin.id
    )
    db.session.add(inv4)
    db.session.commit()

    for nome, valor in [
        ('Nº da DO / Data do obito', 'DO-2026-009123 / 01/06/2026'),
        ('Idade gestacional na 1ª consulta', '10 semanas'),
        ('Numero de consultas pre-natal', '8 consultas'),
        ('Foi considerada gestante de alto risco?', 'Sim. Hipertensao arterial gestacional (DHEG).'),
        ('Patologias/fatores de risco na gestacao', 'DHEG, edema importante, proteinuria ++'),
        ('Foi internada durante a gestacao? Motivo?', 'Sim. 2 internacoes: (1) 32 sem por crise hipertensiva; (2) 38 sem para cesarea'),
        ('Tipo de parto (normal/forceps/cesareo)', 'Cesareo de urgencia por sofrimento fetal agudo'),
        ('Houve emergencia obstetrica?', 'Sim. Atonia uterina pos-parto com hemorragia macica. Nao respondeu a ocitocina e misoprostol. Realizada histerectomia, mas paciente entrou em CIVD e obito.'),
        ('Causas do obito registradas no prontuario', 'Hemorragia pos-parto por atonia uterina. CIVD.'),
        ('Resumo do caso / conclusao', 'Paciente primigesta, 27 anos. Pre-natal com 8 consultas, diagnosticada com DHEG. Cesarea de urgencia por sofrimento fetal. Apos parto, apresentou atonia uterina com hemorragia refrataria. Histerectomia de urgencia. Evoluiu com CIVD e parada cardiorrespiratoria. Obito materno investigado.')
    ]:
        c = InvestigacaoCampo(investigacao_id=inv4.id, nome_campo=nome, valor=valor)
        db.session.add(c)
    db.session.commit()

    # ============ PACIENTE 5: INFANTIL/FETAL ============
    obito5 = Obito(
        nome='NATALIA FERNANDES TESTE',
        data_nascimento=date(2026, 5, 20),
        data_obito=date(2026, 5, 20),
        sexo='F',
        nome_mae='PATRICIA FERNANDES',
        numero_dob='DO-2026-009456',
        causa_morte='Anoxia fetal aguda',
        causa_morte_cid='P21.0',
        local_obito='HOSPITAL',
        municipio_ocorrencia='Goianira',
        observacoes='Obito neonatal precoce (0 dias). Anoxia fetal aguda durante trabalho de parto.',
        usuario_id=admin.id
    )
    db.session.add(obito5)
    db.session.commit()

    inv5 = Investigacao(
        obito_id=obito5.id, tipo='INFANTIL_FETAL', status='CONCLUIDA',
        responsavel='Dra. Ana Lucia Medeiros', data_abertura=date(2026, 5, 22),
        data_conclusao=date(2026, 6, 10),
        conclusao='Obito neonatal precoce por anoxia fetal durante trabalho de parto prolongado. Identificou-se que nao foi utilizado partograma durante o trabalho de parto. O descolamento prematuro de placenta foi diagnosticado tardiamente. Recomendado capacitacao da equipe obstetrica para uso sistematico do partograma e protocolo de emergencias obstetricas.',
        observacoes='Caso notificado ao comite de obito fetal e infantil.',
        usuario_id=admin.id
    )
    db.session.add(inv5)
    db.session.commit()

    for nome, valor in [
        ('Nome da crianca', 'NATALIA FERNANDES'),
        ('Nº da DO / Nº da DN', 'DO-2026-009456 / DN-2026-009901'),
        ('Peso ao nascer (gramas)', '3120g'),
        ('Idade gestacional (semanas)', '39 semanas e 2 dias'),
        ('Faixa etaria (fetal/neonatal/precoce/tardio/pos-neonatal)', 'Neonatal precoce (0 dias)'),
        ('Idade da mae / Escolaridade materna', '22 anos / Ensino medio completo'),
        ('A investigacao alterou a causa do obito?', 'Nao. Confirmou a causa original.'),
        ('Causa basica apos investigacao / CID', 'Anoxia fetal aguda (P21.0) devido a descolamento prematuro de placenta (O45.9)'),
        ('Problemas identificados (acesso/assistencia)', 'Falha no uso do partograma. Diagnostico tardio de descolamento prematuro de placenta. Demora na decisao por cesarea de urgencia.'),
        ('Classificacao de evitabilidade', 'Wigglesworth W7 (evitavel). Lista brasileira: 1.2.1'),
        ('Recomendacoes e medidas de prevencao', '1) Capacitacao em partograma para toda equipe; 2) Protocolo de hemorragia obstetrica; 3) Auditoria de obitos perinatais')
    ]:
        c = InvestigacaoCampo(investigacao_id=inv5.id, nome_campo=nome, valor=valor)
        db.session.add(c)
    db.session.commit()

    print('='*60)
    print('  PACIENTES DE TESTE CRIADOS COM SUCESSO!')
    print('='*60)
    print()
    print('  1. PEDRO HENRIQUE SILVA TESTE - Infantil (CONCLUIDA)')
    print('  2. FERNANDA COSTA OLIVEIRA TESTE - MIF (EM ANDAMENTO)')
    print('  3. JOAO BATISTA DOS SANTOS TESTE - Mal Definida (EM ANDAMENTO)')
    print('  4. CAMILA RIBEIRO NOGUEIRA TESTE - Materno (AGUARDANDO)')
    print('  5. NATALIA FERNANDES TESTE - Infantil/Fetal (CONCLUIDA)')
    print()
    print('  Acesse: http://localhost:5000')
    print('  Login: admin / admin123')
