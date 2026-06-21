from __future__ import annotations

import os
import subprocess
import sys


def resolve_output_path(dir_: str, base: str, suffix: str, overwrite: bool) -> str:
    out = os.path.join(dir_, f"{base}{suffix}.pdf")
    if overwrite:
        return out
    counter = 1
    while os.path.exists(out):
        out = os.path.join(dir_, f"{base}{suffix}_{counter}.pdf")
        counter += 1
        if counter > 9999:
            break
    return out


def open_in_system(path: str):
    if sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.run(["open", path], check=False)
    else:
        subprocess.run(["xdg-open", path], check=False)
