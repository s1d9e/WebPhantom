<div align="center">

<img src="https://raw.githubusercontent.com/s1d9e/WebPhantom/main/assets/banner.png" width="100%">

# WebPhantom

### Browser Forensics Decoder

**Recover web activity from dead machines — even after history was cleared, the browser was uninstalled, or the drive was formatted.**

![CI](https://img.shields.io/github/actions/workflow/status/s1d9e/WebPhantom/ci.yml?branch=main&label=CI&logo=github)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-19_passing-2ECC71?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-00ff88?style=flat-square)
![Ruff](https://img.shields.io/badge/Ruff-0_errors-000000?style=flat-square)
![Mypy](https://img.shields.io/badge/Mypy-0_errors-964EE8?style=flat-square)

<br>

[Installation](#installation) • [Usage](#usage) • [Features](#features) • [How it works](#how-it-works) • [Roadmap](#roadmap) • [Contributing](#contributing)

</div>

---

## Overview

WebPhantom is a digital forensics tool that extracts and reconstructs **full web browsing activity** from disk images, forensic dumps, or live mounts.

Browsers never truly delete your data. When you "clear history," the old entries often remain in SQLite WAL files, favicon caches, and session storage. WebPhantom recovers this invisible footprint.

```
┌─────────────────────────────────────────────────────────────────┐
│                        WEBPHANTOM                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐                │
│   │  Disk    │────▶│ Scanner  │────▶│ Timeline │                │
│   │  Image   │     │  Engine  │     │ Builder  │                │
│   └──────────┘     └──────────┘     └──────────┘                │
│                         │                                        │
│                         ▼                                        │
│                  ┌──────────────┐                                │
│                  │  WAL Recovery │                               │
│                  │   Engine      │                               │
│                  └──────────────┘                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Installation

```bash
git clone https://github.com/s1d9e/WebPhantom.git
cd WebPhantom
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

---

## Usage

### Quick Start

```bash
# Detect browser profiles on your system
webphantom detect

# Scan a mounted disk image
webphantom scan /mnt/evidence/disk0

# Scan specific browser only
webphantom scan /mnt/evidence/disk0 --browser chrome

# Export results as JSON
webphantom scan /mnt/evidence/disk0 --output timeline.json --format json
```

### WAL Recovery

```bash
# Inspect WAL file
webphantom walinfo /path/to/History

# Attempt to recover deleted entries
webphantom walrecovery /path/to/History urls
```

### Example Output

```
$ webphantom scan ~/.mozilla/firefox

WebPhantom v0.1.0
Scanning: /home/user/.mozilla/firefox

============================================================
Scan Complete
============================================================

Profiles scanned: 1
Browsers found: firefox
Total artifacts: 847
WAL recovered: 23

                           Artifacts Found                           
┏━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Type     ┃ Browser ┃ URL                          ┃ Title       ┃
┡━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ history  │ firefox │ https://github.com/s1d9e     │ GitHub      │
│ wal      │ firefox │ https://internal.corp.com    │ Dashboard   │
│ favicon  │ firefox │ https://mail.google.com      │ Gmail       │
│ cookie   │ firefox │ .google.com/auth             │ SID         │
└──────────┴─────────┴──────────────────────────────┴─────────────┘
```

---

## Features

<table>
<tr>
<td width="50%">

### Core Features

- **SQLite Artifact Parser** — Parse browser databases efficiently
- **WAL Recovery Engine** — Recover deleted history from WAL files
- **Browser Detection** — Auto-discover profiles across OS
- **Timeline Reconstruction** — chronological view of activity
- **JSON/Text Export** — integrate with other tools

</td>
<td width="50%">

### Supported Browsers

- ✅ **Chrome / Chromium**
- ✅ **Firefox**
- ✅ **Edge** (Chromium-based)
- ✅ **Brave**
- 🔜 Safari

</td>
</tr>
</table>

---

## How It Works

WebPhantom scans for residual artifacts that browsers leave behind:

| Artifact | Source | What It Reveals |
|----------|--------|-----------------|
| **SQLite WAL** | `History`, `Cookies` | Deleted entries still in write-ahead log |
| **Favicon Cache** | `Favicons`, Service Worker | Sites visited (even without history) |
| **DNS Cache** | OS resolver cache | Recently resolved domains |
| **Session Restore** | `Session Store` | Tabs open at crash/shutdown |
| **IndexedDB** | Web app storage | PWA data and app states |

### Supported Operating Systems

| OS | Status |
|----|--------|
| Linux | ✅ Full support |
| macOS | ✅ Full support |
| Windows | ✅ Full support |

---

## Architecture

```
src/webphantom/
├── core/
│   ├── parser.py          # SQLite database parser
│   ├── wal_recovery.py    # WAL journal recovery engine
│   ├── detector.py        # Browser profile detection
│   └── models.py          # Data models
├── browsers/
│   ├── chrome.py          # Chrome/Edge/Brave parser
│   └── firefox.py         # Firefox parser
└── cli/
    └── main.py            # Command-line interface
```

---

## Roadmap

- [x] Core SQLite artifact parser
- [x] WAL journal recovery engine
- [x] Browser profile auto-detection
- [x] Chrome/Chromium parser
- [x] Firefox parser
- [x] CLI with rich output
- [x] JSON/Text export
- [x] SQL injection prevention
- [x] Comprehensive test suite
- [x] CI/CD pipeline
- [ ] Timeline visualization
- [ ] HTML report generation
- [ ] GPU cache image extraction
- [ ] Plugin system for custom artifacts
- [ ] Safari support

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run linter
ruff check src/

# Type check
mypy src/ --ignore-missing-imports
```

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

---

<div align="center">

**Built with ❤️ for digital forensics**

[![GitHub](https://img.shields.io/badge/GitHub-s1d9e-181717?style=flat-square&logo=github)](https://github.com/s1d9e)

</div>
