import hashlib
import hmac
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.errors import AppError
from app.models import Trip, now


class Database:
    def __init__(self, path: str):
        self.path = path

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path, timeout=5)
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def initialize(self):
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('CREATE TABLE IF NOT EXISTS trips (id TEXT PRIMARY KEY, revision INTEGER NOT NULL, token_hash TEXT NOT NULL, body TEXT NOT NULL)')
            conn.execute('PRAGMA user_version=1')

    def create(self, trip: Trip, token: str):
        with self.connect() as conn:
            conn.execute('INSERT INTO trips VALUES (?, ?, ?, ?)',
                         (trip.trip_id, trip.revision, self.digest(token), trip.model_dump_json()))

    @staticmethod
    def digest(token):
        return hashlib.sha256(token.encode()).hexdigest()

    def get(self, trip_id: str) -> Trip:
        with self.connect() as conn:
            row = conn.execute('SELECT body FROM trips WHERE id=?', (trip_id,)).fetchone()
        if row is None:
            raise AppError('trip_not_found', '没有找到这个行程，请检查链接。', 404)
        return Trip.model_validate_json(row[0])

    def authorize(self, trip_id: str, token: str):
        with self.connect() as conn:
            row = conn.execute('SELECT token_hash FROM trips WHERE id=?', (trip_id,)).fetchone()
        if row is None:
            raise AppError('trip_not_found', '没有找到这个行程。', 404)
        if not hmac.compare_digest(row[0], self.digest(token)):
            raise AppError('forbidden', '此链接只能查看，请在创建行程的浏览器中继续编辑。', 403)

    def save(self, trip: Trip, expected_revision: int) -> Trip:
        saved = trip.model_copy(update={'revision': expected_revision + 1, 'updated_at': now()})
        with self.connect() as conn:
            count = conn.execute('UPDATE trips SET revision=?, body=? WHERE id=? AND revision=?',
                                 (saved.revision, saved.model_dump_json(), saved.trip_id, expected_revision)).rowcount
        if count != 1:
            raise AppError('revision_conflict', '行程已更新，请刷新后重试。', 409)
        return saved
