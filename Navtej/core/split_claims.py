"""Split a claims .jsonl into n shards, round robin (line 1 -> part 1, line 2 -> part 2, ..., line n+1 -> part 1),
so every shard gets an even mix of claims. Shards are written as <name>.part<i>of<n>.jsonl, by default in a
shards/ folder next to the claims file. If those shards already exist with exactly this content, nothing is rewritten.
  python core/split_claims.py subsets/subset_210.jsonl 2
  -> subsets/shards/subset_210.part1of2.jsonl, subsets/shards/subset_210.part2of2.jsonl
  python core/split_claims.py subsets/subset_210.jsonl 3 /content/shards      (other output folder)"""
import sys
from pathlib import Path

if len(sys.argv) not in (3, 4): raise SystemExit(__doc__)
src, n = Path(sys.argv[1]), int(sys.argv[2])
out_dir = Path(sys.argv[3]) if len(sys.argv) == 4 else src.parent / "shards"
if n < 1: raise SystemExit("n must be at least 1")
lines = [l if l.endswith("\n") else l + "\n" for l in open(src, encoding="utf-8") if l.strip()]
parts = {out_dir / f"{src.stem}.part{i + 1}of{n}.jsonl": "".join(lines[i::n]) for i in range(n)}
if all(p.exists() and p.read_text(encoding="utf-8") == text for p, text in parts.items()):
    print(f"already split into {n} shards in {out_dir}, nothing to do")
    raise SystemExit(0)
out_dir.mkdir(parents=True, exist_ok=True)
for p, text in parts.items():
    p.write_text(text, encoding="utf-8")
    print(f"{text.count(chr(10))} claims -> {p}")
