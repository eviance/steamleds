"""
Low-level x86 I/O-port access backends.

The Steam Machine ("Valve Fremont") front LEDs are controlled by writing bytes
to fixed x86 I/O ports in the Embedded-Controller region (base 0x0DE8). User-mode
code on Windows cannot execute IN/OUT instructions directly, so we go through a
signed ring0 helper driver -- the same approach OpenRGB/HWiNFO use:

  * InpOutBackend   -> inpoutx64.dll   (highrez InpOut, ships hwinterfacex64.sys)
  * WinRing0Backend -> WinRing0x64.dll (OpenLibSys, used by OpenRGB)

On Linux (e.g. testing from SteamOS itself) raw ports are reachable through
/dev/port as root -> DevPortBackend.

DummyBackend keeps everything in RAM so the rest of the code can be exercised on
any machine without hardware or a driver.

All backends implement the same tiny contract:
    read(port: int) -> int      # 0..255
    write(port: int, value: int)
"""
from __future__ import annotations

import abc
import os


class PortIO(abc.ABC):
    name = "abstract"

    @abc.abstractmethod
    def read(self, port: int) -> int: ...

    @abc.abstractmethod
    def write(self, port: int, value: int) -> None: ...

    # backends that hold OS resources can override
    def close(self) -> None:  # pragma: no cover - trivial
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def _clamp_byte(value: int) -> int:
    return max(0, min(255, int(value))) & 0xFF


class InpOutBackend(PortIO):
    """Windows ring0 port I/O via inpoutx64.dll (https://www.highrez.co.uk/downloads/inpout32/)."""

    name = "inpout"

    def __init__(self, dll_path: str = "inpoutx64.dll"):
        import ctypes

        self._dll = ctypes.WinDLL(dll_path)
        # int IsInpOutDriverOpen();
        self._dll.IsInpOutDriverOpen.restype = ctypes.c_uint32
        # void Out32(short PortAddress, short Data);
        self._dll.Out32.argtypes = [ctypes.c_int16, ctypes.c_int16]
        self._dll.Out32.restype = None
        # short Inp32(short PortAddress);
        self._dll.Inp32.argtypes = [ctypes.c_int16]
        self._dll.Inp32.restype = ctypes.c_int16

        if self._dll.IsInpOutDriverOpen() == 0:
            raise RuntimeError(
                "inpoutx64 kernel driver failed to open. Run as Administrator and make "
                "sure inpoutx64.dll (and its driver) is installed next to the app."
            )

    def read(self, port: int) -> int:
        return self._dll.Inp32(port & 0xFFFF) & 0xFF

    def write(self, port: int, value: int) -> None:
        self._dll.Out32(port & 0xFFFF, _clamp_byte(value))


class WinRing0Backend(PortIO):
    """Windows ring0 port I/O via WinRing0x64.dll (the library OpenRGB bundles)."""

    name = "winring0"

    def __init__(self, dll_path: str = "WinRing0x64.dll"):
        import ctypes

        self._dll = ctypes.WinDLL(dll_path)
        self._dll.InitializeOls.restype = ctypes.c_bool
        self._dll.DeinitializeOls.restype = None
        self._dll.ReadIoPortByte.argtypes = [ctypes.c_uint16]
        self._dll.ReadIoPortByte.restype = ctypes.c_uint8
        self._dll.WriteIoPortByte.argtypes = [ctypes.c_uint16, ctypes.c_uint8]
        self._dll.WriteIoPortByte.restype = None

        if not self._dll.InitializeOls():
            raise RuntimeError(
                "WinRing0 driver failed to initialise. Run as Administrator and keep "
                "WinRing0x64.dll + WinRing0x64.sys next to the app."
            )

    def read(self, port: int) -> int:
        return self._dll.ReadIoPortByte(port & 0xFFFF) & 0xFF

    def write(self, port: int, value: int) -> None:
        self._dll.WriteIoPortByte(port & 0xFFFF, _clamp_byte(value))

    def close(self) -> None:
        try:
            self._dll.DeinitializeOls()
        except Exception:
            pass


class DevPortBackend(PortIO):
    """Linux raw port access via /dev/port (needs root). Handy for testing on SteamOS."""

    name = "devport"

    def __init__(self, path: str = "/dev/port"):
        self._fd = os.open(path, os.O_RDWR)

    def read(self, port: int) -> int:
        os.lseek(self._fd, port, os.SEEK_SET)
        return os.read(self._fd, 1)[0]

    def write(self, port: int, value: int) -> None:
        os.lseek(self._fd, port, os.SEEK_SET)
        os.write(self._fd, bytes([_clamp_byte(value)]))

    def close(self) -> None:
        try:
            os.close(self._fd)
        except Exception:
            pass


class DummyBackend(PortIO):
    """In-memory register file. No hardware, no driver -- for development/tests."""

    name = "dummy"

    def __init__(self, verbose: bool = False):
        self.mem: dict[int, int] = {}
        self.verbose = verbose

    def read(self, port: int) -> int:
        return self.mem.get(port & 0xFFFF, 0)

    def write(self, port: int, value: int) -> None:
        v = _clamp_byte(value)
        self.mem[port & 0xFFFF] = v
        if self.verbose:
            print(f"  OUT 0x{port:04x} <- 0x{v:02x}")


_BACKENDS = {
    "inpout": InpOutBackend,
    "winring0": WinRing0Backend,
    "devport": DevPortBackend,
    "dummy": DummyBackend,
}


def open_backend(name: str = "auto", **kwargs) -> PortIO:
    """Open a backend by name, or auto-detect a sensible default per OS."""
    name = (name or "auto").lower()
    if name != "auto":
        if name not in _BACKENDS:
            raise ValueError(f"Unknown backend {name!r}; choose from {list(_BACKENDS)}")
        return _BACKENDS[name](**kwargs)

    if os.name == "nt":
        # Prefer inpout, fall back to WinRing0.
        try:
            return InpOutBackend(**kwargs)
        except Exception as first:
            try:
                return WinRing0Backend()
            except Exception as second:
                raise RuntimeError(
                    f"No Windows port-I/O backend available.\n"
                    f"  inpout:   {first}\n  winring0: {second}"
                )
    if os.path.exists("/dev/port"):
        return DevPortBackend()
    raise RuntimeError("No usable port-I/O backend for this platform.")
