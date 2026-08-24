#!/usr/bin/env python3
"""Merge a batch of translations into i18n/cy.json, refusing silent mistakes."""
import json, os, re, sys
import cy_lib as L

TAGS = re.compile(r'<[^>]+>|⟦\d+⟧')


def tags(s):
    return [t for t in TAGS.findall(s)]


def main():
    path = os.path.join(L.ROOT, 'i18n', 'cy.json')
    table = L.load('cy.json')
    batch = json.load(open(sys.argv[1], encoding='utf-8'))

    known = set()
    for name in L.pages():
        html = open(os.path.join(L.ROOT, name), encoding='utf-8').read()
        known |= {L.mask(html[a:b])[0] for a, b in L.segments(html)}
        known |= {L.norm(v) for _, _, v in L.jsonld_spans(html)}

    bad = []
    for en, cy in batch.items():
        if en not in known:
            bad.append(f'not a unit on any page: {en!r}')
        elif tags(en) != tags(cy):
            bad.append(f'markup changed:\n    en {tags(en)}\n    cy {tags(cy)}\n    {en!r}')
        elif not cy.strip():
            bad.append(f'empty: {en!r}')
    if bad:
        print('\n'.join(bad[:20]), file=sys.stderr)
        print(f'\n{len(bad)} rejected, nothing written', file=sys.stderr)
        return 1

    table.update(batch)
    json.dump(table, open(path, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1, sort_keys=True)
    print(f'{len(batch)} merged, {len(table)} total', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
