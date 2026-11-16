"""Pathway #3, step 3: train the router classifiers on the frozen claim embeddings.

Three tasks (positive class = "send this claim to the cheap path"):
  complexity_strict : gold SQL uses one table, nothing nested
  complexity_loose  : gold SQL uses at most two tables, nothing nested
  answerability     : the claim is NOT ENOUGH INFO (cannot be checked from the database)
Three models per task:
  linear : logistic regression (no hidden layer), the "does an MLP help?" baseline
  mlp2   : 2-layer MLP (768 -> 256 -> 1), ReLU, L2 regularisation, early stopping
  mlp3   : 3-layer MLP (768 -> 256 -> 128 -> 1)
Train on 62 BIRD train databases; the decision threshold is tuned on the 7 held-out validation databases
(max balanced accuracy); test = the 1,000 public-test claims on the 11 unseen dev databases.
Outputs: router/preds/<task>__<model>.csv (claim_id, prob, pred) and router/router_metrics.json
"""
import json, os, time
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, balanced_accuracy_score, f1_score, accuracy_score

HERE = os.path.dirname(os.path.abspath(__file__))

def targets(rows, task):
    if task == "complexity_strict": return np.array([r["simple_strict"] for r in rows])
    if task == "complexity_loose":  return np.array([r["simple_loose"] for r in rows])
    if task == "answerability":     return np.array([int(r["label"] == "NOT ENOUGH INFO") for r in rows])
    raise ValueError(task)

def models(seed=13):
    return {
        "linear": LogisticRegression(max_iter=3000, C=1.0, class_weight="balanced"),
        "mlp2": MLPClassifier(hidden_layer_sizes=(256,), alpha=1e-3, batch_size=256, learning_rate_init=1e-3,
                              max_iter=200, early_stopping=True, validation_fraction=0.1, n_iter_no_change=8,
                              random_state=seed),
        "mlp3": MLPClassifier(hidden_layer_sizes=(256, 128), alpha=1e-3, batch_size=256, learning_rate_init=1e-3,
                              max_iter=200, early_stopping=True, validation_fraction=0.1, n_iter_no_change=8,
                              random_state=seed),
    }

def best_threshold(y, p):
    grid = np.linspace(0.05, 0.95, 91)
    scores = [balanced_accuracy_score(y, (p >= t).astype(int)) for t in grid]
    return float(grid[int(np.argmax(scores))])

def main(emb_name="emb_nomic-embed-text.npy"):
    rows = [json.loads(l) for l in open(os.path.join(HERE, "labels.jsonl"), encoding="utf-8") if l.strip()]
    X = np.load(os.path.join(HERE, emb_name)).astype(np.float32)
    assert len(X) == len(rows), (X.shape, len(rows))
    split = np.array([r["split"] for r in rows])
    ids = np.array([r["claim_id"] for r in rows])
    tr, va, te = split == "train", split == "val", split == "test"
    scaler = StandardScaler().fit(X[tr])
    Xs = scaler.transform(X)
    os.makedirs(os.path.join(HERE, "preds"), exist_ok=True)
    report = {}
    for task in ["complexity_strict", "complexity_loose", "answerability"]:
        y = targets(rows, task)
        for name, m in models().items():
            t0 = time.time()
            Xtr, ytr = Xs[tr], y[tr]
            if name.startswith("mlp"):          # MLPClassifier has no class weights: balance by oversampling
                rng = np.random.default_rng(13)
                pos, neg = np.where(ytr == 1)[0], np.where(ytr == 0)[0]
                small, big = (pos, neg) if len(pos) < len(neg) else (neg, pos)
                idx = np.concatenate([big, rng.choice(small, size=len(big), replace=True)])
                rng.shuffle(idx); Xtr, ytr = Xtr[idx], ytr[idx]
            m.fit(Xtr, ytr)
            pv, pt = m.predict_proba(Xs[va])[:, 1], m.predict_proba(Xs[te])[:, 1]
            thr = best_threshold(y[va], pv)
            yhat = (pt >= thr).astype(int)
            res = {"threshold": thr, "val_auc": roc_auc_score(y[va], pv), "test_auc": roc_auc_score(y[te], pt),
                   "test_bal_acc": balanced_accuracy_score(y[te], yhat), "test_acc": accuracy_score(y[te], yhat),
                   "test_f1_pos": f1_score(y[te], yhat), "test_pos_rate_true": float(y[te].mean()),
                   "test_pos_rate_pred": float(yhat.mean()), "train_seconds": round(time.time() - t0, 1)}
            report[f"{task}__{name}"] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in res.items()}
            with open(os.path.join(HERE, "preds", f"{task}__{name}.csv"), "w", encoding="utf-8") as f:
                f.write("claim_id,prob,pred\n")
                for cid, p, h in zip(ids[te], pt, yhat):
                    f.write(f"{cid},{p:.6f},{h}\n")
            print(f"{task:18s} {name:6s} test AUC {res['test_auc']:.3f}  bal.acc {res['test_bal_acc']:.3f}  "
                  f"F1 {res['test_f1_pos']:.3f}  ({res['train_seconds']} s)", flush=True)
    json.dump(report, open(os.path.join(HERE, "router_metrics.json"), "w"), indent=1)
    print("saved router_metrics.json and preds/", flush=True)

if __name__ == "__main__":
    main()
