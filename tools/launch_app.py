"""Launch the source app without a console, preserving startup errors."""
import ctypes
import datetime
import os
from pathlib import Path
import subprocess
import sys


def launch(root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parents[1]
    logs = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "ConvertitoreUniversale" / "logs"
    path = logs / ("app-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".log")
    try:
        logs.mkdir(parents=True, exist_ok=True)
        executable = Path(sys.executable)
        if os.name == "nt" and executable.name.lower() == "pythonw.exe":
            executable = executable.with_name("python.exe")
        with path.open("w", encoding="utf-8") as output:
            result = subprocess.run(
                [str(executable), str(root / "app" / "main.py")],
                cwd=root, stdout=output, stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        if result.returncode:
            raise RuntimeError(f"Avvio fallito (codice {result.returncode}).")
        return 0
    except Exception as error:
        message = f"{error}\n\nIl registro completo si trova in:\n{path}"
        if os.name == "nt":
            ctypes.windll.user32.MessageBoxW(None, message, "Convertitore Universale", 16)
        elif sys.stderr is not None:
            print(message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(launch())
