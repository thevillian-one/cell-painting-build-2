"""Fetch a frozen Stage 1B target list and inspect identities, not treatment outcomes.

Run with Python 3.11+. Standard library only. No upstream scripts are executed.
"""
from __future__ import annotations
import argparse, csv, datetime, gzip, hashlib, io, json, os, platform, re, shutil, sys, time, traceback
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, quote
from urllib.request import Request, build_opener, HTTPRedirectHandler
import xml.etree.ElementTree as ET
from cohort_tools import dump, sha256, safe_path, inspect_profile, read_table, join_wells, write_table, write_checksums, verify_manifest

HOSTS={'raw.githubusercontent.com','media.githubusercontent.com','cellpainting-gallery.s3.amazonaws.com','www.ebi.ac.uk'}
MAX_UNPACKED=256*1024*1024

def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()

def valid_url(url):
    p=urlparse(url)
    if p.scheme!='https' or p.hostname not in HOSTS or p.username or p.password or p.port not in (None,443):
        raise ValueError('Unapproved URL: '+url)
    return url

class Redirects(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        valid_url(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

class Downloader:
    def __init__(self,root,limit,wall=1800,retries=2,opener=None,sleep=time.sleep):
        self.root=Path(root);self.limit=int(limit);self.total=0;self.deadline=time.monotonic()+wall
        self.retries=retries;self.opener=opener or build_opener(Redirects()).open;self.sleep=sleep;self.records=[]
    def fetch(self,url,relative,max_bytes,expected_size=None,expected_hash=None,etag=None):
        valid_url(url);p=safe_path(self.root,relative);p.parent.mkdir(parents=True,exist_ok=True)
        part=p.with_name(p.name+'.partial')
        for attempt in range(self.retries+1):
            if time.monotonic()>self.deadline:raise TimeoutError('Overall acquisition deadline reached')
            record={'url':url,'destination':relative,'attempt':attempt+1,'started_utc':utc(),'status':'STARTED'}
            self.records.append(record)
            try:
                headers={'User-Agent':'CellPainting-Stage1B/1.0','Accept-Encoding':'identity'}
                if etag:headers['If-Match']=etag
                with self.opener(Request(url,headers=headers),timeout=40) as response:
                    valid_url(response.url)
                    if response.status!=200:raise ValueError('Expected complete HTTP 200 response')
                    length=response.headers.get('Content-Length')
                    if length is not None and (int(length)>max_bytes or self.total+int(length)>self.limit):raise ValueError('Advertised transfer cap exceeded')
                    if etag and response.headers.get('ETag')!=etag:raise ValueError('Source ETag changed from recorded listing')
                    h=hashlib.sha256();size=0
                    with part.open('wb') as f:
                        while True:
                            if time.monotonic()>self.deadline:raise TimeoutError('Overall acquisition deadline reached')
                            chunk=response.read(1024*1024)
                            if not chunk:break
                            size+=len(chunk);self.total+=len(chunk)
                            if size>max_bytes or self.total>self.limit:raise ValueError('Transfer cap exceeded')
                            h.update(chunk);f.write(chunk)
                    if not size:raise ValueError('Empty response')
                    if length is not None and size!=int(length):raise ValueError('Truncated Content-Length')
                    if expected_size is not None and size!=expected_size:raise ValueError('Size differs from source manifest')
                    if expected_hash and h.hexdigest()!=expected_hash:raise ValueError('SHA-256 mismatch')
                    part.replace(p)
                    record.update({'status':'DOWNLOADED','bytes':size,'sha256':h.hexdigest(),'effective_url':response.url,
                                   'etag':response.headers.get('ETag'),'last_modified':response.headers.get('Last-Modified'),'ended_utc':utc()})
                return p
            except Exception as e:
                record.update({'status':'FAILED','error':type(e).__name__+': '+str(e),'ended_utc':utc()})
                part.unlink(missing_ok=True)
                transient=(isinstance(e,HTTPError) and e.code in (429,500,502,503,504)) or (isinstance(e,URLError) and not isinstance(e,HTTPError))
                if transient and attempt<self.retries:
                    self.sleep(min(10,2**attempt));continue
                raise
            finally:dump(self.root/'manifests/http-requests.json',self.records)
        raise RuntimeError('Unreachable retry state')


def git_blob_hash(path):
    p=Path(path);h=hashlib.sha1();h.update(f'blob {p.stat().st_size}\0'.encode())
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def fetch_target(d,t):
    if t['source_kind']=='github_blob':
        pointer_name='provenance/git-blobs/'+hashlib.sha256(t['id'].encode()).hexdigest()+'.blob'
        p=d.fetch(t['url'],pointer_name,t['max_bytes'],expected_size=t['git_blob_bytes'])
        if git_blob_hash(p)!=t['git_blob_sha1']:raise ValueError('Pinned Git blob hash mismatch')
        prefix=p.read_bytes() if p.stat().st_size<2048 else b''
        if prefix.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
            text=prefix.decode('ascii');hm=re.search(r'^oid sha256:([a-f0-9]{64})$',text,re.M);sm=re.search(r'^size ([0-9]+)$',text,re.M)
            if not hm or not sm:raise ValueError('Malformed LFS pointer')
            size=int(sm[1])
            if size>t['max_bytes']:raise ValueError('LFS content exceeds cap')
            url=f'https://media.githubusercontent.com/media/{t["repo"]}/{t["revision"]}/{quote(t["repo_path"],safe="/")}'
            final=d.fetch(url,t['destination'],t['max_bytes'],expected_size=size,expected_hash=hm[1])
            return final,{'lfs':True,'pointer_path':pointer_name,'data_expected_sha256':hm[1],'data_expected_bytes':size}
        final=safe_path(d.root,t['destination']);final.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,final)
        return final,{'lfs':False,'git_blob_sha1':t['git_blob_sha1']}
    p=d.fetch(t['url'],t['destination'],t['max_bytes'],t.get('expected_bytes'),t.get('expected_sha256'),t.get('expected_etag'))
    if t['source_kind']=='article_xml':
        doc=ET.parse(p).getroot()
        if doc.tag!='article':raise ValueError('Not JATS article XML')
        ids=[el.text for el in doc.findall('.//article-id')]
        if t['doi'] not in ids:raise ValueError('Downloaded article DOI does not match requested methods source')
    return p,{'lfs':False}


def bounded_plain(path,root):
    """Validate the full gzip stream with a decompression bound, preserving original bytes."""
    p=Path(path)
    if p.suffix!='.gz':return p,None
    temp=Path(root)/'.scratch'/('unpacked-'+hashlib.sha256(str(p).encode()).hexdigest()+'.csv')
    temp.parent.mkdir(parents=True,exist_ok=True);size=0
    try:
        with gzip.open(p,'rb') as source,temp.open('wb') as dest:
            while True:
                b=source.read(1024*1024)
                if not b:break
                size+=len(b)
                if size>MAX_UNPACKED:raise ValueError('Gzip expansion exceeds 256 MiB cap')
                dest.write(b)
        return temp,temp
    except Exception:
        temp.unlink(missing_ok=True);raise


def profile_audit(path,t,out,code_root):
    plain,temp=bounded_plain(path,out)
    try:
        summary,header,wells=inspect_profile(plain,t['expected_plate'],numeric_qc=False)
        layout=read_table(code_root/'reference-data/layouts'/ (t['cohort_id']+'.tsv'))[1]
        joined=join_wells(wells,layout)
        if summary['missing_wells']:raise ValueError('Incomplete plate, review before accepting cohort')
        write_table(out/'manifests/wells'/ (t['id'].replace('/','_').replace(':','_')+'.tsv'),joined)
        headerpath=out/'manifests/headers'/ (t['id'].replace('/','_').replace(':','_')+'.txt')
        headerpath.parent.mkdir(parents=True,exist_ok=True);headerpath.write_text('\n'.join(header)+'\n',encoding='utf-8')
        # Preserve only explicit metadata columns, not numeric phenotype outcomes.
        with plain.open(encoding='utf-8-sig', errors='strict', newline='') as handle:
            reader=csv.DictReader(handle)
            metadata_fields=[x for x in header if x.startswith('Metadata_')]
            source_metadata=[{x:row[x] for x in metadata_fields} for row in reader]
        metadata_path=out/'manifests/profile-metadata'/(t['id'].replace('/','_').replace(':','_')+'.tsv')
        write_table(metadata_path,source_metadata,metadata_fields)
        conflicts=[];expected={row['well']:row['source_broad_sample'] for row in joined}
        sample_columns=[x for x in metadata_fields if x.lower()=='metadata_broad_sample']
        for row in source_metadata:
            for field in sample_columns:
                from cohort_tools import well
                if row[field].strip()!=expected[well(row['Metadata_Well'])]:
                    conflicts.append({'well':row['Metadata_Well'],'field':field,'profile_value':row[field],
                                      'layout_value':expected[well(row['Metadata_Well'])]})
        counts={role:sum(r['role']==role for r in joined) for role in ['negative_control','positive_control','treatment']}
        return {**summary,'role_counts':counts,'sample_groups':len({r['sample_id'] for r in joined if r['role']!='negative_control'}),
                'header_path':str(headerpath.relative_to(out)),'source_profile_sha256':sha256(path),
                'source_metadata_path':str(metadata_path.relative_to(out)),'embedded_sample_layout_conflicts':conflicts,
                'scope':'identity, layout and schema only; no numeric completeness, phenotype calculation or selection on outcomes',
                'full_cohort_accepted':False,'why_not':'dose/exposure/physical preparation and processing provenance review still required'}
    finally:
        if temp:temp.unlink(missing_ok=True)


def collect(config,out,code_root,downloader=None):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);code_root=Path(code_root)
    d=downloader or Downloader(out,config['total_transfer_limit_bytes'],config.get('wall_seconds',1800),config.get('retries',2))
    records=[];issues=[];notes=[];warnings=[];started=utc();start=time.monotonic()
    dump(out/'environment/runtime.json',{'python':sys.version,'platform':platform.platform(),'cpu_count':os.cpu_count(),
       'disk_before':dict(zip(('total','used','free'),shutil.disk_usage(out))),'scope':'Acquisition and metadata only; no scientific package installation'})
    if shutil.disk_usage(out).free<2*1024**3:raise RuntimeError('Less than 2 GiB free disk; stop before downloads')
    for t in config['targets']:
        print('Acquire:',t['id'],flush=True)
        try:
            p,extra=fetch_target(d,t)
            rec={'id':t['id'],'role':t['role'],'destination':t['destination'],'bytes':p.stat().st_size,'sha256':sha256(p),
                 'source':t,'status':'ACQUIRED',**extra};records.append(rec)
            if t['role']=='profile':
                try:
                    rec['identity_audit']=profile_audit(p,t,out,code_root)
                    if rec['identity_audit']['embedded_sample_layout_conflicts']:
                        notes.append({'id':t['id'],'error':'Embedded sample metadata conflicts with frozen layout; retain source and do not accept cohort.'})
                except Exception as e:
                    note={'id':t['id'],'error':type(e).__name__+': '+str(e)};notes.append(note);rec['identity_audit']={'status':'NEEDS_REVIEW',**note}
                    print('QUALIFICATION NOTE',note,flush=True)
            elif p.name.endswith(('.csv','.tsv')):
                # Capture header only. Some author metadata lives under results/checkpoint paths.
                # Do not summarize any unrecognized performance columns.
                with p.open(encoding='utf-8-sig',errors='strict',newline='') as f:
                    header=next(csv.reader(f,delimiter='\t' if p.suffix=='.tsv' else ','))
                rec['source_header']=header
        except Exception as e:
            issue={'id':t['id'],'required':t['required'],'error':type(e).__name__+': '+str(e)}
            (issues if t['required'] else warnings).append(issue);print('ACQUISITION ISSUE',issue,flush=True)
        dump(out/'manifests/target-receipts.json',records)
    result={'stage':'1B_TARGETED_ACQUISITION','acquisition_status':'PASSED' if not issues else 'BLOCKED',
            'stage1_status':'BLOCKED_PENDING_COHORT_REVIEW','stage2_started':False,'phenotype_analysis_performed':False,
            'started_utc':started,'ended_utc':utc(),'targets_expected':len(config['targets']),
            'targets_acquired':len(records),'profiles_acquired':sum(r['role']=='profile' for r in records),
            'required_acquisition_issues':issues,'optional_methods_warnings':warnings,'identity_review_notes':notes,
            'actual_transfer_bytes':d.total,'elapsed_seconds':time.monotonic()-start,
            'source_code_only_no_scientific_packages':'This is a fresh acquisition runtime, not the Stage 0 analysis environment',
            'github':{k:os.environ.get(k) for k in ['GITHUB_REPOSITORY','GITHUB_SHA','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT']}}
    dump(out/'RUN_MANIFEST.json',result)
    dump(out/'configs/targeted-acquisition.json',config)
    (out/'BUILD_STATUS.md').write_text('# Stage 1B acquisition\n\nAcquisition: '+result['acquisition_status']+'\n\nStage 1: BLOCKED_PENDING_COHORT_REVIEW.\nStage 2: NOT_STARTED, NOT_AUTHORIZED.\n\nReview source receipts and scientific metadata. A green run is not cohort acceptance.\n',encoding='utf-8')
    (out/'BLOCKERS.md').write_text('# Remaining work\n\nConfirm actual protocol assay dose; scope exposure and material aliases; processing stage of Reagent1; cross-cohort feature semantics and independent preparations.\n\nRequired download issues:\n'+json.dumps(issues,indent=2)+'\nOptional methods access warnings:\n'+json.dumps(warnings,indent=2)+'\nIdentity review notes:\n'+json.dumps(notes,indent=2)+'\n',encoding='utf-8')
    return 0 if not issues else 1


