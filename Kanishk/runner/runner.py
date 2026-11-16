"""Tonight's job runner. Double-click run_tonight.bat once; it keeps running.

Reads tonight_queue.txt (one shell command per line, run in sqljudge/code),
runs each new line once, in order, and logs everything to tonight_logs/.
Lines starting with '#' are ignored. Lines starting with 'BG:' start in the
background (used for model downloads). A line 'STOP' ends the runner.
The queue file can be edited while this runs; new lines are picked up.
Close the black window to stop everything.
"""
import os, subprocess, time, datetime, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))          # ...\sqljudge
CODE = os.path.join(HERE, "code")
QUEUE = os.path.join(HERE, "tonight_queue.txt")
DONE = os.path.join(HERE, "tonight_done.txt")
LOGS = os.path.join(HERE, "tonight_logs")
STATUS = os.path.join(HERE, "tonight_status.txt")
os.makedirs(LOGS, exist_ok=True)

def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def status(msg):
    with open(STATUS, "a", encoding="utf-8") as f:
        f.write(f"{now()}  {msg}\n")
    print(f"{now()}  {msg}", flush=True)

def key(line):
    return hashlib.sha1(line.encode("utf-8")).hexdigest()[:12]

def done_keys():
    if not os.path.exists(DONE):
        return set()
    with open(DONE, encoding="utf-8") as f:
        return {l.split()[0] for l in f if l.strip()}

status("runner started")
# make sure the Ollama server is up before any job (after a reboot it may not be running yet)
for attempt in range(12):
    rc = subprocess.call("ollama list", shell=True, cwd=CODE,
                         stdout=open(os.path.join(LOGS, "startup_ollama.log"), "a", encoding="utf-8"),
                         stderr=subprocess.STDOUT)
    if rc == 0:
        status("ollama is up")
        break
    status(f"ollama not ready (rc={rc}), retrying in 10 s")
    time.sleep(10)
time.sleep(5)
while True:
    try:
        lines = []
        if os.path.exists(QUEUE):
            with open(QUEUE, encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
        todo = [l for l in lines if key(l) not in done_keys()]
        if not todo:
            time.sleep(30)
            continue
        line = todo[0]
        k = key(line)
        if line == "STOP":
            status("STOP found, runner exiting")
            break
        log = os.path.join(LOGS, f"{k}.log")
        if line.startswith("BG:"):
            cmd = line[3:].strip()
            status(f"start BG [{k}] {cmd}")
            subprocess.Popen(cmd, shell=True, cwd=CODE, stdout=open(log, "a", encoding="utf-8"),
                             stderr=subprocess.STDOUT)
            rc = "bg"
        else:
            status(f"start [{k}] {line}")
            t0 = time.time()
            with open(log, "a", encoding="utf-8") as lf:
                rc = subprocess.call(line, shell=True, cwd=CODE, stdout=lf, stderr=subprocess.STDOUT)
            status(f"end   [{k}] rc={rc} after {round((time.time()-t0)/60,1)} min")
        with open(DONE, "a", encoding="utf-8") as f:
            f.write(f"{k} rc={rc} {now()} {line}\n")
    except Exception as e:  # never die; report and retry
        status(f"runner error: {e!r}")
        time.sleep(30)
