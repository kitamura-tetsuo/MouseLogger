import argparse
import ctypes
import datetime
import logging
import pathlib

import win32gui
from PIL import ImageGrab
from pynput import mouse
from tzlocal import get_localzone

parser = argparse.ArgumentParser()

parser.add_argument("--window_name", help="window_name")
parser.add_argument("--path", default="screenshot/")

args = parser.parse_args()


class MouseLogger:
    def __init__(self, window_name, path):
        self.path = pathlib.Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.bbox = None
        self.tz = get_localzone()

        hwnd = win32gui.FindWindow(None, window_name)
        if hwnd:
            self.bbox = win32gui.GetWindowRect(hwnd)
            f = ctypes.windll.dwmapi.DwmGetWindowAttribute
            rect = ctypes.wintypes.RECT()
            DWMWA_EXTENDED_FRAME_BOUNDS = 9
            f(
                ctypes.wintypes.HWND(hwnd),
                ctypes.wintypes.DWORD(DWMWA_EXTENDED_FRAME_BOUNDS),
                ctypes.byref(rect),
                ctypes.sizeof(rect),
            )
            self.bbox = (rect.left, rect.top, rect.right, rect.bottom)
            self.rect = rect

    def join(self):
        with mouse.Listener(on_click=self.on_click) as mouse_listener:
            mouse_listener.join()

    def on_click(self, x, y, button, pressed):
        if not self.check_mouse_area(x, y):
            return

        if pressed:
            now = datetime.datetime.now(tz=self.tz)
            self.save_screenshot(f"{now:%Y%m%d%H%M%S}_mouse_pressed_{x}_{y}.png")
        else:
            self.save_screenshot(f"{now:%Y%m%d%H%M%S}_mouse_released_{x}_{y}.png")
        print("{0} at {1}".format("Pressed" if pressed else "Released", (x, y)))

    def on_scroll(self, x, y, dx, dy):
        if not self.check_mouse_area(x, y):
            return

        now = datetime.datetime.now(tz=self.tz)
        self.save_screenshot(f"{now:%Y%m%d%H%M%S}_mouse_scrolled_{x}_{y}_{dx}.png")
        print("Scrolled {0} at {1}".format("down" if dy < 0 else "up", (x, y)))

    def save_screenshot(self, name):
        return ImageGrab.grab(self.bbox).save(self.path + name)

    def check_mouse_area(self, x, y):
        if self.rect.left < x and x < self.rect.right and self.rect.top < y and y < self.rect.bottom:
            x -= self.rect.left
            y -= self.rect.top
            return True
        else:
            return False


mouselogger = MouseLogger(args.window_name)
mouselogger.join()
