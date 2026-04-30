import sqlite3
import os

class WorkspaceDB:
    def __init__(self, db_path="cinepulse_workspace.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_tables()

    def _init_tables(self):
        cursor = self.conn.cursor()
        # 存储分镜大纲与素材路径
        cursor.execute('''CREATE TABLE IF NOT EXISTS scenes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            narration TEXT,
                            visual_desc TEXT,
                            img_path TEXT,
                            aud_path TEXT,
                            status TEXT DEFAULT 'PENDING'
                        )''')
        self.conn.commit()

    def add_scene(self, narration, visual_desc):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO scenes (narration, visual_desc) VALUES (?, ?)", (narration, visual_desc))
        self.conn.commit()

    def update_scene_assets(self, scene_id, img_path=None, aud_path=None, status=None):
        cursor = self.conn.cursor()
        if img_path: cursor.execute("UPDATE scenes SET img_path=? WHERE id=?", (img_path, scene_id))
        if aud_path: cursor.execute("UPDATE scenes SET aud_path=? WHERE id=?", (aud_path, scene_id))
        if status: cursor.execute("UPDATE scenes SET status=? WHERE id=?", (status, scene_id))
        self.conn.commit()

    def get_all_scenes(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM scenes")
        return cursor.fetchall()

    def clear_all(self):
        self.conn.execute("DELETE FROM scenes")
        self.conn.commit()