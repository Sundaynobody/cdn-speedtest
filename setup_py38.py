"""Install packages for Python 3.8 (patches SSL to work around SCHANNEL bug)."""
import ssl, urllib.request, json, os, sys, subprocess, tempfile, shutil

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
ssl._create_default_https_context = lambda: ctx

def get_wheel_url(pkg):
    r = urllib.request.urlopen(f"https://pypi.org/pypi/{pkg}/json")
    data = json.loads(r.read())
    for u in data["urls"]:
        if u["packagetype"] == "bdist_wheel":
            return u["url"]
    return None

PKGS = [
    "pip",
    "setuptools",
    "wheel",
    "certifi",
    "urllib3",
    "charset-normalizer",
    "idna",
    "requests",
    "ttkbootstrap",
    "Pillow",
    "PyInstaller",
]

tmp = tempfile.mkdtemp()
try:
    for pkg in PKGS:
        url = get_wheel_url(pkg)
        if not url:
            print(f"SKIP {pkg}: no wheel")
            continue
        name = url.rsplit("/", 1)[-1]
        path = os.path.join(tmp, name)
        print(f"DL {pkg} -> {name}")
        urllib.request.urlretrieve(url, path)
        print(f"  OK ({os.path.getsize(path)} bytes)")

    wheels = [os.path.join(tmp, f) for f in os.listdir(tmp) if f.endswith(".whl")]
    print(f"\nInstalling {len(wheels)} packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-index"] + wheels)
    print("All installed.")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
