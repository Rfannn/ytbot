import aiosqlite
import os

DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "bot.db")


async def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                bale_id TEXT UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                is_admin INTEGER DEFAULT 0,
                chat_mode TEXT DEFAULT 'none',
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                user_id INTEGER REFERENCES users(id),
                details TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        await db.commit()


async def get_user(bale_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE bale_id = ?", (bale_id,))
        return await cursor.fetchone()


async def create_user(bale_id: str, username: str = None, first_name: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (bale_id, username, first_name) VALUES (?, ?, ?)",
            (bale_id, username, first_name),
        )
        await db.commit()


async def set_chat_mode(bale_id: str, mode: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET chat_mode = ? WHERE bale_id = ?", (mode, bale_id))
        await db.commit()


async def get_chat_mode(bale_id: str):
    user = await get_user(bale_id)
    return user["chat_mode"] if user else "none"


async def add_conversation(bale_id: str, role: str, content: str):
    async with aiosqlite.connect(DB_PATH) as db:
        user = await get_user(bale_id)
        if user:
            await db.execute(
                "INSERT INTO conversations (user_id, role, content) VALUES (?, ?, ?)",
                (user["id"], role, content),
            )
            await db.commit()


async def get_conversation_history(bale_id: str, limit: int = 20):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        user = await get_user(bale_id)
        if not user:
            return []
        cursor = await db.execute(
            "SELECT role, content FROM conversations WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user["id"], limit),
        )
        rows = await cursor.fetchall()
        return list(reversed(rows))


async def clear_conversation(bale_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        user = await get_user(bale_id)
        if user:
            await db.execute("DELETE FROM conversations WHERE user_id = ?", (user["id"],))
            await db.commit()


async def log_stat(action: str, bale_id: str, details: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        user = await get_user(bale_id)
        if user:
            await db.execute(
                "INSERT INTO stats (action, user_id, details) VALUES (?, ?, ?)",
                (action, user["id"], details),
            )
            await db.commit()


async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users ORDER BY created_at DESC")
        return await cursor.fetchall()


async def get_stats_summary():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        total = (await db.execute("SELECT COUNT(*) as c FROM users")).fetchone()
        cursor = await db.execute("SELECT action, COUNT(*) as count FROM stats GROUP BY action")
        stats_rows = await cursor.fetchall()
        return total, stats_rows


async def get_setting(key: str, default: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row[0] if row else default


async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
        )
        await db.commit()


async def set_admin(bale_id: str, is_admin: bool = True):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_admin = ? WHERE bale_id = ?", (int(is_admin), bale_id))
        await db.commit()


async def is_admin(bale_id: str):
    user = await get_user(bale_id)
    return user and user["is_admin"] == 1
