#!/usr/bin/env python3
"""Run ONLY the Stage 0 bootstrap on a user-authorized Python 3.12 Linux runner.

No scientific experiments are present. Network access happens only when main()
is explicitly executed. Full project execution requires a later authorization.
"""
from __future__ import annotations
import csv
import json
import os
from pathlib import Path
import platform
import resource
import shlex
import shutil
import signal
import subprocess
import sys
import time
import traceback

from preflight_support import acquire, dump, lock_from_install_report, runtime_snapshot, sha256, utc

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'stage0-output'
COMMANDS=[]


def command(name, args, timeout=120):
    logs=OUT/'logs'; logs.mkdir(parents=True,exist_ok=True)
    record={'name':name,'command':list(map(str,args)),'cwd':str(ROOT),'started_utc':utc(),'timeout_seconds':timeout}
    start=time.monotonic(); process=None
    print(f'RUN {name}: {shlex.join(record["command"])}',flush=True)
    with (logs/(name+'.stdout.txt')).open('wb') as stdout,(logs/(name+'.stderr.txt')).open('wb') as stderr:
        try:
            process=subprocess.Popen(record['command'],cwd=ROOT,stdout=stdout,stderr=stderr,start_new_session=True)
            code=process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            if process is not None:
                os.killpg(process.pid,signal.SIGTERM)
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired: os.killpg(process.pid,signal.SIGKILL); process.wait()
            code=124; record['error']='Command exceeded its timeout'
        except Exception as e:
            code=127; record['error']=f'{type(e).__name__}: {e}'
    usage=resource.getrusage(resource.RUSAGE_CHILDREN)
    record.update({'exit_code':code,'seconds':time.monotonic()-start,'ended_utc':utc(),
                   'cumulative_children_peak_rss_kib_linux':usage.ru_maxrss,
                   'cumulative_children_user_seconds':usage.ru_utime,'cumulative_children_system_seconds':usage.ru_stime,
                   'stdout':f'logs/{name}.stdout.txt','stderr':f'logs/{name}.stderr.txt'})
    COMMANDS.append(record); dump(logs/(name+'.run.json'),record)
    if code: raise RuntimeError(f'{name} failed with exit {code}; inspect its stdout/stderr logs')
    return record


