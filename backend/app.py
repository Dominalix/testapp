from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
import uuid
from datetime import datetime

app = Flask(__name__, static_folder='../frontend/public', static_url_path='')

DB_PATH = os.path.join(os.path.dirname(__file__), 'fotograf.db')

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

# ─── Chapters ────────────────────────────────────────────────────────────────

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

# ─── Questions ────────────────────────────────────────────────────────────────

@app.route('/api/questions', methods=['GET'])
def get_questions():
    chapter_id = request.args.get('chapter_id')
    conn = get_db()
    
    print(f"DEBUG: get_questions called with chapter_id={chapter_id}")  # Debug
    
    if chapter_id:
        # Get grouped questions for specific chapter
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
        
        print(f"DEBUG: Found {len(groups)} groups for chapter {chapter_id}")  # Debug
        
        # Also get single questions (without group_id)
        singles = conn.execute('''
            SELECT * FROM questions 
            WHERE chapter_id = ? AND (group_id IS NULL OR group_id = '')
            ORDER BY created_at
        ''', (chapter_id,)).fetchall()
        
        print(f"DEBUG: Found {len(singles)} singles for chapter {chapter_id}")  # Debug
    else:
        # Get all grouped questions
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
        
        print(f"DEBUG: Found {len(groups)} total groups")  # Debug
        
        # Also get all single questions
        singles = conn.execute('''
            SELECT * FROM questions 
            WHERE group_id IS NULL OR group_id = ''
            ORDER BY chapter_id, created_at
        ''').fetchall()
        
        print(f"DEBUG: Found {len(singles)} total singles")  # Debug
    
    result = []
    
    # Process grouped questions
    for group in groups:
        group_data = dict(group)
        question_ids = group_data['question_ids'].split(',')
        
        # Get details for both variants
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
        
        # Add stats for the group
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
        
        # Stats
        stats = conn.execute('''
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
            FROM user_answers WHERE question_id = ?
        ''', (qd['id'],)).fetchone()
        qd['stats'] = {'total': stats['total'], 'correct': stats['correct'] or 0}
        
        result.append(qd)
    
    conn.close()
    return jsonify(result)

@app.route('/api/questions', methods=['POST'])
def create_question():
    data = request.json
    qid = str(uuid.uuid4())
    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO questions (id, chapter_id, text, type) VALUES (?, ?, ?, ?)',
            (qid, data['chapter_id'], data['text'], data['type'])
        )
        if data['type'] == 'closed':
            for i, ans in enumerate(data.get('answers', [])):
                aid = str(uuid.uuid4())
                conn.execute(
                    'INSERT INTO answers (id, question_id, text, is_correct, sort_order) VALUES (?, ?, ?, ?, ?)',
                    (aid, qid, ans['text'], 1 if ans.get('is_correct') else 0, i)
                )
        elif data['type'] == 'open':
            oid = str(uuid.uuid4())
            conn.execute(
                'INSERT INTO open_answers (id, question_id, sample_answer) VALUES (?, ?, ?)',
                (oid, qid, data.get('sample_answer', ''))
            )
        conn.commit()
        q = conn.execute('SELECT * FROM questions WHERE id = ?', (qid,)).fetchone()
        conn.close()
        return jsonify(dict(q)), 201
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': str(e)}), 400

@app.route('/api/questions/<qid>', methods=['PUT'])
def update_question(qid):
    data = request.json
    conn = get_db()
    try:
        conn.execute(
            'UPDATE questions SET text = ?, type = ?, chapter_id = ? WHERE id = ?',
            (data['text'], data['type'], data['chapter_id'], qid)
        )
        if data['type'] == 'closed':
            conn.execute('DELETE FROM answers WHERE question_id = ?', (qid,))
            for i, ans in enumerate(data.get('answers', [])):
                aid = str(uuid.uuid4())
                conn.execute(
                    'INSERT INTO answers (id, question_id, text, is_correct, sort_order) VALUES (?, ?, ?, ?, ?)',
                    (aid, qid, ans['text'], 1 if ans.get('is_correct') else 0, i)
                )
        elif data['type'] == 'open':
            conn.execute('DELETE FROM open_answers WHERE question_id = ?', (qid,))
            oid = str(uuid.uuid4())
            conn.execute(
                'INSERT INTO open_answers (id, question_id, sample_answer) VALUES (?, ?, ?)',
                (oid, qid, data.get('sample_answer', ''))
            )
        conn.commit()
        conn.close()
        return jsonify({'ok': True})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': str(e)}), 400

