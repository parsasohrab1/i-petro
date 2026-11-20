# platform_export — payload for the artifact database

The dashboard has TWO update paths; this directory serves method one:

1. **Artifact database (claude.ai)** — apply these documents with the ArtifactData tool
   (see "How to apply" below).
2. **Repo commits** — every repo-backed section is loaded by the dashboard itself (REPO_BASE in
   platform/index.html): data/tenders.json, data/events.json, data/investors.json,
   data/leads.json, data/partners.json, data/scholarships.json, data/patent_ops.json,
   data/papers.json, requests_seed.json, platform/products_seed.json and
   data/articles_export/article_registry.json. Update them with scripts/dashboard_update.py
   or scripts/refresh_tenders.py and just commit+push. This works even when the artifact DB
   is offline or stale. platform/index.html also carries an inline snapshot of all sections
   (window.REPO_SNAPSHOT, rebuilt by scripts/embed_dashboard_data.py), so updating the artifact
   HTML alone refreshes every section even when the artifact cannot fetch the data files.

- `manifest.json` — batches (max 50 writes each). Each entry: `{collection, doc_id, file_path}`;
  `file_path` is relative to the repository root.
- `market/data/tenders/<doc_id>.json` — one file per tender document (collection `market/data/tenders`).
- `settings/…` — settings documents (`settings/investor_mail` etc.).

## How to apply (method one)

1. Open the dashboard artifact session on claude.ai (the session that has the ArtifactData tool).
2. Read `manifest.json` and, batch by batch, write each file's JSON content into the artifact
   database at `collection` / `doc_id` (a batch = one ArtifactData write group of up to 50 docs).
3. Re-run after every collection refresh to pick up the latest snapshot.

## Regenerate locally

```bash
python3 -c "from agent import platform_sync; print(platform_sync.export())"
# or with a live collection run:
python3 scripts/refresh_tenders.py [hand_collected.json]
# or with a small prompt-driven instruction file (tenders, articles, events, investors, leads,
# scholarships, requests, patent_ops — see scripts/dashboard_update.py):
python3 scripts/dashboard_update.py instruction.json
```

Team-side edits (status, history, analysis) made in the dashboard survive the apply: the exported
tender docs carry only listing fields (TENDER_KEEP) and the analysis fields are preserved by
import_tracking / the dashboard merge (mergeRepo in platform/index.html).
