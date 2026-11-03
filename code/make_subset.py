"""Balanced subset of ClaimDB's public test set (n per label), fixed seed, so all runs use identical claims.
  python make_subset.py test-public.jsonl 50 subsets/subset_150.jsonl"""
import json, random, sys
src, per, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
claims = [json.loads(l) for l in open(src, encoding="utf-8")]
picked = []
for L in ["ENTAILED", "CONTRADICTED", "NOT ENOUGH INFO"]:   # per-label seeded shuffle: smaller subsets are nested in larger ones
    pool = sorted((c for c in claims if c["label"] == L), key=lambda c: c["claim_id"])
    random.Random(13).shuffle(pool); picked += pool[:per]
picked.sort(key=lambda c: c["claim_id"])
with open(out, "w", encoding="utf-8") as f:
    for c in picked: f.write(json.dumps(c) + "\n")
print(f"{len(picked)} claims -> {out}")
