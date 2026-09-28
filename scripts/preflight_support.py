"""Stage 0 support: bounded public acquisition, validation and provenance.

No phenotype calculations, normalization or cohort selection are performed.
All fixture-based tests are separate from a real-data acquisition pass.
"""
from __future__ import annotations
import csv
import datetime as dt
import gzip
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import platform
import re
import resource
import shutil
import time
from urllib.parse import urlencode, urlparse, quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

REPO = 'jump-cellpainting/2024_Chandrasekaran_NatureMethods_CPJUMP1'
BUCKET_HOST = 'cellpainting-gallery.s3.amazonaws.com'
ALLOWED_HOSTS = {'api.github.com', 'raw.githubusercontent.com', BUCKET_HOST}
FEATURE_PREFIXES = ('Cells_', 'Cytoplasm_', 'Nuclei_')
PLATE_COLUMNS = ('Metadata_Plate', 'Image_Metadata_Plate', 'Metadata_plate', 'Metadata_Assay_Plate_Barcode', 'Assay_Plate_Barcode')
WELL_COLUMNS = ('Metadata_Well', 'Image_Metadata_Well', 'Metadata_well', 'Metadata_Well_Position', 'Metadata_well_position')

def utc(): return dt.datetime.now(dt.timezone.utc).isoformat()

def dump(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str, allow_nan=False)+'\n', encoding='utf-8')

def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def runtime_snapshot(root):
    root = Path(root)
    cgroup = {}
    for n in ('memory.max','memory.current','memory.peak','cpu.max','pids.max'):
        p = Path('/sys/fs/cgroup') / n
        if p.exists(): cgroup[n] = p.read_text().strip()
    return {
        'utc': utc(), 'python': platform.python_version(), 'python_full': platform.python_version()+': '+platform.python_compiler(),
        'architecture': platform.machine(), 'platform': platform.platform(),
        'cpu_count_reported': os.cpu_count(), 'cpu_affinity_count': len(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else None,
        'cgroup': cgroup, 'disk_bytes': dict(zip(('total','used','free'),shutil.disk_usage(root))),
        'meminfo': Path('/proc/meminfo').read_text() if Path('/proc/meminfo').exists() else None,
        'os_release': Path('/etc/os-release').read_text() if Path('/etc/os-release').exists() else None,
        'process_limits': {n: resource.getrlimit(getattr(resource,n)) for n in ('RLIMIT_AS','RLIMIT_CPU','RLIMIT_FSIZE','RLIMIT_NOFILE','RLIMIT_NPROC') if hasattr(resource,n)},
        'installed_distributions': sorted([{'name':d.metadata.get('Name'), 'version':d.version} for d in importlib.metadata.distributions()], key=lambda x:(x['name'] or '').lower()),
        'tools': {n:shutil.which(n) for n in ('python','python3.12','git','git-lfs','curl','chromium','aws')},
        # Explicit whitelist. Never dump credentials or the complete environment.
        'github_context': {n:os.environ.get(n) for n in ('GITHUB_REPOSITORY','GITHUB_SHA','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT','RUNNER_OS','RUNNER_ARCH')},
    }

class Fetcher:
    """No auth, no custom DNS, no proxy/security overrides; only public sources."""
    def __init__(self, output):
        self.output = Path(output); self.records = []

    def _save(self):
        dump(self.output/'manifests/http-requests.json', self.records)

    def fetch(self, url, relative_path, limit, *, method='GET', extra_headers=None):
        if urlparse(url).scheme != 'https' or urlparse(url).hostname not in ALLOWED_HOSTS:
            raise ValueError('Not an approved public-source host')
        headers = {'User-Agent':'cell-painting-stage0/1.0', 'Accept-Encoding':'identity'}
        headers.update(extra_headers or {})
        relative_path = str(relative_path)
        dest = self.output / relative_path
        if dest.resolve() == self.output.resolve() or self.output.resolve() not in dest.resolve().parents:
            raise ValueError('Destination escapes output directory')
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name+'.partial')
        record = {'url':url, 'method':method, 'destination':relative_path, 'max_bytes':limit, 'started_utc':utc()}
        self.records.append(record); self._save(); start = time.monotonic()
        try:
            with urlopen(Request(url, headers=headers, method=method), timeout=30) as response:
                if urlparse(response.url).hostname not in ALLOWED_HOSTS: raise ValueError('Redirected outside approved source hosts')
                record.update({'status':response.status, 'effective_url':response.url, 'headers':dict(response.headers.items())})
                if response.status != 200: raise ValueError('Expected full HTTP 200 response')
                length = response.headers.get('Content-Length')
                if length is not None and int(length) > limit: raise ValueError(f'Object exceeds {limit} byte cap')
                if method == 'HEAD':
                    record['result'] = 'HEAD_VERIFIED'; return record
                total = 0; h = hashlib.sha256()
                with tmp.open('wb') as f:
                    while True:
                        chunk = response.read(1024*1024)
                        if not chunk: break
                        total += len(chunk)
                        if total > limit: raise ValueError('Download exceeded byte cap')
                        f.write(chunk); h.update(chunk)
                if length is not None and total != int(length): raise ValueError('Content-Length mismatch')
                if total == 0: raise ValueError('Empty response body')
                tmp.replace(dest)
                record.update({'result':'BYTES_DOWNLOADED_NOT_YET_FORMAT_VALIDATED','bytes':total,'sha256':h.hexdigest(), 'checksum_status':'locally calculated, not upstream authenticated SHA-256'})
                return record
        except Exception as e:
            tmp.unlink(missing_ok=True)
            record.update({'result':'FAILED','error':f'{type(e).__name__}: {e}'})
            raise
        finally:
            record['seconds'] = time.monotonic()-start; record['ended_utc']=utc(); self._save()


