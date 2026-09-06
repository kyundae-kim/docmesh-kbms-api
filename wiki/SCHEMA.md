# Wiki Schema

## Domain
RESTful API development for knowledge management systems.

## Conventions
- File names: lowercase, hyphens, no spaces (for example, `api-versioning.md`).
- Every wiki page starts with YAML frontmatter.
- Use `[[wikilinks]]` to link between pages; new pages should have at least 2 outbound links.
- When updating a page, bump the `updated` date.
- Every new page must be added to `index.md` under the correct section.
- Every action must be appended to `log.md`.
- Raw sources are immutable; corrections belong in wiki pages.
- On pages synthesizing 3+ sources, add `^[raw/articles/source-file.md]` markers to source-specific claim paragraphs.

## Frontmatter
```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query | summary
tags: [from taxonomy below]
sources: [raw/articles/source-name.md]
confidence: high | medium | low
contested: true
contradictions: [other-page-slug]
---
```

`confidence`, `contested`, and `contradictions` are optional. Use them for uncertain, opinion-heavy, fast-moving, or conflicting claims.

## Raw Source Frontmatter
```yaml
---
source_url: https://example.com/article
ingested: YYYY-MM-DD
sha256: <hex digest of the raw content below the frontmatter>
---
```

Compute `sha256` over the body after the closing `---`, excluding frontmatter.

## Tag Taxonomy
- API: `rest`, `http`, `endpoint`, `versioning`
- Architecture: `architecture`, `design-pattern`, `microservices`, `integration`
- Data: `database`, `schema`, `search`, `storage`
- Quality: `security`, `performance`, `reliability`, `testing`, `observability`
- Delivery: `deployment`, `operations`, `documentation`
- Context: `knowledge-management`, `entity`, `comparison`, `decision`

Every page tag must appear in this taxonomy. Add a tag here before using it.

## Page Thresholds
- Create a page when an entity or concept appears in 2+ sources or is central to one source.
- Add to an existing page when a source mentions something already covered.
- Do not create pages for passing mentions or topics outside the domain.
- Split pages over approximately 200 lines into focused sub-topics with cross-links.
- Archive fully superseded pages under `_archive/` and remove them from the index.

## Update Policy
When new information conflicts with existing content:
1. Check dates; newer sources generally supersede older ones.
2. If genuinely contradictory, preserve both positions with dates and sources.
3. Mark the contradiction in frontmatter with `contradictions:` and `contested: true`.
4. Flag the conflict for review in lint output.

## Navigation and Logging
- `index.md` lists every wiki page by type with a one-line summary and total count.
- `log.md` is append-only and records every create, ingest, update, query, lint, archive, or delete action.
- Rotate `log.md` after 500 entries by renaming it `log-YYYY.md` and starting a new log.
