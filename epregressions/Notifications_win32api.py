#!/usr/bin/python

from win32api import *
from win32gui import *
import win32con
import sys, os
import struct
import time

# From a gist here: https://gist.github.com/BoppreH/4000505

import os
path = os.path.dirname(__file__)
script_dir = os.path.abspath(path)

class WindowsBalloonTip:
    def __init__(self):
        message_map = {
                win32con.WM_DESTROY: self.OnDestroy,
        }
        # Register the Window class.
        self.wc = WNDCLASS()
        self.hinst = self.wc.hInstance = GetModuleHandle(None)
        self.wc.lpszClassName = "PythonTaskbar"
        self.wc.lpfnWndProc = message_map # could also specify a wndproc.
        self.classAtom = RegisterClass(self.wc)
        self.dontTryAnymore = False
        
    def sendNotification(self, title, msg):
        if self.dontTryAnymore:
            return
        # Create the Window.
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = CreateWindow( self.classAtom, "Taskbar", style, \
                0, 0, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT, \
                0, 0, self.hinst, None)
        UpdateWindow(self.hwnd)
        iconPathName = os.path.abspath(os.path.join( sys.path[0], os.path.join(script_dir, 'ep_icon.png') ))
        icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
        try:
           hicon = LoadImage(self.hinst, iconPathName, \
                    win32con.IMAGE_ICON, 0, 0, icon_flags)
        except:
           hicon = LoadIcon(0, win32con.IDI_APPLICATION)
        flags = NIF_ICON | NIF_MESSAGE | NIF_TIP
        nid = (self.hwnd, 0, flags, win32con.WM_USER+20, hicon, "tooltip")
        Shell_NotifyIcon(NIM_ADD, nid)
        Shell_NotifyIcon(NIM_MODIFY, \
                         (self.hwnd, 0, NIF_INFO, win32con.WM_USER+20,\
                          hicon, "Balloon  tooltip", msg, 200, title))
        # self.show_balloon(title, msg)
        time.sleep(5)
        numTries = 0
        while True:
            numTries += 1
            print(numTries)
            if numTries >= 3:
                self.dontTryAnymore = True
                print("Killing win32 notifications")
                return
            try:
                DestroyWindow(self.hwnd)
                break
            except Exception as e:
                print("Couldnt destroy notification, trying again")
                continue
        
    def OnDestroy(self, hwnd, msg, wparam, lparam):
        nid = (self.hwnd, 0)
        Shell_NotifyIcon(NIM_DELETE, nid)
        PostQuitMessage(0) # Terminate the app.

        
