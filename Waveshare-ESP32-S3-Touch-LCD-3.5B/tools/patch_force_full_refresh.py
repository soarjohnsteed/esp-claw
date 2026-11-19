#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Force full-frame LVGL refresh for PANEL_IF_OTHER displays (AXS15231B QSPI).

Background
----------
The Waveshare ESP32-S3-Touch-LCD-3.5B uses an AXS15231B LCD controller driven
over QSPI. Its ``esp_lcd`` driver skips RASET (0x2B) in QSPI mode, so only a
sequential write that *starts at row 0* (RAMWR, 0x2C) lands on the correct GRAM
rows. Every later LVGL **partial** update falls through to RAMWRC (0x3C), which
continues from the panel's current GRAM cursor instead of the requested row and
tears the image into shifted bands -> "image correct for a moment, then garbled
/ torn". This is the exact symptom seen on first boot.

``esp_lv_adapter`` hard-rejects FULL render mode for ``PANEL_IF_OTHER`` (SPI /
I2C / QSPI) panels unless a TE pin is wired, which this board does not have, so
there is no board-config knob to ask for FULL. The only fix is to force it in
the adapter.

This tool patches
``managed_components/espressif__esp_lvgl_adapter/src/display/display_manager.c``
so that, for ``PANEL_IF_OTHER``, ``render_mode`` is overridden to
``ESP_LV_ADAPTER_DISPLAY_RENDER_MODE_FULL``. FULL allocates two full-frame PSRAM
draw buffers and makes LVGL flush the whole screen from row 0 every frame, which
is the only correct path for this panel.

It is idempotent (skips if the marker is already present) and safe to re-run
after a clean re-fetch of managed_components. Run it from the esp-claw root:

    python tools/patch_force_full_refresh.py
    python tools/patch_force_full_refresh.py --revert   # restore upstream

The board's ``sdkconfig.defaults.board`` keeps ``CONFIG_DISPLAY_SERVICE_FORCE_
FULL_REFRESH=y`` as documentation of intent, but the real switch is this patch
(the Kconfig symbol is not defined anywhere, so it is dropped by confgen).
"""

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(
    ROOT,
    "application",
    "edge_agent",
    "managed_components",
    "espressif__esp_lvgl_adapter",
    "src",
    "display",
    "display_manager.c",
)

# The exact line we inject after.
ANCHOR = "    esp_lv_adapter_display_render_mode_t render_mode = display_manager_pick_render_mode(cfg);\n"

MARKER = "/* Waveshare ESP32-S3-Touch-LCD-3.5B (AXS15231B over QSPI): the panel"

BLOCK = (
    "    /* Waveshare ESP32-S3-Touch-LCD-3.5B (AXS15231B over QSPI): the panel\n"
    "     * driver skips RASET (0x2B) in QSPI mode, so only a sequential write that\n"
    "     * starts at row 0 (RAMWR, 0x2C) lands on the correct rows. Every later\n"
    "     * LVGL partial update falls through to RAMWRC (0x3C) which continues from\n"
    "     * the panel's current GRAM cursor instead of the requested row, tearing\n"
    "     * the image into shifted bands. Force full-frame refresh for this panel\n"
    "     * interface class so LVGL always flushes the whole screen from row 0.\n"
    "     * See board README pitfall 1. This is a board bring-up patch; it is\n"
    "     * re-applied by tools/patch_force_full_refresh.py after a clean re-fetch\n"
    "     * of managed_components. */\n"
    "    if (pub->profile.interface == ESP_LV_ADAPTER_PANEL_IF_OTHER) {\n"
    "        render_mode = ESP_LV_ADAPTER_DISPLAY_RENDER_MODE_FULL;\n"
    "    }\n"
)

REVERT_BLOCK_LINES = (
    "    /* Waveshare ESP32-S3-Touch-LCD-3.5B (AXS15231B over QSPI): the panel\n",
    "     * driver skips RASET (0x2B) in QSPI mode, so only a sequential write that\n",
    "     * starts at row 0 (RAMWR, 0x2C) lands on the correct rows. Every later\n",
    "     * LVGL partial update falls through to RAMWRC (0x3C) which continues from\n",
    "     * the panel's current GRAM cursor instead of the requested row, tearing\n",
    "     * the image into shifted bands. Force full-frame refresh for this panel\n",
    "     * interface class so LVGL always flushes the whole screen from row 0.\n",
    "     * See board README pitfall 1. This is a board bring-up patch; it is\n",
    "     * re-applied by tools/patch_force_full_refresh.py after a clean re-fetch\n",
    "     * of managed_components. */\n",
    "    if (pub->profile.interface == ESP_LV_ADAPTER_PANEL_IF_OTHER) {\n",
    "        render_mode = ESP_LV_ADAPTER_DISPLAY_RENDER_MODE_FULL;\n",
    "    }\n",
)


def apply(path):
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    if any(MARKER in ln for ln in lines):
        print("%s: already patched - nothing to do." % path)
        return 0
    if ANCHOR not in lines:
        print("%s: anchor line not found - refusing to patch (upstream may have "
              "changed):\n  %s" % (path, ANCHOR.strip()))
        return 2
    idx = lines.index(ANCHOR)
    lines.insert(idx + 1, BLOCK)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.writelines(lines)
    print("%s: forced FULL refresh for PANEL_IF_OTHER (patched)." % path)
    return 1


def revert(path):
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    if not any(MARKER in ln for ln in lines):
        print("%s: not patched - nothing to revert." % path)
        return 0
    out, i, n = [], 0, 0
    while i < len(lines):
        if lines[i].rstrip("\n") == REVERT_BLOCK_LINES[0].rstrip("\n") and \
                lines[i:i + len(REVERT_BLOCK_LINES)] == list(REVERT_BLOCK_LINES):
            i += len(REVERT_BLOCK_LINES)
            n += 1
            continue
        out.append(lines[i])
        i += 1
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.writelines(out)
    print("%s: reverted (%d block(s) removed)." % (path, n))
    return 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--revert", action="store_true",
                    help="restore upstream display_manager.c")
    opts = ap.parse_args()

    if not os.path.isfile(TARGET):
        print("Target not found: %s\n"
              "Did you run a build yet, or is managed_components fetched?" % TARGET)
        return 2

    return revert(TARGET) if opts.revert else apply(TARGET)


if __name__ == "__main__":
    sys.exit(main())
