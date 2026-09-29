"""Stage 1B integrity and experimental-identity checks. No phenotype analysis."""
from __future__ import annotations
import csv, gzip, hashlib, json, math, re
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

PLATES = ('BR00117015', 'BR00117016', 'BR00117017', 'BR00117019')
FEATURE_PREFIXES = ('Cells_', 'Cytoplasm_', 'Nuclei_')
CHANNELS = ('DNA', 'ER', 'RNA', 'AGP', 'Mito')


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def dump(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')


def safe_path(root, relative):
    p = PurePosixPath(relative)
    if p.is_absolute() or '..' in p.parts or '\\' in str(p) or ':' in str(p):
        raise ValueError('Unsafe relative path: ' + str(p))
    root = Path(root).resolve(); out = root.joinpath(*p.parts)
    if not out.resolve().is_relative_to(root) or out.resolve() == root:
        raise ValueError('Path escapes root')
    return out


def read_table(path, *, delimiter=None, encoding='utf-8-sig', max_rows=1000000):
    """Strict decoding. A legacy override must be explicitly supplied for its source."""
    p = Path(path)
    delimiter = delimiter or ('\t' if '.tsv' in p.name or p.suffix == '.txt' else ',')
    opener = gzip.open if p.suffix == '.gz' else open
    with opener(p, 'rt', encoding=encoding, errors='strict', newline='') as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        fields = reader.fieldnames
        if not fields or len(fields) != len(set(fields)) or any(not x for x in fields):
            raise ValueError('Missing or duplicate table column')
        rows = []
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise ValueError('Table row width differs from header')
            rows.append(row)
            if len(rows) > max_rows:
                raise ValueError('Table row cap exceeded')
    return fields, rows


def write_table(path, rows, fields=None):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    fields = fields or (list(rows[0]) if rows else [])
    if not fields: raise ValueError('Explicit fields required for empty table')
    with p.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter='\t', lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)


def well(value):
    m = re.fullmatch(r'([A-Pa-p])0*([1-9]|1[0-9]|2[0-4])', str(value).strip())
    if not m: raise ValueError('Invalid 384-well coordinate: ' + str(value))
    return m[1].upper() + m[2].zfill(2)


def annotation_map(rows):
    out = {}
    for row in rows:
        key = row['broad_sample'].strip()
        if key in out: raise ValueError('Duplicate sample annotation: ' + key)
        if not key and not (row.get('pert_type') == 'control' and row.get('control_type') == 'negcon'):
            raise ValueError('Blank sample has no explicit negative-control annotation')
        out[key] = row
    return out


def join_wells(wells, layout, annotations=None):
    """Join identities exactly; blanks require explicit negcon evidence, never solvent alone."""
    a = annotation_map(annotations) if annotations is not None else None
    mapping = {}
    for row in layout:
        key = well(row['well_position'])
        if key in mapping: raise ValueError('Duplicate platemap position')
        mapping[key] = row
    result = []; seen = set()
    for row in wells:
        plate = row['plate']; key = well(row['well'])
        if (plate, key) in seen: raise ValueError('Duplicate profile well')
        seen.add((plate, key))
        if key not in mapping: raise ValueError('Unmapped profile position: ' + key)
        lay = mapping[key]; sample = lay['broad_sample'].strip()
        if a is not None and sample not in a: raise ValueError('Unmapped sample: ' + sample)
        ann = a[sample] if a is not None else lay
        neg = ann.get('pert_type') == 'control' and ann.get('control_type') == 'negcon'
        if not sample and not neg: raise ValueError('Blank sample not explicitly negative control')
        if sample and neg: raise ValueError('Unexpected nonblank negative-control identity')
        result.append({**row, 'well': key, 'sample_id': sample if sample else 'DMSO_NEGCON',
                       'source_broad_sample': sample, 'compound_name': ann.get('pert_iname', ''),
                       'source_inchikey': ann.get('InChIKey', ''),
                       'chemical_identity_status': ('negative_control' if neg else 'source_annotated' if ann.get('InChIKey') else 'undisclosed_or_missing; retain within source, no automatic cross-study match'),
                       'role': 'negative_control' if neg else ('positive_control' if ann.get('control_type','').startswith('poscon') else 'treatment'),
                       'control_type': ann.get('control_type', ''), 'source_pert_type': ann.get('pert_type', ''),
                       'source_library_mmoles_per_liter': lay.get('mmoles_per_liter', ''),
                       'solvent': lay.get('solvent', '')})
    return result