def finalize(out,repo):
    out=Path(out);repo=Path(repo);out.mkdir(parents=True,exist_ok=True)
    (out/'logs').mkdir(exist_ok=True)
    for p in repo.glob('stage1b-*-console.log'):shutil.copy2(p,out/'logs'/p.name)
    if not (out/'RUN_MANIFEST.json').exists():dump(out/'RUN_MANIFEST.json',{'stage':'1B','acquisition_status':'BLOCKED','stage1_status':'BLOCKED','stage2_started':False,'error':'Collector did not reach final status; inspect logs'})
    if not (out/'BUILD_STATUS.md').exists():(out/'BUILD_STATUS.md').write_text('Stage 1B BLOCKED. Collector did not finish. Stage 2 NOT_STARTED.\n',encoding='utf-8')
    code=repo/'stage1b'
    if code.exists():shutil.copytree(code,out/'collector-source',ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'),dirs_exist_ok=True)
    (out/'NEXT_AGENT.md').write_text('Read collector-source/docs/execution-plan.md, collector-source/docs/cohort-audit.md and collector-source/docs/NEXT_AGENT.md. Verify CHECKSUMS.sha256 and target receipts before Stage 1B qualification. Retain parent stage1-acquisition.zip. Do not start Stage 2. The full scientific gate is not passed by acquisition.\n',encoding='utf-8')
    (out/'DECISIONS.md').write_text('Targets selected using experiment-design metadata only. Source raw files unchanged. Keep anonymous Compound1-8 source labels separate from identified cross-study chemicals. No treatment-score or normalization calculations.\n',encoding='utf-8')
    shutil.rmtree(out/'.scratch',ignore_errors=True)
    write_checksums(out)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config');ap.add_argument('--output',required=True);ap.add_argument('--finalize',action='store_true');ap.add_argument('--repo',default='.')
    a=ap.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    if a.finalize:finalize(out,Path(a.repo));return 0
    try:
        config=json.loads(Path(a.config).read_text(encoding='utf-8'))
        return collect(config,out,Path(__file__).resolve().parent.parent)
    except Exception as e:
        dump(out/'evidence/fatal-error.json',{'error':str(e),'traceback':traceback.format_exc(),'utc':utc()})
        (out/'BUILD_STATUS.md').write_text('Stage 1B BLOCKED: '+str(e)+'\nNo Stage 2 work.\n',encoding='utf-8')
        print(traceback.format_exc(),flush=True);return 1
    finally:write_checksums(out)

if __name__=='__main__':sys.exit(main())
