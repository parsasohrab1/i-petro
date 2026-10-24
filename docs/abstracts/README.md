# Abstract drafts for the Articles tab

* `platform/abstracts_seed.json` – formats (`profiles`), one draft per venue id (`abstracts`) and the product/repository map (`products`, `branch`). Edit text here.
* `embed_in_page.py` – copies that JSON into `platform/index.html` (between the `ABS-START` / `ABS-END` markers). Run it after every edit.
* `build_abstracts.py VENUES_JSON [OUT_DIR]` – writes one Word file per venue to `outputs/abstracts/`. `VENUES_JSON` is `ARTICLES_SEED` dumped as JSON:
  `node -e 'const s=require("fs").readFileSync("platform/index.html","utf8");const a=s.indexOf("const ARTICLES_SEED = [")+22,b=s.indexOf("\n];",a)+2;require("fs").writeFileSync("venues.json",JSON.stringify(eval(s.slice(a,b))))'`

Rules of the drafts: numbers are `[placeholders]`, never results; length limits are typical for the venue family and must be confirmed in the venue's author guidelines.
Every venue has its own product: a new product has its own repository (`articles-*`), an existing product has the branch `article-submission-content`.
