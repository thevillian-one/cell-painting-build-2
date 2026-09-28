"""Offline infrastructure fixtures. These are not experimental Cell Painting data."""
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import pytest
import yaml
import preflight_support as s
from smoke import known_answer, MODULES

PLATE='BR00117015'
PREFIX='cpg0000-jump-pilot/source_4/workspace/backend/2020_11_04_CPJUMP1/'+PLATE+'/'
ROOT=Path(__file__).resolve().parents[1]


def fixture_csv(plate=PLATE):
    header=['Metadata_Plate','Metadata_Well']+[f'Cells_Fixture_{i}' for i in range(10)]
    f=io.StringIO(); w=csv.writer(f); w.writerow(header)
    for well in ['A01','A02','A03']: w.writerow([plate,well]+list(range(10)))
    return f.getvalue().encode()


def test_known_ap_cases():
    assert known_answer()['passed']


def test_metadata_identity(tmp_path):
    p=tmp_path/'meta.tsv'; p.write_text('Batch\tAssay_Plate_Barcode\tPerturbation\tCell_type\tTime\n2020_11_04_CPJUMP1\tBR00117015\tcompound\tA549\t48\n')
    result=s.validate_metadata(p,PLATE,'2020_11_04_CPJUMP1')
    assert result['candidate_row']['Assay_Plate_Barcode']==PLATE
    with pytest.raises(ValueError): s.validate_metadata(p,'BR00000000','2020_11_04_CPJUMP1')


def test_metadata_duplicate_identity_rejected(tmp_path):
    p=tmp_path/'meta.tsv'; p.write_text('Batch\tAssay_Plate_Barcode\tPerturbation\tCell_type\tTime\n'+('b\tp\tc\tx\t48\n'*2))
    with pytest.raises(ValueError,match='not unique'): s.validate_metadata(p,'p','b')


def test_listing():
    xml=b'<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><IsTruncated>false</IsTruncated><Contents><Key>a.csv</Key><Size>42</Size><ETag>"test"</ETag></Contents></ListBucketResult>'
    rows,token=s.parse_listing(xml)
    assert rows[0]['size']==42 and token is None


def test_listing_pagination_requires_token():
    xml=b'<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><IsTruncated>true</IsTruncated></ListBucketResult>'
    with pytest.raises(ValueError,match='continuation'): s.parse_listing(xml)


def test_reject_error_listing():
    with pytest.raises(ValueError): s.parse_listing(b'<Error><Code>AccessDenied</Code></Error>')


def test_selects_only_exact_raw_aggregate():
    rows=[{'key':PREFIX+PLATE+'_normalized.csv.gz','size':30},
          {'key':PREFIX+PLATE+'.sqlite','size':50}, {'key':PREFIX+PLATE+'.csv','size':80}]
    assert s.select_raw(rows,PREFIX,PLATE,100)['key']==PREFIX+PLATE+'.csv'


def test_prefers_raw_gzip():
    rows=[{'key':PREFIX+PLATE+'.csv','size':80},{'key':PREFIX+PLATE+'.csv.gz','size':40}]
    assert s.select_raw(rows,PREFIX,PLATE,100)['key'].endswith('.csv.gz')


def test_oversize_is_not_downloaded():
    with pytest.raises(ValueError): s.select_raw([{'key':PREFIX+PLATE+'.csv','size':999}],PREFIX,PLATE,100)


def test_no_normalized_substitution():
    with pytest.raises(ValueError): s.select_raw([{'key':PREFIX+PLATE+'_normalized.csv','size':99}],PREFIX,PLATE,100)

@pytest.mark.parametrize('compressed',[False,True])
def test_profile_header_sample(tmp_path,compressed):
    raw=fixture_csv(); p=tmp_path/('test.csv.gz' if compressed else 'test.csv')
    p.write_bytes(gzip.compress(raw) if compressed else raw)
    r=s.validate_profile(p,PLATE,tmp_path/'evidence')
    assert r['columns']==12 and r['sample_rows_read']==3
    assert r['source_sha256']==hashlib.sha256(p.read_bytes()).hexdigest()
    assert r['full_row_count'] is None
    assert len((tmp_path/'evidence/profile-header.txt').read_text().splitlines())==12

@pytest.mark.parametrize('body',[b'<html>Error</html>',b'<?xml version="1.0"?><Error/>',b'version https://git-lfs.github.com/spec/v1\n'])
def test_no_html_xml_lfs_as_data(tmp_path,body):
    p=tmp_path/'bad.csv'; p.write_bytes(body)
    with pytest.raises(ValueError): s.validate_profile(p,PLATE,tmp_path/'out')


def test_wrong_plate_rejected(tmp_path):
    p=tmp_path/'bad.csv'; p.write_bytes(fixture_csv('BR00000000'))
    with pytest.raises(ValueError,match='Wrong plate'): s.validate_profile(p,PLATE,tmp_path/'out')


def test_wrong_gzip_magic(tmp_path):
    p=tmp_path/'bad.csv.gz'; p.write_bytes(fixture_csv())
    with pytest.raises(ValueError,match='Gzip'): s.validate_profile(p,PLATE,tmp_path/'out')


def test_gzip_integrity_checked(tmp_path):
    p=tmp_path/'bad.csv.gz'; p.write_bytes(gzip.compress(fixture_csv())[:-5])
    with pytest.raises((EOFError,OSError)): s.validate_profile(p,PLATE,tmp_path/'out')


def test_uncompressed_size_cap(tmp_path):
    p=tmp_path/'bad.csv.gz'; p.write_bytes(gzip.compress(fixture_csv()))
    with pytest.raises(ValueError,match='cap'): s.validate_profile(p,PLATE,tmp_path/'out',max_uncompressed_bytes=12)


