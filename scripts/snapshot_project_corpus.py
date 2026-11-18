#!/usr/bin/env python3
"""Acquire one read-only SQLite backup as JSON on stdout; safe to stream over SSH.

Output is private acquisition evidence. Publication requires publish_cache_fixture.py.
"""
import argparse
import base64
import datetime
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time


def fingerprint(path):
    try:
        with path.open('rb') as stream:
            before = os.fstat(stream.fileno())
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            after = os.fstat(stream.fileno())
    except FileNotFoundError:
        return None
    signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if signature(before) != signature(after):
        raise RuntimeError('Source changed while hashing')
    return {'sha256': digest, 'bytes': before.st_size, 'mtime_ns': before.st_mtime_ns}


def acquire(source, dataset, timeout=45, max_bytes=32 * 1024 * 1024):
    source = Path(source).absolute()
    if source.is_symlink() or not source.is_file():
        raise ValueError('Source must be an existing regular database file')
    wal = Path(str(source) + '-wal')
    shm = Path(str(source) + '-shm')
    with source.open('rb') as stream:
        header = stream.read(100)
    if header[18:20] == b'\x02\x02' and (not wal.is_file() or not shm.is_file()):
        raise RuntimeError('WAL-mode database lacks sidecars; refusing a potentially creating open')
    if wal.exists() and not shm.is_file():
        raise RuntimeError('WAL has no existing shared-memory file; refusing source creation')
    if source.stat().st_size + (wal.stat().st_size if wal.exists() else 0) > max_bytes:
        raise ValueError('Source exceeds acquisition byte limit')
    start = time.monotonic()
    before = {'database': fingerprint(source), 'wal': fingerprint(wal)}
    if sum(x['bytes'] for x in before.values() if x) > max_bytes:
        raise ValueError('Source exceeds acquisition byte limit')
    def progress(status, remaining, total):
        if time.monotonic() - start > timeout:
            raise TimeoutError('SQLite backup exceeded acquisition deadline')
    src = sqlite3.connect(source.as_uri() + '?mode=ro', uri=True, timeout=2)
    dst = sqlite3.connect(':memory:')
    try:
        src.execute('PRAGMA query_only=ON')
        src.backup(dst, pages=128, progress=progress, sleep=0.05)
        if dst.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise ValueError('Backup integrity check failed')
        data = dst.serialize()
    finally:
        dst.close()
        src.close()
    if len(data) > max_bytes:
        raise ValueError('Backup exceeds acquisition byte limit')
    meta = Path(str(source) + '.meta.md')
    if meta.exists():
        meta_before = fingerprint(meta)
        if meta_before['bytes'] > 65536:
            raise ValueError('Metadata sidecar exceeds limit')
        metadata = meta.read_text()
        if fingerprint(meta) != meta_before:
            raise RuntimeError('Sidecar changed during acquisition')
    else:
        meta_before = None
        metadata = None
    after = {'database': fingerprint(source), 'wal': fingerprint(wal)}
    if before != after:
        raise RuntimeError('Source database/WAL changed during acquisition; discard and retry')
    if time.monotonic() - start > timeout:
        raise TimeoutError('Acquisition exceeded deadline')
    return {'dataset': dataset, 'observed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'source_fingerprints': before, 'source_unchanged': True,
            'sqlite_version': sqlite3.sqlite_version, 'backup_sha256': hashlib.sha256(data).hexdigest(),
            'backup_base64': base64.b64encode(data).decode('ascii'),
            'metadata_fingerprint': meta_before, 'metadata_text': metadata,
            'elapsed_seconds': time.monotonic() - start}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--dataset', choices=('ssurgo', 'statsgo'), required=True,
                        help='WEPPpy cache/collection label, not source-dataset proof')
    parser.add_argument('--expected-host', required=True)
    args = parser.parse_args()
    if os.uname().nodename != args.expected_host:
        raise RuntimeError('Unexpected host; refusing acquisition')
    print(json.dumps(acquire(args.source, args.dataset)))


if __name__ == '__main__':
    main()
