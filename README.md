# Obvious RPG

A Chrono Trigger (SNES) ROM hack built with AI-assisted development tools.

## Quick Start

```bash
# 1. Verify your environment
bash tests/test_tools.sh

# 2. Place your legally-obtained Chrono Trigger ROM as base.smc
cp /path/to/your/chrono_trigger.smc base.smc

# 3. Build
./scripts/build.sh

# 4. Test
mednafen build/obvious-rpg.smc
```

## Project Structure

```
obvious-rpg/
├── tools/           # ROM hacking tools and scripts
├── src/             # Source files (scripts, dialogue, maps, data)
├── patches/         # IPS/BPS patch files
├── assets/          # Custom sprites, tilesets, music
├── docs/            # Documentation
├── scripts/         # Build/automation scripts
└── tests/           # Testing utilities
```

## Development Environment

See [docs/environment-setup.md](docs/environment-setup.md) for the full environment guide.

**Key tools:**
- **asar** — SNES assembler (65816/SPC700/SuperFX)
- **wla-65816** — Alternative 65816 assembler (WLA-DX)
- **flips** — IPS/BPS patch creation and application
- **mednafen** — Accurate SNES emulator for testing
- **wine** — Windows compatibility for Temporal Flux and other CT editors
- **ct_rom_utils.py** — Custom Chrono Trigger ROM analysis toolkit

## Legal

This repository contains **no copyrighted ROM data**. You must supply your own legally-obtained Chrono Trigger ROM to use the build system. ROM files are excluded via `.gitignore`.

## License

TBD
