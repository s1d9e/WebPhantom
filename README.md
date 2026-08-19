<div align="center">

# `WEBPHANTOM`

### Browser Forensics Decoder — Recover Web Activity from Dead Machines

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-00ff88?style=flat-square)
![Status](https://img.shields.io/badge/Status-Alpha-orange?style=flat-square)

```
  ░▒▓ WEBPHANTOM ▓▒░

  "The browser never truly forgets."
```

</div>

---

## What it does

WebPhantom extracts and reconstructs **full web browsing activity** from disk images, forensic dumps, or live mounts — even when history was cleared, the browser was uninstalled, or the drive was formatted.

It works by scanning **residual artifacts** that browsers leave behind and that nobody ever cleans properly:

| Artifact | Source | What it reveals |
|---|---|---|
| **SQLite WAL/journal** | `History`, `Cookies`, `Login Data` | Deleted history entries still in WAL files |
| **Favicon cache** | `Favicons`, `Service Worker` | Sites visited (even without history) |
| **GPU cache** | Shader cache, decoded images | Thumbnails, rendered page fragments |
| **DNS cache** | OS-level resolver cache | Domains resolved recently |
| **HSTS preload** | Browser internals | Sites forcing HTTPS (high-confidence visits) |
| **Session Restore** | `Session Store` | Exact tabs open at crash/shutdown |
| **IndexedDB** | Web app local storage | PWA data, full app states |
| **Web Archive** | `Session Storage`, `Local Storage` | Site-specific data snapshots |

## Supported browsers

- [ ] Chrome / Chromium
- [ ] Firefox
- [ ] Safari
- [ ] Edge
- [ ] Brave

## Supported OS targets

- [ ] Linux
- [ ] Windows
- [ ] macOS

## Install

```bash
git clone https://github.com/s1d9e/WebPhantom.git
cd WebPhantom
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Usage

```bash
# Scan a mounted disk image
webphantom scan /mnt/evidence/disk0

# Extract artifacts from a specific browser
webphantom scan /mnt/evidence/disk0 --browser chrome

# Export timeline as JSON
webphantom scan /mnt/evidence/disk0 --output timeline.json --format json

# Live mode on running system
webphantom live
```

## Output example

```
[2026-08-19 14:32:01] chrome   HISTORY   https://github.com/s1d9e   title="GitHub"   last_visit=2026-08-17T09:14:22Z
[2026-08-19 14:32:01] chrome   FAVICON   https://mail.google.com   (deleted from history, recovered from favicon cache)
[2026-08-19 14:32:02] firefox  WAL       https://internal.corp.com  title="Dashboard"   (recovered from WAL journal)
[2026-08-19 14:32:02] system   DNS       api.telegram.org          resolved from OS dns cache
```

## Roadmap

- [ ] Core SQLite artifact parser
- [ ] WAL journal recovery engine
- [ ] Browser profile auto-detection
- [ ] Timeline reconstruction
- [ ] JSON/HTML report export
- [ ] CLI with rich output
- [ ] GPU cache image extraction
- [ ] Plugin system for custom artifacts

## License

MIT
