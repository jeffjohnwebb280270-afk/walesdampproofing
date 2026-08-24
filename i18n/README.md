# Welsh build

`cy/` is generated, never hand-edited. English is the source of truth for
structure; `cy.json` supplies the prose.

    python3 scripts/build_cy.py

That writes `cy/*.html`, patches the English pages with their `hreflang`
pairing and language switcher, and lists anything still untranslated in
`cy.todo.json`.

Adding translations:

    python3 scripts/cy_batch.py i18n/cy.todo.json <index-map.json> batch.json
    python3 scripts/cy_merge.py batch.json

`cy_merge.py` refuses a batch whose keys are not real units on a page, or
whose translation changes the inline markup — the two mistakes that would
otherwise ship silently.

After editing any English page, re-run the build so the two languages cannot
drift apart.
