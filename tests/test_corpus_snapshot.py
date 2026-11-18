"""Behavioral checks for source-preserving acquisition and exact clean publication."""
import base64
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from snapshot_project_corpus import acquire
from publish_cache_fixture import publish, SCHEMA
from verify_corpus import verify


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source.sqlite'
        self.writer = sqlite3.connect(self.source)
        self.addCleanup(self.writer.close)
        schema = json.loads(SCHEMA.read_text())
        for spec in schema['tables'].values(): self.writer.execute(spec['sql'])
        for sql in schema['indexes'].values(): self.writer.execute(sql)
        self.writer.commit()

    def test_wal_rows_rowids_nulls_and_source_preserved(self):
        self.writer.execute('PRAGMA journal_mode=WAL')
        self.writer.execute('PRAGMA wal_autocheckpoint=0')
        self.writer.execute('INSERT INTO component(rowid,mukey,cokey,compname,comppct_r) VALUES(19,12,23,?,?)', ('Silt', 0.123456789012345))
        self.writer.execute('INSERT INTO bad_chorizon_cokey VALUES(23)')
        self.writer.commit()
        paths = [self.source, Path(str(self.source)+'-wal')]
        before = [p.read_bytes() for p in paths]
        acquisition = acquire(self.source, 'ssurgo')
        out = self.root / 'public.sqlite'
        manifest = publish(acquisition, out, 'ssurgo-001')
        with sqlite3.connect(out) as conn:
            row = conn.execute('SELECT rowid,mukey,compname,comppct_r,albedodry_r FROM component').fetchone()
            self.assertEqual(row, (19,12,'Silt',0.123456789012345,None))
            self.assertEqual(conn.execute('SELECT * FROM bad_chorizon_cokey').fetchall(), [(23,)])
        self.assertEqual(before, [p.read_bytes() for p in paths])
        self.assertEqual(manifest['tables']['component']['rows'], 1)
        self.assertFalse(manifest['coverage_complete'])

    def test_reconstruction_removes_deleted_payload(self):
        secret = 'PRIVATE_DELETED_PAYLOAD_' * 100
        self.writer.execute('PRAGMA secure_delete=OFF')
        self.writer.execute('INSERT INTO component(cokey,compname) VALUES(1,?)', (secret,))
        self.writer.commit()
        self.writer.execute('DELETE FROM component'); self.writer.commit()
        acquisition = acquire(self.source, 'ssurgo')
        self.assertIn(b'PRIVATE_DELETED_PAYLOAD_', base64.b64decode(acquisition['backup_base64']))
        out = self.root / 'clean.sqlite'
        publish(acquisition, out, 'ssurgo-002')
        self.assertNotIn(b'PRIVATE_DELETED_PAYLOAD_', out.read_bytes())

    def test_unknown_schema_rejected(self):
        self.writer.execute('CREATE TABLE private_project(email TEXT)'); self.writer.commit()
        with self.assertRaisesRegex(ValueError, 'schema'):
            publish(acquire(self.source,'ssurgo'),self.root/'reject.sqlite','ssurgo-003')
        self.assertFalse((self.root/'reject.sqlite').exists())

    def test_corrupt_acquisition_rejected(self):
        a=acquire(self.source,'ssurgo'); a['backup_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'checksum'):
            publish(a,self.root/'reject.sqlite','ssurgo-003')

    def test_private_text_rejected(self):
        self.writer.execute("INSERT INTO component(cokey,compname) VALUES(1,'/geodata/private')"); self.writer.commit()
        with self.assertRaisesRegex(ValueError,'private'):
            publish(acquire(self.source,'ssurgo'),self.root/'reject.sqlite','ssurgo-003')

    def test_wal_header_without_sidecars_fails_without_creating_them(self):
        self.writer.execute('PRAGMA journal_mode=WAL')
        self.writer.close()
        self.assertFalse(Path(str(self.source)+'-wal').exists())
        before = self.source.read_bytes()
        with self.assertRaisesRegex(RuntimeError, 'lacks sidecars'):
            acquire(self.source, 'ssurgo')
        self.assertEqual(before, self.source.read_bytes())
        self.assertFalse(Path(str(self.source)+'-wal').exists())
        self.assertFalse(Path(str(self.source)+'-shm').exists())

    def test_legacy_negative_table_duplicates_preserved(self):
        self.writer.execute('DROP TABLE bad_component_mukey')
        self.writer.execute('CREATE TABLE bad_component_mukey (mukey INTEGER)')
        self.writer.executemany('INSERT INTO bad_component_mukey(rowid,mukey) VALUES(?,?)', [(7,12),(15,12)])
        self.writer.commit()
        out=self.root/'legacy.sqlite'
        publish(acquire(self.source,'ssurgo'),out,'ssurgo-003')
        with sqlite3.connect(out) as c:
            self.assertEqual(c.execute('SELECT rowid,mukey FROM bad_component_mukey ORDER BY rowid').fetchall(),[(7,12),(15,12)])

    def test_fixture_verifier_rejects_tampered_bytes(self):
        (self.root/'contracts').mkdir()
        (self.root/'contracts/wepppy-cache-schema.json').write_bytes(SCHEMA.read_bytes())
        self.writer.execute('INSERT INTO component(mukey,cokey) VALUES(12,23)')
        self.writer.commit()
        out=self.root/'fixtures/wepppy/ssurgo-001/cache.sqlite'
        manifest=publish(acquire(self.source,'ssurgo'),out,'ssurgo-001')
        out.with_suffix('.manifest.json').write_text(json.dumps(manifest))
        artifacts=out.parent/'artifacts'
        artifacts.mkdir()
        soil=b'7778\n# fixture metadata\n1 1\n'
        (artifacts/'source.sol').write_bytes(soil)
        (out.parent/'artifacts.manifest.json').write_text(json.dumps({'artifacts':[{'file':'artifacts/source.sol','bytes':len(soil),'sha256':hashlib.sha256(soil).hexdigest(),'noncomment_payload_sha256':hashlib.sha256(b'7778\n1 1\n').hexdigest(),'mukey':12,'cokey':23}]}))
        self.assertEqual(verify(self.root)[0]['bytes'],out.stat().st_size)
        (artifacts/'source.sol').write_bytes(soil+b'changed')
        with self.assertRaisesRegex(ValueError,'artifact checksum'):
            verify(self.root)
        (artifacts/'source.sol').write_bytes(soil)
        with out.open('ab') as stream: stream.write(b'changed')
        with self.assertRaisesRegex(ValueError,'checksum'):
            verify(self.root)

    def test_existing_output_not_overwritten(self):
        out=self.root/'exists.sqlite'; out.write_bytes(b'existing')
        with self.assertRaises(FileExistsError):publish(acquire(self.source,'ssurgo'),out,'ssurgo-001')
        self.assertEqual(out.read_bytes(),b'existing')


if __name__ == '__main__': unittest.main()
