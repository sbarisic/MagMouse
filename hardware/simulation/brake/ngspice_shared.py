# SPDX-License-Identifier: GPL-3.0-or-later
"""Small synchronous interface to KiCad's installed ngspice shared library."""
import ctypes as C
import os
from pathlib import Path


class Vector(C.Structure):
    _fields_ = [('name', C.c_char_p), ('type', C.c_int), ('flags', C.c_short),
                ('real', C.POINTER(C.c_double)), ('complex', C.c_void_p), ('length', C.c_int)]


class Engine:
    def __init__(self, dll):
        self.dll_path = Path(dll).resolve()
        self.directory = os.add_dll_directory(str(self.dll_path.parent))
        self.lib = C.CDLL(str(self.dll_path))
        self.log = []
        send = C.CFUNCTYPE(C.c_int, C.c_char_p, C.c_int, C.c_void_p)
        leave = C.CFUNCTYPE(C.c_int, C.c_int, C.c_bool, C.c_bool, C.c_int, C.c_void_p)
        self.callbacks = [send(self._message), send(lambda *args: 0), leave(self._exit)]
        self.lib.ngSpice_Init.argtypes = [C.c_void_p] * 7
        self.lib.ngSpice_Command.argtypes = [C.c_char_p]
        self.lib.ngSpice_Circ.argtypes = [C.POINTER(C.c_char_p)]
        self.lib.ngGet_Vec_Info.argtypes = [C.c_char_p]
        self.lib.ngGet_Vec_Info.restype = C.POINTER(Vector)
        self.lib.ngSpice_Init(*self.callbacks, None, None, None, None)
        self.lib.ngSpice_nospiceinit()
        self.command('set ngbehavior=psa')
        self.command('set noaskquit')
        for module in sorted((self.dll_path.parent.parent/'lib/ngspice').glob('*.cm')):
            self.command(f'codemodel {module.as_posix()}')

    def _message(self, message, *_):
        self.log.append(message.decode('utf-8', errors='replace'))
        return 0

    def _exit(self, status, *_):
        self.log.append(f'CONTROLLED EXIT {status}')
        return 0

    def command(self, text):
        result = self.lib.ngSpice_Command(text.encode())
        if result:
            raise RuntimeError('\n'.join(self.log[-30:]))

    def run(self, circuit):
        self.command('destroy all')
        self.log.clear()
        lines = [line.encode('utf-8') for line in circuit.splitlines()]
        array = (C.c_char_p * (len(lines) + 1))(*lines, None)
        if self.lib.ngSpice_Circ(array):
            raise RuntimeError('\n'.join(self.log))
        self.command('run')

    def vector(self, name):
        import numpy as np
        ptr = self.lib.ngGet_Vec_Info(name.encode())
        if not ptr or not ptr.contents.real:
            raise RuntimeError(f'Missing vector {name}\n' + '\n'.join(self.log[-30:]))
        v = ptr.contents
        return np.ctypeslib.as_array(v.real, shape=(v.length,)).copy()