def design_pair_counts(rows, different_position=False):
    """Count design-eligible positives and negatives; no similarities or AP are calculated."""
    result = []
    for q in rows:
        if q['role'] == 'negative_control': continue
        candidates = [r for r in rows if r['physical_plate_id'] != q['physical_plate_id'] and
                      r['condition_id'] == q['condition_id'] and
                      (not different_position or r['well'] != q['well'])]
        pos = [r for r in candidates if r['sample_id'] == q['sample_id'] and r['role'] != 'negative_control']
        neg = [r for r in candidates if r['role'] == 'negative_control']
        result.append({'query_id': q['physical_plate_id'] + '/' + q['well'], 'sample_id': q['sample_id'],
                       'eligible_positives': len(pos), 'eligible_negatives': len(neg),
                       'assessable_by_design': bool(pos and neg), 'different_position_required': different_position})
    return result


def inspect_profile(path, expected_plate, *, numeric_qc=False):
    """All rows: schema/identity; optional finite-value audit for existing development pilot only."""
    path = Path(path); opener = gzip.open if path.suffix == '.gz' else open
    with opener(path, 'rt', encoding='utf-8-sig', errors='strict', newline='') as f:
        reader = csv.reader(f); header = next(reader)
        if len(header) != len(set(header)): raise ValueError('Duplicate profile columns')
        if not {'Metadata_Plate','Metadata_Well'}.issubset(header): raise ValueError('Missing profile identity')
        pi, wi = header.index('Metadata_Plate'), header.index('Metadata_Well')
        jj = [i for i, name in enumerate(header) if name.startswith(FEATURE_PREFIXES)]
        if not jj: raise ValueError('No compartment-prefixed measurements')
        seen=set(); rows=[]; missing=nonfinite=bad=0
        for n, vals in enumerate(reader, 2):
            if len(vals) != len(header): raise ValueError('Malformed profile row ' + str(n))
            if vals[pi].strip() != expected_plate: raise ValueError('Unexpected profile plate')
            w = well(vals[wi])
            if w in seen: raise ValueError('Duplicate profile well')
            seen.add(w); rows.append({'plate':expected_plate, 'well':w, 'source_row':n})
            if numeric_qc:
                for j in jj:
                    v=vals[j].strip()
                    if v.lower() in ('','na','nan','null','none'): missing+=1; continue
                    try:
                        if not math.isfinite(float(v)): nonfinite+=1
                    except ValueError: bad+=1
        expected={f'{chr(65+r)}{c:02d}' for r in range(16) for c in range(1,25)}
        if not rows: raise ValueError('No profile rows')
        return {'rows':len(rows), 'columns':len(header), 'compartment_prefixed_columns':len(jj),
                'missing_wells':sorted(expected-seen),'numeric_qc_run':numeric_qc,
                'missing_numeric_cells':missing if numeric_qc else None,
                'nonfinite_numeric_cells':nonfinite if numeric_qc else None,
                'nonnumeric_cells':bad if numeric_qc else None}, header, rows


def verify_manifest(root, filename):
    root=Path(root); out=[]; seen=set()
    for line in (root/filename).read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        m=re.fullmatch(r'([a-f0-9]{64})  (.+)',line)
        if not m: raise ValueError('Malformed checksum record')
        digest,name=m.groups()
        if name in seen: raise ValueError('Duplicate checksum path')
        seen.add(name); p=safe_path(root,name)
        if not p.is_file() or sha256(p)!=digest: raise ValueError('Checksum mismatch/missing: '+name)
        out.append(name)
    if not out: raise ValueError('Empty checksum manifest')
    return out


def write_checksums(root, filename='CHECKSUMS.sha256'):
    root=Path(root)
    pp=sorted(p for p in root.rglob('*') if p.is_file() and p!=root/filename and
              not any(s in p.parts for s in ['__pycache__','.pytest_cache','.git']))
    (root/filename).write_text(''.join(f'{sha256(p)}  {p.relative_to(root).as_posix()}\n' for p in pp),encoding='utf-8')
    return len(pp)
