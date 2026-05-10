#!/usr/bin/env python3
"""
Tworzy bazę danych fotograf.db z trzech plików .txt z pytaniami.
Uruchom w katalogu fotograf-app/backend/ lub podaj ścieżkę jako argument.

Użycie:
    python3 build_db.py
    python3 build_db.py --db /ścieżka/do/fotograf.db
"""

import sqlite3
import re
import uuid
import sys
import os
import argparse
from pathlib import Path

# ── Kolory terminala ─────────────────────────────────────────────────────────
GRN = "\033[32m"; YLW = "\033[33m"; RED = "\033[31m"; RST = "\033[0m"; BLD = "\033[1m"

def ok(msg):  print(f"  {GRN}✓{RST} {msg}")
def warn(msg): print(f"  {YLW}⚠{RST} {msg}")
def err(msg):  print(f"  {RED}✗{RST} {msg}")

# ── Parsowanie pliku .txt ─────────────────────────────────────────────────────

def parse_file(filepath: Path, chapter_id: int, chapter_name: str):
    """Parsuje plik i zwraca listę słowników z danymi pytań."""
    raw = filepath.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n(?=\d+\.)", raw.strip())

    questions = []
    skipped = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        lines = block.split("\n")

        # Treść pytania
        q_match = re.match(r"^\d+\.\s*(.+)", lines[0].strip())
        if not q_match:
            skipped.append(lines[0][:60])
            continue
        q_text = q_match.group(1).strip()

        # Odpowiedzi A/B/C/D
        answers = {}
        for line in lines[1:]:
            line = line.strip()
            m = re.match(r"^([A-D])\)\s*(.+)", line)
            if not m:
                continue
            letter = m.group(1)
            ans_text = m.group(2).strip()
            is_correct = 1 if "[POPRAWNA]" in ans_text else 0
            ans_text = ans_text.replace("[POPRAWNA]", "").strip()
            answers[letter] = {"text": ans_text, "is_correct": is_correct}

        # Odpowiedź otwarta
        open_match = re.search(
            r"Odpowiedź otwarta:\s*(.+?)(?=\n\d+\.|\Z)", block, re.DOTALL
        )
        sample = ""
        if open_match:
            sample = " ".join(open_match.group(1).strip().split())

        # Walidacja
        issues = []
        if len(answers) < 2:
            issues.append(f"za mało odpowiedzi ({len(answers)})")
        if not any(a["is_correct"] for a in answers.values()):
            issues.append("brak oznaczenia [POPRAWNA]")
        if not sample:
            issues.append("brak odpowiedzi otwartej")

        if "za mało odpowiedzi" in " ".join(issues):
            skipped.append(q_text[:60])
            continue

        questions.append({
            "chapter_id": chapter_id,
            "text": q_text,
            "answers": answers,
            "sample": sample,
            "issues": issues,
        })

    return questions, skipped

# ── Zapis do bazy ─────────────────────────────────────────────────────────────

def insert_questions(conn, questions):
    c = conn.cursor()
    inserted = 0

    for q in questions:
        qid_closed = str(uuid.uuid4())
        qid_open   = str(uuid.uuid4())

        c.execute(
            "INSERT OR IGNORE INTO questions (id, chapter_id, text, type) VALUES (?,?,?,?)",
            (qid_closed, q["chapter_id"], q["text"], "closed")
        )
        c.execute(
            "INSERT OR IGNORE INTO questions (id, chapter_id, text, type) VALUES (?,?,?,?)",
            (qid_open, q["chapter_id"], q["text"], "open")
        )

        for i, letter in enumerate(["A", "B", "C", "D"]):
            if letter not in q["answers"]:
                continue
            ans = q["answers"][letter]
            c.execute(
                "INSERT OR IGNORE INTO answers (id, question_id, text, is_correct, sort_order) VALUES (?,?,?,?,?)",
                (str(uuid.uuid4()), qid_closed, ans["text"], ans["is_correct"], i)
            )

        if q["sample"]:
            c.execute(
                "INSERT OR IGNORE INTO open_answers (id, question_id, sample_answer) VALUES (?,?,?)",
                (str(uuid.uuid4()), qid_open, q["sample"])
            )

        inserted += 1

    return inserted

