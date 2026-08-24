import fitz, os, sys

base = sys.argv[1] if len(sys.argv) > 1 else r'D:\Obito'
files = [
    ('MIF', 'MIF-ficha-investigacao-obito-mulher-idade-fertil-identificacao-possivel-obito-materno.pdf'),
    ('MATERNO', 'M1-ficha-investigacao-obito-materno-servico-saude-ambulatorial.pdf'),
    ('MAL_DEFINIDA', 'IOCMD-ficha-investigacao-obito-causa-mal-definida.pdf'),
    ('INFANTIL_FETAL', 'IF5-ficha-investigacao-obito-infantil-fetal-sintese-conclusoes-recomendacoes.pdf'),
    ('INFANTIL', 'I1-ficha-investigacao-obito-infantil-servico-saude-ambulatorial.pdf'),
]

for tipo, fname in files:
    path = os.path.join(base, fname)
    doc = fitz.open(path)
    print(f'\n=== {tipo} ({doc.page_count}p) ===')
    for i, page in enumerate(doc):
        pw, ph = page.rect.width, page.rect.height
        print(f'\n-- Page {i+1} ({pw:.0f}x{ph:.0f}) --')
        paths = page.get_drawings()
        lines = []
        for path in paths:
            rect = path.get('rect')
            if not rect: continue
            x0, y0, x1, y1 = rect.x0, rect.y0, rect.x1, rect.y1
            w, h = x1-x0, y1-y0
            # Horizontal lines (underlines, h < 1pt)
            if h < 1 and h >= -1 and w > 30:
                xp = x0/pw*100
                yp = y0/ph*100
                wp = w/pw*100
                lines.append((yp, xp, wp, w))
        # Group and sort by Y
        lines.sort()
        prev_y = -1
        for yp, xp, wp, w in lines:
            if abs(yp - prev_y) < 0.3: continue  # dedup
            prev_y = yp
            print(f'  Y:{yp:5.1f}% X:{xp:5.1f}% W:{wp:5.1f}% ({w:.0f}pt)')
    doc.close()
