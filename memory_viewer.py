import sqlite3
from datetime import datetime

db = sqlite3.connect("bot_memory.db")

print("\n=== MEMORIES ===")
memories = db.execute("SELECT user_id, content, timestamp FROM memories ORDER BY timestamp DESC LIMIT 10")
for m in memories:
    print(f"{m[2]}: {m[0]} - {m[1][:50]}...")

print("\n=== RELATIONSHIPS ===")
rels = db.execute("SELECT user_id, friendliness, last_interaction FROM relationships")
for r in rels:
    print(f"{r[0]}: friendliness {r[1]}/10, last: {r[2]}")

print("\n=== THOUGHTS ===")
thoughts = db.execute("SELECT thought, timestamp, expressed FROM thoughts ORDER BY timestamp DESC")
for t in thoughts:
    print(f"{t[1]}: {t[0][:50]}... (expressed: {t[2]})")
