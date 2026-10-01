# Sistema de Óbito - Goianira

Sistema para registro, investigação e relatórios de óbitos (SVO - Sistema de Vigilância de Óbitos) desenvolvido para a Secretaria Municipal de Saúde de Goianira.

---

## 📋 Funcionalidades

### Tipos de Investigação
- **MIF** - Morte Infantil Fetal
- **MATERNO** - Morte Materna
- **INFANTIL_FETAL** - Óbito Infantil/Fetal (IF5 - Ficha Oficial MS)
- **MAL_DEFINIDA** - Causa Mal Definida
- **INFANTIL** - Óbito Infantil

### Módulos Principais
1. **Cadastro de Óbitos** - Registro completo com dados do falecido, mãe, pai, causa CID-10
2. **Investigações** - Formulários específicos por tipo (IF5 com ficha oficial MS)
3. **Relatórios** - Filtros por nome, data, idade; exportação CSV/PDF
4. **Usuários/Perfis** - Admin, Vigilância, Digitador
5. **Estabelecimentos** - Cadastro CNES

---

## 🚀 Instalação no Servidor (Ubuntu 22.04)

### 1. Preparação do Sistema
```bash
# Atualizar sistema
apt-get update && apt-get upgrade -y

# Instalar dependências do sistema
apt-get install -y python3.11 python3.11-venv python3.11-dev \
    postgresql postgresql-contrib libpq-dev \
    nginx git curl \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

# Criar usuário da aplicação
adduser --system --group --home /opt/sistema-obito obito
```

### 2. PostgreSQL
```bash
sudo -u postgres psql <<EOF
CREATE DATABASE obito_db;
CREATE USER obito_user WITH ENCRYPTED PASSWORD 'obito_prod_2026';
GRANT ALL PRIVILEGES ON DATABASE obito_db TO obito_user;
ALTER USER obito_user CREATEDB;
EOF
```

### 3. Código da Aplicação
```bash
cd /opt
git clone https://github.com/mmcerdan/svo.git sistema-obito
cd sistema-obito
git checkout v1.0  # ou main para versão atual
```

### 4. Ambiente Virtual e Dependências
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# WeasyPrint (para PDF) - versões compatíveis
pip install 'weasyprint==70.0' 'cairocffi==1.7.1'
```

### 5. Configuração (.env)
```bash
cat > .env <<EOF
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=sua-chave-secreta-super-segura-aqui
DATABASE_URL=postgresql://obito_user:obito_prod_2026@localhost/obito_db
EOF
```

### 6. Inicialização do Banco
```bash
source venv/bin/activate
flask db upgrade  # se usar Flask-Migrate
# OU criar tabelas diretamente:
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('Tabelas criadas')
"
```

### 7. Usuário Admin Inicial
```bash
python -c "
from app import create_app, db
from app.models import Usuario
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    if not Usuario.query.filter_by(cpf='99999999999').first():
        admin = Usuario(
            cpf='99999999999',
            nome='Administrador',
            email='admin@goianira.go.gov.br',
            perfil='admin',
            senha_hash=generate_password_hash('admin123'),
            ativo=True
        )
        db.session.add(admin)
        db.session.commit()
        print('Admin criado: cpf=99999999999 / senha=admin123')
"
```

### 8. Systemd Service
```bash
cat > /etc/systemd/system/sistema-obito.service <<EOF
[Unit]
Description=Sistema de Óbito Goianira
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=exec
User=obito
Group=obito
WorkingDirectory=/opt/sistema-obito
Environment=PATH=/opt/sistema-obito/venv/bin
ExecStart=/opt/sistema-obito/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 --timeout 120 run:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable sistema-obito
systemctl start sistema-obito
```

### 9. Nginx (Reverse Proxy)
```bash
cat > /etc/nginx/sites-available/sistema-obito <<EOF
server {
    listen 80;
    server_name 192.168.0.225;  # ou seu domínio

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }

    location /static {
        alias /opt/sistema-obito/app/static;
        expires 30d;
    }
}
EOF

ln -s /etc/nginx/sites-available/sistema-obito /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

### 10. Firewall
```bash
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

---

## 🔧 Configurações Importantes

### Variáveis de Ambiente (.env)
| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `SECRET_KEY` | Chave secreta Flask (gere com `secrets.token_hex(32)`) | `abc123...` |
| `DATABASE_URL` | URL PostgreSQL | `postgresql://user:pass@localhost/db` |
| `FLASK_ENV` | Ambiente | `production` |

### Logs
```bash
# Ver logs do systemd
journalctl -u sistema-obito -f

# Ver logs do Nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Backup do Banco
```bash
# Backup diário (crontab)
0 2 * * * pg_dump -U obito_user obito_db | gzip > /opt/backups/db_$(date +\%Y\%m\%d).sql.gz

# Restaurar
gunzip -c /opt/backups/db_20260925.sql.gz | psql -U obito_user obito_db
```

---

## 📖 Manual de Uso

### Acesso
- URL: `http://192.168.0.225:9010` (ou porta 80 via Nginx)
- Login: CPF + Senha
- Admin padrão: `99999999999` / `admin123` **ALTERE IMEDIATAMENTE**

