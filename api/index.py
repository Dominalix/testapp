import os
import sqlite3
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

# Database setup for Vercel
DB_PATH = os.environ.get('VERCEL') == '1' and '/tmp/fotograf.db' or os.path.join(os.path.dirname(__file__), '../fotograf.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
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
            type TEXT NOT NULL CHECK(type IN ('closed', 'open')),
            group_id TEXT,
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

        INSERT OR IGNORE INTO chapters (name, description) VALUES
            ('Technologia', 'Procesy fotograficzne, techniki i metody pracy w fotografii'),
            ('Maszynoznawstwo', 'Aparaty fotograficzne, obiektywy, osprzęt i urządzenia'),
            ('Materiałoznawstwo', 'Materiały światłoczułe, odczynniki chemiczne i nośniki');
    ''')
    conn.commit()
    conn.close()

# Initialize database
init_db()

@app.route('/')
def index():
    return jsonify({"message": "Flask app working!"})

@app.route('/api/test')
def test():
    return jsonify({"status": "API working!"})

# Chapters endpoint
@app.route('/api/chapters', methods=['GET'])
def get_chapters():
    conn = get_db()
    chapters = conn.execute('''
        SELECT c.*, 
               (
                   COUNT(DISTINCT CASE WHEN q.group_id IS NOT NULL THEN q.group_id ELSE q.id END)
               ) as question_count
        FROM chapters c
        LEFT JOIN questions q ON q.chapter_id = c.id
        GROUP BY c.id
        ORDER BY c.id
    ''').fetchall()
    conn.close()
    return jsonify([dict(r) for r in chapters])

# Questions endpoint
@app.route('/api/questions', methods=['GET'])
def get_questions():
    chapter_id = request.args.get('chapter_id')
    conn = get_db()
    
    if chapter_id:
        groups = conn.execute('''
            SELECT group_id, text, chapter_id,
                   GROUP_CONCAT(type) as types,
                   GROUP_CONCAT(id) as question_ids,
                   COUNT(*) as count
            FROM questions 
            WHERE chapter_id = ? AND group_id IS NOT NULL
            GROUP BY group_id
            ORDER BY created_at
        ''', (chapter_id,)).fetchall()
        
        singles = conn.execute('''
            SELECT * FROM questions 
            WHERE chapter_id = ? AND (group_id IS NULL OR group_id = '')
            ORDER BY created_at
        ''', (chapter_id,)).fetchall()
    else:
        groups = conn.execute('''
            SELECT group_id, text, chapter_id,
                   GROUP_CONCAT(type) as types,
                   GROUP_CONCAT(id) as question_ids,
                   COUNT(*) as count
            FROM questions 
            WHERE group_id IS NOT NULL
            GROUP BY group_id
            ORDER BY chapter_id, created_at
        ''').fetchall()
        
        singles = conn.execute('''
            SELECT * FROM questions 
            WHERE group_id IS NULL OR group_id = ''
            ORDER BY chapter_id, created_at
        ''').fetchall()
    
    result = []
    
    # Process grouped questions
    for group in groups:
        group_data = dict(group)
        question_ids = group_data['question_ids'].split(',')
        
        closed_q = None
        open_q = None
        
        for q_id in question_ids:
            q = conn.execute('SELECT * FROM questions WHERE id = ?', (q_id,)).fetchone()
            if q:
                q_dict = dict(q)
                if q_dict['type'] == 'closed':
                    answers = conn.execute(
                        'SELECT * FROM answers WHERE question_id = ? ORDER BY sort_order',
                        (q_id,)
                    ).fetchall()
                    q_dict['answers'] = [dict(a) for a in answers]
                    closed_q = q_dict
                elif q_dict['type'] == 'open':
                    oa = conn.execute(
                        'SELECT * FROM open_answers WHERE question_id = ?',
                        (q_id,)
                    ).fetchone()
                    q_dict['sample_answer'] = dict(oa)['sample_answer'] if oa else ''
                    open_q = q_dict
        
        stats = conn.execute('''
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
            FROM user_answers WHERE question_id IN ({})
        '''.format(','.join(['?' for _ in question_ids])), question_ids).fetchone()
        
        result.append({
            'id': group_data['group_id'],
            'text': group_data['text'],
            'chapter_id': group_data['chapter_id'],
            'type': 'group',
            'closed': closed_q,
            'open': open_q,
            'stats': {'total': stats['total'], 'correct': stats['correct'] or 0},
            'count': group_data['count']
        })
    
    # Process single questions
    for q in singles:
        qd = dict(q)
        if qd['type'] == 'closed':
            answers = conn.execute(
                'SELECT * FROM answers WHERE question_id = ? ORDER BY sort_order',
                (qd['id'],)
            ).fetchall()
            qd['answers'] = [dict(a) for a in answers]
        else:
            oa = conn.execute(
                'SELECT * FROM open_answers WHERE question_id = ?',
                (qd['id'],)
            ).fetchone()
            qd['sample_answer'] = dict(oa)['sample_answer'] if oa else ''
        
        stats = conn.execute('''
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
            FROM user_answers WHERE question_id = ?
        ''', (qd['id'],)).fetchone()
        qd['stats'] = {'total': stats['total'], 'correct': stats['correct'] or 0}
        
        result.append(qd)
    
    conn.close()
    return jsonify(result)
