from app import create_app
app = create_app()
rules = sorted([(r.rule, r.endpoint) for r in app.url_map.iter_rules()], key=lambda x: x[0])
for rule, endpoint in rules:
    if 'investig' in rule or 'obito' in rule:
        print(f'{rule:60s} -> {endpoint}')
