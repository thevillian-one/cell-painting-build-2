"""Stage 1 data qualification helpers. No phenotype scoring or preprocessing.

Only provenance, schemas, well identities, metadata joins and file integrity.
Standard library only: no scientific package installation needed for this substage.
"""
from __future__ import annotations
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import math
import re
from collections import Counter
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse, urlencode, quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
import time

BUCKET = 'cellpainting-gallery.s3.amazonaws.com'
HOSTS = {'api.github.com', 'raw.githubusercontent.com', 'media.githubusercontent.com', BUCKET}
FEATURE_PREFIXES = ('Cells_', 'Cytoplasm_', 'Nuclei_')
PILOT_REPO = 'jump-cellpainting/2024_Chandrasekaran_NatureMethods_CPJUMP1'
PILOT_REV = '56845c7d4dc322652952783d91dae0ffef47829f'
BATCH = '2020_11_04_CPJUMP1'
PLATES = ('BR00117015', 'BR00117016', 'BR00117017', 'BR00117019')


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def safe_path(root, relative):
    p = PurePosixPath(str(relative))
    if p.is_absolute() or '..' in p.parts or '\\' in str(relative):
        raise ValueError(f'Unsafe relative path: {relative}')
    root = Path(root).resolve()
    out = root / p.as_posix()
    if out.resolve() == root or not out.resolve().is_relative_to(root):
        raise ValueError('Path escapes destination')
    return out


def dump(path, obj):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, allow_nan=False, default=str) + '\n', encoding='utf-8')


def write_tsv(path, rows, fields):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter='\t', lineterminator='\n', extrasaction='raise')
        w.writeheader()
        for row in rows:
            w.writerow(row)


def verify_checksums(root, filename='CHECKSUMS.sha256'):
    root = Path(root)
    rows = []
    seen = set()
    for line in (root / filename).read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        m = re.fullmatch(r'([a-fA-F0-9]{64}) [ *](.+)', line)
        if not m:
            raise ValueError('Malformed checksum line')
        expected, name = m.groups()
        if name in seen:
            raise ValueError('Duplicate checksum path')
        seen.add(name)
        p = safe_path(root, name)
        actual = sha256(p) if p.is_file() else None
        rows.append({'path': name, 'expected': expected.lower(), 'actual': actual, 'passed': actual == expected.lower()})
    if not rows:
        raise ValueError('Empty checksum manifest')
    return rows


def write_checksums(root, filename='CHECKSUMS.sha256'):
    root = Path(root)
    paths = sorted(p for p in root.rglob('*') if p.is_file() and p != root / filename
                   and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts)
    (root / filename).write_text(''.join(f'{sha256(p)}  {p.relative_to(root).as_posix()}\n' for p in paths), encoding='utf-8')
    return len(paths)


def canonical_well(x):
    m = re.fullmatch(r'([A-Pa-p])0*([1-9]|1[0-9]|2[0-4])', str(x).strip())
    if not m:
        raise ValueError(f'Not a 384-well coordinate: {x}')
    return f'{m.group(1).upper()}{int(m.group(2)):02d}'


def open_text(path):
    path = Path(path)
    if path.name.endswith('.gz'):
        return gzip.open(path, 'rt', encoding='utf-8-sig', newline='')
    return path.open('r', encoding='utf-8-sig', newline='')


