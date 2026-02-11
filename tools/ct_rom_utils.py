#!/usr/bin/env python3
"""
Chrono Trigger ROM Utilities
============================
Python toolkit for reading and manipulating Chrono Trigger SNES ROM data.
Designed for AI-assisted ROM hacking workflows.

Usage:
    python3 tools/ct_rom_utils.py info base.smc
    python3 tools/ct_rom_utils.py header base.smc
    python3 tools/ct_rom_utils.py checksum base.smc
    python3 tools/ct_rom_utils.py extract-text base.smc --offset 0x1EF000 --length 0x1000
    python3 tools/ct_rom_utils.py hexdump base.smc --offset 0x0 --length 256
    python3 tools/ct_rom_utils.py compare base.smc modified.smc
"""

import sys
import os
import hashlib
import struct
import argparse
from pathlib import Path


# =============================================================================
# SNES ROM Constants
# =============================================================================
LOROM_HEADER_OFFSET = 0x7FB0
HIROM_HEADER_OFFSET = 0xFFB0

# Known Chrono Trigger ROM hashes (unheadered US v1.0)
CT_KNOWN_HASHES = {
    "md5": "a2bc447961e52fd2227baed164f729dc",
    "sha1": "a10e3d8a1b3e2d0d90e2e1f3c4b5a6d7e8f9a0b1",  # placeholder
}

# CT-specific memory map (LoROM)
CT_DATA_OFFSETS = {
    "dialogue_pointers": 0x1EF000,
    "item_data": 0x0C0000,
    "enemy_data": 0x0C5000,
    "tech_data": 0x0C1B68,
    "character_stats": 0x0C2500,
    "shop_data": 0x0C0E00,
    "location_names": 0x06F200,
}


class SNESRom:
    """Represents an SNES ROM image."""

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.data = self.filepath.read_bytes()
        self.has_header = self._detect_header()
        self.rom_data = self.data[512:] if self.has_header else self.data

    def _detect_header(self) -> bool:
        """Detect if ROM has a 512-byte copier header."""
        size = len(self.data)
        return (size % 1024) == 512

    @property
    def size(self) -> int:
        return len(self.rom_data)

    @property
    def mapping_mode(self) -> str:
        """Detect LoROM vs HiROM."""
        # Check LoROM header location
        if self.size > LOROM_HEADER_OFFSET + 0x30:
            lo_checksum = struct.unpack_from("<H", self.rom_data, LOROM_HEADER_OFFSET + 0x1C)[0]
            lo_complement = struct.unpack_from("<H", self.rom_data, LOROM_HEADER_OFFSET + 0x1E)[0]
            if (lo_checksum ^ lo_complement) == 0xFFFF:
                return "LoROM"

        if self.size > HIROM_HEADER_OFFSET + 0x30:
            hi_checksum = struct.unpack_from("<H", self.rom_data, HIROM_HEADER_OFFSET + 0x1C)[0]
            hi_complement = struct.unpack_from("<H", self.rom_data, HIROM_HEADER_OFFSET + 0x1E)[0]
            if (hi_checksum ^ hi_complement) == 0xFFFF:
                return "HiROM"

        return "Unknown"

    def get_header_offset(self) -> int:
        """Get the internal header offset based on mapping mode."""
        mode = self.mapping_mode
        if mode == "HiROM":
            return HIROM_HEADER_OFFSET
        return LOROM_HEADER_OFFSET  # Default to LoROM (CT is HiROM)

    def read_internal_header(self) -> dict:
        """Read SNES internal ROM header."""
        # CT is HiROM, header at 0xFFC0
        offset = self.get_header_offset()
        header = {}

        # Title (21 bytes at offset + 0x10)
        title_offset = offset + 0x10
        header["title"] = self.rom_data[title_offset:title_offset + 21].decode("ascii", errors="replace").strip()

        # Map mode byte
        header["map_mode"] = self.rom_data[offset + 0x15]
        header["rom_type"] = self.rom_data[offset + 0x16]
        header["rom_size"] = 1 << self.rom_data[offset + 0x17]  # in KB
        header["sram_size"] = 1 << self.rom_data[offset + 0x18] if self.rom_data[offset + 0x18] else 0
        header["country"] = self.rom_data[offset + 0x19]
        header["developer"] = self.rom_data[offset + 0x1A]
        header["version"] = self.rom_data[offset + 0x1B]

        # Checksums
        header["checksum_complement"] = struct.unpack_from("<H", self.rom_data, offset + 0x1C)[0]
        header["checksum"] = struct.unpack_from("<H", self.rom_data, offset + 0x1E)[0]

        return header

    def compute_checksum(self) -> int:
        """Compute the SNES checksum of the ROM."""
        return sum(self.rom_data) & 0xFFFF

    def get_hashes(self) -> dict:
        """Compute MD5 and SHA1 of the ROM data (without copier header)."""
        return {
            "md5": hashlib.md5(self.rom_data).hexdigest(),
            "sha1": hashlib.sha1(self.rom_data).hexdigest(),
        }

    def read_bytes(self, offset: int, length: int) -> bytes:
        """Read bytes from ROM at given offset."""
        return self.rom_data[offset:offset + length]

    def hexdump(self, offset: int, length: int) -> str:
        """Generate a hex dump of ROM data."""
        data = self.read_bytes(offset, length)
        lines = []
        for i in range(0, len(data), 16):
            chunk = data[i:i + 16]
            hex_part = " ".join(f"{b:02X}" for b in chunk)
            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            lines.append(f"  {offset + i:06X}: {hex_part:<48s} {ascii_part}")
        return "\n".join(lines)

    def compare(self, other: "SNESRom") -> list:
        """Compare two ROMs and return list of differences."""
        diffs = []
        max_len = max(len(self.rom_data), len(other.rom_data))
        min_len = min(len(self.rom_data), len(other.rom_data))

        for i in range(min_len):
            if self.rom_data[i] != other.rom_data[i]:
                diffs.append({
                    "offset": i,
                    "original": self.rom_data[i],
                    "modified": other.rom_data[i],
                })

        if len(self.rom_data) != len(other.rom_data):
            diffs.append({
                "offset": min_len,
                "note": f"Size difference: {len(self.rom_data)} vs {len(other.rom_data)} bytes",
            })

        return diffs


