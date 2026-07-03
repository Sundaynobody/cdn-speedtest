import urllib.request, json
import time

url = "https://api.github.com/repos/Sundaynobody/cdn-speedtest/actions/runs?per_page=5&event=push"
req = urllib.request.Request(url, headers={"User-Agent": "curl"})
data = json.loads(urllib.request.urlopen(req).read())
for r in data.get("workflow_runs", []):
    print(f"ID={r['id']} status={r['status']} conclusion={r['conclusion']} sha={r['head_sha'][:8]} branch={r['head_branch']}")
    if r["status"] == "completed" and r["conclusion"] == "failure":
        print(f"  FAILED! Getting logs...")
        jobs_url = r["jobs_url"]
        req2 = urllib.request.Request(jobs_url, headers={"User-Agent": "curl"})
        jobs = json.loads(urllib.request.urlopen(req2).read())
        for j in jobs.get("jobs", []):
            for s in j.get("steps", []):
                if s.get("conclusion") == "failure":
                    log_url = s.get("log_url", "")
                    if log_url:
                        req3 = urllib.request.Request(log_url, headers={"User-Agent": "curl"})
                        logs = urllib.request.urlopen(req3, timeout=10).read().decode("utf-8", errors="replace")
                        print(f"  Step: {s['name']}")
                        for line in logs.strip().split("\n")[-30:]:
                            print(f"    {line}")
