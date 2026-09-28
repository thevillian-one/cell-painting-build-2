"""Offline known-input tests. Synthetic fixtures are NOT biological results."""
from pathlib import Path
import tempfile
import hashlib
import json
import gzip
import io
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_support import *
from collect_stage1 import metadata_blob,classify_object,image_references

class Files(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.r=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def put(self,s,name='p.csv'):
        p=self.r/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s);return p
    def test_valid_well(self):self.assertEqual(canonical_well('a1'),'A01')
    def test_last_well(self):self.assertEqual(canonical_well('P24'),'P24')
    def test_invalid_wells(self):
        for s in ('A00','Q01','A25','AA01','1A','A-1',''):
            with self.subTest(s=s):
                with self.assertRaises(ValueError):canonical_well(s)
    def test_path_escape(self):
        for s in ('../x','/tmp/x','a/../../x','a\\x','.'):
            with self.subTest(s=s):
                with self.assertRaises(ValueError):safe_path(self.r,s)
    def test_hash_roundtrip(self):
        self.put('abc','docs/a.txt');write_checksums(self.r)
        self.assertTrue(all(x['passed'] for x in verify_checksums(self.r)))
    def test_hash_tamper(self):
        self.put('abc','a');write_checksums(self.r);self.put('def','a')
        self.assertFalse(verify_checksums(self.r)[0]['passed'])
    def test_hash_missing(self):
        self.put('abc','a');write_checksums(self.r);(self.r/'a').unlink()
        self.assertFalse(verify_checksums(self.r)[0]['passed'])
    def test_hash_manifest_empty(self):
        self.put('','CHECKSUMS.sha256')
        with self.assertRaises(ValueError):verify_checksums(self.r)
    def test_hash_manifest_duplicate(self):
        self.put('abc','a');write_checksums(self.r);s=(self.r/'CHECKSUMS.sha256').read_text();self.put(s+s,'CHECKSUMS.sha256')
        with self.assertRaises(ValueError):verify_checksums(self.r)
    def test_profile_valid(self):
        p=self.put('Metadata_Plate,Metadata_Well,Cells_Test\nP,A01,1\nP,A02,2\n')
        result,_,w,q=inspect_profile(p,'P');self.assertEqual(result['rows'],2);self.assertEqual(q[0]['missing'],0)
    def test_duplicate_headers(self):
        p=self.put('Metadata_Plate,Metadata_Well,Cells_X,Cells_X\nP,A01,1,2\n')
        with self.assertRaises(ValueError):inspect_profile(p)
    def test_wrong_plate(self):
        p=self.put('Metadata_Plate,Metadata_Well,Cells_X\nBAD,A01,1\n')
        with self.assertRaises(ValueError):inspect_profile(p,'P')
    def test_duplicate_well_canonicalized(self):
        p=self.put('Metadata_Plate,Metadata_Well,Cells_X\nP,A1,1\nP,A01,2\n')
        with self.assertRaises(ValueError):inspect_profile(p,'P')
    def test_row_width(self):
        p=self.put('Metadata_Plate,Metadata_Well,Cells_X\nP,A01,1,2\n')
        with self.assertRaises(ValueError):inspect_profile(p)
    def test_missing_identity(self):
        p=self.put('Metadata_Well,Cells_X\nA01,1\n')
        with self.assertRaises(ValueError):inspect_profile(p)
    def test_numeric_diagnostics_not_imputation(self):
        p=self.put('Metadata_Plate,Metadata_Well,Cells_X\nP,A01,NaN\nP,A02,inf\nP,A03,bad\n')
        s,_,_,q=inspect_profile(p)
        self.assertEqual((s['missing_measurement_cells'],s['infinite_measurement_cells'],s['nonnumeric_measurement_cells']),(1,1,1))
        self.assertEqual(p.read_text().count('NaN'),1)
    def test_gzip_profile(self):
        p=self.r/'p.csv.gz'
        with gzip.open(p,'wt') as f:f.write('Metadata_Plate,Metadata_Well,Cells_X\nP,A01,1\n')
        self.assertEqual(inspect_profile(p)[0]['rows'],1)
    def test_metadata_multiline_quoted(self):
        p=self.put('a,b\n1,"first\nsecond"\n');h,r=read_metadata(p);self.assertEqual(r[0]['b'],'first\nsecond')
    def test_metadata_width(self):
        p=self.put('a,b\n1,2,3\n')
        with self.assertRaises(ValueError):read_metadata(p)
    def test_metadata_limit(self):
        p=self.put('a,b\n1,2\n3,4\n')
        with self.assertRaises(ValueError):read_metadata(p,max_rows=1)
    def test_strict_join_success(self):
        r=strict_well_join([{'plate':'P','well':'A1'}],[{'well':'A01','id':'C'}],'well','id')
        self.assertEqual(r[0]['sample_id'],'C')
    def test_strict_join_missing(self):
        with self.assertRaises(ValueError):strict_well_join([{'well':'A01'}],[],'well','id')
    def test_strict_join_duplicates(self):
        with self.assertRaises(ValueError):strict_well_join([],[{'well':'A1'},{'well':'A01'}],'well','id')
    def test_image_manifest_preserves_reference(self):
        p=self.put('Metadata_Plate,Metadata_Well,Metadata_Site,FileName_DNA,PathName_DNA\nP,A01,1,a.tiff,s3://old/source\n')
        r=image_references(p,self.r);self.assertEqual(r[0]['source_directory'],'s3://old/source')
        self.assertEqual(r[0]['verification'],'SOURCE_REFERENCE_ONLY_IMAGE_BYTES_NOT_REQUESTED')
    def test_pilot_design_requires_all4(self):
        p=self.put('Batch,Assay_Plate_Barcode\nB,P\n')
        with self.assertRaises(ValueError):pilot_design(p)

