# Abstract drafts for the Articles tab

* `platform/abstracts_seed.json` – formats (`profiles`), one draft per venue id (`abstracts`) and the product/repository map (`products`, `branch`). Edit text here.
* `embed_in_page.py` – copies that JSON into `platform/index.html` (between the `ABS-START` / `ABS-END` markers). Run it after every edit.
* `build_abstracts.py VENUES_JSON [OUT_DIR]` – writes one Word file per venue to `outputs/abstracts/`. `VENUES_JSON` is `ARTICLES_SEED` dumped as JSON:
  `node -e 'const s=require("fs").readFileSync("platform/index.html","utf8");const a=s.indexOf("const ARTICLES_SEED = [")+22,b=s.indexOf("\n];",a)+2;require("fs").writeFileSync("venues.json",JSON.stringify(eval(s.slice(a,b))))'`

Rules of the drafts: numbers are `[placeholders]`, never results; length limits are typical for the venue family and must be confirmed in the venue's author guidelines.
Every venue has its own product: a new product has its own repository (`articles-*`), an existing product has the branch `article-submission-content`.

## New abstracts from now on (one Word file per venue)
Every abstract written for a venue and its product gets **its own Word file**, not only the ZIP.
1. Add the draft to `platform/abstracts_seed.json` (`abstracts.<venue id>`; a product that is not in `products` can be given inline as `{"name","repo","new"}`) and run `build_abstracts.py` to write `outputs/abstracts/<id>_<venue>.docx`.
2. Make the button appear on the published page without republishing it: write the same record to the database document `settings/article_abstracts`, field `map.<venue id>`
   (`{title, abstract, keywords[], profile, product:{name,repo,new}, draft_note}`; `profile` is one of the keys of `profiles`). The page reads this document live, merges it with the built-in drafts, and offers
   `چکیده (Word)` for that row in every Articles tab plus the ZIP. Rows added by the team in the page work the same way (the venue id is the row id).
3. Keep the numbers as `[bracketed]` until the team has measured them, and respect the patent rule (no claimed method in the abstract).
