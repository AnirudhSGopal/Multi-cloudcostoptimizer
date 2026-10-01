import os
import sqlite3

for root, dirs, files in os.walk(r"c:\Users\ANIRUDHMALU\Documents\cloudProject"):
    for f in files:
        if f.endswith(".db"):
            p = os.path.join(root, f)
            print("Found DB:", p, "size:", os.path.getsize(p))
            try:
                conn = sqlite3.connect(p)
                c = conn.cursor()
                tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
                print("  Tables:", tables)
                for t in tables:
                    count = c.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
                    print(f"    Table {t}: {count} rows")
            except Exception as e:
                print("  Error reading DB:", e)