def finalize(state):
    for folder in ('docs','environment','manifests','evidence','logs'):
        (OUT/folder).mkdir(parents=True,exist_ok=True)
    # Copy only approved source paths. No .git, virtual environment or credentials.
    sources=OUT/'bootstrap-source'; sources.mkdir(exist_ok=True)
    for name in ('scripts','tests','configs','docs','.github'):
        shutil.copytree(ROOT/name,sources/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.pytest_cache'))
    for name in ('README.md','requirements-stage0.in','.gitignore','AUTHORIZATION.md','BOOTSTRAP_CHECKSUMS.sha256'):
        if (ROOT/name).is_file(): shutil.copy2(ROOT/name,sources/name)
    shutil.copy2(ROOT/'docs/execution-plan.md',OUT/'docs/execution-plan.md')
    dump(OUT/'environment/final-runtime.json',runtime_snapshot(OUT))
    # Preserve a transfer inventory even when acquisition failed before a profile existed.
    http=OUT/'manifests/http-requests.json'
    if http.exists():
        with (OUT/'manifests/access-inventory.tsv').open('w',newline='') as f:
            fields=['url','method','destination','result','status','bytes','sha256','error','seconds']
            w=csv.DictWriter(f,fieldnames=fields,delimiter='\t',extrasaction='ignore'); w.writeheader(); w.writerows(json.loads(http.read_text()))
    state['commands']=COMMANDS; state['ended_utc']=utc()
    state['source_hashes']={str(p.relative_to(ROOT)):sha256(p) for base in ('scripts','tests','configs','docs','.github') for p in sorted((ROOT/base).rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    state['spending']={'paid_compute_requested':False,'runner_request':'ubuntu-24.04 standard public repository only','account_quota_verified_by_assistant':False}
    state['biological_analysis_performed']=False
    state['artifact_review_status']='REQUIRES_RETURN_TO_CHAT_AND_HASH_VERIFICATION'
    dump(OUT/'RUN_MANIFEST.json',state)
    ok=state['runner_checks']=='PASSED'
    (OUT/'BUILD_STATUS.md').write_text('# Stage 0 runner result\n\nStage 0: '+('RUNNING' if ok else 'BLOCKED')+'\n\nRunner technical checks: '+state['runner_checks']+'.\n\n'+
        ('The runner has completed the requested preflight. Overall Stage 0 acceptance awaits return and inspection of this artifact by the assistant.' if ok else 'A required preflight failed. Inspect BLOCKERS.md and logs; do not proceed.')+
        '\n\nStages 1-8: NOT_STARTED. No biological analysis, normalization experiment, holdout evaluation, microscopy analysis or project application has been produced.\n')
    (OUT/'BLOCKERS.md').write_text('# Blockers\n\n'+('Awaiting artifact transfer and assistant verification.\n' if ok else state.get('error','Unknown failure')+'\n\n'+state.get('traceback','')))
    (OUT/'NEXT_AGENT.md').write_text('# Continue Stage 0 only\n\nRead docs/execution-plan.md, BUILD_STATUS.md and RUN_MANIFEST.json. Verify CHECKSUMS.sha256 before interpreting results. Check complete profile bytes against manifest, upstream stage documentation, metadata identity, sample/header, install report and hashed lock, pip-check, all import results, known-answer JSON, browser DOM/button result and test logs. A green GitHub check alone is insufficient. Confirm the archive includes all intended evidence. If any gate failed, debug Stage 0 only using bootstrap-source. If all gates pass, record Stage 0 PASSED and request separate Stage 1 authorization. No holdout has been selected or examined.\n')
    (OUT/'DECISIONS.md').write_text('# Stage 0 decisions\n\nUse Python 3.12 because copairs 0.5.4 declares Python <3.13. Use the single prespecified pilot plate BR00117015 only for access and schema checks, not cohort acceptance. Resolve source ref to a commit before downloading metadata. Select the raw aggregate from an actual public bucket listing. Hash the source bytes locally; do not mislabel an S3 ETag as a SHA-256. A new isolated environment resolves dependencies and records all fetched wheel hashes; this is a preflight lock, not a validated reference-analysis environment. All browser checks use an infrastructure-only fixture.\n')
    (OUT/'docs/environment-and-access.md').write_text('# Environment and access evidence\n\nSee environment/initial-runtime.json and final-runtime.json for actual measured resources. See manifests/http-requests.json for actual requests and response headers, provenance/ for source commit/listing/metadata, evidence/profile-inspection.json for header/sample validation, environment/install-report.json for fetched dependencies, and logs/ for actual command exit codes and timing.\n\nExpected limits are configured, not guarantees of later scientific capacity. Read configs/stage0.json under bootstrap-source. No raw images are downloaded. Browser/OS coverage is limited to the runner actually used. Subsequent biological-validation stages have not run.\n')
    files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='CHECKSUMS.sha256')
    (OUT/'CHECKSUMS.sha256').write_text(''.join(f'{sha256(p)}  {p.relative_to(OUT).as_posix()}\n' for p in files))
    # Check every just-created inventory entry by reading it back.
    for line in (OUT/'CHECKSUMS.sha256').read_text().splitlines():
        expected, rel=line.split('  ',1)
        if sha256(OUT/rel)!=expected: raise RuntimeError('Artifact integrity verification failed')
    print('RUNNER CHECKS: '+state['runner_checks']+'; artifact return/review still required.',flush=True)


def main():
    # Fresh output avoids old PASS evidence being mistaken for the current run.
    if OUT.exists() and any(OUT.iterdir()):
        raise SystemExit('stage0-output is not empty. Preserve its previous evidence and use a fresh runner/workspace.')
    OUT.mkdir(parents=True,exist_ok=True)
    state={'stage':0,'started_utc':utc(),'runner_checks':'FAILED','route':'user-authorized GitHub Actions (or equivalent Python 3.12 Linux runtime)',
           'steps':{},'github_context':{n:os.environ.get(n) for n in ('GITHUB_REPOSITORY','GITHUB_SHA','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT')}}
    try:
        dump(OUT/'environment/initial-runtime.json',runtime_snapshot(OUT))
        config=json.loads((ROOT/'configs/stage0.json').read_text())
        if sys.version_info[:2]!=(3,12): raise RuntimeError('Prepared runtime requires Python 3.12; do not override package Python constraints')
        if platform.system()!='Linux': raise RuntimeError('Prepared bootstrap targets Linux; local Mac execution is not requested')
        if shutil.disk_usage(OUT).free < config['min_free_disk_bytes']: raise RuntimeError('Below configured free-disk safety floor')
        state['steps']['runtime']='PASSED'
        print('Resolve official metadata and one listed raw aggregate.',flush=True)
        state['acquisition']=acquire(config,OUT); state['steps']['data']='PASSED'
        env=ROOT/'.stage0-venv'
        if env.exists(): raise RuntimeError('Use a fresh isolated environment; existing .stage0-venv was not reused')
        command('create-environment',[sys.executable,'-m','venv',str(env)],60)
        py=str(env/'bin/python')
        command('install-dependencies',[py,'-m','pip','install','--index-url','https://pypi.org/simple','--disable-pip-version-check','--no-cache-dir','--retries','1','--timeout','30','--only-binary=:all:','--report',str(OUT/'environment/install-report.json'),'-r',str(ROOT/'requirements-stage0.in')],720)
        state['lock']=lock_from_install_report(OUT/'environment/install-report.json',OUT/'environment/requirements-linux-py312.lock.txt')
        command('pip-check',[py,'-m','pip','check'])
        command('pip-freeze',[py,'-m','pip','freeze','--all'])
        shutil.copy2(OUT/'logs/pip-freeze.stdout.txt',OUT/'environment/resolved-freeze.txt')
        command('pip-inspect',[py,'-m','pip','inspect','--local'])
        shutil.copy2(OUT/'logs/pip-inspect.stdout.txt',OUT/'environment/pip-inspect.json')
        command('imports',[py,str(ROOT/'scripts/smoke.py'),'imports','--output',str(OUT/'evidence/smoke')],120)
        state['steps']['dependencies']='PASSED'
        command('known-answer',[py,str(ROOT/'scripts/smoke.py'),'known-answer','--output',str(OUT/'evidence/smoke')],60)
        state['steps']['known_answer']='PASSED'
        command('bootstrap-tests',[py,'-m','pytest','-q','tests','--junitxml',str(OUT/'evidence/bootstrap-tests.xml')],120)
        state['steps']['bootstrap_tests']='PASSED'
        command('install-browser',[py,'-m','playwright','install','--with-deps','chromium'],600)
        command('streamlit-browser',[py,str(ROOT/'scripts/smoke.py'),'browser','--output',str(OUT/'evidence/smoke')],120)
        state['steps']['streamlit_browser']='PASSED'
        state['runner_checks']='PASSED'
    except Exception as e:
        state['error']=f'{type(e).__name__}: {e}'; state['traceback']=traceback.format_exc()
        print(state['traceback'],file=sys.stderr,flush=True)
    finally:
        finalize(state)
    return 0 if state['runner_checks']=='PASSED' else 1

if __name__=='__main__': raise SystemExit(main())