class Selection(unittest.TestCase):
    def test_pilot_metadata_selected(self):self.assertTrue(metadata_blob(PILOT_REPO,'metadata/platemaps/x.tsv'))
    def test_pilot_load_data_selected(self):self.assertTrue(metadata_blob(PILOT_REPO,'load_data_csv/'+BATCH+'/BR00117015.csv.gz'))
    def test_other_pilot_plate_not_selected(self):self.assertFalse(metadata_blob(PILOT_REPO,'load_data_csv/'+BATCH+'/BR00117020.csv.gz'))
    def test_external_images_not_selected(self):self.assertFalse(metadata_blob('jump-cellpainting/jump-scope','load_data_csv/P.csv.gz'))
    def test_result_tables_not_selected(self):
        for path in ('output/score.csv','results/metadata.csv','notebooks/metadata.csv','source_data_files/data.csv'):
            with self.subTest(path=path):self.assertFalse(metadata_blob(PILOT_REPO,path))
    def test_raw_selector(self):
        keys=['x/backend/P/P.csv','x/backend/P/P_normalized.csv','x/backend/P/P.sqlite','x/profiles/P/P.csv','x/backend/P/X.csv']
        self.assertEqual([x['key'] for x in raw_profile_candidates([{'key':k} for k in keys])],keys[:1])
    def test_aggregate_does_not_become_raw_automatically(self):
        self.assertEqual(classify_object('cpg0002-jump-scope/source_4/workspace/profiles/P/P.csv.gz'),
                         'AGGREGATE_CANDIDATE_PROCESSING_STAGE_NEEDS_CONFIRMATION')
    def test_protocol_master_selected(self):self.assertTrue(metadata_blob('carpenter-singh-lab/2023_Cimini_NatureProtocols','JUMPExperimentMasterTable.csv'))
    def test_moa_table_selected(self):self.assertTrue(metadata_blob('jump-cellpainting/JUMP-MOA','JUMP-MOA_compound_metadata.tsv'))

