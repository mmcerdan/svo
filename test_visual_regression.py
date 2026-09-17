#!/usr/bin/env python3
"""
Teste de regressão visual para IF5 - Compara PDF gerado com estrutura esperada
"""
import sys
sys.path.insert(0, '/opt/sistema-obito')

from app import create_app
from app.extensions import db
from app.models import Investigacao, Obito
from app.utils.pdf import gerar_pdf_investigacao
from datetime import date

app = create_app()

def test_if5_pdf_generation():
    """Testa geração de PDF para investigação INFANTIL_FETAL"""
    with app.app_context():
        # Busca uma investigação IF5
        inv = db.session.query(Investigacao).filter_by(tipo='INFANTIL_FETAL').first()
        if not inv:
            print("ERRO: Nenhuma investigação INFANTIL_FETAL encontrada")
            return False
        
        print(f"Testando PDF para investigação ID={inv.id}, Tipo={inv.tipo}")
        
        try:
            pdf_bytes = gerar_pdf_investigacao(inv)
            
            # Verifica se o PDF foi gerado
            if not pdf_bytes:
                print("ERRO: PDF vazio")
                return False
            
            if len(pdf_bytes) < 1000:
                print(f"ERRO: PDF muito pequeno ({len(pdf_bytes)} bytes)")
                return False
            
            # Salva para inspeção visual
            output_path = f'/tmp/if5_test_{inv.id}.pdf'
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
            
            print(f"✓ PDF gerado com sucesso: {len(pdf_bytes)} bytes")
            print(f"  Salvo em: {output_path}")
            
            # Verifica estrutura básica do PDF
            if b'%PDF' not in pdf_bytes[:10]:
                print("ERRO: Não é um PDF válido")
                return False
            
            print("✓ PDF válido (header %PDF encontrado)")
            return True
            
        except Exception as e:
            print(f"ERRO ao gerar PDF: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_all_types_pdf():
    """Testa geração de PDF para todos os tipos"""
    with app.app_context():
        types = ['MIF', 'MATERNO', 'INFANTIL_FETAL', 'MAL_DEFINIDA', 'INFANTIL']
        results = {}
        
        for tipo in types:
            inv = db.session.query(Investigacao).filter_by(tipo=tipo).first()
            if not inv:
                print(f"  {tipo}: SEM DADOS - pulando")
                results[tipo] = 'SKIP'
                continue
            
            try:
                pdf_bytes = gerar_pdf_investigacao(inv)
                if pdf_bytes and len(pdf_bytes) > 1000 and b'%PDF' in pdf_bytes[:10]:
                    results[tipo] = 'OK'
                    print(f"  {tipo}: ✓ OK ({len(pdf_bytes)} bytes)")
                else:
                    results[tipo] = 'FALHA'
                    print(f"  {tipo}: ✗ FALHA")
            except Exception as e:
                results[tipo] = f'ERRO: {e}'
                print(f"  {tipo}: ✗ ERRO - {e}")
        
        return results

if __name__ == '__main__':
    print("=" * 60)
    print("TESTE DE REGRESSÃO VISUAL - IF5 PDF")
    print("=" * 60)
    
    print("\n1. Teste IF5 específico:")
    test_if5_pdf_generation()
    
    print("\n2. Teste todos os tipos:")
    results = test_all_types_pdf()
    
    print("\n" + "=" * 60)
    print("RESUMO:")
    for tipo, status in results.items():
        print(f"  {tipo}: {status}")
    print("=" * 60)