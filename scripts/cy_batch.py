#!/usr/bin/env python3
"""Turn an index->Welsh mapping into a batch keyed by the real source strings.

Indices refer to the current i18n/cy.todo.json, so transcribing long English
sentences by hand is never necessary and cannot go wrong.
"""
import json, os, sys
import cy_lib as L

todo = json.load(open(sys.argv[1], encoding='utf-8'))
pairs = json.load(open(sys.argv[2], encoding='utf-8'))
out = {}
for k, cy in pairs.items():
    out[todo[int(k)]] = cy
json.dump(out, open(sys.argv[3], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'{len(out)} pairs', file=sys.stderr)
