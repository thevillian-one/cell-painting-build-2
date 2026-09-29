"""Regenerate the additive update manifest after an intentional reviewed code change.

Run from the repository root: python stage1b/scripts/update_package_checksums.py
Never use this to conceal an unexplained downloaded-data hash mismatch.
"""
from pathlib import Path
import hashlib

root=Path(__file__).resolve().parents[2]
folder=root/'stage1b'
manifest=folder/'PACKAGE_CHECKSUMS.sha256'
files=[p for p in folder.rglob('*') if p.is_file() and p!=manifest and
       not any(x in p.parts for x in ['__pycache__','.pytest_cache','.git'])]
files += [root/'.github/workflows/stage1b.yml',root/'.github/workflows/.gitattributes']
missing=[str(p) for p in files if not p.is_file()]
if missing:raise SystemExit('Incomplete repository structure: '+repr(missing))
manifest.write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(root).as_posix()+'\n' for p in sorted(files)),encoding='utf-8')
print('Updated',len(files),'file digests in stage1b/PACKAGE_CHECKSUMS.sha256')
