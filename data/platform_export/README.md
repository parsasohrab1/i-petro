# platform_export — payload for the artifact database

The dashboard has TWO update paths; this directory serves method one:

1. **Artifact database (claude.ai)** — apply these documents with the ArtifactData tool
   (see "How to apply" below).
2. **Repo commits** — data/tenders.json and data/articles_export/article_registry.json are
   loaded by the dashboard itself (loadRepoData in platform/index.html); update them with
   scripts/dashboard_update.py or scripts/refresh_tenders.py and just commit+push. This works
   even when the artifact DB is offline or stale.

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
# or with a small prompt-driven instruction file (tenders and/or articles):
python3 scripts/dashboard_update.py instruction.json
```

Team-side edits (status, history, analysis) made in the dashboard survive the apply: the exported
tender docs carry only listing fields (TENDER_KEEP) and the analysis fields are preserved by
import_tracking / the dashboard merge (mergeTendersRepo in platform/index.html).
