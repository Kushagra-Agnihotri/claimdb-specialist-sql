"""Merge shard results (one results.jsonl per worker) into a single results.jsonl.
Lines are put back in the order of the original claims file; a claim that appears twice keeps its first line.
  python core/merge_results.py subsets/subset_210.jsonl results/.../subset_210/results.jsonl \\
      results/.../subset_210.part1of2/results.jsonl results/.../subset_210.part2of2/results.jsonl [--delete-parts]
Arguments: the original claims file (for the order), the output file (folders are created), then the shard results.
--delete-parts removes the shard result folders, but only when the merged file has every claim. Shard paths that no
longer exist are skipped, so running it again after a successful merge just reports the existing merged file."""
import argparse, json, shutil
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("claims"); ap.add_argument("out"); ap.add_argument("parts", nargs="*")
ap.add_argument("--delete-parts", action="store_true")
a = ap.parse_args()
claims_file, out = Path(a.claims), Path(a.out)
order = [json.loads(l)["claim_id"] for l in open(claims_file, encoding="utf-8") if l.strip()]
parts = [Path(p) for p in a.parts if Path(p).exists()]

def ids(path):
    return {json.loads(l)["claim_id"] for l in open(path, encoding="utf-8") if l.strip()}

if not parts:
    if out.exists():
        have = ids(out) & set(order)
        print(f"no shard results left; {out} already has {len(have)} of {len(order)} claims")
        raise SystemExit(0 if len(have) == len(order) else 1)
    raise SystemExit("no shard results found and no merged file yet")

by_id, from_parts, dupes = {}, set(), 0
if out.exists():   # keep what an earlier merge already wrote (its shards may be gone)
    for l in open(out, encoding="utf-8"):
        if l.strip(): by_id.setdefault(json.loads(l)["claim_id"], l if l.endswith("\n") else l + "\n")
for p in parts:
    for l in open(p, encoding="utf-8"):
        if not l.strip(): continue
        cid = json.loads(l)["claim_id"]
        if cid in from_parts: dupes += 1   # same claim in two shard files (an earlier merge is not a duplicate)
        from_parts.add(cid)
        by_id.setdefault(cid, l if l.endswith("\n") else l + "\n")
out.parent.mkdir(parents=True, exist_ok=True)
tmp = out.with_suffix(".tmp")
with open(tmp, "w", encoding="utf-8") as f:
    f.writelines(by_id[c] for c in order if c in by_id)
tmp.replace(out)
missing = [c for c in order if c not in by_id]
extra = set(by_id) - set(order)
print(f"{len(order) - len(missing)} of {len(order)} claims -> {out}"
      + (f" | missing {len(missing)}" if missing else "") + (f" | duplicates dropped {dupes}" if dupes else "")
      + (f" | ignored {len(extra)} not in the claims file" if extra else ""))

if a.delete_parts:
    if missing:
        print(f"not deleting shard results: {len(missing)} claims still missing (rerun those shards, then merge again)")
    else:
        for p in parts:
            d = p.parent
            if ".part" in d.name and d.resolve() != out.parent.resolve():   # only ever remove shard folders
                shutil.rmtree(d); print(f"deleted {d}")
