#!/usr/bin/env python3
"""
Script de backup automatizado do banco de dados e uploads.
Executar via cron diário.
"""
import os
import sys
import subprocess
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Adiciona path da aplicação
sys.path.insert(0, os.environ.get('APP_DIR', '/opt/sistema-obito'))

from app import create_app
from app.extensions import db

def backup_database(app):
    """Faz backup do banco PostgreSQL/SQLite."""
    db_url = app.config['SQLALCHEMY_DATABASE_URI']
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = Path(app.config.get('BACKUP_DIR', '/opt/sistema-obito/backups'))
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    if 'postgresql' in db_url:
        # Extrai credenciais da URL
        # postgresql://user:pass@host:port/db
        import re
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(\w+)', db_url)
        if match:
            user, password, host, port, dbname = match.groups()
            filename = f"obito_db_{timestamp}.sql.gz"
            filepath = backup_dir / filename
            
            env = os.environ.copy()
            env['PGPASSWORD'] = password
            
            cmd = [
                'pg_dump',
                '-h', host,
                '-p', port,
                '-U', user,
                '-d', dbname,
                '--no-owner', '--no-acl', '--clean', '--if-exists'
            ]
            
            with gzip.open(filepath, 'wt') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, env=env, text=True)
                if result.returncode != 0:
                    raise RuntimeError(f"pg_dump falhou: {result.stderr}")
            
            print(f"Backup PostgreSQL salvo: {filepath}")
            return filepath
    
    elif 'sqlite' in db_url:
        # Backup SQLite - copia arquivo
        db_path = db_url.replace('sqlite:///', '')
        filename = f"obito_db_{timestamp}.sqlite.gz"
        filepath = backup_dir / filename
        
        with open(db_path, 'rb') as f_in:
            with gzip.open(filepath, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        print(f"Backup SQLite salvo: {filepath}")
        return filepath
    
    return None

def backup_uploads(app):
    """Faz backup dos arquivos de upload."""
    upload_dir = Path(app.config['UPLOAD_FOLDER'])
    if not upload_dir.exists():
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = Path(app.config.get('BACKUP_DIR', '/opt/sistema-obito/backups'))
    filename = f"uploads_{timestamp}.tar.gz"
    filepath = backup_dir / filename
    
    shutil.make_archive(str(filepath).replace('.tar.gz', ''), 'gztar', upload_dir)
    print(f"Backup uploads salvo: {filepath}")
    return filepath

def cleanup_old_backups(app, days=30):
    """Remove backups mais antigos que N dias."""
    backup_dir = Path(app.config.get('BACKUP_DIR', '/opt/sistema-obito/backups'))
    if not backup_dir.exists():
        return
    
    cutoff = datetime.now() - timedelta(days=days)
    for filepath in backup_dir.glob('*'):
        if filepath.is_file():
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
            if mtime < cutoff:
                filepath.unlink()
                print(f"Removido backup antigo: {filepath}")

def main():
    app = create_app('production')
    
    with app.app_context():
        try:
            print(f"[{datetime.now()}] Iniciando backup...")
            
            # Backup database
            db_file = backup_database(app)
            
            # Backup uploads
            up_file = backup_uploads(app)
            
            # Limpeza
            cleanup_old_backups(app, days=30)
            
            print(f"[{datetime.now()}] Backup concluído com sucesso!")
            if db_file:
                print(f"  Database: {db_file}")
            if up_file:
                print(f"  Uploads: {up_file}")
                
        except Exception as e:
            print(f"[{datetime.now()}] ERRO no backup: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == '__main__':
    main()