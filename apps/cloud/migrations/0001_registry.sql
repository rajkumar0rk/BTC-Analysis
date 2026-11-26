-- All write invariants enforced inside SQLite/D1 transactions.
CREATE TABLE strategies (
  owner TEXT NOT NULL,
  id TEXT NOT NULL CHECK(length(id)=32),
  name TEXT NOT NULL CHECK(length(CAST(name AS BLOB)) BETWEEN 1 AND 160),
  latest_version INTEGER NOT NULL DEFAULT 0 CHECK(latest_version BETWEEN 0 AND 100),
  created INTEGER NOT NULL,
  PRIMARY KEY(owner,id)
);
CREATE TABLE revisions (
  owner TEXT NOT NULL,
  strategy_id TEXT NOT NULL,
  version INTEGER NOT NULL CHECK(version BETWEEN 1 AND 100),
  source TEXT NOT NULL CHECK(length(CAST(source AS BLOB)) BETWEEN 1 AND 65536),
  code_sha256 TEXT NOT NULL CHECK(length(code_sha256)=64),
  created INTEGER NOT NULL,
  PRIMARY KEY(owner,strategy_id,version),
  FOREIGN KEY(owner,strategy_id) REFERENCES strategies(owner,id)
);
CREATE TRIGGER strategy_quota BEFORE INSERT ON strategies
WHEN (SELECT count(*) FROM strategies WHERE owner=NEW.owner)>=30
BEGIN SELECT RAISE(ABORT,'quota_exceeded'); END;
CREATE TRIGGER revision_guard BEFORE INSERT ON revisions
BEGIN
  SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM strategies WHERE owner=NEW.owner AND id=NEW.strategy_id AND latest_version=NEW.version-1)
    THEN RAISE(ABORT,'version_conflict') END;
  SELECT CASE WHEN (SELECT count(*) FROM revisions WHERE owner=NEW.owner)>=300
    THEN RAISE(ABORT,'quota_exceeded') END;
END;
CREATE TRIGGER revision_advance AFTER INSERT ON revisions
BEGIN UPDATE strategies SET latest_version=NEW.version WHERE owner=NEW.owner AND id=NEW.strategy_id; END;
CREATE TRIGGER revision_immutable_update BEFORE UPDATE ON revisions
BEGIN SELECT RAISE(ABORT,'immutable_revision'); END;
CREATE TRIGGER revision_immutable_delete BEFORE DELETE ON revisions
BEGIN SELECT RAISE(ABORT,'immutable_revision'); END;

CREATE TABLE results (
 owner TEXT NOT NULL,
 id TEXT NOT NULL CHECK(length(id)=32),
 strategy_id TEXT NOT NULL,
 version INTEGER NOT NULL,
 symbol TEXT NOT NULL CHECK(symbol IN ('BTCUSD','ETHUSD')),
 dataset_sha256 TEXT NOT NULL CHECK(length(dataset_sha256)=64),
 result_sha256 TEXT NOT NULL CHECK(length(result_sha256)=64),
 payload_sha256 TEXT NOT NULL CHECK(length(payload_sha256)=64),
 payload TEXT NOT NULL CHECK(length(CAST(payload AS BLOB))<=32768),
 created INTEGER NOT NULL,
 PRIMARY KEY(owner,id),
 FOREIGN KEY(owner,strategy_id,version) REFERENCES revisions(owner,strategy_id,version)
);
CREATE TRIGGER result_quota BEFORE INSERT ON results
WHEN NOT EXISTS(SELECT 1 FROM results WHERE owner=NEW.owner AND id=NEW.id)
 AND (SELECT count(*) FROM results WHERE owner=NEW.owner)>=200
BEGIN SELECT RAISE(ABORT,'quota_exceeded'); END;
CREATE TRIGGER result_immutable BEFORE UPDATE ON results
BEGIN SELECT RAISE(ABORT,'immutable_result'); END;