### Perfis de Usuário
| Perfil | Permissões |
|--------|------------|
| **Admin** | Todo o sistema, usuários, configurações |
| **Vigilância** | Óbitos, Investigações, Relatórios, Exportar |
| **Digitador** | Cadastrar/Editar óbitos próprios, Investigar |

---

### 1. Cadastrar Óbito
1. Menu **Óbitos** → **Novo Óbito**
2. Preencher:
   - Dados do falecido (nome, datas, sexo, filiação)
   - Causa básica (CID-10) - use busca
   - Local/Município do óbito
   - Estabelecimento (CNES)
3. **Salvar** → Gera número DO automático

### 2. Iniciar Investigação
1. Na lista de óbitos, clique **Investigar**
2. Escolha o **Tipo** (MIF, MATERNO, INFANTIL_FETAL, etc.)
3. Preencha a ficha específica:
   - **IF5 (INFANTIL_FETAL)**: Ficha oficial MS com:
     - Lista Brasileira (8 itens oficiais)
     - 3 Estabelecimentos (Pré-natal, Parto, Atenção Básica)
     - Matriz 26 (Problemas) e 26.10 (Organização)
     - Escolaridade mãe (Anos/Série/Grau/Ignorado)
     - 8 Recomendações (textareas)
4. **Salvar** → Status: "Aguardando" → "Em Andamento" → "Concluída"

### 3. Relatórios
Menu **Relatórios** → Filtros disponíveis:
- **Busca por nome** (parcial, case-insensitive)
- **Período**: botões rápidos (Mês, Trimestre, Semestre, Ano, Todos)
- **Faixa etária**: Idade mín/máx
- **Tipos**: Visão Geral, Investigações, Causas (CID-10)
- **Exportar**: CSV ou PDF

#### Visão Geral mostra:
- Total de óbitos
- Por Sexo (M/F)
- Por Tipo de Ficha (MIF, MATERNO, INFANTIL_FETAL...)
- Por CID-10 (código + quantidade)
- Por Local (Hospital, Domicílio, etc.)

### 4. Imprimir Ficha (PDF)
- Em qualquer investigação: botão **Imprimir**
- Gera PDF oficial formatado (WeasyPrint)
- IF5 segue layout Ministério da Saúde

---

## 🔄 Atualização do Sistema

```bash
cd /opt/sistema-obito
sudo -u obito bash -c 'source venv/bin/activate && git pull origin main'
sudo -u obito bash -c 'source venv/bin/activate && pip install -r requirements.txt'
# Se houver migrações:
sudo -u obito bash -c 'source venv/bin/activate && flask db upgrade'
systemctl restart sistema-obito
```

---

## 🐛 Solução de Problemas

### PDF não gera (`'super' object has no attribute 'transform'`)
```bash
# Atualizar WeasyPrint e dependências
apt-get install -y libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0
sudo -u obito bash -c 'source /opt/sistema-obito/venv/bin/activate && pip install --upgrade weasyprint cairocffi'
systemctl restart sistema-obito
```

### Erro CSRF (403) em formulários
- Verifique se `{{ form.csrf_token }}` está no template
- Limpe cookies do navegador
- Verifique `SECRET_KEY` no .env

### Serviço não inicia
```bash
journalctl -u sistema-obito -n 50
# Verifique: permissões, DATABASE_URL, venv ativo
```

### Porta 5000 ocupada
```bash
lsof -i :5000
kill -9 <PID>
systemctl restart sistema-obito
```

---

## 📁 Estrutura do Projeto

```
sistema-obito/
├── app/
│   ├── models/           # Models SQLAlchemy
│   ├── routes/           # Blueprints (main, obitos, investigacoes, relatorios, auth)
│   ├── services/         # Lógica de negócio (RelatorioService, ObitoService)
│   ├── utils/            # Utilitários (PDF, campos, validators)
│   ├── templates/        # Jinja2 templates
│   │   ├── investigacoes/partials/  # Partials por seção (IF5)
│   │   └── relatorios/
│   └── static/           # CSS, JS, imagens
├── migrations/           # Alembic (se usado)
├── venv/                 # Virtualenv (não versionado)
├── run.py                # Entry point
├── requirements.txt
├── .env                  # Configurações (não versionado)
└── README.md
```

---

## 📝 Versionamento

- **Tag v1.0** - Versão estável em produção (25/09/2026)
- Branch `main` - Desenvolvimento contínuo
- Backups em `/opt/backups/` no servidor

```bash
# Voltar para v1.0
git checkout v1.0

# Ver tags
git tag -l
```

---

## 📞 Suporte

- **Desenvolvedor**: Marcos Cerdan
- **Email**: mm.cerdan@gmail.com
- **Repositório**: https://github.com/mmcerdan/svo
- **Telefone**: (62)99345-8069

---

## ⚠️ Notas Importantes

1. **Troque a senha do admin** no primeiro acesso
2. **Configure HTTPS** (Let's Encrypt) em produção
3. **Backup diário** do banco é obrigatório
4. **WeasyPrint** requer libs do sistema (cairo, pango, gdk-pixbuf)
5. **CSRF** ativo em todos formulários - inclua `{{ form.csrf_token }}`