def validate_metadata(path, plate, batch):
    text = Path(path).read_text(encoding='utf-8-sig')
    if text.lstrip().lower().startswith(('<!doctype','<html','version https://git-lfs')): raise ValueError('Not TSV bytes')
    reader = csv.DictReader(io.StringIO(text), delimiter='\t')
    required = {'Batch','Assay_Plate_Barcode','Perturbation','Cell_type','Time'}
    if not required.issubset(reader.fieldnames or []): raise ValueError('Metadata columns do not match official experiment table')
    rows = [r for r in reader if r['Assay_Plate_Barcode']==plate and r['Batch']==batch]
    if len(rows) != 1: raise ValueError('Candidate plate/batch metadata match is not unique')
    return {'header':reader.fieldnames,'candidate_row':rows[0], 'scope':'identity check only, not cohort qualification'}


def parse_listing(xml_bytes):
    root = ET.fromstring(xml_bytes)
    ns = {'s':'http://s3.amazonaws.com/doc/2006-03-01/'}
    if root.tag != '{'+ns['s']+'}ListBucketResult': raise ValueError('Not an S3 object-list response')
    items=[]
    for el in root.findall('s:Contents',ns):
        items.append({'key':el.findtext('s:Key',namespaces=ns), 'size':int(el.findtext('s:Size',namespaces=ns)),
                      'etag':el.findtext('s:ETag',namespaces=ns), 'last_modified':el.findtext('s:LastModified',namespaces=ns)})
    more=root.findtext('s:IsTruncated',default='false',namespaces=ns).lower()=='true'
    token=root.findtext('s:NextContinuationToken',namespaces=ns)
    if more and not token: raise ValueError('Truncated listing without continuation token')
    return items, token if more else None


def select_raw(items, prefix, plate, cap):
    # A normalized or augmented profile is never accepted as an unnormalized input.
    exact = {prefix+plate+'.csv', prefix+plate+'.csv.gz'}
    candidates = [x for x in items if x['key'] in exact and 0 < x['size'] <= cap]
    if not candidates: raise ValueError('No recognized unnormalized aggregate within cap; inspect listing. No guessed substitute downloaded.')
    # Prefer existing gzip encoding of the same raw aggregate when both exist.
    candidates.sort(key=lambda x:(not x['key'].endswith('.gz'),x['key']))
    return candidates[0]


