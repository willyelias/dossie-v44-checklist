#!/usr/bin/env python3
"""
Servidor local com banco de dados relacional SQLite (estudos.db) e espelhamento JSON
para o Dossiê Operacional v44 (ABDI + TJPB + TJRN).
"""
import http.server
import json
import os
import sqlite3
from datetime import datetime

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "estudos.db")
JSON_PATH = os.path.join(DATA_DIR, "progress_db.json")

os.makedirs(DATA_DIR, exist_ok=True)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS state_snapshots (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            version INTEGER,
            updated_at TEXT,
            payload_json TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS checklist_items (
            item_id TEXT PRIMARY KEY,
            collection TEXT NOT NULL,
            title TEXT,
            date_str TEXT,
            done INTEGER DEFAULT 0,
            acertos TEXT,
            target_q INTEGER,
            notes TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_state_to_sqlite(data: dict):
    now = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO state_snapshots (id, version, updated_at, payload_json)
        VALUES (1, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            version = excluded.version,
            updated_at = excluded.updated_at,
            payload_json = excluded.payload_json
    """, (data.get("version", 44), now, json.dumps(data, ensure_ascii=False)))

    for col in ("anexoA", "admin", "sprints", "nucleos", "grades"):
        for item in data.get(col, []):
            cur.execute("""
                INSERT INTO checklist_items (item_id, collection, title, date_str, done, acertos, target_q, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(item_id) DO UPDATE SET
                    done = excluded.done,
                    acertos = excluded.acertos,
                    notes = excluded.notes,
                    updated_at = excluded.updated_at
            """, (
                item.get("id"),
                col,
                item.get("title", ""),
                item.get("date") or item.get("period") or item.get("dia") or "",
                1 if item.get("done") else 0,
                str(item.get("acertos", item.get("qDone", ""))),
                int(item.get("targetQ", 0) or 0),
                item.get("notes", ""),
                now
            ))

    conn.commit()
    conn.close()

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_state_from_sqlite():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT payload_json FROM state_snapshots WHERE id = 1")
    row = cur.fetchone()
    conn.close()
    if row and row[0]:
        return json.loads(row[0])
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


class ChecklistRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/state"):
            data = load_state_from_sqlite()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(json.dumps(data or {}, ensure_ascii=False).encode("utf-8"))
            return
        super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/state"):
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length).decode("utf-8")
            data = json.loads(raw)
            save_state_to_sqlite(data)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "db": DB_PATH}).encode("utf-8"))
            return
        self.send_error(404)


if __name__ == "__main__":
    init_db()
    print(f"============================================================")
    print(f" Dossiê v44 Server + SQLite Ativo!")
    print(f" Banco SQLite: {DB_PATH}")
    print(f" Acesse no navegador: http://localhost:{PORT}")
    print(f"============================================================")
    with http.server.ThreadingHTTPServer(("127.0.0.1", PORT), ChecklistRequestHandler) as httpd:
        httpd.serve_forever()
