# Obvious RPG — Development Environment Setup

> Complete guide to the Chrono Trigger ROM hacking development environment.

## Table of Contents

- [Overview](#overview)
- [Installed Tools](#installed-tools)
- [Tool Details](#tool-details)
- [Directory Structure](#directory-structure)
- [Build System](#build-system)
- [Workflow Guide](#workflow-guide)
- [Windows-Only Tools](#windows-only-tools)
- [Troubleshooting](#troubleshooting)

---

## Overview

This environment runs on **Debian Linux (trixie)** and provides a complete SNES ROM hacking toolkit for Chrono Trigger. Most tools run natively on Linux; Windows-only tools (like Temporal Flux) can run via Wine.

**Base Platform:** Debian GNU/Linux 13 (trixie), x86_64

---

## Installed Tools

### Assemblers

| Tool | Version | Platform | Purpose |
|------|---------|----------|---------|
| **asar** | 1.91 | Native Linux | Primary SNES assembler (65816, SPC700, SuperFX). Patch-oriented — designed for applying ASM patches to existing ROMs. |
| **wla-65816** | 10.7a | Native Linux | Alternative 65816 assembler. Part of WLA-DX multi-platform assembler suite. Good for building from scratch. |
| **wlalink** | — | Native Linux | Linker for WLA-DX assembler output. |

### Patchers

| Tool | Version | Platform | Purpose |
|------|---------|----------|---------|
| **flips** (Floating IPS) | v199 | Native Linux (built from source) | Creates and applies IPS and BPS patches. Gold standard for ROM patch distribution. |

### Emulators

| Tool | Version | Platform | Purpose |
|------|---------|----------|---------|
| **mednafen** | 1.32.1 | Native Linux | Multi-system emulator with accurate SNES emulation. Supports command-line operation for automated testing. |

### Hex / Binary Tools

| Tool | Purpose |
|------|---------|
| **xxd** | Hex dump and reverse hex dump (included with vim) |
| **hexedit** | Terminal-based hex editor for direct ROM editing |

### Wine (Windows Compatibility Layer)

| Tool | Version | Purpose |
|------|---------|---------|
| **wine** | 10.0 | Runs Windows-only ROM hacking tools (Temporal Flux, etc.) |

### Python Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| **Python** | 3.12 | Runtime for custom ROM tools |
| **bitstring** | 4.3.1 | Bit-level data manipulation |
| **construct** | 2.10.70 | Declarative binary data parsing/building |
| **Pillow** | 11.3.0 | Image processing (sprites, tilesets) |
| **numpy** | 1.26.4 | Array operations for tile/map data |
| **hexdump** | — | Hex dump utilities |

### Custom Tools

| Tool | Location | Purpose |
|------|----------|---------|
| **ct_rom_utils.py** | `tools/ct_rom_utils.py` | CT-specific ROM analysis: info, hexdump, compare, known data offsets |
| **build.sh** | `scripts/build.sh` | Build system: applies ASM + binary patches to produce output ROM |
| **test_tools.sh** | `tests/test_tools.sh` | Verifies all tools are installed and functional |

---

## Tool Details

### asar (SNES Assembler)

The primary assembler for this project. Built from source (GitHub: RPGHacker/asar).

```bash
# Apply an ASM patch to a ROM
asar patch.asm rom.smc

# asar modifies the ROM in-place, so always work on a copy
cp base.smc working.smc
asar my_patch.asm working.smc
```

**Key features:**
- Patch-oriented (modifies existing ROMs rather than building from scratch)
- Supports 65c816, SPC700, and SuperFX architectures
- Freespace finder for inserting new code
- Math expressions with proper operator priority
- Macro support

**Documentation:** https://rpghacker.github.io/asar/manual/

### wla-65816 (WLA-DX Assembler)

Alternative assembler, better suited for building ROMs from scratch or large-scale rewrites.

```bash
# Assemble a source file
wla-65816 -o output.o source.asm

# Link object files
wlalink linkfile output.smc
```

### flips (Floating IPS)

Creates and applies IPS/BPS patches — the standard distribution format for ROM hacks.

```bash
# Apply a patch
flips --apply patch.bps original.smc output.smc

# Create a BPS patch (preferred format)
flips --create --bps original.smc modified.smc patch.bps

# Create an IPS patch
flips --create --ips original.smc modified.smc patch.ips
```

**BPS vs IPS:**
- **BPS** (preferred): Includes checksums, supports larger ROMs, delta encoding
- **IPS**: Legacy format, simpler but no integrity checks

### mednafen (SNES Emulator)

Accurate multi-system emulator. Use for testing ROM modifications.

```bash
# Run a ROM
mednafen rom.smc

# mednafen creates config on first run at ~/.mednafen/
# For headless/automated testing, use with Xvfb:
# xvfb-run mednafen -video.driver softfb rom.smc
```

### ct_rom_utils.py (Custom CT Toolkit)

Python utility for Chrono Trigger ROM analysis.

```bash
# Display ROM information
python3 tools/ct_rom_utils.py info base.smc

# Hex dump a section
python3 tools/ct_rom_utils.py hexdump base.smc --offset 0xFFC0 --length 64

# Compare two ROMs
python3 tools/ct_rom_utils.py compare original.smc modified.smc

# Show known CT data offsets
python3 tools/ct_rom_utils.py offsets
```

---

## Directory Structure

```
obvious-rpg/
├── README.md              # Project overview
├── .gitignore             # Excludes ROM files, build output
├── tools/                 # ROM hacking tools and scripts
│   └── ct_rom_utils.py    # CT-specific ROM utilities
├── src/                   # Source files for the hack
│   ├── scripts/           # Event scripts (ASM)
│   ├── dialogue/          # Dialogue text files
│   ├── maps/              # Map/location data
│   └── data/              # Game data tables (items, enemies, etc.)
├── patches/               # IPS/BPS patch files for distribution
├── assets/                # Custom game assets
│   ├── sprites/           # Character/enemy sprites
│   ├── tilesets/          # Map tilesets
│   └── music/             # Custom music (SPC format)
├── docs/                  # Documentation
│   └── environment-setup.md  # This file
├── scripts/               # Build and automation scripts
│   └── build.sh           # Main build script
└── tests/                 # Testing utilities
    └── test_tools.sh      # Tool verification tests
```

---

## Build System

The build script (`scripts/build.sh`) handles the full build pipeline:

```bash
# Basic build (requires base.smc in project root)
./scripts/build.sh

# Build and create distribution patch
./scripts/build.sh --create-patch
```

**Build pipeline:**
1. **Preflight** — Verifies base ROM exists, checks size, removes copier header if present
2. **Prepare** — Copies base ROM to `build/` directory
3. **ASM Patches** — Applies all `.asm` files from `src/` using asar
4. **Binary Patches** — Applies all `.bps`/`.ips` files from `patches/` using flips
5. **Verify** — Displays output ROM size and checksums
6. **Create Patch** (optional) — Generates a BPS patch for distribution

**Important:** Place your legally-obtained Chrono Trigger ROM as `base.smc` in the project root. The ROM should be an unheadered US v1.0 ROM (4,194,304 bytes).

---

## Workflow Guide

### Starting a New Modification

1. **Identify what to change** using `ct_rom_utils.py`:
   ```bash
   python3 tools/ct_rom_utils.py offsets  # See known data locations
   python3 tools/ct_rom_utils.py hexdump base.smc --offset 0x0C0000 --length 256
   ```

2. **Write an ASM patch** in `src/`:
   ```asm
   ; src/scripts/my_change.asm
   lorom  ; or hirom for CT
   
   org $C00000  ; SNES address
   db $FF       ; New data
   ```

3. **Build and test:**
   ```bash
   ./scripts/build.sh
   mednafen build/obvious-rpg.smc
   ```

4. **Compare changes:**
   ```bash
   python3 tools/ct_rom_utils.py compare base.smc build/obvious-rpg.smc
   ```

### Using Temporal Flux (via Wine)

Temporal Flux is the premier Chrono Trigger editor but is Windows-only. To use it:

1. Download Temporal Flux from https://www.romhacking.net/utilities/262/
2. Run via Wine:
   ```bash
   wine temporal_flux.exe
   ```
3. Export changes as ASM or note the modified offsets

---

## Windows-Only Tools (via Wine)

These CT-specific tools require Wine:

| Tool | Purpose | Wine Status |
|------|---------|-------------|
| **Temporal Flux** | Comprehensive CT editor (events, maps, dialogue, enemies) | Works well under Wine |
| **Chrono Tweaker** | Quick stat/item editor | Works under Wine |
| **Chrono Trigger Tech Editor** | Tech/ability editor | Works under Wine |
| **Chrono Trigger Shop Editor** | Shop inventory editor | Works under Wine |

**Linux Alternatives:**
- For dialogue editing: Use hex editor + `ct_rom_utils.py` with known offsets
- For data editing: Use Python scripts with `construct` library for structured binary parsing
- For map editing: No good Linux alternative to Temporal Flux yet — use Wine

---

## Troubleshooting

### asar reports "ROM too small"
The base ROM may need to be expanded. Use the build script which handles this, or manually:
```bash
# Expand ROM to 6MB (if needed for extra content)
truncate -s 6291456 rom.smc
```

### Wine fails to start
```bash
# Initialize Wine prefix
WINEARCH=win32 wineboot
```

### mednafen shows black screen
Ensure you're using a valid, unheadered ROM. Check with:
```bash
python3 tools/ct_rom_utils.py info your_rom.smc
```

### Build script says "Base ROM not found"
Place your legally-obtained Chrono Trigger ROM as `base.smc` in the project root directory.
