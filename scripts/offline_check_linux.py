"""Linux test sürecinde ağ syscall'larını engelle, sonra normal CLI'yi çalıştır.

Örnek: python scripts/offline_check_linux.py ask "break nedir?" --chat-model qwen2.5-1.5b
Önce normal prepare/ingest tamamlanmalıdır. Windows kabul testinin yerini tutmaz.
"""
import ctypes
import ctypes.util
import errno
from pathlib import Path
import runpy
import socket
import sys


def block_network():
    if sys.platform != "linux":
        raise RuntimeError("Bu kontrol Linux ve libseccomp gerektirir.")
    library = ctypes.util.find_library("seccomp")
    if not library:
        raise RuntimeError("libseccomp bulunamadı; test ağ engeli olmadan çalıştırılmaz.")
    lib = ctypes.CDLL(library)
    lib.seccomp_init.argtypes = [ctypes.c_uint32]
    lib.seccomp_init.restype = ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    lib.seccomp_syscall_resolve_name.restype = ctypes.c_int
    lib.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    lib.seccomp_rule_add.restype = ctypes.c_int
    lib.seccomp_load.argtypes = [ctypes.c_void_p]
    lib.seccomp_load.restype = ctypes.c_int
    lib.seccomp_release.argtypes = [ctypes.c_void_p]
    ctx = lib.seccomp_init(0x7fff0000)  # default: allow unrelated system calls
    if not ctx:
        raise RuntimeError("seccomp_init başarısız.")
    try:
        for name in ("socket", "socketpair", "connect", "sendto", "sendmsg", "sendmmsg", "socketcall", "io_uring_setup"):
            number = lib.seccomp_syscall_resolve_name(name.encode())
            if number >= 0 and lib.seccomp_rule_add(ctx, 0x00050000 | errno.EPERM, number, 0) != 0:
                raise RuntimeError(f"Ağ engeli eklenemedi: {name}")
        if lib.seccomp_load(ctx) != 0:
            raise RuntimeError("Ağ filtresi yüklenemedi; test çalıştırılmadı.")
    finally:
        lib.seccomp_release(ctx)
    # Check both TCP and UDP and both IP families before importing the native SDK.
    for family in (socket.AF_INET, socket.AF_INET6):
        for kind in (socket.SOCK_STREAM, socket.SOCK_DGRAM):
            try:
                sock = socket.socket(family, kind)
            except OSError as exc:
                if exc.errno != errno.EPERM:
                    raise
            else:
                sock.close()
                raise RuntimeError("Ağ engeli kontrolü başarısız.")
    print("OFFLINE GUARD: IPv4/IPv6 TCP/UDP socket oluşturma EPERM ile engellendi.", flush=True)


if __name__ == "__main__":
    block_network()
    if sys.argv[1:] == ["--self-test"]:
        raise SystemExit(0)
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    sys.argv[0] = str(root / "main.py")
    runpy.run_path(sys.argv[0], run_name="__main__")
