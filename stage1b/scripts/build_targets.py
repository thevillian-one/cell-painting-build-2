"""Select exact publicly listed profile objects using design metadata only."""
from pathlib import Path
import json
from urllib.parse import quote
from cohort_tools import dump, sha256, write_table

def build(root,out):
    root=Path(root);out=Path(out)
    inv=json.loads((root/'manifests/external-objects.json').read_text())
    invby={x['key']:x for x in inv}
    revs=json.loads((root/'manifests/repository-revisions.json').read_text())
    targets=[];seen=set()
    def s3(cohort,batch,plate,dataset,ext='.csv'):
        key=f'{dataset}/source_4/workspace/backend/{batch}/{plate}/{plate}{ext}'
        if key not in invby:raise ValueError('Not listed: '+key)
        obj=invby[key]
        if obj['classification']!='RAW_AGGREGATE_CANDIDATE':raise ValueError('Not a raw filename candidate')
        targets.append({'id':cohort+'__'+plate,'source_kind':'s3','role':'profile', 'cohort_id':cohort,
          'expected_plate':plate,'url':'https://cellpainting-gallery.s3.amazonaws.com/'+quote(key,safe='/'),
          'source_key':key,'destination':'data/'+cohort+'/'+plate+ext,
          'expected_bytes':obj['bytes'],'expected_etag':obj['etag'],'expected_sha256':None,
          'max_bytes':64*1024*1024,'required':True,'listing_evidence':obj['listing_evidence'],
          'listing_evidence_sha256':sha256(root/obj['listing_evidence']),
          'processing_stage':'raw unnormalized backend aggregate candidate; verify schema only in collector',
          'holdout_protection':'no numeric summary, ranking, similarity, normalization or outcome-based exclusions'})
    for i in range(23,27):s3('protocol_stain5_thermo_standard','2021_03_04_Stain5_CondA_Thermo_Standard','BR001205'+str(i),'cpg0001-cellpainting-protocol')
    for i in range(29,32):s3('protocol_stain4_standard','2020_09_22_Stain4_Standard','BR001166'+str(i),'cpg0001-cellpainting-protocol')
    for i in range(1,5):s3('scope_pe_c_bin1_1plane','2020_11_16_Scope1_PE','CP_Broad_Phenix_C_BIN1_1Plane_P'+str(i),'cpg0002-jump-scope','.csv.gz')
    def github(repo,path,role='metadata',plate=None,cohort=None,required=True):
        slug=repo.replace('/','__');tree=json.loads((root/'provenance/repos'/slug/'tree.json').read_text())['tree']
        matches=[x for x in tree if x['path']==path and x['type']=='blob']
        if len(matches)!=1:raise ValueError('Git path missing/ambiguous: '+repo+':'+path)
        obj=matches[0];rev=revs[repo]
        dest=('data/'+cohort+'/'+plate+'.csv.gz') if role=='profile' else 'source-data/'+slug+'/'+path
        t={'id':repo+':'+path,'source_kind':'github_blob','repo':repo,'revision':rev,'repo_path':path,
           'git_blob_sha1':obj['sha'],'git_blob_bytes':obj['size'],'url':f'https://raw.githubusercontent.com/{repo}/{rev}/{quote(path,safe="/")}',
           'destination':dest,'role':role,'max_bytes':64*1024*1024 if role=='profile' else 4*1024*1024,'required':required,
           'expected_plate':plate,'cohort_id':cohort,'processing_stage':'unnormalized annotation-stage candidate, not confirmed by filename alone' if role=='profile' else 'source metadata/methods; never execute upstream code',
           'expected_sha256':None,'expected_bytes':None if obj['size']<300 and role=='profile' else obj['size'],
           'note':'If LFS pointer: verify pointer Git hash, then actual size and SHA-256 from pointer; tree size is not data size'}
        targets.append(t)
    for i in range(1,5):
        plate=f'CPJUMP{i:03d}'
        github('jump-cellpainting/pilot-data-public',f'profiles/2020_12_11_Reagent1_Pfizer/{plate}/{plate}.csv.gz','profile',plate,'protocol_reagent1_thermo_standard')
    # Essential design-only metadata previously filtered out by folder, not a published results table.
    for p in ['checkpoints/all_profile_metadata.csv','output/experiment-metadata.tsv','output/experiment-metadata-updated.tsv']:
        github('jump-cellpainting/jump-scope-analysis',p)
    github('carpenter-singh-lab/2023_Cimini_NatureProtocols','pipelines/analysis.cppipe')
    tree=json.loads((root/'provenance/repos/jump-cellpainting__jump-scope/tree.json').read_text())['tree']
    pipeline_entries=[e for e in tree if e['type']=='blob' and e['path'].startswith('pipelines/2020_11_16_Scope1_PE/') and e['path'].endswith('.cppipe') and '/previous' not in e['path']]
    for e in pipeline_entries:github('jump-cellpainting/jump-scope',e['path'])
    # Primary article XML endpoints. Optional acquisition failures do not hide scientific blockers.
    for pmcid,doi in [('PMC11166567','10.1038/s41592-024-02241-6'),('PMC10536784','10.1038/s41596-023-00840-9')]:
        targets.append({'id':'methods-'+pmcid,'source_kind':'article_xml','url':f'https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML',
          'role':'methods','destination':f'source-data/articles/{pmcid}.xml','pmcid':pmcid,'doi':doi,
          'required':False,'max_bytes':8*1024*1024,'expected_bytes':None,'expected_sha256':None,
          'status':'official endpoint; raw retrieval not verified in chat; optional document acquisition, not guaranteed available'})
    for t in targets:
        if t['destination'] in seen:raise ValueError('Duplicate target path')
        seen.add(t['destination'])
    manifest={'schema':1,'stage':'1B-targeted-acquisition','parent_acquisition_zip_sha256':'e435e4bf38fdb5b7fd8ebf7d46f1d71b16adc8b1c8711686a58f5cbeb050fd24',
              'total_transfer_limit_bytes':768*1024*1024,'wall_seconds':1800,'retries':2,
              'prohibited_work':['normalization','compound scoring','heldout performance inspection','image pixels','app development'],
              'known_s3_profile_bytes':sum(t['expected_bytes'] for t in targets if t['source_kind']=='s3'),
              'lfs_profile_sizes':'four actual data sizes resolved and bounded using verified LFS pointers at run time',
              'targets':targets}
    dump(out/'configs/targeted-acquisition.json',manifest)
    write_table(out/'manifests/targeted-acquisition.tsv',[{k:t.get(k,'') for k in ['id','cohort_id','role','source_kind','url','destination','expected_bytes','git_blob_bytes','expected_etag','git_blob_sha1','required','processing_stage']} for t in targets])
    print('Targets:',len(targets),'profiles:',sum(t['role']=='profile' for t in targets),'listed S3 bytes:',manifest['known_s3_profile_bytes'])
    print('scope pipeline targets',len(pipeline_entries))
    return manifest

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();build(a.input,a.output)
