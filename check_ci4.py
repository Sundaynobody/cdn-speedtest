import urllib.request, json

# Check if the workflow exists
url = "https://api.github.com/repos/Sundaynobody/cdn-speedtest/actions/workflows"
req = urllib.request.Request(url, headers={"User-Agent": "curl"})
data = json.loads(urllib.request.urlopen(req).read())
for w in data.get("workflows", []):
    print(f"Workflow: {w['name']} - state={w['state']} path={w['path']}")
    if w.get("badge_url"):
        print(f"  Badge: {w['badge_url']}")
