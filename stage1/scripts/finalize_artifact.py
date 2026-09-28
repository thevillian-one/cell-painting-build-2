"""Finalize acquisition evidence after console output stops; works even on failed runs."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import sys
import datetime as dt


def finalize(root, repo):
    root=Path(root).resolve();repo=Path(repo).resolve();root.mkdir(parents=True,exist_ok=True)
    logs=root/'logs';logs.mkdir(exist_ok=True)
    for name in ('stage1-bootstrap-console.log','stage1-tests-console.log','stage1-acquisition-console.log'):
        p=repo/name
        if p.is_file():shutil.copy2(p,logs/name)
    for name in ('STAGE1_CHECKSUMS.sha256','.github/workflows/stage1.yml'):
        p=repo/name
        if p.is_file():
            target=root/'workflow-source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    ctx={k:os.environ.get(k) for k in ('GITHUB_REPOSITORY','GITHUB_SHA','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT','GITHUB_WORKFLOW')}
    ctx['collection_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
    (logs/'workflow-context.json').write_text(json.dumps(ctx,indent=2)+'\n',encoding='utf-8')
    if not (root/'BUILD_STATUS.md').exists():
        (root/'BUILD_STATUS.md').write_text('# Stage 1\n\nBLOCKED. Acquisition did not produce a completion record. Inspect workflow and console logs. No Stage 1 scientific acceptance is implied.\n')
    if not (root/'RUN_MANIFEST.json').exists():
        (root/'RUN_MANIFEST.json').write_text(json.dumps({'stage':'1A','acquisition_status':'BLOCKED','stage1_acceptance':'BLOCKED','reason':'No collector completion record','workflow':ctx},indent=2)+'\n')
    files=sorted(p for p in root.rglob('*') if p.is_file() and p!=root/'CHECKSUMS.sha256' and '__pycache__' not in p.parts)
    lines=[]
    for p in files:
        h=hashlib.sha256()
        with p.open('rb') as f:
            for b in iter(lambda:f.read(1048576),b''):h.update(b)
        lines.append(f'{h.hexdigest()}  {p.relative_to(root).as_posix()}\n')
    (root/'CHECKSUMS.sha256').write_text(''.join(lines),encoding='utf-8')
    manifest=json.loads((root/'RUN_MANIFEST.json').read_text())
    summary=os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary,'a',encoding='utf-8') as f:
            f.write('## Stage 1A acquisition\n\n')
            f.write('Acquisition status: **'+str(manifest.get('acquisition_status','BLOCKED'))+'**.\n\n')
            f.write('This is not the full Stage 1 acceptance gate. Return the **stage1-acquisition** artifact to the assistant for cohort review. Do not proceed to Stage 2.\n')
    print(f'Finalized {len(files)} artifact file hashes. Stage 1 remains pending cohort review.')
    return len(files)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--repo',default='.')
    a=p.parse_args();finalize(a.root,a.repo)
