"""
Build CDNSpeedTest for the current platform.

Architecture notes:
  macOS:  run with --arch universal2  to create a fat binary (Intel+Apple Silicon)
  Windows: PyInstaller builds ONLY for the host Python's architecture.
           Use CI/CD (GitHub Actions) or an ARM64 Windows VM for cross-arch builds.
  Linux:   Same limitation — use Docker+QEMU or CI/CD for cross-arch builds.
"""
import os, sys, platform, shutil, subprocess, tempfile, argparse

ARCH_MAP = {"AMD64": "x86_64", "x86_64": "x86_64", "x86": "x86",
            "ARM64": "arm64", "aarch64": "arm64", "armv7l": "armv7"}

def build():
    ap = argparse.ArgumentParser(description="Build CDNSpeedTest")
    ap.add_argument("--arch", default=None,
                    help="Target architecture (macOS: 'universal2', 'x86_64', 'arm64'; ignored on Windows/Linux)")
    args = ap.parse_args()

    src = os.path.dirname(os.path.abspath(__file__))
    system = platform.system()
    host_arch = ARCH_MAP.get(platform.machine(), platform.machine())
    target_arch = host_arch

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
        if args.arch:
            print(f"WARNING: --arch is ignored on Windows. Building for host architecture: {host_arch}")
    elif system == "Darwin":
        flags.extend(["--windowed"])
        if args.arch == "universal2":
            flags.extend(["--target-arch", "universal2"])
            target_arch = "universal2"
        elif args.arch in ("x86_64", "arm64"):
            flags.extend(["--target-arch", args.arch])
            target_arch = args.arch
        elif args.arch:
            print(f"ERROR: Unsupported --arch '{args.arch}'. Use: universal2, x86_64, arm64")
            shutil.rmtree(tmp, ignore_errors=True)
            sys.exit(1)
    elif system == "Linux":
        if args.arch:
            print(f"WARNING: --arch is ignored on Linux. Building for host architecture: {host_arch}")

    for f in ("icon.ico", "icon.png"):
        p = os.path.join(tmp, f)
        if os.path.exists(p):
            flags.extend(["--add-data", f"{p}{sep}."])

    name = f"CDNSpeedTest_{target_arch}"
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
