"""Load project venv packages when launched with system Python (no pygubu)."""
import os
import sys
from pathlib import Path


def _venv_paths(root: Path):
    venv_root = root / "venv"
    if sys.platform == "win32":
        venv_py = venv_root / "Scripts" / "python.exe"
        site_packages = venv_root / "Lib" / "site-packages"
    else:
        venv_py = venv_root / "bin" / "python"
        site_packages = (
            venv_root
            / "lib"
            / f"python{sys.version_info.major}.{sys.version_info.minor}"
            / "site-packages"
        )
    return venv_root, venv_py, site_packages


def _pygubu_importable():
    try:
        import pygubu  # noqa: F401
        return True
    except ImportError:
        return False


def ensure_venv():
    root = Path(__file__).resolve().parent
    venv_root, venv_py, site_packages = _venv_paths(root)

    if _pygubu_importable():
        return

    # Prefer sys.path injection so Cursor/debugpy can keep using /bin/python.
    if site_packages.is_dir():
        site = str(site_packages)
        if site not in sys.path:
            sys.path.insert(0, site)
        if _pygubu_importable():
            return

    in_venv = Path(sys.prefix).resolve() == venv_root.resolve()
    debugging = "debugpy" in sys.modules
    # argv[0] must be the venv python path, not resolve() to /usr/bin/python3,
    # or Python ignores pyvenv.cfg and re-exec loops without pygubu.
    if venv_py.is_file() and not in_venv and not debugging:
        os.execv(str(venv_py), [str(venv_py), *sys.argv])

    sys.stderr.write(
        "pygubu is not installed. From the project directory run:\n"
        "  python3 -m venv venv && venv/bin/pip install -r requirements.txt\n"
    )
    raise SystemExit(1)


ensure_venv()
