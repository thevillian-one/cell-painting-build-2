"""Stage 1A: acquire exact pilot files and design metadata for cohort review.

This is a deliberately bounded substage of Stage 1, not a scientific pass gate.
It never normalizes, scores compounds, opens image pixels, or chooses a holdout.
"""
from __future__ import annotations
import argparse
import configparser
import csv
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import resource
import shutil
import sys
import time
import traceback
from urllib.parse import quote
from audit_support import *

DATA_EXTENSIONS=('.csv','.tsv','.csv.gz','.tsv.gz','.json','.yaml','.yml','.txt')
DOC_NAMES={'readme.md','license','license.md','license_bsd3.md','license_cc0.md','.gitmodules','.gitattributes','environment.yml'}


def metadata_blob(repo,path):
    low=path.lower();base=PurePosixPath(low).name
    if base in DOC_NAMES and '/' not in path:return True
    # Do not read notebooks or benchmark/result tables during cohort selection.
    if any(x in PurePosixPath(low).parts for x in ('output','outputs','results','figures','notebooks','checkpoints','source_data_files')):
        return False
    if '/.ipynb_checkpoints/' in '/'+low:return False
    if repo.endswith(('JUMP-Target','JUMP-MOA')):
        return low.endswith(DATA_EXTENSIONS) and any(k in low for k in ('compound','moa','platemap','metadata'))
    if low.startswith(('metadata/','batchfiles/','config_files/')) and low.endswith(DATA_EXTENSIONS):return True
    if base in ('jumpexperimentmastertable.csv','cellprofiler_features.csv'):return True
    if low.startswith('load_data_csv/') and any(p in path for p in PLATES) and low.endswith(('.csv','.csv.gz')):
        return repo==PILOT_REPO
    if low.startswith('pipelines/') and BATCH in path and low.endswith('.cppipe'):
        return repo==PILOT_REPO
    if repo.endswith('pilot-data-public'):
        return low.startswith(('metadata/','batchfiles/','config_files/')) and low.endswith(DATA_EXTENSIONS)
    return False


def table_inventory(path,root):
    header,rows=read_metadata(path)
    return {'path':str(path.relative_to(root)),'rows':len(rows),'columns':len(header),'header':header,
            'scope':'Metadata schema/row count, not treatment performance'},header,rows


def image_references(path,root):
    header,rows=read_metadata(path,200000)
    pcol=next((c for c in ('Metadata_Plate','Image_Metadata_Plate','Metadata_Assay_Plate_Barcode') if c in header),None)
    wcol=next((c for c in ('Metadata_Well','Image_Metadata_Well','Metadata_well') if c in header),None)
    scol=next((c for c in ('Metadata_Site','Image_Metadata_Site','Metadata_Field','Metadata_site') if c in header),None)
    files=[c for c in header if c.startswith('FileName_')]
    out=[]
    for i,r in enumerate(rows,2):
        for f in files:
            channel=f[len('FileName_'):];directory=r.get('PathName_'+channel,'')
            out.append({'mapping_source':str(path.relative_to(root)),'source_row':i,
                        'plate':r.get(pcol,'') if pcol else '', 'well':r.get(wcol,'') if wcol else '',
                        'site':r.get(scol,'') if scol else '', 'channel_source_label':channel,
                        'source_directory':directory,'source_filename':r[f],
                        'verification':'SOURCE_REFERENCE_ONLY_IMAGE_BYTES_NOT_REQUESTED'})
    return out


def classify_object(key):
    p=PurePosixPath(key);name=p.name.lower()
    if name.endswith(('.sqlite','.parquet','.h5')) and '/backend/' in key:return 'SINGLE_CELL_OR_UNQUALIFIED_FORMAT_NOT_DOWNLOADED'
    if any(t in name for t in ('normalized','spherized','feature_select')):return 'PROCESSED_NOT_RAW'
    if raw_profile_candidates([{'key':key}]):return 'RAW_AGGREGATE_CANDIDATE'
    if '/profiles/' in key and name in (p.parent.name.lower()+'.csv',p.parent.name.lower()+'.csv.gz'):
        return 'AGGREGATE_CANDIDATE_PROCESSING_STAGE_NEEDS_CONFIRMATION'
    return 'INVENTORY_ONLY'