def validate_profile(path, expected_plate, output, sample_rows=3, max_uncompressed_bytes=1024**3):
    path=Path(path); output=Path(output); output.mkdir(parents=True,exist_ok=True)
    with path.open('rb') as f: magic=f.read(256)
    if magic.lstrip().lower().startswith((b'<!doctype',b'<html',b'<?xml',b'version https://git-lfs')):
        raise ValueError('Downloaded object is HTML/XML or an LFS pointer, not profiles')
    zipped=magic.startswith(b'\x1f\x8b')
    if path.suffix=='.gz' and not zipped: raise ValueError('Gzip filename does not contain gzip bytes')
    if zipped:
        # Read through gzip to verify the complete trailer/CRC; no phenotype processing.
        size=0
        with gzip.open(path,'rb') as f:
            for c in iter(lambda:f.read(1024*1024),b''):
                size+=len(c)
                if size>max_uncompressed_bytes: raise ValueError('Uncompressed CSV exceeds cap')
    else:
        size=path.stat().st_size
        if size>max_uncompressed_bytes: raise ValueError('Uncompressed CSV exceeds cap')
    opener=gzip.open if zipped else open
    with opener(path,'rt',encoding='utf-8-sig',newline='') as f:
        reader=csv.reader(f)
        header=next(reader)
        if len(header)!=len(set(header)): raise ValueError('Duplicate header columns')
        features=[x for x in header if x.startswith(FEATURE_PREFIXES)]
        if len(features)<10: raise ValueError('Too few recognized CellProfiler measurement columns')
        platecol=next((x for x in PLATE_COLUMNS if x in header),None)
        wellcol=next((x for x in WELL_COLUMNS if x in header),None)
        if not wellcol: raise ValueError('Well identity column not recognized; manual schema review needed')
        sample=[]
        for _ in range(sample_rows):
            row=next(reader,None)
            if row is None: break
            if len(row)!=len(header): raise ValueError('Sample row/header width mismatch')
            if platecol and row[header.index(platecol)]!=expected_plate: raise ValueError('Wrong plate in profile sample')
            if not re.fullmatch(r'[A-Pa-p](?:0?[1-9]|1[0-9]|2[0-4])',row[header.index(wellcol)]): raise ValueError('Unexpected well identifier format')
            for feature in features[:10]:
                value=row[header.index(feature)]
                if value.strip(): float(value)  # blanks/nonfinite retained; full QC is Stage 1/3
            sample.append(row)
    if len(sample)!=sample_rows: raise ValueError('Too few sample rows')
    (output/'profile-header.txt').write_text('\n'.join(header)+'\n')
    with (output/'profile-preview.csv').open('w',newline='') as f:
        w=csv.writer(f); w.writerow(header); w.writerows(sample)
    summary={'source_file':path.name,'source_sha256':sha256(path),'source_bytes':path.stat().st_size,
             'encoding':'gzip CSV' if zipped else 'CSV','uncompressed_bytes':size,
             'columns':len(header),'recognized_measurement_columns':len(features),'sample_rows_read':len(sample),
             'plate_column':platecol,'well_column':wellcol,
             'identity_caveat':None if platecol else 'Plate inferred from officially listed object path only; full validation pending Stage 1',
             'full_row_count':None,'scope':'Header and first sample rows only; no biological computation; full schema/QC pending Stage 1'}
    dump(output/'profile-inspection.json',summary)
    return summary


