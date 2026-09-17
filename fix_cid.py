#!/usr/bin/env python
# Script to fix the cid.get() issue in obito_service.py

with open('app/services/obito_service.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "cid = dados.get('causa_morte_cid', '').strip().upper()" in line:
        # Replace both occurrences with the fixed version
        new_lines.append("cid = (dados.get('causa_morte_cid') or '').strip().upper()\n")
    else:
        new_lines.append(line)

with open('app/services/obito_service.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Fixed cid.get() issue')