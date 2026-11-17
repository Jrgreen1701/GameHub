"""Verified GitHub Releases updater for GameHub."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from urllib.request import Request, urlopen

REPO = 'Jrgreen1701/GameHub'
API = f'https://api.github.com/repos/{REPO}/releases/latest'
MAX_SIZE = 250 * 1024 * 1024

def version_tuple(v):
    parts = v.lstrip('v').split('.')
    if len(parts) != 3 or not all(x.isdigit() for x in parts):
        raise ValueError('Invalid version number')
    return tuple(map(int, parts))

def fetch(url, limit=100000):
    if not url.startswith('https://'):
        raise ValueError('HTTPS required')
    req = Request(url, headers={'User-Agent':'GameHub-Updater/3.6','Accept':'application/vnd.github+json'})
    with urlopen(req, timeout=15) as resp:
        data = resp.read(limit + 1)
        if len(data) > limit:
            raise ValueError('Update metadata too large')
        return data

def check_for_update(current_version):
    release = json.loads(fetch(API))
    version = str(release['tag_name']).lstrip('v')
    if release.get('draft') or release.get('prerelease') or version_tuple(version) <= version_tuple(current_version):
        return None
    assets = {a['name']: a for a in release.get('assets', [])}
    installer_name = f'GameHub_Setup_v{version}.exe'
    if installer_name not in assets or 'SHA256SUMS.txt' not in assets:
        raise ValueError('Release is missing the installer or checksum file')
    installer_url = assets[installer_name]['browser_download_url']
    checksum_url = assets['SHA256SUMS.txt']['browser_download_url']
    for url in (installer_url, checksum_url):
        if not url.startswith(f'https://github.com/{REPO}/releases/download/'):
            raise ValueError('Unexpected release asset URL')
    checksum_text = fetch(checksum_url, 8192).decode('utf-8')
    expected = None
    for line in checksum_text.splitlines():
        fields = line.strip().split()
        if len(fields) == 2 and fields[1].lstrip('*') == installer_name and len(fields[0]) == 64:
            expected = fields[0].lower()
    if not expected or any(c not in '0123456789abcdef' for c in expected):
        raise ValueError('No valid installer SHA-256 checksum')
    return {'version': version, 'url': installer_url, 'sha256': expected, 'filename': installer_name}

def download_and_install(info):
    destination = Path(tempfile.mkdtemp(prefix='gamehub-update-')) / info['filename']
    digest = hashlib.sha256()
    total = 0
    req = Request(info['url'], headers={'User-Agent':'GameHub-Updater/3.6'})
    with urlopen(req, timeout=30) as resp, destination.open('wb') as out:
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk: break
            total += len(chunk)
            if total > MAX_SIZE: raise ValueError('Update exceeds size limit')
            digest.update(chunk)
            out.write(chunk)
    if digest.hexdigest() != info['sha256']:
        destination.unlink(missing_ok=True)
        raise ValueError('Update checksum mismatch. Installation cancelled.')
    subprocess.Popen([str(destination), '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART'], close_fds=True)
    return destination
