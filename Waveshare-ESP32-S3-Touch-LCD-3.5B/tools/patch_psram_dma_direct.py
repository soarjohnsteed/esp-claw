#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Sanitize generated board config: drop any psram_dma_direct initializer.

Background
----------
``esp_lcd_panel_io_spi_config_t::flags.psram_dma_direct`` is an **IDF 6.1+**
feature. On IDF v5.5.x the field is simply absent from the anonymous
``flags`` struct in ``esp_lcd_io_spi.h``, so:

  * if a (patched) board manager force-emits ``.psram_dma_direct = true`` into
    the generated C code, the firmware **fails to compile** with
    "'struct <anonymous>' has no member named 'psram_dma_direct'";
  * worse, a binary built on an IDF that *does* have the member but on a board
    whose PSRAM setup does not support direct DMA **crashes in LCD init at
    boot** -> endless reboot loop / CDC (COM port) disconnect-reconnect.

This tool makes the committed generated code safe regardless of which board
manager version produced it: it removes any ``.psram_dma_direct = ...``
initializer line from ``gen_board_device_config.c`` (and any other generated
board-config .c under ``components/gen_bmgr_codes/``). It is idempotent.

It deliberately does **NOT** touch the board manager's version gate any more -
forcing the field on is what caused the breakage. The board works correctly
on v5.5.x with the field left at its default (false); the small
``max_transfer_sz`` only costs one memcpy per chunk.

Run it from the esp-claw root:

    python tools/patch_psram_dma_direct.py
"""

import argparse
import os
import re
import sys

SEARCH_ROOTS = (
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "application",
        "edge_agent",
        "components",
        "gen_bmgr_codes",
    ),
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "components",
        "gen_bmgr_codes",
    ),
)

# Matches: "                    .psram_dma_direct = true," / "= false," etc.
LINE_RE = re.compile(r"^\s*\.psram_dma_direct\s*=\s*[A-Za-z0-9_]+\s*,?\s*$")


def find_targets():
    found = []
    for root in SEARCH_ROOTS:
        if not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            if name.endswith(".c"):
                found.append(os.path.join(root, name))
    return found


def sanitize(path):
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    kept, removed = [], 0
    for ln in lines:
        if LINE_RE.match(ln):
            removed += 1
            continue
        kept.append(ln)
    if removed:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.writelines(kept)
    return removed


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    opts = ap.parse_args()

    targets = find_targets()
    if not targets:
        print("No gen_bmgr_codes .c files found - nothing to do.")
        return 0

    total = 0
    for path in targets:
        n = sanitize(path)
        total += n
        print("%s: removed %d line(s)" % (path, n))
    if total == 0:
        print("Already clean - no psram_dma_direct initializer present.")
    else:
        print("Sanitized %d line(s) total." % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