def inspect_profile(path, expected_plate=None, numeric_qc=True):
    """Read all rows, checking structure and missingness, never treatment effects."""
    p = Path(path)
    start = time.monotonic()
    with open_text(p) as f:
        reader = csv.reader(f)
        header = next(reader)
        if len(header) != len(set(header)):
            raise ValueError('Duplicate feature/header names')
        for field in ('Metadata_Plate', 'Metadata_Well'):
            if field not in header:
                raise ValueError('Missing identifier column: ' + field)
        pi, wi = header.index('Metadata_Plate'), header.index('Metadata_Well')
        features = [x for x in header if x.startswith(FEATURE_PREFIXES)]
        indices = [header.index(x) for x in features]
        missing = Counter(); nonnumeric = Counter(); infinite = Counter()
        seen = set(); wells = []
        for rownum, row in enumerate(reader, 2):
            if len(row) != len(header):
                raise ValueError(f'Row {rownum}: {len(row)} fields, expected {len(header)}')
            plate, well = row[pi].strip(), canonical_well(row[wi])
            if expected_plate is not None and plate != expected_plate:
                raise ValueError('Unexpected plate identity')
            key = (plate, well)
            if key in seen:
                raise ValueError('Duplicate plate/well identity')
            seen.add(key)
            wells.append({'plate': plate, 'well': well, 'source_row': rownum})
            if numeric_qc:
                for j in indices:
                    v = row[j].strip()
                    if v.lower() in ('', 'na', 'nan', 'null', 'none'):
                        missing[header[j]] += 1
                        continue
                    try:
                        x = float(v)
                        if math.isnan(x): missing[header[j]] += 1
                        elif not math.isfinite(x): infinite[header[j]] += 1
                    except ValueError:
                        nonnumeric[header[j]] += 1
    if not wells or not features:
        raise ValueError('No well rows or recognized measurement columns')
    rows_by_plate = Counter(w['plate'] for w in wells)
    expected_wells = {f'{chr(65+r)}{c:02d}' for r in range(16) for c in range(1,25)}
    missing_wells = {plate: sorted(expected_wells - {w['well'] for w in wells if w['plate']==plate}) for plate in rows_by_plate}
    summary = {'file':p.name,'bytes':p.stat().st_size,'sha256':sha256(p),'rows':len(wells),
               'unique_plate_wells':len(seen),'columns':len(header),'recognized_measurements':len(features),
               'measurement_compartments':dict(Counter(x.split('_')[0] for x in features)),
               'row_counts_by_plate':dict(rows_by_plate),'missing_wells':missing_wells,
               'missing_measurement_cells':sum(missing.values()),'infinite_measurement_cells':sum(infinite.values()),
               'nonnumeric_measurement_cells':sum(nonnumeric.values()),'features_with_missing':len(missing),
               'all_missing_features':[x for x,n in missing.items() if n==len(wells)],
               'structural_checks_passed':True,'numeric_qc_run':numeric_qc,
               'scope':'Schema, identity and missingness only; no compound scoring, normalization or feature selection.',
               'elapsed_seconds':time.monotonic()-start}
    quality = [{'feature':x,'missing':missing[x],'infinite':infinite[x],'nonnumeric':nonnumeric[x]} for x in features]
    return summary, header, wells, quality


def read_metadata(path, max_rows=1000000):
    p = Path(path)
    sep = '\t' if '.tsv' in p.name else ','
    with open_text(p) as f:
        reader = csv.DictReader(f, delimiter=sep)
        if not reader.fieldnames or len(reader.fieldnames)!=len(set(reader.fieldnames)):
            raise ValueError('Missing/duplicate metadata header')
        rows = []
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise ValueError('Metadata row width differs from header')
            rows.append(row)
            if len(rows)>max_rows: raise ValueError('Metadata row limit exceeded')
    return reader.fieldnames, rows


def pilot_design(path):
    header, rows = read_metadata(path)
    required={'Batch','Plate_Map_Name','Assay_Plate_Barcode','Perturbation','Cell_type','Time','Density',
              'Antibiotics','Cell_line','Time_delay','Times_imaged','Anomaly'}
    if not required.issubset(header): raise ValueError('Pilot metadata fields are incomplete')
    out=[]
    for plate in PLATES:
        matches=[r for r in rows if r['Batch']==BATCH and r['Assay_Plate_Barcode']==plate]
        if len(matches)!=1: raise ValueError(f'{plate}: expected one metadata record, found {len(matches)}')
        r=matches[0]
        expected={'Perturbation':'compound','Cell_type':'A549','Time':'48','Density':'100',
                  'Antibiotics':'absent','Cell_line':'Parental','Time_delay':'Day0','Times_imaged':'1','Anomaly':'none'}
        if any(r[k]!=v for k,v in expected.items()): raise ValueError(f'{plate}: candidate design changed')
        out.append(r)
    return out


def strict_well_join(profile_wells, platemap_rows, well_col, id_col):
    """No inner-join dropping or uncontrolled many-to-many joins."""
    mapping={}
    for row in platemap_rows:
        key=canonical_well(row[well_col])
        if key in mapping: raise ValueError('Duplicate platemap well')
        mapping[key]=row
    result=[]
    for well in profile_wells:
        key=canonical_well(well['well'])
        if key not in mapping: raise ValueError('Missing platemap well: '+key)
        row=mapping[key]
        result.append({**well,'sample_id':row.get(id_col,''),'platemap_row':row})
    return result


