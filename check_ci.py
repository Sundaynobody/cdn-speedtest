import urllib.request, json

url = "https://api.github.com/repos/Sundaynobody/cdn-speedtest/actions/runs?per_page=5"
req = urllib.request.Request(url, headers={"User-Agent": "curl"})
data = json.loads(urllib.request.urlopen(req).read())
for r in data.get("workflow_runs", []):
    print(f"{r['id']}: {r['name']} - {r['status']}/{r['conclusion']} - branch={r['head_branch']} sha={r['head_sha'][:8]}")

# Get the latest failed run's logs
failed = [r for r in data.get("workflow_runs", []) if r["conclusion"] == "failure"]
if failed:
    r = failed[0]
    print(f"\nLatest failed: {r['id']}")
    # Try to get jobs
    jobs_url = r["jobs_url"]
    req = urllib.request.Request(jobs_url, headers={"User-Agent": "curl"})
    jobs = json.loads(urllib.request.urlopen(req).read())
    for j in jobs.get("jobs", []):
        print(f"  Job: {j['name']} - {j['status']}/{j['conclusion']}")
        for s in j.get("steps", []):
            conclusion = s.get("conclusion", "?")
            if conclusion == "failure":
                print(f"    Failed step: {s['name']}")