def run(config,output):
    out=Path(output).resolve();out.mkdir(parents=True,exist_ok=True)
    fetch=Fetcher(out,config['total_download_limit_bytes'])
    issues=[];repos={};acquired=[];tables=[];objects=[];profiles=[];image_rows=[]
    started=utc();start=time.monotonic()
    dump(out/'environment/runtime.json',{'utc':started,'python':sys.version,'platform':platform.platform(),
          'cpu_count':os.cpu_count(),'disk':dict(zip(('total','used','free'),shutil.disk_usage(out))),
          'scope':'Standard-library acquisition only; no reinstallation or numerical use of the Stage 0 scientific environment.',
          'github':{k:os.environ.get(k) for k in ('GITHUB_REPOSITORY','GITHUB_SHA','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT')}})

    def issue(task,e):
        message=f'{type(e).__name__}: {e}'
        issues.append({'task':task,'message':message});print('ISSUE',task,message,flush=True)
        dump(out/'evidence/acquisition-issues.json',issues)

    def collect_repo(repo,ref=None):
        if repo in repos:return repos[repo]
        print('Repository inventory:',repo,flush=True)
        rev,tree=fetch.github_tree(repo,ref)
        repos[repo]={'revision':rev,'tree':tree}
        selected=[e for e in tree if e.get('type')=='blob' and metadata_blob(repo,e['path'])]
        dump(out/f'manifests/repos/{repo.replace("/","__")}-selection.json',
             {'repo':repo,'revision':rev,'all_tree_entries':len(tree),'metadata_entries':selected})
        for e in selected:
            try:
                p=fetch.github_blob(repo,rev,e,config['metadata_object_limit_bytes'])
                acquired.append({'repo':repo,'revision':rev,'repo_path':e['path'],'path':str(p.relative_to(out)),
                                 'bytes':p.stat().st_size,'sha256':sha256(p),'role':'SOURCE_METADATA_OR_METHODS'})
                if p.name.endswith(('.csv','.tsv','.csv.gz','.tsv.gz')):
                    inv,header,rows=table_inventory(p,out);tables.append(inv)
                    if p.name=='JUMPExperimentMasterTable.csv':
                        # Preserve design columns; do not summarize published conclusions.
                        keep=[x for x in header if x not in ('Qualitative conclusion drawn (if any)',)]
                        design=[{'source_row':i,**{k:r[k] for k in keep}} for i,r in enumerate(rows,2)]
                        write_tsv(out/'manifests/protocol-master-design.tsv',design,['source_row']+keep)
                        moa=[r for r in design if re.search('MOA',str(r.get('Treatments','')),re.I)]
                        write_tsv(out/'manifests/protocol-moa-text-candidates.tsv',moa,['source_row']+keep)
                    if repo==PILOT_REPO and e['path'].startswith('load_data_csv/'):
                        image_rows.extend(image_references(p,out))
            except Exception as ex:issue(f'{repo}:{e["path"]}',ex)
        return repos[repo]

    # Reuse the exact pilot revision independently verified from the returned Stage 0 evidence.
    for spec in config['repositories']:
        try:collect_repo(spec['repo'],spec.get('ref'))
        except Exception as e:issue('repo '+spec['repo'],e)

    # Follow the protocol's actual profiles-pilots gitlink only for metadata, never all profiles.
    prot='carpenter-singh-lab/2023_Cimini_NatureProtocols'
    if prot in repos:
        item=repos[prot];mods=out/'source-data/repos'/prot.replace('/','__')/'.gitmodules'
        try:
            if not mods.exists():raise ValueError('Protocol .gitmodules was not acquired')
            cp=configparser.ConfigParser();cp.read(mods)
            for section in cp.sections():
                if cp.get(section,'path',fallback='')!='profiles-pilots':continue
                url=cp.get(section,'url');m=re.fullmatch(r'https://github.com/([^/]+/[^/]+?)(?:\.git)?',url)
                if not m:raise ValueError('Unrecognized public submodule URL')
                entries=[e for e in item['tree'] if e.get('path')=='profiles-pilots' and e.get('type')=='commit']
                if len(entries)!=1:raise ValueError('Missing/ambiguous profiles-pilots gitlink')
                collect_repo(m[1],entries[0]['sha'])
        except Exception as e:issue('protocol submodule metadata',e)

    # Download the exact experiment metadata and the four listed raw pilot aggregates.
    try:
        item=repos[PILOT_REPO]
        matches=[e for e in item['tree'] if e.get('path')=='benchmark/output/experiment-metadata.tsv']
        if len(matches)!=1:raise ValueError('Expected one pinned experiment-metadata.tsv')
        meta=fetch.github_blob(PILOT_REPO,item['revision'],matches[0],2*1024*1024)
        acquired.append({'repo':PILOT_REPO,'revision':item['revision'],'repo_path':matches[0]['path'],'path':str(meta.relative_to(out)), 'bytes':meta.stat().st_size,'sha256':sha256(meta),'role':'SOURCE_EXPERIMENT_DESIGN'})
        if sha256(meta)!=config['expected_pilot_metadata_sha256']:raise ValueError('Pilot metadata differs from Stage 0')
        design=pilot_design(meta)
        write_tsv(out/'manifests/pilot-experimental-design.tsv',design,list(design[0]))
        for plate in PLATES:
            try:
                prefix=f'cpg0000-jump-pilot/source_4/workspace/backend/{BATCH}/{plate}/'
                listed,_=fetch.s3_list(prefix,label='pilot-'+plate)
                raw=raw_profile_candidates(listed)
                exact=[x for x in raw if PurePosixPath(x['key']).name==plate+'.csv']
                if len(exact)!=1:raise ValueError('Expected one exact raw CSV from actual S3 listing')
                obj=exact[0]
                local=f'data/pilot/{plate}.csv'
                p=fetch.fetch('https://'+BUCKET+'/'+quote(obj['key'],safe='/'),local,
                              config['profile_object_limit_bytes'],expected_size=obj['bytes'],
                              expected_hash=config['expected_first_profile_sha256'] if plate==PLATES[0] else None)
                summary,header,wells,quality=inspect_profile(p,plate)
                summary.update({'key':obj['key'],'role':'RAW_AGGREGATE_UNNORMALIZED', 'local_path':local})
                profiles.append(summary)
                dump(out/f'evidence/profiles/{plate}.json',summary)
                (out/'evidence/profiles'/f'{plate}-header.txt').write_text('\n'.join(header)+'\n')
                write_tsv(out/f'manifests/{plate}-wells.tsv',wells,['plate','well','source_row'])
                write_tsv(out/f'manifests/{plate}-missingness.tsv',quality,['feature','missing','infinite','nonnumeric'])
            except Exception as e:issue('pilot '+plate,e)
    except Exception as e:issue('pilot design acquisition',e)

    # Metadata + numerical object inventories only for external candidates. No outcome-based selection.
    # Full external profiles are deliberately not fetched until their condition/replicate metadata is reviewed.
    for dataset in ('cpg0001-cellpainting-protocol','cpg0002-jump-scope'):
        try:
            _,sources=fetch.s3_list(dataset+'/',delimiter='/',label=dataset+'-root')
            selected=[s for s in sources if re.fullmatch(re.escape(dataset)+r'/source_\d+/',s)]
            if not selected:raise ValueError('No source prefixes in actual bucket listing')
            if len(selected)>config['max_sources_per_dataset']:raise ValueError('Too many sources for bounded inventory')
            for source in selected:
                for folder in ('workspace/backend/','workspace/profiles/','workspace/metadata/'):
                    try:
                        listed,_=fetch.s3_list(source+folder,max_pages=config['max_listing_pages'],
                                              label=(source+folder).replace('/','-'))
                        for obj in listed:
                            objects.append({'dataset':dataset,**obj,'classification':classify_object(obj['key'])})
                        if folder=='workspace/metadata/':
                            for obj in listed:
                                if not obj['key'].lower().endswith(DATA_EXTENSIONS):continue
                                p=fetch.fetch('https://'+BUCKET+'/'+quote(obj['key'],safe='/'),
                                              'source-data/s3/'+obj['key'],config['metadata_object_limit_bytes'],expected_size=obj['bytes'])
                                acquired.append({'repo':'S3','revision':'','repo_path':obj['key'],'path':str(p.relative_to(out)),
                                                  'bytes':p.stat().st_size,'sha256':sha256(p),'role':'SOURCE_METADATA'})
                                if p.name.endswith(('.csv','.tsv','.csv.gz','.tsv.gz')):
                                    inv,_,_=table_inventory(p,out);tables.append(inv)
                    except Exception as e:issue(source+folder,e)
        except Exception as e:issue(dataset+' source discovery',e)

    # Verify required design inputs were really obtained, not merely listed.
    required_sources = {
        'jump-cellpainting/JUMP-Target': ('JUMP-Target-1_compound_platemap.tsv','JUMP-Target-1_compound_metadata.tsv'),
        'jump-cellpainting/JUMP-MOA': ('JUMP-MOA_compound_platemap.tsv','JUMP-MOA_compound_metadata.tsv'),
        prot: ('JUMPExperimentMasterTable.csv',),
    }
    for repo,paths in required_sources.items():
        for path in paths:
            if not any(x['repo']==repo and x['repo_path']==path for x in acquired):
                issue('required design input', ValueError(repo+':'+path+' was not acquired'))
    if not any(x['repo']=='jump-cellpainting/jump-scope' and x['repo_path'].startswith('metadata/') for x in acquired):
        issue('scope metadata',ValueError('No source metadata table was acquired'))
    if not image_rows:
        issue('pilot image references',ValueError('No image-reference rows were extracted; inspect source layout'))
    for dataset in ('cpg0001-cellpainting-protocol','cpg0002-jump-scope'):
        if not any(x['dataset']==dataset for x in objects):
            issue(dataset+' inventory',ValueError('No numerical or metadata objects were listed'))

    dump(out/'manifests/repository-revisions.json',{r:d['revision'] for r,d in repos.items()})
    dump(out/'manifests/source-files.json',acquired)
    dump(out/'manifests/metadata-tables.json',tables)
    dump(out/'manifests/pilot-profiles.json',profiles)
    dump(out/'manifests/external-objects.json',objects)
    write_tsv(out/'manifests/external-profile-inventory.tsv',objects,
              ['dataset','key','bytes','etag','last_modified','listing_evidence','classification'])
    image_fields=['mapping_source','source_row','plate','well','site','channel_source_label','source_directory','source_filename','verification']
    write_tsv(out/'manifests/image-references.tsv',image_rows,image_fields)
    # No compound/control/dose guesses: preserve every source table for strict joins during Stage 1B review.
    acquisition_status='PASSED' if not issues and len(profiles)==4 else 'BLOCKED'
    status={'stage':'1A','task':'Raw pilot acquisition and external design inventory',
            'acquisition_status':acquisition_status,'stage1_acceptance':'BLOCKED_PENDING_COHORT_REVIEW',
            'pilot_profiles_acquired':len(profiles),'source_files_acquired':len(acquired),
            'image_reference_rows':len(image_rows),'external_object_count':len(objects),
            'issues':issues,'prohibited_work_performed':False,'started_utc':started,'ended_utc':utc(),
            'elapsed_seconds':time.monotonic()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'total_download_bytes':fetch.total}
    dump(out/'RUN_MANIFEST.json',status)
    (out/'BUILD_STATUS.md').write_text(f'''# Stage 1A acquisition result\n\nAcquisition: {acquisition_status}\n\nStage 1: BLOCKED_PENDING_COHORT_REVIEW. This workflow does not approve scientific cohorts.\n\nStage 0 evidence was verified in the parent checkpoint; this run uses a fresh acquisition-only Python runtime.\n\nNo normalization, effect scores, compound rankings, holdout evaluation, image pixels or application code were run.\n\nReturn this complete artifact to the assistant for continued Stage 1 review. Do not proceed to Stage 2.\n''')
    (out/'BLOCKERS.md').write_text('# Stage 1 blockers\n\n'+ '\n'.join('- '+x['task']+': '+x['message'] for x in issues)+
        '\n\nScientific gate still requires treatment/control/dose joins, independent-unit audit, external cohort selection and acquisition, and comparison counts.\n')
    (out/'NEXT_AGENT.md').write_text('''# Continue Stage 1, not Stage 2\n\nVerify CHECKSUMS.sha256, RUN_MANIFEST.json, actual logs and all downloaded file hashes. Read docs/execution-plan.md and docs/stage1-current-audit.md. Resolve acquisition issues before interpreting data.\n\nUse the returned pilot platemap and annotation tables for strict well/sample/compound joins. Do not assume the recommended JUMP-Target concentration is the applied pilot dose, or that solvent=DMSO means a negative control. Review the protocol master design and source metadata for coherent U2OS JUMP-MOA subsets. Resolve the scope acquisition labels to physical preparations before counting replication. Select exact external raw aggregates using the returned listing, never an outcome-based subset.\n\nPrepare a bounded Stage 1B acquisition if compatible external profiles are not yet present. An inventory-only external cohort is not accepted. Complete manifests, independent comparison counts and the Stage 1 gate before seeking Stage 2 authorization. This is still the user-authorized Stage 1.\n''')
    (out/'DECISIONS.md').write_text('''# Stage 1A decisions\n\nKeep the verified pilot source revision. Collect only documented candidate profiles and design metadata. Record all inventories before choosing external profiles. Never execute downloaded source scripts. Preserve LFS hashes and original metadata. Do not pool A549 and U2OS or count reimages as separate preparations. All cohort roles remain pending scientific review.\n\nA workflow success means the acquisition substage executed, not that Stage 1 scientific acceptance has passed.\n''')
    return 0 if acquisition_status=='PASSED' else 1


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
    try:
        config=json.loads(Path(a.config).read_text())
        # Save exactly the code/configuration used without caches or real-data copies from the repository.
        src=Path(__file__).resolve().parent.parent
        shutil.copytree(src,out/'collector-source',ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'),dirs_exist_ok=True)
        (out/'docs').mkdir(exist_ok=True)
        for source,dest in [('docs/execution-plan.md','docs/execution-plan.md'),('docs/current-audit.md','docs/stage1-current-audit.md')]:
            if (src/source).exists():shutil.copy2(src/source,out/dest)
        rc=run(config,out)
    except Exception as e:
        dump(out/'evidence/fatal-error.json',{'error':str(e),'traceback':traceback.format_exc(),'utc':utc()})
        (out/'BUILD_STATUS.md').write_text('# Stage 1\n\nBLOCKED: acquisition did not complete. See evidence/fatal-error.json.\n')
        rc=1
    write_checksums(out)
    return rc

if __name__=='__main__':sys.exit(main())
