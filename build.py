import os, sys, platform, shutil, subprocess, tempfile

ARCH_MAP = {"AMD64": "x86_64", "x86_64": "x86_64", "x86": "x86",
            "ARM64": "arm64", "aarch64": "arm64", "armv7l": "armv7"}

def build():
    src = os.path.dirname(os.path.abspath(__file__))
    system = platform.system()
    arch = ARCH_MAP.get(platform.machine(), platform.machine())
    tmp = tempfile.mkdtemp(prefix="cdn-")

    for f in ("icon.ico", "icon.png"):
        p = os.path.join(src, f)
        if os.path.exists(p):
            shutil.copy2(p, os.path.join(tmp, f))

    flags = ["--onefile", "--noconfirm"]
    sep = ";" if system == "Windows" else ":"

    if system == "Windows":
        flags.extend(["--noconsole"])
        ico = os.path.join(tmp, "icon.ico")
        if os.path.exists(ico):
            flags.extend(["--icon", ico])
    elif system == "Darwin":
        flags.extend(["--windowed"])
    elif system == "Linux":
        pass

    for f in ("icon.ico", "icon.png"):
        p = os.path.join(tmp, f)
        if os.path.exists(p):
            flags.extend(["--add-data", f"{p}{sep}."])

    name = f"CDNSpeedTest_{arch}"
    if system == "Windows":
        name += ".exe"

    flags.extend(["--name", name,
                  "--distpath", os.path.join(src, "dist"),
                  "--workpath", os.path.join(tmp, "build"),
                  "--specpath", tmp,
                  os.path.join(src, "main.py")])

    subprocess.check_call(["pyinstaller"] + flags)
    shutil.rmtree(tmp, ignore_errors=True)

    out = os.path.join(src, "dist", name)
    print(f"\nOK: {out}")
    return out

if __name__ == "__main__":
    build()
