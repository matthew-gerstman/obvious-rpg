#!/usr/bin/env bash
# =============================================================================
# Tool Verification Tests
# Ensures all ROM hacking tools are installed and functional
# =============================================================================

PASS=0
FAIL=0

check() {
    local name="$1"
    shift
    if "$@" &>/dev/null; then
        echo "  ✓ $name"
        PASS=$((PASS + 1))
    else
        echo "  ✗ $name"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Obvious RPG Tool Verification ==="
echo ""

echo "Assemblers:"
check "asar" which asar
check "wla-65816" which wla-65816
check "wlalink" which wlalink

echo ""
echo "Patchers:"
check "flips" which flips

echo ""
echo "Emulators:"
check "mednafen" which mednafen

echo ""
echo "Wine (for Windows tools):"
check "wine" which wine

echo ""
echo "Hex/Binary Tools:"
check "xxd" which xxd
check "hexedit" which hexedit

echo ""
echo "Python Libraries:"
check "python3" which python3
check "bitstring" python3 -c "import bitstring"
check "construct" python3 -c "import construct"
check "pillow" python3 -c "import PIL"
check "numpy" python3 -c "import numpy"

echo ""
echo "CT ROM Utils:"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
check "ct_rom_utils.py" python3 "$PROJECT_ROOT/tools/ct_rom_utils.py" offsets

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -eq 0 ]; then
    echo "All tools verified!"
else
    echo "Some tools are missing!"
    exit 1
fi