class FakeResponse(io.BytesIO):
    def __init__(self,body,url,status=200,headers=None):
        super().__init__(body);self.url=url;self.status=status;self.headers=headers or {'Content-Length':str(len(body))}

class Network(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.r=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def fetcher(self,body=b'abc',headers=None,status=200):
        return Fetcher(self.r,opener=lambda req,timeout:FakeResponse(body,req.full_url,status,headers))
    def test_valid_download(self):
        f=self.fetcher();p=f.fetch('https://raw.githubusercontent.com/o/r/main/file','x',10,expected_size=3,
                                 expected_hash=hashlib.sha256(b'abc').hexdigest());self.assertEqual(p.read_bytes(),b'abc')
    def test_disallowed_host(self):
        with self.assertRaises(ValueError):self.fetcher().fetch('https://example.com/x','x',10)
    def test_disallowed_scheme(self):
        with self.assertRaises(ValueError):self.fetcher().fetch('http://raw.githubusercontent.com/x','x',10)
    def test_response_size_mismatch(self):
        with self.assertRaises(ValueError):self.fetcher(headers={'Content-Length':'5'}).fetch('https://raw.githubusercontent.com/x','x',10)
    def test_listing_size_mismatch(self):
        with self.assertRaises(ValueError):self.fetcher().fetch('https://raw.githubusercontent.com/x','x',10,expected_size=4)
    def test_hash_mismatch(self):
        with self.assertRaises(ValueError):self.fetcher().fetch('https://raw.githubusercontent.com/x','x',10,expected_hash='0'*64)
    def test_partial_response_rejected(self):
        with self.assertRaises(ValueError):self.fetcher(status=206).fetch('https://raw.githubusercontent.com/x','x',10)
    def test_download_limit(self):
        with self.assertRaises(ValueError):self.fetcher().fetch('https://raw.githubusercontent.com/x','x',2)
    def test_cleanup_failure(self):
        f=self.fetcher()
        with self.assertRaises(ValueError):f.fetch('https://raw.githubusercontent.com/x','x',10,expected_size=4)
        self.assertFalse((self.r/'x.partial').exists());self.assertEqual(f.records[-1]['status'],'FAILED')
    def test_budget(self):
        f=self.fetcher();f.limit=2
        with self.assertRaises(ValueError):f.fetch('https://raw.githubusercontent.com/x','x',10)
    def test_recursive_image_listing_prohibited(self):
        with self.assertRaises(ValueError):self.fetcher().s3_list('cpg0000-jump-pilot/source_4/images/')
    def test_s3_listing_realistic(self):
        key='cpg0000-jump-pilot/source_4/workspace/backend/P/P.csv'
        xml=f'<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><IsTruncated>false</IsTruncated><Contents><Key>{key}</Key><Size>3</Size><ETag>abc</ETag><LastModified>date</LastModified></Contents></ListBucketResult>'.encode()
        objs,prefixes=self.fetcher(xml).s3_list('cpg0000-jump-pilot/source_4/workspace/backend/')
        self.assertEqual(objs[0]['bytes'],3);self.assertEqual(prefixes,[])
    def test_s3_not_html(self):
        with self.assertRaises(ValueError):self.fetcher(b'<html/>').s3_list('cpg0000-jump-pilot/source_4/workspace/backend/')
    def test_s3_truncated_missing_token(self):
        xml=b'<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><IsTruncated>true</IsTruncated></ListBucketResult>'
        with self.assertRaises(ValueError):self.fetcher(xml).s3_list('cpg0000-jump-pilot/source_4/workspace/backend/')
    def test_git_blob_identity(self):
        f=self.fetcher();sha=hashlib.sha1(b'blob 3\0abc').hexdigest()
        p=f.github_blob('o/r','0'*40,{'path':'metadata/a.csv','type':'blob','sha':sha});self.assertEqual(p.read_bytes(),b'abc')
    def test_git_blob_mismatch(self):
        with self.assertRaises(ValueError):self.fetcher().github_blob('o/r','0'*40,{'path':'a','type':'blob','sha':'0'*40})
    def test_lfs_real_bytes_and_oid(self):
        body=b'abc';h=hashlib.sha256(body).hexdigest()
        pointer=f'version https://git-lfs.github.com/spec/v1\noid sha256:{h}\nsize 3\n'.encode()
        def opener(req,timeout):return FakeResponse(body if 'media.githubusercontent.com' in req.full_url else pointer,req.full_url)
        f=Fetcher(self.r,opener=opener);p=f.github_blob('o/r','0'*40,{'path':'a','type':'blob'},limit=1024)
        self.assertEqual(p.read_bytes(),b'abc');self.assertEqual(len(f.records),2)


# Synthetic, network-free integration tests of collection/bookkeeping only.
# No fixture output is included as real experimental evidence.
from unittest.mock import patch
import os
import contextlib
import collect_stage1
from finalize_artifact import finalize

class CollectorIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.r=Path(self.tmp.name)
        names=['Batch','Plate_Map_Name','Assay_Plate_Barcode','Perturbation','Cell_type','Time','Density','Antibiotics','Cell_line','Time_delay','Times_imaged','Anomaly']
        rows=[[BATCH,'JUMP-Target-1_compound_platemap',p,'compound','A549','48','100','absent','Parental','Day0','1','none'] for p in PLATES]
        self.meta=('\t'.join(names)+'\n'+'\n'.join('\t'.join(r) for r in rows)+'\n').encode()
        self.config={'total_download_limit_bytes':10000000,'metadata_object_limit_bytes':1000000,'profile_object_limit_bytes':1000000,
                     'max_sources_per_dataset':12,'max_listing_pages':30,'expected_pilot_metadata_sha256':hashlib.sha256(self.meta).hexdigest(),
                     'expected_first_profile_sha256':hashlib.sha256(self.profile(PLATES[0])).hexdigest(),
                     'repositories':[{'repo':PILOT_REPO,'ref':PILOT_REV},{'repo':'jump-cellpainting/JUMP-Target'},
                      {'repo':'jump-cellpainting/JUMP-MOA'},{'repo':'carpenter-singh-lab/2023_Cimini_NatureProtocols'},
                      {'repo':'jump-cellpainting/jump-scope'}]}
    def tearDown(self):self.tmp.cleanup()
    @staticmethod
    def profile(p):return f'Metadata_Plate,Metadata_Well,Cells_Test\n{p},A01,1\n'.encode()
    def fake(self,fail_plate=None):
        owner=self
        class Fake:
            def __init__(self,root,limit):self.root=Path(root);self.total=0
            def github_tree(self,repo,ref=None):
                paths=[];extra=[]
                if repo==PILOT_REPO:
                    paths=['benchmark/output/experiment-metadata.tsv','load_data_csv/'+BATCH+'/'+PLATES[0]+'.csv']
                elif repo.endswith('JUMP-Target'):
                    paths=['JUMP-Target-1_compound_metadata.tsv','JUMP-Target-1_compound_platemap.tsv']
                elif repo.endswith('JUMP-MOA'):
                    paths=['JUMP-MOA_compound_metadata.tsv','JUMP-MOA_compound_platemap.tsv']
                elif repo.endswith('2023_Cimini_NatureProtocols'):
                    paths=['.gitmodules','JUMPExperimentMasterTable.csv'];extra=[{'path':'profiles-pilots','type':'commit','sha':'b'*40}]
                elif repo.endswith('jump-scope'):paths=['metadata/plates.tsv']
                return ref or 'a'*40,[{'path':p,'type':'blob'} for p in paths]+extra
            def github_blob(self,repo,rev,entry,limit):
                p=self.root/'source-data/repos'/repo.replace('/','__')/entry['path'];p.parent.mkdir(parents=True,exist_ok=True)
                if entry['path']=='benchmark/output/experiment-metadata.tsv':data=owner.meta
                elif entry['path']=='.gitmodules':data=b'[submodule "profiles-pilots"]\npath=profiles-pilots\nurl=https://github.com/jump-cellpainting/pilot-data-public.git\n'
                elif entry['path']=='JUMPExperimentMasterTable.csv':data=b'Batch,Treatments,Qualitative conclusion drawn (if any)\nsynthetic,JUMP-MOA,DO_NOT_USE\n'
                elif entry['path'].startswith('load_data_csv/'):
                    data=b'Metadata_Plate,Metadata_Well,Metadata_Site,FileName_DNA,PathName_DNA\nSYNTHETIC,A01,1,f.tiff,s3://synthetic\n'
                else:data=b'well_position\tbroad_sample\nA01\tSYNTHETIC\n'
                p.write_bytes(data);self.total+=len(data);return p
            def s3_list(self,prefix,delimiter=None,**kwargs):
                if prefix.count('/')==1:return [],[prefix+'source_4/']
                if prefix.startswith('cpg0000'):
                    p=PurePosixPath(prefix).name
                    return [{'key':prefix+p+'.csv','bytes':len(owner.profile(p))}],[]
                if 'backend/' in prefix:
                    return [{'key':prefix+'SYNTHETIC/SYNTHETIC.csv','bytes':1,'etag':'x','last_modified':'x','listing_evidence':'mock'}],[]
                return [],[]
            def fetch(self,url,relative,limit,expected_size=None,expected_hash=None):
                plate=PurePosixPath(relative).stem
                if plate==fail_plate:raise RuntimeError('Simulated download failure')
                data=owner.profile(plate)
                if expected_size!=len(data):raise ValueError('Mock size mismatch')
                if expected_hash and hashlib.sha256(data).hexdigest()!=expected_hash:raise ValueError('Mock hash mismatch')
                p=self.root/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);self.total+=len(data);return p
        return Fake
    def test_collection_success_is_not_scientific_stage_pass(self):
        with patch.object(collect_stage1,'Fetcher',self.fake()),contextlib.redirect_stdout(io.StringIO()):
            rc=collect_stage1.run(self.config,self.r)
        m=json.loads((self.r/'RUN_MANIFEST.json').read_text())
        self.assertEqual(rc,0);self.assertEqual(m['pilot_profiles_acquired'],4)
        self.assertEqual(m['stage1_acceptance'],'BLOCKED_PENDING_COHORT_REVIEW')
        self.assertNotIn('DO_NOT_USE',(self.r/'manifests/protocol-master-design.tsv').read_text())
        self.assertFalse(m['prohibited_work_performed'])
    def test_partial_acquisition_blocks(self):
        with patch.object(collect_stage1,'Fetcher',self.fake(PLATES[1])),contextlib.redirect_stdout(io.StringIO()):
            rc=collect_stage1.run(self.config,self.r)
        self.assertEqual(rc,1)
        m=json.loads((self.r/'RUN_MANIFEST.json').read_text());self.assertEqual(m['acquisition_status'],'BLOCKED')
        self.assertEqual(m['pilot_profiles_acquired'],3)
    def test_failed_start_finalizer_preserves_failure(self):
        repo=self.r/'repo';repo.mkdir();(repo/'stage1-bootstrap-console.log').write_text('Simulated missing file')
        with patch.dict(os.environ,{},clear=True),contextlib.redirect_stdout(io.StringIO()):finalize(self.r/'out',repo)
        m=json.loads((self.r/'out/RUN_MANIFEST.json').read_text());self.assertEqual(m['acquisition_status'],'BLOCKED')
        self.assertTrue(all(r['passed'] for r in verify_checksums(self.r/'out')))

if __name__=='__main__':unittest.main(verbosity=2)