def test_duplicate_headers_rejected(tmp_path):
    raw=fixture_csv().replace(b'Cells_Fixture_1,',b'Cells_Fixture_0,')
    p=tmp_path/'bad.csv'; p.write_bytes(raw)
    with pytest.raises(ValueError,match='Duplicate'): s.validate_profile(p,PLATE,tmp_path/'out')


def test_fetch_blocks_unknown_host(tmp_path):
    with pytest.raises(ValueError,match='approved'): s.Fetcher(tmp_path).fetch('https://example.com/file.csv','data/x.csv',100)


def test_fetch_path_traversal_rejected(tmp_path):
    with pytest.raises(ValueError,match='escapes'): s.Fetcher(tmp_path).fetch('https://raw.githubusercontent.com/test','../outside.csv',100)

class FakeResponse(io.BytesIO):
    status=200
    url='https://raw.githubusercontent.com/test'
    def __init__(self,content,claimed=None):
        super().__init__(content); self.headers={'Content-Length':str(len(content) if claimed is None else claimed)}


def test_fetch_checks_size_and_logs(tmp_path,monkeypatch):
    monkeypatch.setattr(s,'urlopen',lambda *a,**kw:FakeResponse(b'123',5))
    with pytest.raises(ValueError,match='mismatch'):
        s.Fetcher(tmp_path).fetch('https://raw.githubusercontent.com/test','data/file',100)
    assert not (tmp_path/'data/file.partial').exists()
    logs=json.loads((tmp_path/'manifests/http-requests.json').read_text())
    assert logs[0]['result']=='FAILED'


def test_fetch_success_hash(tmp_path,monkeypatch):
    monkeypatch.setattr(s,'urlopen',lambda *a,**kw:FakeResponse(b'123'))
    r=s.Fetcher(tmp_path).fetch('https://raw.githubusercontent.com/test','data/file',100)
    assert r['bytes']==3 and r['sha256']==hashlib.sha256(b'123').hexdigest()
    assert r['result']=='BYTES_DOWNLOADED_NOT_YET_FORMAT_VALIDATED'


def test_hashed_lock(tmp_path):
    p=tmp_path/'report.json'; out=tmp_path/'lock.txt'
    p.write_text(json.dumps({'install':[{'metadata':{'name':'sample','version':'1.0'},'download_info':{'url':'https://files.pythonhosted.org/sample.whl','archive_info':{'hashes':{'sha256':'a'*64}}}}]}))
    r=s.lock_from_install_report(p,out)
    assert r['packages']==1 and '--hash=sha256:'+'a'*64 in out.read_text()


def test_workflow_scope_and_safety():
    # BaseLoader retains the YAML key 'on' rather than treating it as YAML 1.1 true.
    workflow=yaml.load((ROOT/'.github/workflows/stage0.yml').read_text(),Loader=yaml.BaseLoader)
    assert set(workflow['on'])=={'workflow_dispatch'}
    job=workflow['jobs']['preflight']
    assert job['runs-on']=='ubuntu-24.04'
    assert job['if']=='github.event.repository.private == false && inputs.confirm_no_paid_usage == true'
    assert workflow['on']['workflow_dispatch']['inputs']['confirm_no_paid_usage']['default']=='false'
    assert int(job['timeout-minutes'])<=40
    assert workflow['permissions']=={'contents':'read'}
    for step in job['steps']:
        if 'uses' in step: assert re.fullmatch(r'actions/[a-z-]+@[0-9a-f]{40}',step['uses'])
    assert sum('uses' in x and 'upload-artifact' in x['uses'] for x in job['steps'])==1


def test_all_requested_packages_covered():
    req=(ROOT/'requirements-stage0.in').read_text().lower()
    for name in MODULES: assert name.lower() in req


def test_orchestrator_fails_closed_on_wrong_python(tmp_path,monkeypatch):
    import run_stage0 as run
    monkeypatch.setattr(run,'OUT',tmp_path/'out')
    monkeypatch.setattr(run,'COMMANDS',[])
    monkeypatch.setattr(run.sys,'version_info',(3,13,5))
    monkeypatch.setattr(run,'runtime_snapshot',lambda path:{'fixture':True})
    monkeypatch.setattr(run,'acquire',lambda *args:pytest.fail('Network acquisition must not run after runtime guard fails'))
    assert run.main()==1
    result=json.loads((run.OUT/'RUN_MANIFEST.json').read_text())
    assert result['runner_checks']=='FAILED'
    assert result['biological_analysis_performed'] is False
    assert 'BLOCKED' in (run.OUT/'BUILD_STATUS.md').read_text()
    for line in (run.OUT/'CHECKSUMS.sha256').read_text().splitlines():
        expected,path=line.split('  ',1)
        assert s.sha256(run.OUT/path)==expected


def test_stale_output_is_not_reused(tmp_path,monkeypatch):
    import run_stage0 as run
    out=tmp_path/'out'; out.mkdir(); (out/'old.json').write_text('{}')
    monkeypatch.setattr(run,'OUT',out)
    with pytest.raises(SystemExit,match='not empty'): run.main()


def test_lock_rejects_untrusted_source(tmp_path):
    p=tmp_path/'report.json'
    p.write_text(json.dumps({'install':[{'metadata':{'name':'sample','version':'1.0'},'download_info':{'url':'https://example.com/sample.whl','archive_info':{'hashes':{'sha256':'a'*64}}}}]}))
    with pytest.raises(ValueError,match='Unexpected'): s.lock_from_install_report(p,tmp_path/'lock.txt')
