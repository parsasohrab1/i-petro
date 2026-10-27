"""Word submission sheet: say that new article repositories are private (GitHub shows 404 to anyone without access).
python docs/abstracts/patch_private_note.py <index.html in> <index.html out>"""
import sys
src, out = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()
old = '["Repository status",prod.new?"New repository created for this article.":'
new = '["Repository status",prod.new?"New repository created for this article. It is PRIVATE: GitHub shows a 404 page to anyone who is not a collaborator (ask the owner for access; the repository is also hidden from search and from the repository list).":'
assert s.count(old) == 1, s.count(old)
open(out, "w", encoding="utf-8").write(s.replace(old, new))
print("ok")
