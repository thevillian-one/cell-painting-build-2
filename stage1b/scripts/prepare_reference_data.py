"""Prepare small frozen layout fixtures from verified public metadata.
These are real experimental designs, not synthetic scientific outcomes.
"""
from pathlib import Path
import argparse, json, shutil
from cohort_tools import read_table, write_table, dump, sha256, annotation_map


def build(root,out):
    root=Path(root);out=Path(out);source=root/'source-data/repos';receipts=[]
    def record(p,role):
        receipts.append({'path_in_stage1a':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':sha256(p),'role':role})
    public='jump-cellpainting__pilot-data-public'
    for cid,folder in [('protocol_stain5_thermo_standard','Stain5_CondAB_Standard'),('protocol_stain4_standard','2020_09_22_Stain4_Standard'),('protocol_reagent1_thermo_standard','2020_12_11_Reagent1_Pfizer')]:
        p=source/public/f'metadata/platemaps/{folder}/platemap/JUMP-MOA_compound_platemap_with_metadata.txt'
        h,rows=read_table(p);write_table(out/'reference-data/layouts'/f'{cid}.tsv',rows,h);record(p,'source layout with embedded annotations; delimiter normalized to TSV')
    scope='jump-cellpainting__jump-scope'
    p=source/scope/'metadata/platemaps/Scope1_PE_Bin1_Confocal_1Plane/platemap/JUMP-MOA_compound_platemap.txt'
    annpath=source/scope/'metadata/external_metadata/JUMP-MOA_compound_metadata.tsv'
    h,lay=read_table(p);_,ann=read_table(annpath);lookup=annotation_map(ann)
    rows=[]
    for row in lay:
        sample=row['broad_sample'];aa=lookup[sample]
        rows.append({**row,**{k:v for k,v in aa.items() if k!='broad_sample'}})
    write_table(out/'reference-data/layouts/scope_pe_c_bin1_1plane.tsv',rows)
    record(p,'scope source layout');record(annpath,'scope source annotation, exact broad_sample join; explicit negative-control annotation')
    # Retain raw table bytes alongside derived layouts for reinspection.
    for rec in receipts:
        p=root/rec['path_in_stage1a'];dest=out/'reference-data/originals'/rec['path_in_stage1a']
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    for slug in [public,scope,'carpenter-singh-lab__2023_Cimini_NatureProtocols']:
        p=source/slug/'LICENSE';dest=out/'reference-data/notices'/f'{slug}-LICENSE';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);record(p,'upstream license notice')
    targets=json.loads((out/'configs/targeted-acquisition.json').read_text())['targets']
    evidence={t['listing_evidence'] for t in targets if t['source_kind']=='s3'}
    evidence.update(f'provenance/repos/{t["repo"].replace("/","__")}/tree.json' for t in targets if t['source_kind']=='github_blob')
    for rel in sorted(evidence):
        p=root/rel;dest=out/'reference-data'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);record(p,'original listing/tree supporting frozen target selection')
    dump(out/'reference-data/provenance.json',receipts)
    print('Prepared frozen layouts and original selection evidence:',len(receipts),'source records')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();build(a.input,a.output)
