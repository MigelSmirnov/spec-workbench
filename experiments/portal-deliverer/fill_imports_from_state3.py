"""Write the State 3 dependency table into 65_imports.json as decided uses.

Until the State 7 notes exist, the drafted imports table holds only the types of
signatures; the projector needs every edge. Each row of 30_modules.md
"Dependencies" becomes a use of the consumer module scope with basis
"author: 30_modules.md Dependencies"; generated modules are skipped.

    python -I experiments/portal-deliverer/fill_imports_from_state3.py examples/portal-deliverer

Once 80_notes.md exists the script refuses: from then on the imports closure
is the Workbench's step (tools/design_imports.py --draft, then the author's
decisions and --coverage), and this script would accept its pending
candidates for the author. On 2026-11-20 it was run after the notes and the
closure stayed open with 207 findings nobody saw.
"""
import json,re,sys
from pathlib import Path
case=Path(sys.argv[1])
if (case/'80_notes.md').is_file():
    raise SystemExit(
        f"fill_imports_from_state3: refused: {case/'80_notes.md'} exists, so the State 3 table is no longer "
        f"the imports decision. Run: python tools/design_imports.py {case} --draft, decide its pending "
        f"candidates, then python tools/design_imports.py {case} --coverage")
p=case/'65_imports.json'; d=json.loads(p.read_text())
text=(case/'30_modules.md').read_text()
table=text.split("## Dependencies",1)[1].split("\n## ",1)[0]
contracts=json.loads((case/'60_contracts.json').read_text())['contracts']
exc={e['symbol'] for e in json.loads((case/'60_exception_taxonomy.json').read_text())['exceptions']}
mm=lambda n:'models' if n=='domain_models' else n
generated={'deliverer_router','system_clock','data_provider'}
added=0
for c,pv,syms in re.findall(r"^\| `([a-z_]+)` \| `([a-z_]+)` \| (.+) \|$", table, re.M):
    c,pv=mm(c),mm(pv)
    if c in generated: continue
    scope=d['scopes'].setdefault(c,{"uses":[],"rejected":[]})
    have={(u['symbol'],u['provider']) for k,v in d['scopes'].items() if k==c or k.startswith(c+'.') for u in v.get('uses',[])}
    for s in re.findall(r"`([A-Za-z_]\w*)`",syms):
        if (s,pv) in have: continue
        kind='calls' if s in contracts else ('reads' if re.fullmatch(r'[A-Z][A-Z0-9_]+',s) else ('creates' if s in exc else 'annotates'))
        scope['uses'].append({"symbol":s,"provider":pv,"as":kind,"basis":"author:30_modules.md Dependencies, the State 3 decision until the State 7 notes are written"})
        added+=1
for k,v in list(d['scopes'].items()):
    for pend in v.pop('pending',[]) or []:
        prov=mm(pend['provider'])
        if pend['symbol']=='*':
            continue  # a knows-candidate: the table rows above already carry the module's uses
        if (pend['symbol'],prov) not in {(u['symbol'],u['provider']) for u in v['uses']}:
            v['uses'].append({"symbol":pend['symbol'],"provider":prov,"as":"creates" if pend['symbol'] in exc else "annotates","basis":"contract"})
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
print('added',added)
