"""End-to-end acquisition fixtures, entirely synthetic and offline."""
import csv, gzip, hashlib, io, json, sys, tempfile, unittest
from collections import namedtuple
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import cohort_tools as c
import collect_targeted as t

class Response(io.BytesIO):
    def __init__(self,b,url,headers=None):
        super().__init__(b);self.url=url;self.status=200;self.headers={'Content-Length':str(len(b)), **(headers or {})}

class PipelineFixtureTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.code=self.root/'stage1b';self.out=self.root/'out';self.out.mkdir()
        layout=[{'well_position':f'{chr(65+r)}{col:02d}', 'broad_sample':'BRD-SYNTHETIC' if col<=20 else '',
                 'pert_type':'trt' if col<=20 else 'control','control_type':'' if col<=20 else 'negcon','pert_iname':'Synthetic compound' if col<=20 else 'DMSO','InChIKey':'SYNTHETIC-NOT-CHEMICAL' if col<=20 else ''}
                for r in range(16) for col in range(1,25)]
        c.write_table(self.code/'reference-data/layouts/fixture.tsv',layout)
        self.payload=('Metadata_Plate,Metadata_Well,Cells_AreaShape_Area\n'+''.join(f'FIXTURE,{r["well_position"]},NOT_EVALUATED\n' for r in layout)).encode()
        self.target={'id':'fixture-profile','source_kind':'s3','role':'profile','cohort_id':'fixture','expected_plate':'FIXTURE',
          'url':'https://cellpainting-gallery.s3.amazonaws.com/fixture.csv','destination':'data/fixture.csv',
          'expected_bytes':len(self.payload),'expected_sha256':hashlib.sha256(self.payload).hexdigest(),'expected_etag':'"fixture"','max_bytes':100000,'required':True}
    def tearDown(self):self.tmp.cleanup()
    def execute(self,body,target=None):
        d=t.Downloader(self.out,1000000,opener=lambda req,timeout:Response(body,req.full_url,{'ETag':'"fixture"'}),sleep=lambda _:None)
        rc=t.collect({'targets':[target or self.target],'total_transfer_limit_bytes':1000000},self.out,self.code,downloader=d)
        return rc,json.loads((self.out/'RUN_MANIFEST.json').read_text())
    def test_success_preserves_complete_file_and_never_scores(self):
        rc,status=self.execute(self.payload);self.assertEqual(rc,0);self.assertEqual(status['profiles_acquired'],1)
        receipt=json.loads((self.out/'manifests/target-receipts.json').read_text())[0]
        self.assertEqual(receipt['identity_audit']['rows'],384);self.assertEqual(receipt['identity_audit']['role_counts']['negative_control'],64)
        self.assertFalse(receipt['identity_audit']['numeric_qc_run']);self.assertFalse(status['phenotype_analysis_performed'])
        self.assertEqual((self.out/'data/fixture.csv').read_bytes(),self.payload)
        self.assertEqual(status['stage1_status'],'BLOCKED_PENDING_COHORT_REVIEW')
    def test_gzip_complete_profile(self):
        body=gzip.compress(self.payload,mtime=0);target={**self.target,'destination':'data/fixture.csv.gz','expected_bytes':len(body),'expected_sha256':hashlib.sha256(body).hexdigest()}
        rc,status=self.execute(body,target);self.assertEqual(rc,0);self.assertFalse(status['identity_review_notes']);self.assertFalse(list((self.out/'.scratch').glob('*')))
    def test_incomplete_wells_recorded_not_silently_accepted(self):
        body=b'Metadata_Plate,Metadata_Well,Cells_AreaShape_Area\nFIXTURE,A01,NOT_EVALUATED\n'
        target={**self.target,'expected_bytes':len(body),'expected_sha256':hashlib.sha256(body).hexdigest()}
        rc,status=self.execute(body,target);self.assertEqual(rc,0);self.assertEqual(len(status['identity_review_notes']),1)
        self.assertEqual(status['stage1_status'],'BLOCKED_PENDING_COHORT_REVIEW')
    def test_embedded_identity_conflict_blocks_cohort_not_file_receipt(self):
        text=self.payload.decode().splitlines();text[0]+=',Metadata_broad_sample'
        body=('\n'.join([text[0]]+[line+',WRONG-ID' for line in text[1:]])+'\n').encode()
        target={**self.target,'expected_bytes':len(body),'expected_sha256':hashlib.sha256(body).hexdigest()}
        rc,status=self.execute(body,target);self.assertEqual(rc,0);self.assertTrue(status['identity_review_notes'])
        self.assertEqual(status['stage1_status'],'BLOCKED_PENDING_COHORT_REVIEW')
    def test_integrity_failure_blocks_and_no_partial_source(self):
        rc,status=self.execute(b'wrong');self.assertEqual(rc,1);self.assertEqual(len(status['required_acquisition_issues']),1)
        self.assertFalse((self.out/'data/fixture.csv').exists())
    def test_finalized_artifact_contains_code_and_verifiable_receipts(self):
        self.execute(self.payload);t.finalize(self.out,self.root)
        manifest=c.verify_manifest(self.out,'CHECKSUMS.sha256');self.assertIn('RUN_MANIFEST.json',manifest);self.assertIn('collector-source/reference-data/layouts/fixture.tsv',manifest)
    def test_space_gate_rejects_before_network(self):
        with patch.object(t.shutil,'disk_usage',return_value=namedtuple('Usage','total used free')(4096,3072,1024)),self.assertRaises(RuntimeError):self.execute(self.payload)

if __name__=='__main__':unittest.main()
