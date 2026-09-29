"""Offline known-answer tests. Fixtures are synthetic, never biological evidence."""
import csv, gzip, hashlib, io, json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import cohort_tools as c
import collect_targeted as t

class TableTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def test_utf8_preserves_micro_and_greek(self):
        p=self.root/'x.csv';p.write_text('id,name\n1,µM α β\n',encoding='utf-8');self.assertEqual(c.read_table(p)[1][0]['name'],'µM α β')
    def test_utf8_bom(self):
        p=self.root/'x.csv';p.write_text('id,name\n1,µ\n',encoding='utf-8-sig');self.assertEqual(c.read_table(p)[0],['id','name'])
    def test_legacy_requires_explicit_override(self):
        p=self.root/'x.csv';p.write_bytes(b'id,name\n1,\xb5M\n')
        with self.assertRaises(UnicodeDecodeError):c.read_table(p)
        self.assertEqual(c.read_table(p,encoding='cp1252')[1][0]['name'],'µM')
    def test_invalid_utf8_not_replaced(self):
        p=self.root/'x.csv';p.write_bytes(b'id,name\n1,\xff\n')
        with self.assertRaises(UnicodeDecodeError):c.read_table(p)
    def test_gzip_utf8(self):
        p=self.root/'x.csv.gz';p.write_bytes(gzip.compress('id,name\n1,β\n'.encode()));self.assertEqual(c.read_table(p)[1][0]['name'],'β')
    def test_txt_platemap_tabs(self):
        p=self.root/'x.txt';p.write_text('well_position\tbroad_sample\nA01\tTEST\n');self.assertEqual(c.read_table(p)[1][0]['broad_sample'],'TEST')
    def test_row_width(self):
        p=self.root/'x.tsv';p.write_text('a\tb\n1\t2\t3\n')
        with self.assertRaises(ValueError):c.read_table(p)
    def test_duplicate_headers(self):
        p=self.root/'x.csv';p.write_text('a,a\n1,2\n')
        with self.assertRaises(ValueError):c.read_table(p)
    def test_row_limit(self):
        p=self.root/'x.csv';p.write_text('a,b\n1,2\n3,4\n')
        with self.assertRaises(ValueError):c.read_table(p,max_rows=1)
    def test_csv_quoted_delimiter(self):
        p=self.root/'x.csv';p.write_text('a,b\n1,"a,b"\n');self.assertEqual(c.read_table(p)[1][0]['b'],'a,b')
    def test_empty_fails(self):
        p=self.root/'x.csv';p.write_text('')
        with self.assertRaises(ValueError):c.read_table(p)
    def test_path_escape(self):
        for p in ['../bad','/absolute','a/../../b','a\\b','C:/bad']:
            with self.subTest(p=p),self.assertRaises(ValueError):c.safe_path(self.root,p)
    def test_well(self):self.assertEqual(c.well('a1'),'A01');self.assertEqual(c.well('P24'),'P24')
    def test_invalid_well(self):
        for p in ['Q01','A00','A25','a-1','']:
            with self.subTest(p=p),self.assertRaises(ValueError):c.well(p)
    def test_checksums_detect_changed_file(self):
        (self.root/'a.txt').write_text('a');c.write_checksums(self.root);c.verify_manifest(self.root,'CHECKSUMS.sha256')
        (self.root/'a.txt').write_text('b')
        with self.assertRaises(ValueError):c.verify_manifest(self.root,'CHECKSUMS.sha256')
    def test_no_float_infinite_json(self):
        with self.assertRaises(ValueError):c.dump(self.root/'x.json',{'x':float('nan')})

