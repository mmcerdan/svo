import re
import sys

# Read the saved output
with open(r'C:\Users\mm.cerdan\.local\share\opencode\tool-output\tool_06be4ae870017PWV9YGBGoxyRU', 'r', encoding='utf-8') as f:
    content = f.read()

# The CID data is all on one line, format: "A00 Cólera A00.0 Cólera devida a..."
# Pattern: code followed by description (2+ chars)
pattern = r'([A-TV-Z]\d{2}(?:\.\d{1,4})?)\s+([A-ZÀ-Ú][^A-TV-Z\d]*?(?=[A-TV-Z]\d{2}(?:\.\d{1,4})?\s|$))'
matches = re.findall(pattern, content)

print(f"Found {len(matches)} CID codes")

# Remove duplicates, keep order
seen = set()
unique_cids = []
for code, desc in matches:
    code = code.strip()
    desc = desc.strip().rstrip(' ')
    if code not in seen and len(desc) > 3:
        seen.add(code)
        unique_cids.append((code, desc))

print(f"Unique CIDs: {len(unique_cids)}")
print("Sample:")
for code, desc in unique_cids[:10]:
    print(f"  {code}: {desc[:70]}")
print("...")
for code, desc in unique_cids[-5:]:
    print(f"  {code}: {desc[:70]}")

# Save to file for import
with open('cid_data.py', 'w', encoding='utf-8') as f:
    f.write('CIDS = [\n')
    for code, desc in unique_cids:
        # Escape quotes in description
        safe_desc = desc.replace('"', '\\"')
        f.write(f'    ("{code}", "{safe_desc}"),\n')
    f.write(']\n')

print(f"\nSaved {len(unique_cids)} CIDs to cid_data.py")