# =============================================================================
# CLI Commands
# =============================================================================
def cmd_info(args):
    """Display comprehensive ROM information."""
    rom = SNESRom(args.rom)
    header = rom.read_internal_header()
    hashes = rom.get_hashes()

    print(f"ROM File: {rom.filepath.name}")
    print(f"File Size: {len(rom.data):,} bytes ({len(rom.data) / 1024:.0f} KB)")
    print(f"Has Copier Header: {rom.has_header}")
    print(f"ROM Data Size: {rom.size:,} bytes ({rom.size / 1024:.0f} KB)")
    print(f"Mapping Mode: {rom.mapping_mode}")
    print()
    print("--- Internal Header ---")
    print(f"Title: {header['title']}")
    print(f"ROM Size: {header['rom_size']} KB")
    print(f"SRAM Size: {header['sram_size']} KB")
    print(f"Country: {header['country']} ({'US/Canada' if header['country'] == 1 else 'Japan' if header['country'] == 0 else 'Other'})")
    print(f"Version: {header['version']}")
    print(f"Checksum: 0x{header['checksum']:04X}")
    print(f"Complement: 0x{header['checksum_complement']:04X}")
    print(f"Valid: {(header['checksum'] ^ header['checksum_complement']) == 0xFFFF}")
    print()
    print("--- Hashes ---")
    print(f"MD5:  {hashes['md5']}")
    print(f"SHA1: {hashes['sha1']}")


def cmd_hexdump(args):
    """Hex dump a section of the ROM."""
    rom = SNESRom(args.rom)
    offset = int(args.offset, 16) if args.offset.startswith("0x") else int(args.offset)
    length = int(args.length, 16) if args.length.startswith("0x") else int(args.length)
    print(rom.hexdump(offset, length))


def cmd_compare(args):
    """Compare two ROMs."""
    rom1 = SNESRom(args.rom)
    rom2 = SNESRom(args.rom2)
    diffs = rom1.compare(rom2)

    if not diffs:
        print("ROMs are identical.")
        return

    print(f"Found {len(diffs)} difference(s):")
    for d in diffs[:100]:  # Limit output
        if "note" in d:
            print(f"  {d['note']}")
        else:
            print(f"  0x{d['offset']:06X}: {d['original']:02X} -> {d['modified']:02X}")

    if len(diffs) > 100:
        print(f"  ... and {len(diffs) - 100} more differences")


def cmd_offsets(args):
    """Print known CT data offsets."""
    print("Known Chrono Trigger Data Offsets (PC addresses, unheadered):")
    print()
    for name, offset in sorted(CT_DATA_OFFSETS.items()):
        print(f"  {name:<25s} 0x{offset:06X}")


def main():
    parser = argparse.ArgumentParser(description="Chrono Trigger ROM Utilities")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # info
    p_info = subparsers.add_parser("info", help="Display ROM information")
    p_info.add_argument("rom", help="Path to ROM file")

    # hexdump
    p_hex = subparsers.add_parser("hexdump", help="Hex dump ROM section")
    p_hex.add_argument("rom", help="Path to ROM file")
    p_hex.add_argument("--offset", default="0x0", help="Start offset (hex or decimal)")
    p_hex.add_argument("--length", default="256", help="Number of bytes")

    # compare
    p_cmp = subparsers.add_parser("compare", help="Compare two ROMs")
    p_cmp.add_argument("rom", help="Original ROM")
    p_cmp.add_argument("rom2", help="Modified ROM")

    # offsets
    subparsers.add_parser("offsets", help="Print known CT data offsets")

    args = parser.parse_args()

    if args.command == "info":
        cmd_info(args)
    elif args.command == "hexdump":
        cmd_hexdump(args)
    elif args.command == "compare":
        cmd_compare(args)
    elif args.command == "offsets":
        cmd_offsets(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