@app.route('/api/questions/<qid>', methods=['DELETE'])
def delete_question(qid):
    conn = get_db()
    conn.execute('DELETE FROM answers WHERE question_id = ?', (qid,))
    conn.execute('DELETE FROM open_answers WHERE question_id = ?', (qid,))
    conn.execute('DELETE FROM user_answers WHERE question_id = ?', (qid,))
    conn.execute('DELETE FROM questions WHERE id = ?', (qid,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# ─── Tests / Sessions ─────────────────────────────────────────────────────────

@app.route('/api/test/generate', methods=['POST'])
def generate_test():
    data = request.json
    chapter_id = data.get('chapter_id')
    question_count = data.get('question_count', 15)  # Default 15 questions
    conn = get_db()
    
    # If chapter_id is 'all' or null, get questions from all chapters
    if chapter_id == 'all' or chapter_id is None:
        # Get all questions (both variants for grouped questions)
        questions = conn.execute('''
            SELECT q.*,
                   COUNT(ua.id) as answer_count,
                   SUM(CASE WHEN ua.is_correct = 1 THEN 1 ELSE 0 END) as correct_count
            FROM questions q
            LEFT JOIN user_answers ua ON ua.question_id = q.id
            GROUP BY q.id
        ''').fetchall()
    else:
        # Get all questions for specific chapter with their answer history
        questions = conn.execute('''
            SELECT q.*,
                   COUNT(ua.id) as answer_count,
                   SUM(CASE WHEN ua.is_correct = 1 THEN 1 ELSE 0 END) as correct_count
            FROM questions q
            LEFT JOIN user_answers ua ON ua.question_id = q.id
            WHERE q.chapter_id = ?
            GROUP BY q.id
        ''', (chapter_id,)).fetchall()
    
    closed_qs = [dict(q) for q in questions if q['type'] == 'closed']
    open_qs = [dict(q) for q in questions if q['type'] == 'open']
    
    def weight(q):
        total = q['answer_count'] or 0
        correct = q['correct_count'] or 0
        if total == 0:
            return 3.0  # never seen → higher priority
        rate = correct / total
        return 1.0 + (1.0 - rate) * 2.0  # wrong answers → higher weight
    
    import random
    
    def weighted_sample(pool, n):
        if len(pool) <= n:
            return pool[:]
        weights = [weight(q) for q in pool]
        total_w = sum(weights)
        probs = [w / total_w for w in weights]
        chosen = []
        chosen_ids = set()
        chosen_groups = set()  # Track group_ids to avoid duplicates
        attempts = 0
        while len(chosen) < n and attempts < 1000:
            attempts += 1
            r = random.random()
            cumulative = 0
            for i, p in enumerate(probs):
                cumulative += p
                if r <= cumulative:
                    q = pool[i]
                    # Skip if we already chose this question or another from the same group
                    if q['id'] not in chosen_ids and (q['group_id'] is None or q['group_id'] not in chosen_groups):
                        chosen.append(q)
                        chosen_ids.add(q['id'])
                        if q['group_id'] is not None:
                            chosen_groups.add(q['group_id'])
                    break
        # fill remainder randomly if needed
        remaining = [q for q in pool if q['id'] not in chosen_ids and (q['group_id'] is None or q['group_id'] not in chosen_groups)]
        random.shuffle(remaining)
        chosen.extend(remaining[:n - len(chosen)])
        return chosen
    
    # Calculate question counts based on 4:1 ratio (closed:open)
    # For every 5 questions: 4 closed, 1 open
    
    if question_count % 5 == 0:
        # Perfect division
        total_closed = (question_count // 5) * 4
        total_open = question_count // 5
    else:
        # Not divisible by 5 - find closest divisible number
        lower_divisible = (question_count // 5) * 5
        higher_divisible = ((question_count // 5) + 1) * 5
        
        # Choose which is closer
        if question_count - lower_divisible <= higher_divisible - question_count:
            target_total = lower_divisible
        else:
            target_total = higher_divisible
        
        total_closed = (target_total // 5) * 4
        total_open = target_total // 5
        
        # If we need to add extra questions to reach the requested count
        if target_total < question_count:
            extra = question_count - target_total
            total_closed += extra
    
    # Ensure at least 1 closed and 1 open if possible
    if total_closed == 0 and question_count >= 1:
        total_closed = 1
    if total_open == 0 and question_count >= 2:
        total_open = 1
    
    selected_closed = weighted_sample(closed_qs, total_closed)
    selected_open = weighted_sample(open_qs, total_open)
    selected = selected_closed + selected_open
    random.shuffle(selected)
    
    # Attach answers
    result = []
    for q in selected:
        if q['type'] == 'closed':
            answers = conn.execute(
                'SELECT * FROM answers WHERE question_id = ? ORDER BY sort_order',
                (q['id'],)
            ).fetchall()
            q['answers'] = [dict(a) for a in answers]
            # Shuffle answer order
            random.shuffle(q['answers'])
        else:
            oa = conn.execute(
                'SELECT sample_answer FROM open_answers WHERE question_id = ?',
                (q['id'],)
            ).fetchone()
            q['sample_answer'] = oa['sample_answer'] if oa else ''
        result.append(q)
    
    # Create session
    sid = str(uuid.uuid4())
    conn.execute(
        'INSERT INTO sessions (id, chapter_id, total) VALUES (?, ?, ?)',
        (sid, chapter_id, len(result))
    )
    conn.commit()
    conn.close()
    
    return jsonify({'session_id': sid, 'questions': result})

@app.route('/api/test/answer', methods=['POST'])
def record_answer():
    data = request.json
    conn = get_db()
    aid = str(uuid.uuid4())
    conn.execute(
        'INSERT INTO user_answers (id, question_id, session_id, answer_id, open_text, is_correct) VALUES (?, ?, ?, ?, ?, ?)',
        (aid, data['question_id'], data.get('session_id'), data.get('answer_id'), data.get('open_text'), data.get('is_correct'))
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/test/finish', methods=['POST'])
def finish_test():
    data = request.json
    sid = data.get('session_id')
    score = data.get('score', 0)
    total = data.get('total', 0)
    conn = get_db()
    conn.execute(
        "UPDATE sessions SET finished_at = datetime('now'), score = ?, total = ? WHERE id = ?",
        (score, total, sid)
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# ─── Statistics ───────────────────────────────────────────────────────────────

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    
    overall = conn.execute('''
        SELECT COUNT(*) as total_answers,
               SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as total_correct,
               COUNT(DISTINCT session_id) as total_sessions
        FROM user_answers
    ''').fetchone()
    
    by_chapter = conn.execute('''
        SELECT c.name, c.id,
               (
                   COUNT(DISTINCT CASE WHEN q.group_id IS NOT NULL THEN q.group_id ELSE q.id END)
               ) as question_count,
               COUNT(ua.id) as answer_count,
               SUM(CASE WHEN ua.is_correct = 1 THEN 1 ELSE 0 END) as correct_count
        FROM chapters c
        LEFT JOIN questions q ON q.chapter_id = c.id
        LEFT JOIN user_answers ua ON ua.question_id = q.id
        GROUP BY c.id
        ORDER BY c.id
    ''').fetchall()
    
    hardest = conn.execute('''
        SELECT q.text, q.type, q.chapter_id, c.name as chapter_name,
               COUNT(ua.id) as attempts,
               SUM(CASE WHEN ua.is_correct = 1 THEN 1 ELSE 0 END) as correct,
               CAST(SUM(CASE WHEN ua.is_correct = 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(ua.id) as rate
        FROM questions q
        JOIN user_answers ua ON ua.question_id = q.id
        JOIN chapters c ON c.id = q.chapter_id
        GROUP BY q.id
        HAVING attempts >= 2
        ORDER BY rate ASC
        LIMIT 5
    ''').fetchall()
    
    recent_sessions = conn.execute('''
        SELECT s.*, c.name as chapter_name
        FROM sessions s
        LEFT JOIN chapters c ON c.id = s.chapter_id
        WHERE s.finished_at IS NOT NULL
        ORDER BY s.finished_at DESC
        LIMIT 10
    ''').fetchall()
    
    conn.close()
    return jsonify({
        'overall': dict(overall),
        'by_chapter': [dict(r) for r in by_chapter],
        'hardest': [dict(r) for r in hardest],
        'recent_sessions': [dict(r) for r in recent_sessions]
    })

@app.route('/api/question/<qid>/history', methods=['GET'])
def question_history(qid):
    conn = get_db()
    history = conn.execute('''
        SELECT ua.*, 
               CASE WHEN ua.answer_id IS NOT NULL THEN a.text ELSE ua.open_text END as given_answer
        FROM user_answers ua
        LEFT JOIN answers a ON a.id = ua.answer_id
        WHERE ua.question_id = ?
        ORDER BY ua.answered_at DESC
        LIMIT 20
    ''', (qid,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in history])

@app.route('/api/session/<sid>/details', methods=['GET'])
def session_details(sid):
    conn = get_db()
    # Get session info
    session = conn.execute('''
        SELECT s.*, c.name as chapter_name
        FROM sessions s
        LEFT JOIN chapters c ON c.id = s.chapter_id
        WHERE s.id = ?
    ''', (sid,)).fetchone()
    
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    # Get session answers with question details
    answers = conn.execute('''
        SELECT ua.*, q.text as question_text, q.type as question_type,
               CASE WHEN ua.answer_id IS NOT NULL THEN a.text ELSE ua.open_text END as given_answer,
               oa.sample_answer
        FROM user_answers ua
        JOIN questions q ON q.id = ua.question_id
        LEFT JOIN answers a ON a.id = ua.answer_id
        LEFT JOIN open_answers oa ON oa.question_id = q.id
        WHERE ua.session_id = ?
        ORDER BY ua.answered_at
    ''', (sid,)).fetchall()
    
    conn.close()
    return jsonify({
        'session': dict(session),
        'answers': [dict(r) for r in answers]
    })

# ─── Reset ────────────────────────────────────────────────────────────────────

@app.route('/api/reset', methods=['POST'])
def reset_progress():
    secret = request.json.get('secret')
    if secret != 'RESETASTER2137':
        return jsonify({'error': 'forbidden'}), 403
    conn = get_db()
    conn.execute('DELETE FROM user_answers')
    conn.execute('DELETE FROM sessions')
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# ─── Serve Frontend ───────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('../frontend/public', 'index.html')


if __name__ == '__main__':
    init_db()
    print("🎞️  Fotograf Czeladnik — serwer startuje na http://localhost:5000")
    app.run(debug=False, port=5000, host='0.0.0.0')
