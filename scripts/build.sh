#!/usr/bin/env bash
# =============================================================================
# Obvious RPG - Build Script
# Applies patches and ASM modifications to a base Chrono Trigger ROM
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
BASE_ROM="${PROJECT_ROOT}/base.smc"
OUTPUT_DIR="${PROJECT_ROOT}/build"
OUTPUT_ROM="${OUTPUT_DIR}/obvious-rpg.smc"
PATCHES_DIR="${PROJECT_ROOT}/patches"
SRC_DIR="${PROJECT_ROOT}/src"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# =============================================================================
# Preflight checks
# =============================================================================
preflight() {
    log_info "Running preflight checks..."

    # Check for base ROM
    if [[ ! -f "$BASE_ROM" ]]; then
        log_error "Base ROM not found at: $BASE_ROM"
        log_info "Place your legally-obtained Chrono Trigger ROM as 'base.smc' in the project root."
        log_info "Expected: unheadered US v1.0 ROM (4,194,304 bytes)"
        exit 1
    fi

    # Verify ROM size (unheadered CT US is exactly 4MB)
    local rom_size
    rom_size=$(stat -c%s "$BASE_ROM" 2>/dev/null || stat -f%z "$BASE_ROM" 2>/dev/null)
    
    if [[ "$rom_size" -eq 4194304 ]]; then
        log_ok "ROM size OK (4MB, unheadered)"
    elif [[ "$rom_size" -eq 4194816 ]]; then
        log_warn "ROM appears to have a 512-byte header. Removing..."
        dd if="$BASE_ROM" of="${BASE_ROM}.tmp" bs=512 skip=1 2>/dev/null
        mv "${BASE_ROM}.tmp" "$BASE_ROM"
        log_ok "Header removed"
    else
        log_warn "Unexpected ROM size: $rom_size bytes (expected 4194304)"
    fi

    # Check for required tools
    local missing=0
    for tool in asar flips; do
        if ! command -v "$tool" &>/dev/null; then
            log_error "Required tool not found: $tool"
            missing=1
        fi
    done
    [[ $missing -eq 1 ]] && exit 1

    log_ok "All preflight checks passed"
}

# =============================================================================
# Build steps
# =============================================================================
prepare_output() {
    log_info "Preparing output directory..."
    mkdir -p "$OUTPUT_DIR"
    cp "$BASE_ROM" "$OUTPUT_ROM"
    log_ok "Working ROM copied to: $OUTPUT_ROM"
}

apply_asm_patches() {
    log_info "Applying ASM patches..."
    local count=0
    
    # Apply any .asm files in src/ directory tree
    while IFS= read -r -d '' asm_file; do
        log_info "  Assembling: $(basename "$asm_file")"
        if asar "$asm_file" "$OUTPUT_ROM" 2>&1; then
            log_ok "  Applied: $(basename "$asm_file")"
            ((count++))
        else
            log_error "  Failed to apply: $(basename "$asm_file")"
            exit 1
        fi
    done < <(find "$SRC_DIR" -name "*.asm" -print0 2>/dev/null | sort -z)

    if [[ $count -eq 0 ]]; then
        log_info "  No ASM patches found (this is fine for initial setup)"
    else
        log_ok "Applied $count ASM patch(es)"
    fi
}

apply_binary_patches() {
    log_info "Applying binary patches (BPS/IPS)..."
    local count=0

    # Apply BPS patches in order
    while IFS= read -r -d '' patch_file; do
        local ext="${patch_file##*.}"
        log_info "  Applying: $(basename "$patch_file")"
        
        case "$ext" in
            bps)
                flips --apply "$patch_file" "$OUTPUT_ROM" "$OUTPUT_ROM" 2>&1
                ;;
            ips)
                flips --apply "$patch_file" "$OUTPUT_ROM" "$OUTPUT_ROM" 2>&1
                ;;
            *)
                log_warn "  Unknown patch format: $ext (skipping)"
                continue
                ;;
        esac
        
        log_ok "  Applied: $(basename "$patch_file")"
        ((count++))
    done < <(find "$PATCHES_DIR" -name "*.bps" -o -name "*.ips" -print0 2>/dev/null | sort -z)

    if [[ $count -eq 0 ]]; then
        log_info "  No binary patches found (this is fine for initial setup)"
    else
        log_ok "Applied $count binary patch(es)"
    fi
}

verify_rom() {
    log_info "Verifying output ROM..."
    local rom_size
    rom_size=$(stat -c%s "$OUTPUT_ROM" 2>/dev/null || stat -f%z "$OUTPUT_ROM" 2>/dev/null)
    
    # Generate checksums
    local md5sum sha1sum
    md5sum=$(md5sum "$OUTPUT_ROM" | cut -d' ' -f1)
    sha1sum=$(sha1sum "$OUTPUT_ROM" | cut -d' ' -f1)
    
    log_ok "Output ROM: $OUTPUT_ROM"
    log_info "  Size: $rom_size bytes"
    log_info "  MD5:  $md5sum"
    log_info "  SHA1: $sha1sum"
}

create_patch() {
    if [[ "${1:-}" == "--create-patch" ]]; then
        log_info "Creating distribution patch..."
        local patch_file="${OUTPUT_DIR}/obvious-rpg.bps"
        flips --create --bps "$BASE_ROM" "$OUTPUT_ROM" "$patch_file" 2>&1
        log_ok "Patch created: $patch_file"
    fi
}

# =============================================================================
# Main
# =============================================================================
main() {
    echo "============================================="
    echo "  Obvious RPG Build System"
    echo "  Chrono Trigger ROM Hack"
    echo "============================================="
    echo ""
    
    preflight
    prepare_output
    apply_asm_patches
    apply_binary_patches
    verify_rom
    create_patch "$@"
    
    echo ""
    log_ok "Build complete!"
    log_info "Test with: mednafen ${OUTPUT_ROM}"
}

main "$@"
