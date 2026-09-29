"""Check frozen real-design metadata and target selection, without profile outcomes."""
import json, sys, unittest, hashlib, xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import cohort_tools as c
ROOT=Path(__file__).resolve().parents[1]

class FrozenDesignTests(unittest.TestCase):
    def setUp(self):self.config=json.loads((ROOT/'configs/targeted-acquisition.json').read_text())
    def test_target_counts_and_destinations(self):
        ts=self.config['targets'];self.assertEqual(len(ts),32);self.assertEqual(sum(t['role']=='profile' for t in ts),15)
        self.assertEqual(len({t['destination'] for t in ts}),len(ts));self.assertEqual(len({t['id'] for t in ts}),len(ts))
    def test_s3_entries_in_original_listing(self):
        ns={'s':'http://s3.amazonaws.com/doc/2006-03-01/'}
        for target in self.config['targets']:
            if target['source_kind']!='s3':continue
            p=ROOT/'reference-data'/target['listing_evidence'];self.assertEqual(c.sha256(p),target['listing_evidence_sha256'])
            doc=ET.parse(p).getroot();rows=[x for x in doc.findall('s:Contents',ns) if x.findtext('s:Key',namespaces=ns)==target['source_key']]
            self.assertEqual(len(rows),1);self.assertEqual(int(rows[0].findtext('s:Size',namespaces=ns)),target['expected_bytes']);self.assertEqual(rows[0].findtext('s:ETag',namespaces=ns),target['expected_etag'])
    def test_github_entries_in_original_tree(self):
        for target in self.config['targets']:
            if target['source_kind']!='github_blob':continue
            tree=json.loads((ROOT/'reference-data/provenance/repos'/target['repo'].replace('/','__')/'tree.json').read_text())['tree']
            rows=[x for x in tree if x['path']==target['repo_path'] and x['type']=='blob'];self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]['sha'],target['git_blob_sha1']);self.assertEqual(rows[0]['size'],target['git_blob_bytes'])
    def test_complete_layouts_preserve_unknowns(self):
        for path in (ROOT/'reference-data/layouts').glob('*.tsv'):
            rows=c.read_table(path)[1];self.assertEqual(len(rows),384)
            joined=c.join_wells([{'plate':'TEMPLATE','well':r['well_position']} for r in rows],rows)
            self.assertEqual(sum(r['role']=='negative_control' for r in joined),24)
            samples={r['sample_id']:r for r in joined if r['role']!='negative_control'};self.assertEqual(len(samples),90)
            self.assertEqual(sum(bool(r['source_inchikey']) for r in samples.values()),82)
    def test_known_transfer_size_is_not_lfs_pointer_size(self):
        self.assertEqual(sum(t['expected_bytes'] for t in self.config['targets'] if t['source_kind']=='s3'),284524641)
        lfs=[t for t in self.config['targets'] if t['role']=='profile' and t['source_kind']=='github_blob']
        self.assertEqual(len(lfs),4);self.assertTrue(all(t['expected_bytes'] is None for t in lfs))
    def test_scientific_gate_remains_unpassed(self):
        d=json.loads((ROOT/'configs/cohorts.yaml').read_text());self.assertFalse(d['stage1_passed']);self.assertFalse(d['stage2_authorized'])

if __name__=='__main__':unittest.main()
