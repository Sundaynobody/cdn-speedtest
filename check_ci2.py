import urllib.request, json

url = "https://api.github.com/repos/Sundaynobody/cdn-speedtest/actions/runs?per_page=10&status=completed"
req = urllib.request.Request(url, headers={"User-Agent": "curl"})
data = json.loads(urllib.request.urlopen(req).read())
for r in data.get("workflow_runs", []):
    print(f"{r['id']}: {r['name']} - {r['conclusion']} - branch={r['head_branch']} sha={r['head_sha'][:8]}")

print("\n--- Failed runs ---")
failed = [r for r in data.get("workflow_runs", []) if r["conclusion"] == "failure"]
if failed:
    r = failed[0]
    print(f"Checking failed run: {r['id']}")
    jobs_url = r["jobs_url"]
    req = urllib.request.Request(jobs_url, headers={"User-Agent": "curl"})
    jobs = json.loads(urllib.request.urlopen(req).read())
    for j in jobs.get("jobs", []):
        print(f"  Job: {j['name']} - {j['conclusion']}")
        steps = j.get("steps", [])
        for s in steps:
            c = s.get("conclusion", "?")
            if c in ("failure", "cancelled"):
                print(f"    Step: {s['name']} - {c}")
                # Get logs
                if s.get("log_url"):
                    log_url = s["log_url"]
                    req2 = urllib.request.Request(log_url, headers={"User-Agent": "curl"})
                    try:
                        logs = urllib.request.urlopen(req2, timeout=10).read().decode("utf-8", errors="replace")
                        print(f"    Logs (last 20 lines):")
                        lines = logs.strip().split("\n")
                        for line in lines[-20:]:
                            print(f"      {line}")
                    except Exception as e:
                        print(f"      (log fetch failed: {e})")
else:
    print("No failed runs found")
