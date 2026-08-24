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

## Strings inside `<script>`

`cy.script.json` is an explicit allowlist of user-facing JS string literals —
form validation, the button's sending state, the wall diagram's readouts.
Only literals listed there are substituted; guessing which literal in a
script is prose would eventually rewrite a selector and break the page.

Welsh is full of apostrophes, so the quote delimiter is escaped on
substitution, and the build parses every generated page's inline JS with
`node --check` and fails if it does not parse.

## What stays in English

- The trading name, so the business's name/address/phone stays consistent
  for local search.
- schema.org `name` values — an organisation, a person, a city, a
  certificate — so the structured data names the same entity in both
  languages. `description` localises, and so do `BreadcrumbList` names,
  which are navigation labels rather than identifiers.
