"""Local SQLite history; live and demonstration sessions are kept distinct."""
import json
import sqlite3
import time
from datetime import datetime, timezone
from dataclasses import asdict


class Store:
    def __init__(self, path):
        self.path=path
        self.db = sqlite3.connect(path)
        self.db.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS saved_references(profile_key TEXT PRIMARY KEY, payload TEXT);
        CREATE TABLE IF NOT EXISTS pit_reports(id INTEGER PRIMARY KEY, session_id INTEGER, sim_time REAL, payload TEXT);
        CREATE TABLE IF NOT EXISTS setup_tests(id INTEGER PRIMARY KEY, created TEXT, payload TEXT);
        CREATE TABLE IF NOT EXISTS sessions(id INTEGER PRIMARY KEY, started TEXT, ended TEXT,
          mode TEXT, profile TEXT, sim_start REAL, sim_end REAL);
        CREATE TABLE IF NOT EXISTS samples(id INTEGER PRIMARY KEY, session_id INTEGER,
          sim_time REAL, lap INTEGER, distance REAL, data TEXT);
        CREATE INDEX IF NOT EXISTS samples_session ON samples(session_id,lap,sim_time);
        CREATE TABLE IF NOT EXISTS laps(id INTEGER PRIMARY KEY, session_id INTEGER,
          lap INTEGER, lap_time REAL, clean INTEGER, reasons TEXT, recording TEXT, reviews TEXT, context TEXT);
        ''')
        self.session = None
        self.last_commit = time.monotonic()

    def start(self, mode, profile, sim_time):
        self.finish()
        self.session = self.db.execute('INSERT INTO sessions(started,mode,profile,sim_start,sim_end) VALUES(?,?,?,?,?)',
            (datetime.now(timezone.utc).isoformat(), mode, json.dumps(profile),sim_time,sim_time)).lastrowid
        self.db.commit()
        return self.session

    def record(self, d):
        if self.session is None:
            return
        self.db.execute('INSERT INTO samples(session_id,sim_time,lap,distance,data) VALUES(?,?,?,?,?)',
            (self.session,d.get('SessionTime'),d.get('Lap'),d.get('LapDistPct'),json.dumps(d,allow_nan=False)))
        self.db.execute('UPDATE sessions SET sim_end=? WHERE id=?',(d.get('SessionTime'),self.session))
        if time.monotonic()-self.last_commit >= 2:
            self.db.commit(); self.last_commit = time.monotonic()

    def save_pit_report(self,report):
        if self.session is None:return
        self.db.execute('INSERT INTO pit_reports(session_id,sim_time,payload) VALUES(?,?,?)',(self.session,report.get('sim_time'),json.dumps(report,allow_nan=False)));self.db.commit()

    def lap(self, lap):
        cursor = self.db.execute('INSERT INTO laps(session_id,lap,lap_time,clean,reasons,recording,reviews,context) VALUES(?,?,?,?,?,?,?,?)',
            (self.session,lap['lap'],lap['lap_time'],lap['clean'],json.dumps(lap['reasons']),
             json.dumps([asdict(s) for s in lap['samples']]),json.dumps(lap['reviews']),json.dumps(lap['context'])))
        self.db.commit()
        return cursor.lastrowid

    @staticmethod
    def reference_key(meta,conditions,mode="LIVE"):
        return json.dumps([mode,str(meta.get('track_id','')),str(meta.get('config','')).casefold(),str(meta.get('car_path','')).casefold(),str(meta.get('car_id','')),list(conditions)],sort_keys=True)

    def reference(self,meta,conditions,mode="LIVE"):
        key=self.reference_key(meta,conditions,mode)
        row=self.db.execute('SELECT payload FROM saved_references WHERE profile_key=?',(key,)).fetchone()
        if row:return json.loads(row[0])
        # Preserve compatible pre-0.8 references; never cross known car IDs.
        legacy=json.dumps([mode,str(meta.get('track_id','')),str(meta.get('config','')).casefold(),str(meta.get('car_path','')).casefold(),list(conditions)],sort_keys=True)
        row=self.db.execute('SELECT payload FROM saved_references WHERE profile_key=?',(legacy,)).fetchone()
        if not row:return None
        payload=json.loads(row[0]);old=payload.get('profile',{}).get('car_id')
        if old not in (None,'') and meta.get('car_id') not in (None,'') and str(old)!=str(meta['car_id']):return None
        return payload

    def save_external_reference(self,payload,mode="LIVE"):
        key=self.reference_key(payload['profile'],payload['context'],mode)
        self.db.execute('INSERT OR REPLACE INTO saved_references(profile_key,payload) VALUES(?,?)',(key,json.dumps(payload)))
        self.db.commit()

    def save_reference(self,lap,meta,mode="LIVE"):
        if not lap.get('clean'):return False
        from .core import reference_payload
        key=self.reference_key(meta,lap['context'],mode)
        current=self.reference(meta,lap['context'],mode)
        if current and current['lap_time']<=lap['lap_time']:return False
        payload=reference_payload(lap,meta)
        self.db.execute('INSERT OR REPLACE INTO saved_references(profile_key,payload) VALUES(?,?)',(key,json.dumps(payload)))
        self.db.commit();return True

    def personal_best(self,meta,conditions,mode="LIVE"):
        target=self.reference_key(meta,conditions,mode)
        rows=self.db.execute('SELECT l.lap_time,s.profile FROM laps l JOIN sessions s ON s.id=l.session_id WHERE l.clean=1 AND s.mode=? AND l.context=? ORDER BY l.lap_time ASC',(mode,json.dumps(list(conditions))))
        for seconds,profile in rows:
            if self.reference_key(json.loads(profile),conditions,mode)==target:return seconds
        return None

    def save_test(self, payload):
        self.db.execute('INSERT INTO setup_tests(created,payload) VALUES(?,?)',
            (datetime.now(timezone.utc).isoformat(),json.dumps(payload)))
        self.db.commit()

    def latest_test(self):
        row=self.db.execute('SELECT payload FROM setup_tests ORDER BY id DESC LIMIT 1').fetchone()
        return json.loads(row[0]) if row else None

    def history(self):
        return self.db.execute('''SELECT l.id,l.lap,l.lap_time,l.clean,s.started,s.mode,s.profile,
          s.sim_end-s.sim_start,s.id FROM laps l JOIN sessions s ON s.id=l.session_id ORDER BY l.id DESC LIMIT 1000''').fetchall()

    def sessions(self):
        return self.db.execute('''SELECT id,started,mode,profile,sim_end-sim_start,
          (SELECT COUNT(*) FROM laps WHERE session_id=s.id) FROM sessions s ORDER BY id DESC LIMIT 300''').fetchall()

    def get_lap(self, lap_id):
        row = self.db.execute('''SELECT l.*,s.profile FROM laps l JOIN sessions s ON s.id=l.session_id WHERE l.id=?''',(lap_id,)).fetchone()
        return dict(lap=row[2],lap_time=row[3],clean=bool(row[4]),reasons=json.loads(row[5]),
                    samples=json.loads(row[6]),reviews=json.loads(row[7]),context=json.loads(row[8]),profile=json.loads(row[9]))

    def finish(self):
        if self.session:
            self.db.execute('UPDATE sessions SET ended=? WHERE id=?',(datetime.now(timezone.utc).isoformat(),self.session))
            self.db.commit(); self.session = None

    def close(self):
        self.finish(); self.db.close()
