# SPDX-License-Identifier: GPL-3.0-or-later
"""Publish complete KiCad exports without truncating Windows-mapped files."""
from pathlib import Path
import subprocess
import tempfile


def write(path, data):
    """Replace a complete generated file, including files mapped by a viewer."""
    path=Path(path)
    if isinstance(data,str):data=data.encode('utf-8')
    with tempfile.NamedTemporaryFile(prefix='.'+path.name+'-',dir=path.parent,delete=False) as stream:
        temporary=Path(stream.name)
        stream.write(data)
    try:temporary.replace(path)
    finally:
        if temporary.exists():temporary.unlink()


def run(cli, args, **kwargs):
    args=list(map(str,args))
    if '-o' not in args:
        return subprocess.run([str(cli),*args],**kwargs)
    index=args.index('-o')+1
    original=args[index];destination=Path(original)
    directory=original.endswith(('/', '\\'))
    parent=destination.parent
    parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.kicad-export-',dir=parent) as temporary:
        staging=Path(temporary)
        staged=staging/'output' if directory else staging/destination.name
        args[index]=str(staged)+('/' if directory else '')
        result=subprocess.run([str(cli),*args],**kwargs)
        if result.returncode:return result
        if directory:
            destination.mkdir(parents=True,exist_ok=True)
            for source in staged.rglob('*'):
                if source.is_file():
                    target=destination/source.relative_to(staged)
                    target.parent.mkdir(parents=True,exist_ok=True)
                    source.replace(target)
        else:
            staged.replace(destination)
        return result
