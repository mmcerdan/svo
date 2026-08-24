#!/usr/bin/env python3
"""
Ponto de entrada da aplicação.
"""
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Em produção, use gunicorn: gunicorn -w 4 -b 0.0.0.0:5000 run:app
    app.run(host='0.0.0.0', port=5000, debug=False)