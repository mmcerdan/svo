#!/usr/bin/env python3
"""
Script de migração para popular novos campos IF5 em investigações existentes
Versão 2 - Com todos os novos campos IF5
"""
import sys
sys.path.insert(0, '/opt/sistema-obito')

from app import create_app
from app.extensions import db
from app.models import Investigacao, InvestigacaoCampo
from app.utils.campos import get_campos_padrao_investigacao

app = create_app()

def migrar_investigacoes():
    with app.app_context():
        print("=" * 60)
        print("MIGRAÇÃO DE CAMPOS IF5 - v2")
        print("=" * 60)
        
        # Busca todas as investigações
        invs = Investigacao.query.all()
        print(f"Total de investigações: {len(invs)}")
        
        total_adicionados = 0
        
        for inv in invs:
            campos_padrao = get_campos_padrao_investigacao(inv.tipo)
            existing = {c.nome_campo for c in inv.campos}
            missing = [c for c in campos_padrao if c not in existing]
            
            if missing:
                print(f"\nInvestigação {inv.id} ({inv.tipo}): adicionando {len(missing)} campos")
                for nome in missing:
                    campo = InvestigacaoCampo(
                        investigacao_id=inv.id,
                        nome_campo=nome,
                        valor=''
                    )
                    db.session.add(campo)
                total_adicionados += len(missing)
            else:
                print(f"Investigação {inv.id} ({inv.tipo}): OK ({len(existing)} campos)")
        
        if total_adicionados > 0:
            db.session.commit()
            print(f"\n✓ Total de campos adicionados: {total_adicionados}")
        else:
            print("\n✓ Nenhum campo novo necessário")
        
        # Verificação final
        print("\n--- VERIFICAÇÃO FINAL ---")
        for inv in Investigacao.query.all():
            count = len(inv.campos.all())
            lb_count = len([c for c in inv.campos if 'Lista Brasileira' in c.nome_campo])
            est_count = len([c for c in inv.campos if 'Estabelecimento' in c.nome_campo])
            print(f"  Inv {inv.id:3d} ({inv.tipo:18s}): {count:4d} campos | LB: {lb_count:2d} | Est: {est_count:2d}")

if __name__ == '__main__':
    migrar_investigacoes()