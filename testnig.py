
import ctypes
import time
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
MAPVK_VK_TO_VSC = 0

ULONG_PTR = ctypes.c_size_t


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
        ("padding", ctypes.c_byte * (
            32 if ctypes.sizeof(ctypes.c_void_p) == 8 else 16
        )),
    ]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("u", INPUT_UNION),
    ]

user32.SendInput.argtypes = (
    wintypes.UINT,
    ctypes.POINTER(INPUT),
    ctypes.c_int,
)
user32.SendInput.restype = wintypes.UINT

user32.MapVirtualKeyW.argtypes = (
    wintypes.UINT,
    wintypes.UINT,
)
user32.MapVirtualKeyW.restype = wintypes.UINT


def send_scan_code(scan_code, key_up=False):
    flags = KEYEVENTF_SCANCODE
    if key_up:
        flags |= KEYEVENTF_KEYUP

    event = INPUT(
        type=INPUT_KEYBOARD,
        ki=KEYBDINPUT(
            wVk=0,
            wScan=scan_code,
            dwFlags=flags,
            time=0,
            dwExtraInfo=0,
        ),
    )

    sent = user32.SendInput(
        1, ctypes.byref(event), ctypes.sizeof(INPUT)
    )

    if sent != 1:
        raise ctypes.WinError(ctypes.get_last_error())


# Convert virtual-key W (0x57) to a scan code.
scan_code = user32.MapVirtualKeyW(0x57, MAPVK_VK_TO_VSC)

print(f"W scan code: 0x{scan_code:02X}")
print("Focus the target window within 3 seconds.")
time.sleep(3)

try:
    send_scan_code(scan_code)       # Key down
    time.sleep(1)
finally:
    send_scan_code(scan_code, True) # Key up
