"""Overnight job queue for Colab. Started in the background by sqljudge_colab.ipynb.

For each job (judge + builder, setup C, all 1,000 claims):
  * skips it if its results file in Drive already has 1,000 valid rows
  * makes sure Ollama is up, downloads the models, runs run_judge.py (which resumes by itself)
  * removes rows that failed only because of infrastructure (Ollama down, connection errors),
    so those claims are retried instead of being counted as wrong; up to 3 attempts per job
  * if a model cannot be downloaded, logs it and moves on to the next job
Everything is logged to <drive>/queue_log.txt.
"""
import argparse, json, os, subprocess, time, urllib.request, datetime

INFRA = ("connect", "refused", "502", "503", "504", " 500", "not found", "serverdisconnected",
         "remoteprotocolerror", "readtimeout", "apitimeout", "timed out")

def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log(base, msg):
    line = f"{now()}  {msg}"
    print(line, flush=True)
    with open(f"{base}/queue_log.txt", "a", encoding="utf-8") as f:
        f.write(line + "\n")

def safe(s):
    return s.replace(":", "_").replace("/", "_")

def out_path(base, job):
    return f"{base}/results/{safe(job['judge'])}__C__{safe(job['builder'])}.jsonl"

def read_rows(path):
    rows = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for l in f:
                try:
                    rows.append(json.loads(l))
                except Exception:
                    pass  # a half-written last line after a crash
    return rows

def is_infra_failure(r):
    return (not r.get("verdict")) and any(k in (r.get("error") or "").lower() for k in INFRA)

def clean(path):
    """Rewrite the file without infra failures and broken lines. Returns (kept, removed)."""
    rows = read_rows(path)
    keep = [r for r in rows if not is_infra_failure(r)]
    seen, uniq = set(), []
    for r in keep:
        if r["claim_id"] not in seen:
            seen.add(r["claim_id"]); uniq.append(r)
    if os.path.exists(path):
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for r in uniq:
                f.write(json.dumps(r, default=str) + "\n")
        os.replace(tmp, path)
    return len(uniq), len(rows) - len(uniq)

def ollama_up():
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5).read()
        return True
    except Exception:
        return False

def ensure_ollama(base, env):
    if ollama_up():
        return True
    log(base, "Ollama not responding, starting it")
    subprocess.Popen("nohup ollama serve >> /content/ollama.log 2>&1 &", shell=True, env=env)
    for _ in range(30):
        time.sleep(2)
        if ollama_up():
            return True
    log(base, "Ollama did not start")
    return False

def pull(base, model, env):
    rc = subprocess.call(f"ollama pull {model} >> /content/pull.log 2>&1", shell=True, env=env)
    log(base, f"pull {model}: {'ok' if rc == 0 else 'FAILED rc=' + str(rc)}")
    return rc == 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True); ap.add_argument("--drive", required=True)
    ap.add_argument("--db-root", required=True); ap.add_argument("--code", default="/content/sqljudge/code")
    a = ap.parse_args()
    jobs = json.load(open(a.jobs))
    env = dict(os.environ, OLLAMA_CONTEXT_LENGTH="16384", OLLAMA_MAX_LOADED_MODELS="2")
    os.makedirs(f"{a.drive}/results", exist_ok=True); os.makedirs(f"{a.drive}/logs", exist_ok=True)
    log(a.drive, f"queue started with {len(jobs)} jobs")
    for job in jobs:
        out = out_path(a.drive, job)
        name = os.path.basename(out)[:-6]
        for attempt in range(1, 5):
            kept, removed = clean(out)
            if removed:
                log(a.drive, f"{name}: removed {removed} infrastructure failures, they will be retried")
            if kept >= 1000:
                log(a.drive, f"{name}: complete (1000 claims)")
                break
            if attempt == 4:
                log(a.drive, f"{name}: stopped after 3 attempts with {kept} claims, check logs/{name}.log")
                break
            if not ensure_ollama(a.drive, env):
                time.sleep(60); continue
            if not pull(a.drive, job["judge"], env):
                break
            if job.get("backend", "openai") == "openai" and not pull(a.drive, job["builder"], env):
                break
            log(a.drive, f"{name}: attempt {attempt}, starting at {kept} claims done")
            cmd = (f'python -u run_judge.py --claims subsets/test-public.jsonl --db-root "{a.db_root}" '
                   f'--model {job["judge"]} --condition C --builder {job["builder"]} '
                   f'--builder-backend {job.get("backend", "openai")} --builder-template {job.get("template", "omnisql")} '
                   f'--out "{out}" >> "{a.drive}/logs/{name}.log" 2>&1')
            t0 = time.time()
            rc = subprocess.call(cmd, shell=True, cwd=a.code, env=env)
            log(a.drive, f"{name}: run ended rc={rc} after {round((time.time() - t0) / 60, 1)} min")
    log(a.drive, "queue finished")

if __name__ == "__main__":
    main()
