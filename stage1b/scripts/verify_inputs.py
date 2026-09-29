"""Verify supplied checkpoints. This does not recompute biological outcomes."""
from pathlib import Path
import hashlib, json, re, argparse, datetime


def digest(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def verify(root):
    rows = []
    for line in (root / 'CHECKSUMS.sha256').read_text('utf-8').splitlines():
        if not line: continue
        m = re.fullmatch(r'([0-9a-fA-F]{64}) [ *](.+)', line)
        if not m: raise ValueError('Invalid checksum record')
        expected, name = m.groups()
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()): raise ValueError('Unsafe checksum path')
        rows.append({'path': name, 'expected': expected.lower(), 'actual': digest(path) if path.is_file() else None})
    if len({x['path'] for x in rows}) != len(rows): raise ValueError('Duplicate manifest entries')
    failures = [x for x in rows if x['actual'] != x['expected']]
    unlisted = sorted(set(str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()) - {x['path'] for x in rows} - {'CHECKSUMS.sha256'})
    if failures or unlisted: raise ValueError({'failures': failures, 'unlisted': unlisted})
    return {'records': len(rows), 'matched': len(rows), 'failed': failures, 'unlisted': unlisted, 'details': rows}


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--root',type=Path,required=True); parser.add_argument('--archive',type=Path,required=True); args=parser.parse_args()
    root=args.root.resolve(); a=root/'inputs/acquisition'; prior=root/'inputs/prior-review/stage1-review'
    output={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'acquisition':verify(a),'prior_review':verify(prior)}
    sources=json.loads((a/'manifests/source-files.json').read_text())
    output['source_manifest']={'records':len(sources),'passed':0,'failures':[]}
    for x in sources:
        p=a/x['path']; passed=p.stat().st_size==x['bytes'] and digest(p)==x['sha256']
        if passed:output['source_manifest']['passed']+=1
        else:output['source_manifest']['failures'].append(x['path'])
    output['source_archive_sha256']=digest(args.archive)
    output['source_archive_expected']='e435e4bf38fdb5b7fd8ebf7d46f1d71b16adc8b1c8711686a58f5cbeb050fd24'
    assert output['source_archive_sha256']==output['source_archive_expected']
    assert not output['source_manifest']['failures']
    (root/'evidence/input-verification.json').write_text(json.dumps(output,indent=2)+'\n')
    print({k:{kk:vv for kk,vv in v.items() if kk!='details'} if isinstance(v,dict) else v for k,v in output.items()})

if __name__=='__main__':main()
