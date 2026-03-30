# SoulsPerMin

A small desktop calculator for **Souls per minute** and related game values. Pick a run length from **1 to 60 minutes** with a slider or numeric input; all totals update live.

Built with **Python** and **PySide6** (Qt), packaged as a Windows executable with **PyInstaller**.

## Requirements

- **Python 3.10+** (3.12+ recommended)
- Windows, macOS, or Linux (the UI is cross-platform; builds below are documented for Windows)

## Install

```bash
git clone <your-repo-url>
cd Dl_SoulsPerMin
python -m venv .venv
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux:**

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Build a standalone executable (Windows)

Install build tools:

```powershell
pip install -r requirements-dev.txt
```

This project builds from the spec file by default (recommended).

Place your icon at:

- `assets/app.ico`

Then build using the spec:

```powershell
pyinstaller SoulsPerMin.spec
```

Output: `dist\SoulsPerMin.exe` (uses `assets/app.ico` via `SoulsPerMin.spec`)

If you want to bypass the spec file for a one-off build:

```powershell
pyinstaller --onefile --windowed --icon="assets/app.ico" --name SoulsPerMin main.py
```

## What it calculates (overview)

| Label | Rule (summary) |
|--------|----------------|
| **Trooper** | `116 + 1.16 × minutes` |
| **Wave** | Trooper × 4 |
| **2 person share** | Wave × 0.54 |
| **Boxes** | `0` before 2 minutes; then `23 + 2 × minutes` |
| **Box Run** | Boxes × 4 |
| **Tier 1–3 Denizen** | Linear formulas per tier (see constants in `main.py`) |
| **Camps / church / combo / Tripple** | Combinations of Tier 1–3 values |
| **Wave**-adjacent and **Boxes** rows | As labeled in the app |

Exact constants and formulas live in `main.py` (e.g. `BASE`, `PER_MINUTE`, `boxes_total`, `denizen_totals`, camp definitions).

## Project layout

| Path | Purpose |
|------|---------|
| `main.py` | Application entry point and UI |
| `requirements.txt` | Runtime dependency (`PySide6`) |
| `requirements-dev.txt` | Includes PyInstaller for building the `.exe` |
| `SoulsPerMin.spec` | PyInstaller spec for reproducible builds |
| `dist/` | Generated folder when you build the executable (ignored by git) |
| `build/` | PyInstaller intermediate output (ignored by git) |

## License

See [LICENSE](LICENSE). Third-party libraries (PySide6 / Qt, PyInstaller) have their own licenses.

## Contributing

Issues and pull requests are welcome. For code changes, match the existing style in `main.py` and keep UI changes focused and testable by running `python main.py` locally.
