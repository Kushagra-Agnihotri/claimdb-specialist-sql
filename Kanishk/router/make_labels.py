"""Pathway #3, step 1: simple / complex labels for every ClaimDB claim.

The label comes from the gold SQL of the BIRD question each claim was generated from
(BIRD-source.jsonl). It is computed once and shared by every judge.

  strict  simple = one table, no nested SELECT, no set operations (UNION/INTERSECT/EXCEPT), no window functions
  loose   simple = at most two tables (one join), with the same other conditions

Output: router/labels.jsonl with one line per claim:
  claim_id, split (train / val / test), db_name, text (claim + hint, the router's only input),
  n_tables, nested, simple_strict, simple_loose
Train and validation use ClaimDB's train split on the 69 BIRD databases that are NOT in the test set
(validation = 7 whole databases held out). Test = the 1,000 public-test claims on the 11 dev databases.
"""
import argparse, json, random
import sqlglot
from sqlglot import exp

def sql_features(sql):
    try:
        tree = sqlglot.parse_one(sql, read="sqlite")
    except Exception:
        return None
    tables = {t.name.lower() for t in tree.find_all(exp.Table)}
    selects = list(tree.find_all(exp.Select))
    setops = any(True for _ in tree.find_all(exp.Union, exp.Intersect, exp.Except))
    window = any(True for _ in tree.find_all(exp.Window))
    nested = len(selects) > 1 or setops or window
    return {"n_tables": len(tables), "nested": nested,
            "simple_strict": int(len(tables) <= 1 and not nested),
            "simple_loose": int(len(tables) <= 2 and not nested)}

def text_of(c):
    hint = (c.get("extra_info") or "").strip()
    return f"Claim: {c['claim']}" + (f"\nExtra Information: {hint}" if hint else "")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True); ap.add_argument("--train", required=True)
    ap.add_argument("--test", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--val-dbs", type=int, default=7); ap.add_argument("--seed", type=int, default=13)
    a = ap.parse_args()
    src = {}
    for l in open(a.source, encoding="utf-8"):
        d = json.loads(l); src[d["bird_id"]] = d
    test = [json.loads(l) for l in open(a.test, encoding="utf-8") if l.strip()]
    test_dbs = {c["db_name"] for c in test}
    train = [json.loads(l) for l in open(a.train, encoding="utf-8") if l.strip()]
    train = [c for c in train if c["db_name"] not in test_dbs]          # keep the 11 test databases unseen
    dbs = sorted({c["db_name"] for c in train})
    random.Random(a.seed).shuffle(dbs)
    val_dbs = set(dbs[:a.val_dbs])
    feats, n_bad = {}, 0
    with open(a.out, "w", encoding="utf-8") as f:
        for split_name, rows in (("train", train), ("test", test)):
            for c in rows:
                b = c["bird_id"]
                if b not in feats:
                    feats[b] = sql_features(src[b]["SQL"])
                ft = feats[b]
                if ft is None:
                    n_bad += 1; continue
                split = "val" if split_name == "train" and c["db_name"] in val_dbs else split_name
                f.write(json.dumps({"claim_id": c["claim_id"], "split": split, "db_name": c["db_name"],
                                    "label": c.get("label"), "text": text_of(c), **ft}) + "\n")
    print(f"validation databases: {sorted(val_dbs)}")
    print(f"unparseable gold SQL skipped: {n_bad}")

if __name__ == "__main__":
    main()
