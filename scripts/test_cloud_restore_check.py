import hashlib,sqlite3,tempfile,unittest
from pathlib import Path
from cloud_restore_check import verify

class RestoreTest(unittest.TestCase):
    def test_restore_and_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);db=sqlite3.connect(":memory:")
            db.executescript(Path("apps/cloud/migrations/0001_registry.sql").read_text())
            db.execute("INSERT INTO strategies(owner,id,name,created) VALUES(?,?,?,?)",("test","a"*32,"test",1))
            db.execute("INSERT INTO revisions VALUES(?,?,?,?,?,?)",("test","a"*32,1,"pass",hashlib.sha256(b"pass").hexdigest(),1))
            # SQLite dump order can put triggers before data depending on exporter.
            # Explicit dump with base schema, rows and triggers restored last.
            rows=list(db.iterdump());source=root/"backup.sql"
            # iterdump creates results/revisions before strategies and includes
            # all triggers after INSERTs, preserving current heads.
            source.write_text("\n".join(rows));db.close()
            self.assertEqual(verify(source,root/"restored.sqlite"),{"strategies":1,"revisions":1,"results":0})
            with self.assertRaises(FileExistsError):verify(source,root/"restored.sqlite")
            source.write_text(source.read_text().replace(hashlib.sha256(b"pass").hexdigest(),"0"*64))
            with self.assertRaises(ValueError):verify(source,root/"bad.sqlite")
if __name__=="__main__":unittest.main()
