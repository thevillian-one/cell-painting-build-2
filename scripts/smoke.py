#!/usr/bin/env python3
"""Stage 0 imports, known-answer arithmetic and browser startup only."""
import argparse
import datetime as dt
import importlib
import importlib.metadata as metadata
import json
import math
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import traceback
from urllib.request import urlopen

MODULES = {
    'pycytominer': 'pycytominer', 'copairs': 'copairs', 'pyarrow': 'pyarrow',
    'scikit-learn': 'sklearn', 'streamlit': 'streamlit', 'pytest': 'pytest',
    'numpy': 'numpy', 'pandas': 'pandas', 'scipy': 'scipy', 'tifffile': 'tifffile',
    'Pillow': 'PIL', 'plotly': 'plotly', 'matplotlib': 'matplotlib',
    'pytest-cov': 'pytest_cov', 'playwright': 'playwright.sync_api',
    'PyYAML': 'yaml', 'jsonschema': 'jsonschema', 'boto3': 'boto3',
}

def imports():
    results = {}
    for distribution, module in MODULES.items():
        start = time.monotonic()
        try:
            importlib.import_module(module)
            results[distribution] = {'status': 'PASSED', 'version': metadata.version(distribution)}
        except Exception as e:
            results[distribution] = {'status': 'FAILED', 'error': f'{type(e).__name__}: {e}'}
        results[distribution]['seconds'] = time.monotonic() - start
    return {'passed': all(v['status'] == 'PASSED' for v in results.values()), 'packages': results}

def known_answer():
    # Inputs and exact expected results are fixed here before execution.
    # These are retrieval arithmetic fixtures, never biological evidence.
    from sklearn.metrics import average_precision_score
    cases = [
        ('positives_at_1_and_3', [1, 0, 1, 0], [0.9, 0.8, 0.7, 0.6], 5 / 6),
        ('perfect_retrieval', [1, 1, 0, 0], [0.9, 0.8, 0.7, 0.6], 1.0),
        ('all_tied_scores', [1, 0, 1, 0], [0.5, 0.5, 0.5, 0.5], 0.5),
    ]
    out = []
    for name, labels, scores, expected in cases:
        actual = float(average_precision_score(labels, scores))
        out.append({'case': name, 'labels': labels, 'scores': scores, 'expected': expected,
                    'actual': actual, 'passed': math.isclose(actual, expected, rel_tol=0, abs_tol=1e-12)})
    return {'passed': all(x['passed'] for x in out), 'test_scope': 'sklearn AP arithmetic only; copairs numerical reproduction is Stage 2', 'cases': out}

def browser(output, streamlit=True, executable=None):
    from playwright.sync_api import sync_playwright
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    process = None; log = None
    start = time.monotonic()
    info = {'test_scope': 'Streamlit fixture startup and button' if streamlit else 'static fixture only; NOT a Streamlit test'}
    try:
        if streamlit:
            importlib.import_module('streamlit')
            with socket.socket() as s:
                s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]
            log = (output / 'streamlit-server.log').open('w')
            cmd = [sys.executable, '-m', 'streamlit', 'run',
                   str(Path(__file__).with_name('smoke_streamlit_app.py')),
                   '--server.address=127.0.0.1', f'--server.port={port}',
                   '--server.headless=true', '--browser.gatherUsageStats=false',
                   '--server.fileWatcherType=none']
            info['server_command'] = cmd
            process = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            url = f'http://127.0.0.1:{port}'
            for _ in range(60):
                if process.poll() is not None:
                    raise RuntimeError('Streamlit exited before health check; inspect server log')
                try:
                    with urlopen(url + '/_stcore/health', timeout=1) as r:
                        if r.status == 200 and r.read().strip() == b'ok':
                            info['health_status'] = 200; break
                except Exception:
                    time.sleep(0.5)
            else:
                raise RuntimeError('Streamlit health check did not pass')
        with sync_playwright() as p:
            options = {'headless': True}
            if executable: options['executable_path'] = executable
            b = p.chromium.launch(**options)
            info['browser_version'] = b.version
            info['browser_executable'] = executable or p.chromium.executable_path
            ctx = b.new_context(viewport={'width': 960, 'height': 640}, device_scale_factor=2)
            # Browser traffic is limited to the local smoke fixture.
            blocked = []
            def route(r):
                if r.request.url.startswith(('http://127.0.0.1:', 'data:', 'blob:')):
                    r.continue_()
                else:
                    blocked.append(r.request.url); r.abort()
            ctx.route('**/*', route)
            page = ctx.new_page(); errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            if streamlit:
                response = page.goto(url, wait_until='domcontentloaded', timeout=30000)
                if not response or response.status != 200: raise AssertionError('HTTP startup failed')
                page.get_by_role('heading', name='Stage 0 runtime smoke test', exact=True).wait_for(timeout=30000)
                page.get_by_role('button', name='Confirm runtime', exact=True).click()
                page.get_by_text('BUTTON_OK', exact=True).wait_for(timeout=10000)
                if page.locator('[data-testid="stException"]').count(): raise AssertionError('Streamlit exception in page')
            else:
                page.set_content('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Stage 0 browser fixture</title></head><body><h1>Stage 0 browser fixture</h1><p>No Streamlit or biological data.</p><button id="check" onclick="document.getElementById(\'result\').textContent=\'BUTTON_OK\'">Confirm runtime</button><p id="result"></p></body></html>')
                page.get_by_role('button', name='Confirm runtime').click()
                page.get_by_text('BUTTON_OK', exact=True).wait_for(timeout=10000)
            page.screenshot(path=str(output / ('streamlit-smoke.png' if streamlit else 'browser-only-smoke.png')), full_page=True)
            info.update({'page_errors': errors, 'blocked_external_requests': blocked, 'passed': not errors})
            ctx.close(); b.close()
        return info
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=5)
        if log: log.close()
        info['seconds'] = time.monotonic() - start

def main():
    a = argparse.ArgumentParser(); a.add_argument('mode', choices=['imports','known-answer','browser','browser-only'])
    a.add_argument('--output', required=True); a.add_argument('--browser-executable'); ns = a.parse_args()
    out = Path(ns.output); out.mkdir(parents=True,exist_ok=True)
    try:
        if ns.mode == 'imports': result = imports()
        elif ns.mode == 'known-answer': result = known_answer()
        else: result = browser(out, ns.mode == 'browser', ns.browser_executable)
    except Exception as e:
        result = {'passed': False, 'error': f'{type(e).__name__}: {e}', 'traceback': traceback.format_exc()}
    result['utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    result['python'] = sys.version
    (out / (ns.mode + '.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2)); return 0 if result['passed'] else 1

if __name__ == '__main__': raise SystemExit(main())
