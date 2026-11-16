"""Pathway #3, step 2: turn every claim (claim + hint) into a fixed vector with a small frozen text encoder.

Uses Ollama's embedding endpoint (default model nomic-embed-text, 768 numbers per claim) on the local GPU.
Input:  router/labels.jsonl   Output: router/emb_<model>.npy (rows in the same order as labels.jsonl)
Saves a checkpoint every 4,096 claims, so a crash resumes instead of restarting.
"""
import argparse, json, os, time, urllib.request
import numpy as np

def embed_batch(url, model, texts):
    body = json.dumps({"model": model, "input": texts, "truncate": True}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read())["embeddings"]
        except Exception as e:
            print(f"retry {attempt + 1}: {e!r}", flush=True); time.sleep(10)
    raise RuntimeError("embedding failed 5 times")

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default=os.path.join(here, "labels.jsonl"))
    ap.add_argument("--model", default="nomic-embed-text")
    ap.add_argument("--prefix", default="classification: ")   # nomic task prefix
    ap.add_argument("--url", default="http://localhost:11434/api/embed")
    ap.add_argument("--batch", type=int, default=64)
    a = ap.parse_args()
    texts = [a.prefix + json.loads(l)["text"] for l in open(a.labels, encoding="utf-8") if l.strip()]
    out = os.path.join(here, f"emb_{a.model.replace(':', '_').replace('/', '_')}.npy")
    ckpt = out + ".partial.npy"
    done = np.load(ckpt) if os.path.exists(ckpt) else None
    vecs = [done] if done is not None else []
    start = 0 if done is None else len(done)
    print(f"{len(texts)} texts, starting at {start}", flush=True)
    t0, since = time.time(), 0
    for i in range(start, len(texts), a.batch):
        vecs.append(np.asarray(embed_batch(a.url, a.model, texts[i:i + a.batch]), dtype=np.float32))
        since += a.batch
        if since >= 4096 or i + a.batch >= len(texts):
            arr = np.concatenate(vecs); np.save(ckpt, arr); vecs = [arr]; since = 0
            print(f"{len(arr)}/{len(texts)} done, {len(arr) / (time.time() - t0 + 1e-9):.0f} per s", flush=True)
    arr = np.concatenate(vecs)
    assert arr.shape[0] == len(texts), (arr.shape, len(texts))
    np.save(out, arr); os.remove(ckpt)
    print("saved", out, arr.shape, flush=True)

if __name__ == "__main__":
    main()
