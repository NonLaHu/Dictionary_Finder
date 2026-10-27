"""
Calibrate Windows On-Screen Keyboard key positions.

How to use:
1. Open Windows On-Screen Keyboard (OSK) and leave it visible.
2. Run: python calibrate_osk_keys.py
3. Click the CENTER of these keys in this exact order:
       Q, P, A, L, Z, M
4. The script interpolates the keys between each row's endpoints and overwrites
   key.json beside this script.

Requires:
    py -m pip install pynput

Coordinates are screen coordinates from pynput. This script only records clicks;
it does not click keys or type anything.
"""

import json
import sys
import time
from pathlib import Path

try:
    from pynput import mouse
except ImportError:
    print("Missing dependency. Install it with:")
    print("  py -m pip install pynput")
    raise SystemExit(1)


OUTPUT_PATH = Path(__file__).resolve().with_name("key.json")

# Click the two endpoints of each alphabetic row, left to right.
CALIBRATION_STEPS = [
    ("Q", "top row: click the CENTER of Q"),
    ("P", "top row: click the CENTER of P"),
    ("A", "middle row: click the CENTER of A"),
    ("L", "middle row: click the CENTER of L"),
    ("Z", "bottom row: click the CENTER of Z"),
    ("M", "bottom row: click the CENTER of M"),
]

ROWS = {
    "top": list("qwertyuiop"),
    "middle": list("asdfghjkl"),
    "bottom": list("zxcvbnm"),
}


def interpolate_row(keys, left_point, right_point):
    """Interpolate key centers evenly between the two clicked endpoints."""
    x1, y1 = left_point
    x2, y2 = right_point
    last = len(keys) - 1
    points = {}
    for index, key in enumerate(keys):
        ratio = index / last if last else 0
        points[key] = {
            "x": round(x1 + (x2 - x1) * ratio),
            "y": round(y1 + (y2 - y1) * ratio),
        }
    # Preserve the exact positions the user clicked at both endpoints.
    points[keys[0]] = {"x": int(x1), "y": int(y1)}
    points[keys[-1]] = {"x": int(x2), "y": int(y2)}
    return points


def main():
    print("=" * 64)
    print("OSK KEY COORDINATE CALIBRATION")
    print("=" * 64)
    print("Make sure the Windows On-Screen Keyboard is open and visible.")
    print("Click the CENTER of each requested key when prompted.")
    print("Do not click this console or another window.")
    print("The existing key.json will be OVERWRITTEN after all 6 clicks.")
    print("Press Ctrl+C to cancel.\n")

    captured = {}
    step_index = 0

    def on_click(x, y, button, pressed):
        nonlocal step_index
        if not pressed or button != mouse.Button.left:
            return

        if step_index >= len(CALIBRATION_STEPS):
            return False

        key, _ = CALIBRATION_STEPS[step_index]
        captured[key] = (round(x), round(y))
        print(f"Recorded {key}: x={round(x)}, y={round(y)}")
        step_index += 1

        if step_index < len(CALIBRATION_STEPS):
            next_key, instruction = CALIBRATION_STEPS[step_index]
            print(f"\nNext ({step_index + 1}/6): {instruction}")
        else:
            print("\nAll six points captured.")
            return False

    print(f"Step 1/6: {CALIBRATION_STEPS[0][1]}")
    print("Waiting for mouse clicks...\n")

    listener = mouse.Listener(on_click=on_click)
    listener.start()

    try:
        while listener.is_alive() and step_index < len(CALIBRATION_STEPS):
            time.sleep(0.05)
        listener.join()
    except KeyboardInterrupt:
        listener.stop()
        print("\nCancelled. key.json was not changed.")
        return

    if len(captured) != 6:
        print(f"Only captured {len(captured)} of 6 points. key.json was not changed.")
        return

    key_positions = {}
    key_positions.update(
        interpolate_row(ROWS["top"], captured["Q"], captured["P"])
    )
    key_positions.update(
        interpolate_row(ROWS["middle"], captured["A"], captured["L"])
    )
    key_positions.update(
        interpolate_row(ROWS["bottom"], captured["Z"], captured["M"])
    )

    data = {
        "coordinate_system": "screen",
        "description": "Interpolated centers of Windows On-Screen Keyboard alphabet keys",
        "calibration_points": {
            key.lower(): {"x": point[0], "y": point[1]}
            for key, point in captured.items()
        },
        "keys": key_positions,
    }

    try:
        OUTPUT_PATH.write_text(
            json.dumps(data, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"Failed to write {OUTPUT_PATH}: {exc}")
        raise SystemExit(1)

    print(f"\nSaved {len(key_positions)} key positions to:")
    print(f"  {OUTPUT_PATH}")
    print("\nPreview:")
    for row_name, row_keys in ROWS.items():
        values = "  ".join(
            f"{key.upper()}=({key_positions[key]['x']},{key_positions[key]['y']})"
            for key in row_keys
        )
        print(f"  {row_name}: {values}")

    print("\nNote: interpolation assumes evenly spaced keys within each row.")
    print("If the OSK is moved, resized, or its layout changes, recalibrate.")


if __name__ == "__main__":
    main()