# ── Inicjalizacja bazy (taka sama jak w app.py) ───────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,
    chapter_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('closed','open')),
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (chapter_id) REFERENCES chapters(id)
);
CREATE TABLE IF NOT EXISTS answers (
    id TEXT PRIMARY KEY,
    question_id TEXT NOT NULL,
    text TEXT NOT NULL,
    is_correct INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    FOREIGN KEY (question_id) REFERENCES questions(id)
);
CREATE TABLE IF NOT EXISTS open_answers (
    id TEXT PRIMARY KEY,
    question_id TEXT NOT NULL UNIQUE,
    sample_answer TEXT NOT NULL,
    FOREIGN KEY (question_id) REFERENCES questions(id)
);
CREATE TABLE IF NOT EXISTS user_answers (
    id TEXT PRIMARY KEY,
    question_id TEXT NOT NULL,
    session_id TEXT,
    answer_id TEXT,
    open_text TEXT,
    is_correct INTEGER,
    answered_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (question_id) REFERENCES questions(id)
);
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    chapter_id INTEGER,
    started_at TEXT DEFAULT (datetime('now')),
    finished_at TEXT,
    score INTEGER,
    total INTEGER
);
"""

CHAPTERS = [
    (1, "Technologia",       "Procesy fotograficzne, techniki i metody pracy w fotografii"),
    (2, "Maszynoznawstwo",   "Aparaty fotograficzne, obiektywy, osprzęt i urządzenia"),
    (3, "Materiałoznawstwo", "Materiały światłoczułe, odczynniki chemiczne i nośniki"),
]

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Buduje bazę danych fotograf.db z plików .txt")
    parser.add_argument("--db", default=None, help="Ścieżka do pliku .db (domyślnie: szukaj fotograf.db)")
    args = parser.parse_args()

    print(f"\n{BLD}📷 Fotograf Czeladnik — Builder bazy danych{RST}\n")

    # Znajdź pliki .txt
    script_dir = Path(__file__).parent
    search_dirs = [script_dir, script_dir.parent, Path(".")]

    file_map = {
        1: ["technologia.txt"],
        2: ["maszynoznawstwo.txt", "maszynoznastwo.txt"],
        3: ["materialoznawstwo.txt", "materiałoznawstwo.txt", "materialoznwstwo.txt"],
    }

    found_files = {}
    for chapter_id, candidates in file_map.items():
        for d in search_dirs:
            for name in candidates:
                p = d / name
                if p.exists():
                    found_files[chapter_id] = p
                    break
            if chapter_id in found_files:
                break

    if not found_files:
        err("Nie znaleziono żadnego pliku .txt!")
        print("\n  Upewnij się, że pliki są w tym samym katalogu co skrypt:")
        print("    technologia.txt")
        print("    maszynoznawstwo.txt  (lub maszynoznastwo.txt)")
        print("    materialoznawstwo.txt  (lub materialoznwstwo.txt)")
        sys.exit(1)

    for cid, p in found_files.items():
        name = next(c[1] for c in CHAPTERS if c[0] == cid)
        ok(f"Znaleziono [{name}]: {p}")

    missing = set(range(1, 4)) - set(found_files.keys())
    for cid in missing:
        name = next(c[1] for c in CHAPTERS if c[0] == cid)
        warn(f"Brak pliku dla działu [{name}] — pomijam")

    # Znajdź / utwórz bazę danych
    if args.db:
        db_path = Path(args.db)
    else:
        candidates = [
            script_dir / "fotograf.db",
            script_dir.parent / "backend" / "fotograf.db",
            Path("fotograf.db"),
        ]
        db_path = next((p for p in candidates if p.exists()), candidates[0])

    print(f"\n  Baza danych: {db_path}\n")

    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)

    # Wstaw działy
    for cid, name, desc in CHAPTERS:
        conn.execute(
            "INSERT OR IGNORE INTO chapters (id, name, description) VALUES (?,?,?)",
            (cid, name, desc)
        )
    conn.commit()

    # Przetwórz każdy plik
    total_inserted = 0
    total_skipped = 0

    for chapter_id, filepath in sorted(found_files.items()):
        chapter_name = next(c[1] for c in CHAPTERS if c[0] == chapter_id)
        print(f"  {BLD}[{chapter_name}]{RST} ← {filepath.name}")

        questions, skipped = parse_file(filepath, chapter_id, chapter_name)

        # Pokaż ostrzeżenia per pytanie
        for q in questions:
            for issue in q["issues"]:
                warn(f"  {q['text'][:50]}... → {issue}")

        # Wstaw do bazy
        inserted = insert_questions(conn, questions)
        conn.commit()

        ok(f"  Wstawiono {inserted} pytań ({inserted * 2} rekordów: closed + open)")
        if skipped:
            for s in skipped:
                warn(f"  Pominięto: {s}...")
            warn(f"  Łącznie pominięto: {len(skipped)} bloków")

        total_inserted += inserted
        total_skipped += len(skipped)
        print()

    # Podsumowanie
    print(f"  {BLD}{'─'*50}{RST}")

    cur = conn.execute("""
        SELECT c.name, q.type, COUNT(*) as cnt
        FROM questions q JOIN chapters c ON c.id = q.chapter_id
        GROUP BY c.id, q.type ORDER BY c.id, q.type
    """)
    rows = cur.fetchall()

    chapter_totals = {}
    for name, qtype, cnt in rows:
        if name not in chapter_totals:
            chapter_totals[name] = {}
        chapter_totals[name][qtype] = cnt

    for name, types in chapter_totals.items():
        closed = types.get("closed", 0)
        open_  = types.get("open", 0)
        print(f"  {GRN}{name:20s}{RST}  {closed} zamkniętych  {open_} otwartych")

    ans_count = conn.execute("SELECT COUNT(*) FROM answers").fetchone()[0]
    open_count = conn.execute("SELECT COUNT(*) FROM open_answers").fetchone()[0]

    print(f"\n  {BLD}Razem pytań wstawionych:{RST} {total_inserted} ({total_inserted*2} rekordów)")
    print(f"  Rekordów w answers:      {ans_count}")
    print(f"  Rekordów w open_answers: {open_count}")
    if total_skipped:
        warn(f"Pominięto łącznie: {total_skipped} bloków z powodu błędów formatu")

    conn.close()
    print(f"\n  {GRN}{BLD}Gotowe!{RST} Baza zapisana w: {db_path}\n")

if __name__ == "__main__":
    main()
