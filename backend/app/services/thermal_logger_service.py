"""Lifecycle-managed thermal logger: exactly one instance, tied to the backend process.

The logger runs inside a Windows job object with JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
so it (and its shutdown watchdog) die whenever the backend exits, even on a crash.
"""
import ctypes
import os
import subprocess
import sys
import threading
from ctypes import wintypes

import psutil

JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
_JOB_INFO_CLASS = 9  # JobObjectExtendedLimitInformation


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class _Kernel32:
    def __init__(self):
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.CreateJobObjectW.restype = wintypes.HANDLE
        k.CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
        k.SetInformationJobObject.restype = wintypes.BOOL
        k.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD]
        k.AssignProcessToJobObject.restype = wintypes.BOOL
        k.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        k.TerminateJobObject.restype = wintypes.BOOL
        k.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        k.CloseHandle.restype = wintypes.BOOL
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        self._k = k

    def create_job(self):
        job = self._k.CreateJobObjectW(None, None)
        if not job:
            return None
        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self._k.SetInformationJobObject(job, _JOB_INFO_CLASS, ctypes.byref(info), ctypes.sizeof(info)):
            self._k.CloseHandle(job)
            return None
        return int(job)

    def assign(self, job, proc_handle):
        return bool(self._k.AssignProcessToJobObject(wintypes.HANDLE(job), wintypes.HANDLE(proc_handle)))

    def terminate_job(self, job):
        self._k.TerminateJobObject(wintypes.HANDLE(job), 0)
        self._k.CloseHandle(wintypes.HANDLE(job))


class ThermalLoggerService:
    def __init__(self):
        self._proc = None
        self._job = None
        self._kernel32 = None
        self._lock = threading.Lock()

    def _ensure_kernel(self):
        if self._kernel32 is None:
            self._kernel32 = _Kernel32()

    def is_running(self) -> bool:
        if self._proc is None:
            return False
        try:
            return self._proc.poll() is None
        except Exception:
            return False

    def start(self):
        with self._lock:
            if self.is_running():
                return
            self._ensure_kernel()
            self._cleanup_orphans()
            script = os.path.abspath(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools", "thermal_diag_logger.py")
            )
            self._job = self._kernel32.create_job()
            self._proc = subprocess.Popen(
                [sys.executable, script],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if self._job is not None and not self._kernel32.assign(self._job, self._proc._handle):
                print("[THERMAL] failed to assign logger to job object")
            print(f"[THERMAL] logger started (pid {self._proc.pid})")

    def stop(self):
        with self._lock:
            if self._job is not None:
                self._kernel32.terminate_job(self._job)
                self._job = None
            if self._proc is not None:
                try:
                    self._proc.wait(timeout=3)
                except Exception:
                    try:
                        self._proc.kill()
                    except Exception:
                        pass
                self._proc = None
            print("[THERMAL] logger stopped")

    @staticmethod
    def _cleanup_orphans():
        own = os.getpid()
        for p in psutil.process_iter(["cmdline"]):
            if p.pid == own:
                continue
            try:
                cmd = " ".join(p.info.get("cmdline") or [])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            if "thermal_diag_logger" in cmd or "Win32_ComputerShutdownEvent" in cmd:
                try:
                    p.terminate()
                    print(f"[THERMAL] killed orphan {p.pid}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass


thermal_logger_service = ThermalLoggerService()