def acquire(config, output):
    out=Path(output); fetch=Fetcher(out)
    if config['repository']!=REPO or config['bucket']!='cellpainting-gallery': raise ValueError('Unexpected source configuration')
    if not re.fullmatch(r'BR[0-9]+',config['plate']): raise ValueError('Invalid plate identifier')
    if not config['prefix'].startswith('cpg0000-jump-pilot/source_4/workspace/backend/') or not config['prefix'].endswith('/'+config['plate']+'/'):
        raise ValueError('Unexpected pilot backend prefix')
    limit=config['max_metadata_bytes']
    rev_record=fetch.fetch(f'https://api.github.com/repos/{REPO}/commits/{quote(config["source_ref"],safe="")}', 'provenance/upstream-commit.json',limit)
    rev=json.loads((out/rev_record['destination']).read_text())['sha']
    if not re.fullmatch(r'[0-9a-f]{40}',rev): raise ValueError('Invalid upstream source revision')
    raw_base=f'https://raw.githubusercontent.com/{REPO}/{rev}/'
    meta=fetch.fetch(raw_base+config['metadata_path'],'data/experiment-metadata.tsv',limit)
    meta_check=validate_metadata(out/meta['destination'],config['plate'],config['batch'])
    meta['result']='VERIFIED_TSV'; fetch._save(); dump(out/'provenance/metadata-inspection.json',meta_check)
    # Source README documents backend CSVs as well-level, prior to normalization.
    readme=fetch.fetch(raw_base+'README.md','provenance/upstream-README.md',limit)
    text=(out/readme['destination']).read_text()
    if 'backend/' not in text or 'well-level' not in text: raise ValueError('Upstream processing-stage description needs review')
    readme['result']='VERIFIED_SOURCE_TEXT'; fetch._save()
    items=[]; token=None
    for i in range(config['max_listing_pages']):
        args={'list-type':'2','prefix':config['prefix'],'max-keys':'1000'}
        if token: args['continuation-token']=token
        listed=fetch.fetch(f'https://{BUCKET_HOST}/?'+urlencode(args),f'provenance/s3-list-{i+1}.xml',limit)
        batch,token=parse_listing((out/listed['destination']).read_bytes()); items.extend(batch)
        listed['result']='VERIFIED_OBJECT_LIST'; fetch._save()
        if not token: break
    if token: raise ValueError('Listing exceeds bounded page limit')
    dump(out/'manifests/s3-objects.json',items)
    selected=select_raw(items,config['prefix'],config['plate'],config['max_profile_bytes'])
    url=f'https://{BUCKET_HOST}/'+quote(selected['key'],safe='/')
    head=fetch.fetch(url,'provenance/profile-head-placeholder',config['max_profile_bytes'],method='HEAD')
    headers={k.lower():v for k,v in head['headers'].items()}
    if int(headers.get('content-length','-1'))!=selected['size']: raise ValueError('Listing and HEAD object size disagree')
    if selected.get('etag') and headers.get('etag')!=selected['etag']: raise ValueError('Listing and HEAD ETag disagree')
    extra={'If-Match':headers['etag']} if headers.get('etag') else {}
    profile=fetch.fetch(url,'data/'+selected['key'].split('/')[-1],config['max_profile_bytes'],extra_headers=extra)
    if profile['bytes']!=selected['size']: raise ValueError('Full downloaded byte count differs from inventory')
    inspected=validate_profile(out/profile['destination'],config['plate'],out/'evidence',config['sample_rows'],config['max_uncompressed_bytes'])
    profile.update({'result':'VERIFIED_PROFILE_BYTES_AND_SAMPLE','source_revision':rev,'source_stage':'unnormalized well-level aggregate (upstream backend convention)','upstream_checksum':None,'s3_etag':headers.get('etag'),'s3_version_id':headers.get('x-amz-version-id')})
    fetch._save()
    dump(out/'provenance/acquisition-summary.json',{'source_revision':rev,'metadata':meta_check,'selected_object':selected,'profile':inspected})
    with (out/'manifests/access-inventory.tsv').open('w',newline='') as f:
        names=['url','method','destination','result','bytes','sha256','status','source_revision','source_stage','s3_etag','s3_version_id','checksum_status']
        w=csv.DictWriter(f,fieldnames=names,delimiter='\t',extrasaction='ignore'); w.writeheader(); w.writerows(fetch.records)
    return {'source_revision':rev,'profile':inspected,'selected_object':selected}


def lock_from_install_report(report_path, output_path):
    report=json.loads(Path(report_path).read_text()); lines=[]
    for p in report['install']:
        name=p['metadata']['name']; version=p['metadata']['version']
        info=p['download_info']
        if urlparse(info['url']).hostname!='files.pythonhosted.org': raise ValueError('Unexpected non-PyPI package source')
        hash_=info.get('archive_info',{}).get('hashes',{}).get('sha256')
        if not hash_ or not re.fullmatch('[0-9a-f]{64}',hash_): raise ValueError('Package hash missing from installation report')
        lines.append(f'{name}=={version} --hash=sha256:{hash_}')
    Path(output_path).write_text('# Resolved artifacts for this Python/OS/architecture only. Not cross-platform.\n'+'\n'.join(sorted(lines,key=str.lower))+'\n')
    return {'packages':len(lines), 'sha256':sha256(output_path), 'scope':'Stage 0 resolved wheel artifacts, not yet validated against published biology'}
