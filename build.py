"""
Build CDNSpeedTest for the current platform.

Architecture notes:
  macOS:  run with --arch universal2  to create a fat binary (Intel+Apple Silicon)
  Windows: use --python to specify a different arch Python.
           Needs separate Python installs (x86 + x64) on the same machine.
  Linux:   Use Docker+QEMU or CI/CD for cross-arch builds.
"""
import os, sys, platform, shutil, subprocess, tempfile, argparse, struct

ARCH_MAP = {"AMD64": "x86_64", "x86_64": "x86_64", "x86": "x86",
            "ARM64": "arm64", "aarch64": "arm64", "armv7l": "armv7"}


def _detect_arch(python_exe):
    """Return arch label for the given python executable."""
    out = subprocess.check_output([python_exe, "-c",
        "import platform, struct; print(platform.machine(), struct.calcsize('P')*8)"],
        text=True).strip()
    machine, bits = out.split()
    return ARCH_MAP.get(machine, machine) + (" (32-bit)" if bits == "32" else "")


def build():
    ap = argparse.ArgumentParser(description="Build CDNSpeedTest")
    ap.add_argument("--python", default=sys.executable,
                    help="Python interpreter path (default: current python)")
    ap.add_argument("--arch", default=None,
                    help="macOS: 'universal2', 'x86_64', 'arm64'. On Windows use --python instead.")
    args = ap.parse_args()

    python_exe = os.path.abspath(args.python)
    if not os.path.exists(python_exe):
        print(f"ERROR: Python not found: {python_exe}")
        sys.exit(1)

    src = os.path.dirname(os.path.abspath(__file__))
    system = platform.system()
    host_arch = _detect_arch(python_exe)
    target_arch = host_arch

    print(f"Python: {python_exe}  =>  {host_arch}")

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

    subprocess.check_call([python_exe, "-m", "PyInstaller"] + flags)
    shutil.rmtree(tmp, ignore_errors=True)

    out = os.path.join(src, "dist", name)
    print(f"\nOK: {out}")
    return out


def _find_python_by_arch(target_arch):
    """Auto-find common Python install paths for the given arch on Windows."""
    if platform.system() != "Windows":
        return None
    local = os.path.expanduser(r"~\AppData\Local\Programs\Python")
    prog = os.environ.get("ProgramFiles", r"C:\Program Files")
    prog86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    patterns = []
    if target_arch == "x86":
        patterns.extend([
            os.path.join(local, f"Python{suffix}-32")
            for suffix in [f"3{n}" for n in range(13, 8, -1)]
        ])
        patterns.extend([
            os.path.join(prog86, f"Python{suffix}-32")
            for suffix in [f"3{n}" for n in range(13, 8, -1)]
        ])
    for base in patterns:
        exe = os.path.join(base, "python.exe")
        if os.path.exists(exe):
            return exe
    return None


if __name__ == "__main__":
    # Auto-resolve --arch x86 to a 32-bit Python on Windows
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--arch", default=None)
    ap.add_argument("--python", default=None)
    pre, _ = ap.parse_known_args()

    if pre.arch == "x86" and platform.system() == "Windows" and not pre.python:
        found = _find_python_by_arch("x86")
        if found:
            print(f"Auto-detected 32-bit Python: {found}")
            sys.argv = [a for a in sys.argv if a != "--arch" and a != "x86"]
            sys.argv.extend(["--python", found])
        else:
            print("ERROR: No 32-bit Python found. Install Python 3.x (32-bit) from python.org")
            print("Tip: during install, check 'Install for all users' or keep default path.")
            print("      Typical path: %LOCALAPPDATA%\\Programs\\Python\\Python313-32\\python.exe")
            sys.exit(1)

    build()
