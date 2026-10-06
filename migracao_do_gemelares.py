#!/usr/bin/env python3
"""
Remove a restrição UNIQUE do campo obitos.numero_dob.

Motivo: óbitos de gemelares compartilham o mesmo número de DO.
Antes: unique=True no model + validação bloqueante impedia cadastrar
o segundo gêmeo com a mesma DO.

Uso:
    python migracao_do_gemelares.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app import create_app
from app.extensions import db


def migrar_sqlite(engine, conn):
    """SQLite: remove UNIQUE constraint da tabela obitos (recria tabela)."""
    print('[SQLite] Verificando restrição UNIQUE em obitos.numero_dob...')

    # Descobre se existe índice/unique em numero_dob
    rows = conn.execute(text(
        "SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='obitos' AND sql LIKE '%numero_dob%'"
    )).fetchall()
    print(f'[SQLite] Índices encontrados em numero_dob: {[r[0] for r in rows]}')

    # Verifica constraints UNIQUE via PRAGMA
    pragma = conn.execute(text("PRAGMA index_list('obitos')")).fetchall()
    for idx in pragma:
        # idx: (seq, name, unique, origin, partial)
        if idx[2] == 1:  # unique
            info = conn.execute(text(f"PRAGMA index_info('{idx[1]}')")).fetchall()
            cols = [i[2] for i in info]
            if 'numero_dob' in cols:
                print(f'[SQLite] Constraint único encontrado: {idx[1]} em {cols}')
                try:
                    conn.execute(text(f"DROP INDEX IF EXISTS {idx[1]}"))
                    print(f'[SQLite] Índice único {idx[1]} removido.')
                except Exception as e:
                    print(f'[SQLite] Erro ao remover índice {idx[1]}: {e}')

    # Remove também índices listados no sqlite_master com UNIQUE
    for r in rows:
        name, sql = r[0], r[1] or ''
        if 'UNIQUE' in sql.upper():
            print(f'[SQLite] Removendo índice único do sqlite_master: {name}')
            conn.execute(text(f"DROP INDEX IF EXISTS {name}"))
            print(f'[SQLite] Índice {name} removido.')

    # Garante índice simples para busca
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_obitos_numero_dob ON obitos (numero_dob)"
    ))
    print('[SQLite] Índice simples criado (se não existia).')

    # Garante colunas que podem faltar em bancos antigos
    pragma_cols = conn.execute(text("PRAGMA table_info('obitos')")).fetchall()
    existing = {r[1] for r in pragma_cols}
    colunas_necessarias = {
        'causas_morte_cids': 'TEXT',
        'estabelecimento_id': 'INTEGER',
        'usuario_id': 'INTEGER NOT NULL DEFAULT 1',
    }
    for col, tipo in colunas_necessarias.items():
        if col not in existing:
            conn.execute(text(f"ALTER TABLE obitos ADD COLUMN {col} {tipo}"))
            print(f'[SQLite] Coluna {col} adicionada.')

    conn.commit()


def migrar_postgresql(engine, conn):
    """PostgreSQL: remove UNIQUE constraint de obitos.numero_dob."""
    print('[PostgreSQL] Verificando restrição UNIQUE em obitos.numero_dob...')

    # Procura constraints UNIQUE que incluam numero_dob
    rows = conn.execute(text("""
        SELECT conname, conkey
        FROM pg_constraint
        WHERE contype = 'u'
          AND conrelid = 'obitos'::regclass
    """)).fetchall()

    # Também procura índices únicos
    idx_rows = conn.execute(text("""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = 'obitos'
          AND indexdef ILIKE '%numero_dob%'
    """)).fetchall()

    print(f'[PostgreSQL] Constraints únicos na tabela obitos: {[r[0] for r in rows]}')
    print(f'[PostgreSQL] Índices em numero_dob: {[r[0] for r in idx_rows]}')

    # Mapeia colunas dos constraints
    col_rows = conn.execute(text("""
        SELECT a.attname
        FROM pg_attribute a
        WHERE a.attrelid = 'obitos'::regclass
          AND a.attnum = ANY(ARRAY(
              SELECT unnest(conkey) FROM pg_constraint
              WHERE contype = 'u' AND conrelid = 'obitos'::regclass
          ))
    """)).fetchall()
    unique_cols = [r[0] for r in col_rows]
    print(f'[PostgreSQL] Colunas em constraints únicos: {unique_cols}')

    if 'numero_dob' in unique_cols:
        # Descobre o nome do constraint
        for conname, _ in rows:
            cols = conn.execute(text("""
                SELECT a.attname
                FROM pg_attribute a
                WHERE a.attrelid = 'obitos'::regclass
                  AND a.attnum = ANY(ARRAY(
                      SELECT unnest(conkey) FROM pg_constraint
                      WHERE contype = 'u' AND conrelid = 'obitos'::regclass AND conname = :cname
                  ))
            """), {'cname': conname}).fetchall()
            col_names = [c[0] for c in cols]
            if 'numero_dob' in col_names:
                print(f'[PostgreSQL] Removendo constraint: {conname} ({col_names})')
                conn.execute(text(f'ALTER TABLE obitos DROP CONSTRAINT IF EXISTS "{conname}"'))
                print(f'[PostgreSQL] Constraint {conname} removido.')

    # Remove índices únicos órfãos em numero_dob
    for idxname, idxdef in idx_rows:
        if 'UNIQUE' in (idxdef or '').upper():
            print(f'[PostgreSQL] Removendo índice único: {idxname}')
            conn.execute(text(f'DROP INDEX IF EXISTS "{idxname}"'))
            print(f'[PostgreSQL] Índice {idxname} removido.')

    # Garante índice simples para busca
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_obitos_numero_dob ON obitos (numero_dob)"
    ))
    print('[PostgreSQL] Índice simples garantido.')
    conn.commit()


def main():
    app = create_app()
    with app.app_context():
        engine = db.engine
        url = str(engine.url)
        print(f'Banco: {url}')

        with engine.connect() as conn:
            if 'sqlite' in url:
                migrar_sqlite(engine, conn)
            elif 'postgres' in url:
                migrar_postgresql(engine, conn)
            else:
                print(f'Banco não suportado: {url}')
                sys.exit(1)

        # Valida: tenta criar dois óbitos com a mesma DO
        print()
        print('=== Validação pós-migração ===')
        from app.models import Obito, Usuario
        from datetime import date
        from sqlalchemy import inspect as sa_inspect

        # Verifica se a coluna causas_morte_cids existe no banco
        insp = sa_inspect(engine)
        cols_obitos = [c['name'] for c in insp.get_columns('obitos')]
        tem_jsonb = 'causas_morte_cids' in cols_obitos
        print(f'Coluna causas_morte_cids presente: {tem_jsonb}')

        # Usa usuário existente; só cria temporário se não houver nenhum
        user = Usuario.query.first()
        user_temporario = False
        if not user:
            from werkzeug.security import generate_password_hash
            user = Usuario(
                nome='Teste Migração',
                usuario='teste_migracao',
                cargo='Admin',
                senha_hash=generate_password_hash(''),
                ativo=False,
            )
            db.session.add(user)
            db.session.commit()
            user_temporario = True

        # Tenta criar dois óbitos com a mesma DO
        do_teste = 'DO-TESTE-GEMELOS-001'
        # Limpa óbitos de teste anteriores
        Obito.query.filter_by(numero_dob=do_teste).delete()
        db.session.commit()

        o1 = Obito(
            nome='Gêmeo Teste A',
            data_obito=date.today(),
            numero_dob=do_teste,
            usuario_id=user.id,
        )
        o2 = Obito(
            nome='Gêmeo Teste B',
            data_obito=date.today(),
            numero_dob=do_teste,
            usuario_id=user.id,
        )
        db.session.add(o1)
        db.session.add(o2)
        db.session.commit()

        print(f'Óbito 1 criado: id={o1.id}, DO={o1.numero_dob}')
        print(f'Óbito 2 criado: id={o2.id}, DO={o2.numero_dob}')
        print('OK - DO duplicada aceita, gemeos podem ser cadastrados!')

        # Limpa dados de teste
        Obito.query.filter_by(numero_dob=do_teste).delete()
        if user_temporario:
            db.session.delete(user)
        db.session.commit()
        print('Dados de teste removidos.')

        print()
        print('=== Migração concluída com sucesso ===')


if __name__ == '__main__':
    main()
