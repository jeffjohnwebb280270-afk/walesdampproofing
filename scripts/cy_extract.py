#!/usr/bin/env python3
"""Report every translatable unit, and which of them still lack Welsh."""
import json, os, sys
import cy_lib as L

def main():
    have = L.load('cy.json')
    seen, per_page = {}, {}
    for name in L.pages():
        html = open(os.path.join(L.ROOT, name), encoding='utf-8').read()
        units = [L.mask(html[a:b])[0] for a, b in L.segments(html)]
        units += [v for _, _, v in L.jsonld_spans(html)]
        units = [u for u in units if L.translatable(u)]
        per_page[name] = len(units)
        for u in units:
            seen[u] = seen.get(u, 0) + 1

    for name, n in sorted(per_page.items()):
        print(f'{n:5d}  {name}', file=sys.stderr)
    todo = [u for u in seen if u not in have]
    print(f'\n{len(seen)} unique units, {sum(len(u.split()) for u in seen)} words'
          f'\n{len(seen) - len(todo)} translated, {len(todo)} outstanding '
          f'({sum(len(u.split()) for u in todo)} words)\n', file=sys.stderr)
    json.dump(sorted(todo, key=lambda u: (-seen[u], u)), sys.stdout,
              ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main()
