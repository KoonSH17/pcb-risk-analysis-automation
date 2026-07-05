# PCB CAM Risk Analysis Automation

> GUI-driven Python automation for PCB reliability risk classification.  
> Reduces manual report generation from **~2 hours to ~5 minutes** per board.

---

## Background

PCB reliability risk analysis requires engineers to manually open an ODB++ file in a CAM tool, navigate multiple menus to assign risk classes (RC0–RC4) to netlist entries, run a reliability check, export top and bottom layer CSVs, capture board screenshots, and consolidate everything into a report — for every board, every ECN cycle.

This tool automates the entire workflow end-to-end via a one-click GUI. The engineer selects the ODB file; the script handles everything else.

---

## What It Does

```
Engineer selects ODB++ file via GUI
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│           PCB CAM Risk Analysis Automation              │
│                                                         │
│  Step 1: Launch PCB CAM Tool and load ODB file          │
│  Step 2: Open Netlist tool (CAD Net)                    │
│  Step 3: Detect column positions (DPI-aware)            │
│  Step 4: Assign Risk Classes RC1–RC4 to nets            │
│  Step 5: Run Reliability Check                          │
│  Step 6: Export Top and Bottom reliability CSVs         │
│  Step 7: Capture Top and Bottom board screenshots       │
│  Step 8: Process CSVs with Pandas (map RC codes,        │
│           filter passing nets)                          │
│  Step 9: Consolidate into formatted Excel report        │
└─────────────────────────────────────────────────────────┘
              │
              ▼
  Excel report (.xlsx) + Board screenshots (.png)
  stored in: PCB CAM OUTPUT / [ODB filename] /
```

---

## Key Technical Features

- **DPI-aware window targeting** — detects monitor scaling factor at runtime using `ctypes.windll.shcore`; all click coordinates are scaled accordingly, ensuring correct targeting on 125%, 150%, and 200% display scaling
- **Dynamic column detection** — scans CAD Net header control at runtime to locate `clearanceClass` and `netComment` column midpoints; no hardcoded pixel coordinates
- **Multi-window orchestration** — manages simultaneous handles across PCB CAM main window, CAD Net netlist tool, Reliability Check dialog, Check Results window, and file export dialogs via `pywinauto`
- **Risk class assignment loop** — iterates RC1–RC4, filters by class in both `clearanceClass` and `netComment` columns, select-all, right-click assigns via keyboard navigation
- **Bilateral screenshot capture** — captures top and bottom board views with and without component overlay; bottom view is horizontally mirrored to match physical orientation
- **Pandas post-processing** — maps `Given Value` (µm thresholds) to RC codes, filters out passing nets (Value == Given Value), outputs clean Top and Bottom sheets with autofilter

---

## Output

For each ODB file processed:

```
PCB CAM OUTPUT/
└── [ODB_filename]/
    ├── [ODB_filename].xlsx          # Consolidated report
    │   ├── Top Reliability Check   # Sheet 1 — top layer violations
    │   └── Bot Reliability Check   # Sheet 2 — bottom layer violations
    ├── Top_View/
    │   ├── [ODB_filename]_top.png           # Top layer view
    │   └── [ODB_filename]_comp_+_top.png    # Top layer + components overlay
    └── Bot_View/
        ├── [ODB_filename]_bot.png           # Bottom layer view (mirrored)
        └── [ODB_filename]_comp_+_bot.png    # Bottom + components overlay (mirrored)
```

### Risk Class mapping

| Given Value | Risk Class |
|-------------|-----------|
| 200 µm      | RC0        |
| 400 µm      | RC1        |
| 600 µm      | RC2        |
| 800 µm      | RC3        |
| 1000 µm     | RC4        |

---

## Requirements

- Windows OS
- Python 3.x
- PCB CAM Tool installed at `C:\CAx\App\PCBCAMTool\PCB-CAM-Tool.exe`
- ODB++ files located under `C:\CAx\Prj\`

```bash
pip install -r requirements.txt
```

Dependencies: `pywinauto`, `pypiwin32`, `pandas`, `Pillow`, `xlsxwriter`, `comtypes`

---

## Usage

```bash
python pcb_cam_auto.py
```

1. GUI window opens — click **Load file into PCB CAM**
2. File explorer opens — select your ODB++ file
3. Click OK on the confirmation popup — **do not touch mouse or keyboard** while running
4. Script runs automatically (~5 minutes)
5. Output location shown in final popup

### Distributing as an executable

The repo includes a PyInstaller spec file to package the tool as a standalone `.exe`:

```bash
pyinstaller pcb_cam_auto.spec
```

---

## Architecture

| File | Role |
|------|------|
| `pcb_cam_auto.py` | GUI layer — Tkinter window, button layout, entry point |
| `pcb_cam_auto_support.py` | Automation core — `pcb_run()` and `open_file()` functions |
| `pcb_cam_auto.spec` | PyInstaller packaging spec |
| `requirements.txt` | Python dependencies |

---

## Performance

| Metric | Manual | Automated |
|--------|--------|-----------|
| Time per board | ~2 hours | ~5 minutes |
| Risk class assignment steps | ~200 manual clicks | 0 |
| Screenshot capture | Manual, inconsistent | Automated, standardised |
| Report consolidation | Manual copy-paste | Auto-generated Excel |

---

## Known Limitations

- **Windows only** — relies on `pywinauto` and `ctypes.windll` (Windows API)
- **Fixed tool path** — PCB CAM Tool must be installed at the hardcoded path
- **No headless mode** — requires a visible desktop session; screen must not be locked during run
- **Single board per run** — processes one ODB file per execution

---

## Context

Built to eliminate a recurring manual bottleneck in PCB reliability reporting at a Tier-1 automotive electronics supplier. The tool was packaged as a standalone `.exe` and distributed to the engineering team for daily use.