class JoinTests(unittest.TestCase):
    def setUp(self):
        self.ws=[{'plate':'P','well':'A01'},{'plate':'P','well':'A02'}]
        self.layout=[{'well_position':'A01','broad_sample':'BRD-TEST','solvent':'DMSO'}, {'well_position':'A02','broad_sample':'','solvent':'DMSO'}]
        self.ann=[{'broad_sample':'BRD-TEST','InChIKey':'TEST-KEY','pert_type':'trt','control_type':''}, {'broad_sample':'','InChIKey':'','pert_type':'control','control_type':'negcon'}]
    def test_treated_solvent_not_negative(self):self.assertEqual([r['role'] for r in c.join_wells(self.ws,self.layout,self.ann)],['treatment','negative_control'])
    def test_blank_needs_control_evidence(self):
        self.ann[1]['control_type']=''
        with self.assertRaises(ValueError):c.join_wells(self.ws,self.layout,self.ann)
    def test_unknown_sample(self):
        self.layout[0]['broad_sample']='NOT_ANNOTATED'
        with self.assertRaises(ValueError):c.join_wells(self.ws,self.layout,self.ann)
    def test_duplicate_layout(self):
        with self.assertRaises(ValueError):c.join_wells(self.ws,self.layout+self.layout[:1],self.ann)
    def test_duplicate_profile_well(self):
        with self.assertRaises(ValueError):c.join_wells(self.ws+self.ws[:1],self.layout,self.ann)
    def test_duplicate_annotation(self):
        with self.assertRaises(ValueError):c.join_wells(self.ws,self.layout,self.ann+self.ann[:1])
    def test_missing_well(self):
        with self.assertRaises(ValueError):c.join_wells(self.ws,self.layout[:1],self.ann)
    def test_anonymous_group_preserved(self):
        self.layout[0]['broad_sample']='Compound1';self.ann[0]['broad_sample']='Compound1';self.ann[0]['InChIKey']=''
        row=c.join_wells(self.ws,self.layout,self.ann)[0]
        self.assertEqual(row['sample_id'],'Compound1');self.assertTrue(row['chemical_identity_status'].startswith('undisclosed'))
    def test_nonblank_negative_rejected(self):
        self.ann[0]['pert_type']='control';self.ann[0]['control_type']='negcon'
        with self.assertRaises(ValueError):c.join_wells(self.ws,self.layout,self.ann)

class PairTests(unittest.TestCase):
    def rows(self):
        return [{'physical_plate_id':plate,'well':well,'sample_id':sid,'role':role,'condition_id':'same'}
                for plate in ['P1','P2'] for well,sid,role in [('A01','X','treatment'),('A02','X','treatment'),('B01','DMSO','negative_control')]]
    def test_symmetric_cross_plate(self):
        r=c.design_pair_counts(self.rows());self.assertEqual(len(r),4);self.assertTrue(all(x['eligible_positives']==2 and x['eligible_negatives']==1 for x in r))
    def test_position_excluded(self):self.assertTrue(all(x['eligible_positives']==1 for x in c.design_pair_counts(self.rows(),True)))
    def test_reimage_not_positive(self):
        rows=self.rows()[:3];rows[0]['acquisition']='image1';rows[1]['acquisition']='image2'
        self.assertTrue(all(not x['assessable_by_design'] for x in c.design_pair_counts(rows)))
    def test_condition_mismatch(self):
        rows=self.rows()
        for r in rows[3:]:r['condition_id']='different_dose'
        self.assertTrue(all(x['eligible_positives']==0 and x['eligible_negatives']==0 for x in c.design_pair_counts(rows)))
    def test_control_not_query(self):self.assertTrue(all(x['sample_id']!='DMSO' for x in c.design_pair_counts(self.rows())))

class ProfileTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def file(self,text):p=self.root/'p.csv';p.write_text(text);return p
    def test_identity_schema_not_numeric_outcomes(self):
        p=self.file('Metadata_Plate,Metadata_Well,Cells_AreaShape_Area\nP,A01,DO_NOT_USE\n')
        summary,_,_=c.inspect_profile(p,'P',numeric_qc=False);self.assertIsNone(summary['nonnumeric_cells']);self.assertFalse(summary['numeric_qc_run'])
    def test_numeric_qc_only_explicit(self):
        p=self.file('Metadata_Plate,Metadata_Well,Cells_AreaShape_Area\nP,A01,notnumeric\n');self.assertEqual(c.inspect_profile(p,'P',numeric_qc=True)[0]['nonnumeric_cells'],1)
    def test_wrong_plate(self):
        p=self.file('Metadata_Plate,Metadata_Well,Cells_AreaShape_Area\nP,A01,2\n')
        with self.assertRaises(ValueError):c.inspect_profile(p,'WRONG')
    def test_duplicate_well(self):
        p=self.file('Metadata_Plate,Metadata_Well,Cells_AreaShape_Area\nP,A01,2\nP,A01,3\n')
        with self.assertRaises(ValueError):c.inspect_profile(p,'P')
    def test_bad_header(self):
        p=self.file('Plate,Well,Cells_AreaShape_Area\nP,A01,2\n')
        with self.assertRaises(ValueError):c.inspect_profile(p,'P')
    def test_no_measurements(self):
        p=self.file('Metadata_Plate,Metadata_Well\nP,A01\n')
        with self.assertRaises(ValueError):c.inspect_profile(p,'P')
    def test_malformed_row(self):
        p=self.file('Metadata_Plate,Metadata_Well,Cells_AreaShape_Area\nP,A01\n')
        with self.assertRaises(ValueError):c.inspect_profile(p,'P')
    def test_gzip(self):
        p=self.root/'p.csv.gz';p.write_bytes(gzip.compress(b'Metadata_Plate,Metadata_Well,Cells_AreaShape_Area\nP,A01,1\n'))
        plain,temp=t.bounded_plain(p,self.root);self.assertEqual(c.inspect_profile(plain,'P')[0]['rows'],1);temp.unlink()
    def test_gzip_expansion_limit(self):
        p=self.root/'p.csv.gz';p.write_bytes(gzip.compress(b'x'*200))
        with patch.object(t,'MAX_UNPACKED',100),self.assertRaises(ValueError):t.bounded_plain(p,self.root)

class Response(io.BytesIO):
    def __init__(self,body,url,headers=None):
        super().__init__(body);self.url=url;self.status=200;self.headers={'Content-Length':str(len(body)),**(headers or {})}

class DownloadTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.url='https://raw.githubusercontent.com/test/repo/rev/a.txt'
    def tearDown(self):self.temp.cleanup()
    def downloader(self,body=b'hello',headers=None,limit=1000):
        return t.Downloader(self.root,limit,opener=lambda req,timeout:Response(body,req.full_url,headers),sleep=lambda _:None)
    def test_bytes_size_hash(self):
        d=self.downloader();p=d.fetch(self.url,'a.txt',20,5,hashlib.sha256(b'hello').hexdigest());self.assertEqual(p.read_bytes(),b'hello')
    def test_wrong_hash(self):
        with self.assertRaises(ValueError):self.downloader().fetch(self.url,'a.txt',20,expected_hash='0'*64)
        self.assertFalse((self.root/'a.txt.partial').exists())
    def test_wrong_size(self):
        with self.assertRaises(ValueError):self.downloader().fetch(self.url,'a.txt',20,expected_size=10)
    def test_small_cap(self):
        with self.assertRaises(ValueError):self.downloader().fetch(self.url,'a.txt',2)
    def test_total_cap(self):
        d=self.downloader(limit=7);d.fetch(self.url,'a.txt',20)
        with self.assertRaises(ValueError):d.fetch(self.url,'b.txt',20)
    def test_bad_url(self):
        for url in ['http://raw.githubusercontent.com/x','https://evil.example/x','https://token@raw.githubusercontent.com/x','https://raw.githubusercontent.com:444/x']:
            with self.subTest(url=url),self.assertRaises(ValueError):self.downloader().fetch(url,'x',100)
    def test_source_etag_change(self):
        with self.assertRaises(ValueError):self.downloader(headers={'ETag':'"new"'}).fetch(self.url,'x',10,etag='"old"')
    def test_retry_network_error(self):
        n=[0]
        def opener(req,timeout):
            n[0]+=1
            if n[0]==1:raise URLError('temporary fixture failure')
            return Response(b'hello',req.full_url)
        d=t.Downloader(self.root,100,opener=opener,sleep=lambda _:None);d.fetch(self.url,'x',20);self.assertEqual(n[0],2)
    def test_unapproved_redirect(self):
        d=t.Downloader(self.root,100,opener=lambda req,timeout:Response(b'x','https://other.example/'),sleep=lambda _:None)
        with self.assertRaises(ValueError):d.fetch(self.url,'x',20)
    def test_pinned_git_blob(self):
        b=b'hello';target={'source_kind':'github_blob','id':'r:a','url':self.url,'max_bytes':100,'git_blob_bytes':5,
                'git_blob_sha1':hashlib.sha1(b'blob 5\0'+b).hexdigest(),'destination':'source-data/a.txt'}
        p,extra=t.fetch_target(self.downloader(b),target);self.assertEqual(p.read_bytes(),b);self.assertFalse(extra['lfs'])
    def test_lfs_pointer_not_treated_as_data(self):
        data=b'actual fixture data';hs=hashlib.sha256(data).hexdigest();pointer=f'version https://git-lfs.github.com/spec/v1\noid sha256:{hs}\nsize {len(data)}\n'.encode()
        def opener(req,timeout):return Response(data if 'media.githubusercontent.com' in req.full_url else pointer,req.full_url)
        d=t.Downloader(self.root,1000,opener=opener,sleep=lambda _:None)
        target={'source_kind':'github_blob','id':'r:a','url':self.url,'max_bytes':500,'git_blob_bytes':len(pointer),
          'git_blob_sha1':hashlib.sha1(f'blob {len(pointer)}\0'.encode()+pointer).hexdigest(),'destination':'data/a.csv','repo':'a/b','revision':'1'*40,'repo_path':'a.csv'}
        p,extra=t.fetch_target(d,target);self.assertEqual(p.read_bytes(),data);self.assertTrue(extra['lfs'])
    def test_article_wrong_doi(self):
        target={'source_kind':'article_xml','url':self.url,'max_bytes':1000,'destination':'x.xml','doi':'wanted'}
        with self.assertRaises(ValueError):t.fetch_target(self.downloader(b'<article><article-id>other</article-id></article>'),target)
    def test_finalizer_without_success(self):
        out=self.root/'out';t.finalize(out,self.root);d=json.loads((out/'RUN_MANIFEST.json').read_text());self.assertEqual(d['acquisition_status'],'BLOCKED');c.verify_manifest(out,'CHECKSUMS.sha256')
    def test_optional_failure_not_hidden(self):
        target={'id':'optional','required':False,'source_kind':'article_xml','url':self.url,'max_bytes':100,'destination':'x.xml','role':'methods','doi':'x'}
        out=self.root/'out';out.mkdir()
        rc=t.collect({'targets':[target],'total_transfer_limit_bytes':100},out,self.root,downloader=t.Downloader(out,100,opener=lambda req,timeout:Response(b'<wrong/>',req.full_url),sleep=lambda _:None))
        status=json.loads((out/'RUN_MANIFEST.json').read_text());self.assertEqual(rc,0);self.assertEqual(len(status['optional_methods_warnings']),1);self.assertEqual(status['stage1_status'],'BLOCKED_PENDING_COHORT_REVIEW')
    def test_required_failure_blocks(self):
        target={'id':'required','required':True,'source_kind':'article_xml','url':self.url,'max_bytes':100,'destination':'x.xml','role':'methods','doi':'x'}
        out=self.root/'out';out.mkdir()
        rc=t.collect({'targets':[target],'total_transfer_limit_bytes':100},out,self.root,downloader=t.Downloader(out,100,opener=lambda req,timeout:Response(b'<wrong/>',req.full_url),sleep=lambda _:None))
        self.assertEqual(rc,1)

if __name__=='__main__':unittest.main()