class Fetcher:
    """Bounded, anonymous HTTPS requests with hashes and explicit failure records."""
    def __init__(self, root, total_limit=768*1024*1024, opener=urlopen):
        self.root=Path(root);self.records=[];self.total=0;self.limit=total_limit;self.opener=opener

    def save(self):
        dump(self.root/'manifests/http-requests.json',self.records)

    def fetch(self,url,relative,limit,expected_size=None,expected_hash=None):
        parsed=urlparse(url)
        if parsed.scheme!='https' or parsed.hostname not in HOSTS or parsed.username or parsed.password:
            raise ValueError('Unapproved URL')
        dest=safe_path(self.root,relative);dest.parent.mkdir(parents=True,exist_ok=True)
        rec={'url':url,'destination':relative,'started_utc':utc(),'limit_bytes':limit,'status':'STARTED'}
        self.records.append(rec);self.save();t=time.monotonic();tmp=dest.with_name(dest.name+'.partial')
        try:
            req=Request(url,headers={'User-Agent':'CellPaintingStage1/1.0','Accept-Encoding':'identity'})
            with self.opener(req,timeout=40) as r:
                if urlparse(r.url).hostname not in HOSTS or urlparse(r.url).scheme!='https':
                    raise ValueError('Unapproved redirect')
                if r.status!=200:raise ValueError('Expected complete HTTP 200 bytes')
                length=r.headers.get('Content-Length')
                if length is not None and (int(length)>limit or self.total+int(length)>self.limit):
                    raise ValueError('Download size exceeds configured limit')
                h=hashlib.sha256();size=0
                with tmp.open('wb') as f:
                    while True:
                        b=r.read(1024*1024)
                        if not b:break
                        size+=len(b);self.total+=len(b)
                        if size>limit or self.total>self.limit:raise ValueError('Transfer limit exceeded')
                        h.update(b);f.write(b)
                if length is not None and size!=int(length):raise ValueError('Truncated HTTP response')
                if expected_size is not None and size!=expected_size:raise ValueError('Size differs from listing')
                if expected_hash is not None and h.hexdigest()!=expected_hash:raise ValueError('SHA-256 mismatch')
                tmp.replace(dest)
                rec.update({'status':'DOWNLOADED','http_status':r.status,'bytes':size,'sha256':h.hexdigest(),
                            'effective_url':r.url,'etag':r.headers.get('ETag'),
                            'last_modified':r.headers.get('Last-Modified'),'seconds':time.monotonic()-t})
            return dest
        except Exception as e:
            rec.update({'status':'FAILED','error':f'{type(e).__name__}: {e}','seconds':time.monotonic()-t})
            if tmp.exists():tmp.unlink()
            raise
        finally:self.save()

    def github_tree(self,repo,ref=None):
        slug=repo.replace('/','__')
        if ref is None:
            p=self.fetch(f'https://api.github.com/repos/{repo}',f'provenance/repos/{slug}/repository.json',2*1024*1024)
            info=json.loads(p.read_text());ref=info['default_branch']
        p=self.fetch(f'https://api.github.com/repos/{repo}/commits/{quote(ref,safe="")}',
                     f'provenance/repos/{slug}/commit.json',4*1024*1024)
        info=json.loads(p.read_text());rev=info['sha']
        if not re.fullmatch('[a-f0-9]{40}',rev):raise ValueError('Invalid source revision')
        if re.fullmatch('[a-f0-9]{40}',ref) and rev!=ref:raise ValueError('Pinned source revision mismatch')
        p=self.fetch(f'https://api.github.com/repos/{repo}/git/trees/{rev}?recursive=1',
                     f'provenance/repos/{slug}/tree.json',32*1024*1024)
        tree=json.loads(p.read_text())
        if tree.get('truncated'):raise ValueError('GitHub source tree is truncated; need explicit subtree traversal')
        return rev,tree['tree']

    def github_blob(self,repo,rev,entry,limit=16*1024*1024):
        """Fetch only exact tree entries; handle LFS without treating its pointer as data."""
        if entry.get('type')!='blob':raise ValueError('Not a Git blob')
        path=entry['path'];slug=repo.replace('/','__')
        dest=f'source-data/repos/{slug}/{path}'
        p=self.fetch(f'https://raw.githubusercontent.com/{repo}/{rev}/{quote(path,safe="/")}',dest,limit)
        size=p.stat().st_size
        b=p.read_bytes() if size<1024 else None
        if b and b.startswith(b'version https://git-lfs.github.com/spec/v1'):
            text=b.decode();hm=re.search(r'^oid sha256:([a-f0-9]{64})$',text,re.M);sm=re.search(r'^size (\d+)$',text,re.M)
            if not hm or not sm:raise ValueError('Malformed LFS pointer')
            data_size=int(sm[1])
            if data_size>limit:raise ValueError('LFS content exceeds per-object limit')
            pointer=safe_path(self.root,f'provenance/lfs/{slug}/{path}.pointer');pointer.parent.mkdir(parents=True,exist_ok=True)
            pointer.write_bytes(b);p.unlink()
            p=self.fetch(f'https://media.githubusercontent.com/media/{repo}/{rev}/{quote(path,safe="/")}',dest,limit,
                         expected_size=data_size,expected_hash=hm[1])
        else:
            # Verify the Git blob hash from the pinned repository tree.
            h=hashlib.sha1();h.update(f'blob {size}\0'.encode())
            with p.open('rb') as f:
                for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
            if entry.get('sha') and h.hexdigest()!=entry['sha']:raise ValueError('Pinned Git blob hash mismatch')
        return p

    def s3_list(self,prefix,*,delimiter=None,max_pages=30,label=None):
        """No listing of all images. Must name a bounded dataset workspace prefix."""
        if not prefix.startswith(('cpg0000-jump-pilot/','cpg0001-cellpainting-protocol/','cpg0002-jump-scope/')):
            raise ValueError('Not an allowed dataset prefix')
        if '/images/' in prefix and delimiter is None:raise ValueError('Recursive raw image listing disabled')
        label=label or hashlib.sha256((prefix+str(delimiter)).encode()).hexdigest()[:16]
        objects=[];prefixes=[];token=None;seen_tokens=set()
        ns={'s':'http://s3.amazonaws.com/doc/2006-03-01/'}
        for page in range(1,max_pages+1):
            params={'list-type':'2','prefix':prefix,'max-keys':'1000'}
            if delimiter:params['delimiter']=delimiter
            if token:params['continuation-token']=token
            p=self.fetch('https://'+BUCKET+'/?'+urlencode(params),f'provenance/s3/{label}-{page}.xml',4*1024*1024)
            doc=ET.fromstring(p.read_bytes())
            if doc.tag!='{http://s3.amazonaws.com/doc/2006-03-01/}ListBucketResult':raise ValueError('Not an S3 object listing')
            for c in doc.findall('s:Contents',ns):
                obj={'key':c.findtext('s:Key',namespaces=ns),'bytes':int(c.findtext('s:Size',namespaces=ns)),
                     'etag':c.findtext('s:ETag',namespaces=ns),'last_modified':c.findtext('s:LastModified',namespaces=ns),
                     'listing_evidence':str(p.relative_to(self.root))}
                if not obj['key'].startswith(prefix):raise ValueError('Listing key outside requested prefix')
                objects.append(obj)
            prefixes.extend(x.findtext('s:Prefix',namespaces=ns) for x in doc.findall('s:CommonPrefixes',ns))
            if doc.findtext('s:IsTruncated',namespaces=ns)!='true':return objects,prefixes
            token=doc.findtext('s:NextContinuationToken',namespaces=ns)
            if not token or token in seen_tokens:raise ValueError('Invalid S3 continuation')
            seen_tokens.add(token)
        raise ValueError('Listing page cap reached; inventory is incomplete')


def raw_profile_candidates(objects):
    """Conservative raw-aggregate identity. Other files remain inventory-only."""
    out=[]
    for obj in objects:
        p=PurePosixPath(obj['key']);base=p.name
        if '/backend/' not in str(p):continue
        if base not in (p.parent.name+'.csv',p.parent.name+'.csv.gz'):continue
        if re.search('normaliz|feature_select|spher|augment',base,re.I):continue
        out.append(obj)
    return sorted(out,key=lambda x:x['key'])
