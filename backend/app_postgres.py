from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
from datetime import datetime
import random
import math
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# Database connection for Vercel Postgres
def get_db():
    # Vercel automatically provides these environment variables
    db_url = os.environ.get('POSTGRES_URL')
    if not db_url:
        raise Exception("POSTGRES_URL environment variable not found")
    
    conn = psycopg2.connect(db_url)
    conn.cursor_factory = RealDictCursor
    return conn

def init_db():
    try:
        conn = get_db()
        c = conn.cursor()
        c.executescript('''
            CREATE TABLE IF NOT EXISTS chapters (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY,
                chapter_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('closed', 'open')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
                answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (question_id) REFERENCES questions(id)
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                chapter_id INTEGER,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                finished_at TIMESTAMP,
                score INTEGER,
                total INTEGER
            );

            INSERT INTO chapters (name, description) VALUES
                ('Technologia', 'Procesy fotograficzne, techniki i metody pracy w fotografii'),
                ('Maszynoznawstwo', 'Aparaty fotograficzne, obiektywy, osprzęt i urządzenia'),
                ('Materiałoznawstwo', 'Materiały światłoczułe, odczynniki chemiczne i nośniki')
            ON CONFLICT (name) DO NOTHING;
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database initialization error: {e}")
        raise

# Ensure database is initialized
def ensure_db_initialized():
    try:
        # Check if chapters table has data
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM chapters")
        count = c.fetchone()['count']
        conn.close()
        
        if count == 0:
            init_db()
    except:
        init_db()

# ─── Chapters ────────────────────────────────────────────────────────────────

@app.route('/api/chapters', methods=['GET'])
def get_chapters():
    ensure_db_initialized()
    conn = get_db()
    chapters = conn.execute('''
        SELECT c.*, 
               COUNT(DISTINCT q.id) as question_count
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
    ensure_db_initialized()
    chapter_id = request.args.get('chapter_id')
    conn = get_db()
    if chapter_id:
        questions = conn.execute(
            'SELECT * FROM questions WHERE chapter_id = %s ORDER BY created_at',
            (chapter_id,)
        ).fetchall()
    else:
        questions = conn.execute('SELECT * FROM questions ORDER BY chapter_id, created_at').fetchall()
    
    result = []
    for q in questions:
        qd = dict(q)
        if qd['type'] == 'closed':
            answers = conn.execute(
                'SELECT * FROM answers WHERE question_id = %s ORDER BY sort_order',
                (qd['id'],)
            ).fetchall()
            qd['answers'] = [dict(a) for a in answers]
        else:
            oa = conn.execute(
                'SELECT * FROM open_answers WHERE question_id = %s',
                (qd['id'],)
            ).fetchone()
            qd['sample_answer'] = dict(oa)['sample_answer'] if oa else ''
        
        # Stats
        stats = conn.execute('''
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
            FROM user_answers WHERE question_id = %s
        ''', (qd['id'],)).fetchone()
        qd['stats'] = {'total': stats['total'], 'correct': stats['correct'] or 0}
        
        result.append(qd)
    
    conn.close()
    return jsonify(result)

@app.route('/api/questions', methods=['POST'])
def create_question():
    ensure_db_initialized()
    data = request.json
    qid = str(uuid.uuid4())
    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO questions (id, chapter_id, text, type) VALUES (%s, %s, %s, %s)',
            (qid, data['chapter_id'], data['text'], data['type'])
        )
        if data['type'] == 'closed':
            for i, ans in enumerate(data.get('answers', [])):
                aid = str(uuid.uuid4())
                conn.execute(
                    'INSERT INTO answers (id, question_id, text, is_correct, sort_order) VALUES (%s, %s, %s, %s, %s)',
                    (aid, qid, ans['text'], 1 if ans.get('is_correct') else 0, i)
                )
        elif data['type'] == 'open':
            oid = str(uuid.uuid4())
            conn.execute(
                'INSERT INTO open_answers (id, question_id, sample_answer) VALUES (%s, %s, %s)',
                (oid, qid, data.get('sample_answer', ''))
            )
        conn.commit()
        q = conn.execute('SELECT * FROM questions WHERE id = %s', (qid,)).fetchone()
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
            'UPDATE questions SET text = %s, type = %s, chapter_id = %s WHERE id = %s',
            (data['text'], data['type'], data['chapter_id'], qid)
        )
        if data['type'] == 'closed':
            conn.execute('DELETE FROM answers WHERE question_id = %s', (qid,))
            for i, ans in enumerate(data.get('answers', [])):
                aid = str(uuid.uuid4())
                conn.execute(
                    'INSERT INTO answers (id, question_id, text, is_correct, sort_order) VALUES (%s, %s, %s, %s, %s)',
                    (aid, qid, ans['text'], 1 if ans.get('is_correct') else 0, i)
                )
        elif data['type'] == 'open':
            conn.execute('DELETE FROM open_answers WHERE question_id = %s', (qid,))
            oid = str(uuid.uuid4())
            conn.execute(
                'INSERT INTO open_answers (id, question_id, sample_answer) VALUES (%s, %s, %s)',
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
    conn.execute('DELETE FROM answers WHERE question_id = %s', (qid,))
    conn.execute('DELETE FROM open_answers WHERE question_id = %s', (qid,))
    conn.execute('DELETE FROM user_answers WHERE question_id = %s', (qid,))
    conn.execute('DELETE FROM questions WHERE id = %s', (qid,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

# ─── Tests / Sessions ─────────────────────────────────────────────────────────

@app.route('/api/test/generate', methods=['POST'])
def generate_test():
    data = request.json
    chapter_id = data.get('chapter_id')
    question_count = data.get('question_count', 15)
    conn = get_db()
    
    # Get all questions with their answer history
    if chapter_id:
        questions = conn.execute('''
            SELECT q.*,
                   COUNT(ua.id) as answer_count,
                   SUM(CASE WHEN ua.is_correct = 1 THEN 1 ELSE 0 END) as correct_count
            FROM questions q
            LEFT JOIN user_answers ua ON ua.question_id = q.id
            WHERE q.chapter_id = %s
            GROUP BY q.id
        ''', (chapter_id,)).fetchall()
    else:
        questions = conn.execute('''
            SELECT q.*,
                   COUNT(ua.id) as answer_count,
                   SUM(CASE WHEN ua.is_correct = 1 THEN 1 ELSE 0 END) as correct_count
            FROM questions q
            LEFT JOIN user_answers ua ON ua.question_id = q.id
            GROUP BY q.id
        ''').fetchall()
    
    closed_qs = [dict(q) for q in questions if q['type'] == 'closed']
    open_qs = [dict(q) for q in questions if q['type'] == 'open']
    
    def weight(q):
        total = q['answer_count'] or 0
        correct = q['correct_count'] or 0
        if total == 0:
            return 3.0  # never seen → higher priority
        rate = correct / total
        return 1.0 + (1.0 - rate) * 2.0  # wrong answers → higher weight
    
    def weighted_sample(pool, n):
        if len(pool) <= n:
            return pool[:]
        weights = [weight(q) for q in pool]
        total_w = sum(weights)
        probs = [w / total_w for w in weights]
        chosen = []
        chosen_ids = set()
        attempts = 0
        while len(chosen) < n and attempts < 1000:
            attempts += 1
            r = random.random()
            cumulative = 0
            for i, p in enumerate(probs):
                cumulative += p
                if r <= cumulative:
                    if pool[i]['id'] not in chosen_ids:
                        chosen.append(pool[i])
                        chosen_ids.add(pool[i]['id'])
                    break
        # fill remainder randomly if needed
        remaining = [q for q in pool if q['id'] not in chosen_ids]
        random.shuffle(remaining)
        chosen.extend(remaining[:n - len(chosen)])
        return chosen
    
    # Calculate question distribution (1:5 ratio open:closed)
    open_count = math.ceil(question_count / 6)
    closed_count = question_count - open_count
    
    if closed_count == 0 and question_count > 0:
        closed_count = 1
        open_count = min(open_count, question_count - 1)
    
    selected_closed = weighted_sample(closed_qs, closed_count)
    selected_open = weighted_sample(open_qs, open_count)
    selected = selected_closed + selected_open
    random.shuffle(selected)
    
    # Attach answers
    result = []
    for q in selected:
        if q['type'] == 'closed':
            answers = conn.execute(
                'SELECT * FROM answers WHERE question_id = %s ORDER BY sort_order',
                (q['id'],)
            ).fetchall()
            q['answers'] = [dict(a) for a in answers]
            random.shuffle(q['answers'])
        else:
            oa = conn.execute(
                'SELECT sample_answer FROM open_answers WHERE question_id = %s',
                (q['id'],)
            ).fetchone()
            q['sample_answer'] = oa['sample_answer'] if oa else ''
        result.append(q)
    
    # Create session
    sid = str(uuid.uuid4())
    conn.execute(
        'INSERT INTO sessions (id, chapter_id, total) VALUES (%s, %s, %s)',
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
        'INSERT INTO user_answers (id, question_id, session_id, answer_id, open_text, is_correct) VALUES (%s, %s, %s, %s, %s, %s)',
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
        "UPDATE sessions SET finished_at = CURRENT_TIMESTAMP, score = %s, total = %s WHERE id = %s",
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
               COUNT(DISTINCT s.id) as test_count,
               COUNT(ua.id) as answer_count,
               SUM(CASE WHEN ua.is_correct = 1 THEN 1 ELSE 0 END) as correct_count
        FROM chapters c
        LEFT JOIN questions q ON q.chapter_id = c.id
        LEFT JOIN sessions s ON s.chapter_id = c.id AND s.finished_at IS NOT NULL
        LEFT JOIN user_answers ua ON ua.question_id = q.id
        GROUP BY c.id
        ORDER BY c.id
    ''').fetchall()
    
    hardest = conn.execute('''
        SELECT q.id, q.text, q.type, q.chapter_id, c.name as chapter_name,
               COUNT(ua.id) as attempts,
               SUM(CASE WHEN ua.is_correct = 1 THEN 1 ELSE 0 END) as correct,
               CAST(SUM(CASE WHEN ua.is_correct = 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(ua.id) as rate
        FROM questions q
        JOIN user_answers ua ON ua.question_id = q.id
        JOIN chapters c ON c.id = q.chapter_id
        GROUP BY q.id, c.name
        HAVING COUNT(ua.id) >= 2
        ORDER BY rate ASC
        LIMIT 5
    ''').fetchall()
    
    all_sessions = conn.execute('''
        SELECT s.*, c.name as chapter_name
        FROM sessions s
        LEFT JOIN chapters c ON c.id = s.chapter_id
        WHERE s.finished_at IS NOT NULL
        ORDER BY s.finished_at DESC
    ''').fetchall()
    
    conn.close()
    return jsonify({
        'overall': dict(overall),
        'by_chapter': [dict(r) for r in by_chapter],
        'hardest': [dict(r) for r in hardest],
        'all_sessions': [dict(r) for r in all_sessions]
    })

@app.route('/api/session/<sid>/details', methods=['GET'])
def session_details(sid):
    conn = get_db()
    session = conn.execute('''
        SELECT s.*, c.name as chapter_name
        FROM sessions s
        LEFT JOIN chapters c ON c.id = s.chapter_id
        WHERE s.id = %s
    ''', (sid,)).fetchone()
    
    if not session:
        conn.close()
        return jsonify({'error': 'Session not found'}), 404
    
    answers = conn.execute('''
        SELECT ua.*, q.text as question_text, q.type,
               CASE 
                 WHEN ua.answer_id IS NOT NULL THEN a.text 
                 ELSE ua.open_text 
               END as given_answer,
               CASE 
                 WHEN ua.answer_id IS NOT NULL THEN 
                   (SELECT text FROM answers WHERE id = ua.answer_id AND is_correct = 1)
                 ELSE NULL
               END as correct_answer
        FROM user_answers ua
        JOIN questions q ON q.id = ua.question_id
        LEFT JOIN answers a ON a.id = ua.answer_id
        WHERE ua.session_id = %s
        ORDER BY ua.answered_at
    ''', (sid,)).fetchall()
    
    conn.close()
    return jsonify({
        'session': dict(session),
        'answers': [dict(r) for r in answers]
    })

@app.route('/api/question/<qid>/history', methods=['GET'])
def question_history(qid):
    conn = get_db()
    history = conn.execute('''
        SELECT ua.*, 
               CASE WHEN ua.answer_id IS NOT NULL THEN a.text ELSE ua.open_text END as given_answer
        FROM user_answers ua
        LEFT JOIN answers a ON a.id = ua.answer_id
        WHERE ua.question_id = %s
        ORDER BY ua.answered_at DESC
        LIMIT 20
    ''', (qid,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in history])

@app.route('/api/question/<qid>', methods=['GET'])
def get_question_by_id(qid):
    conn = get_db()
    question = conn.execute('SELECT * FROM questions WHERE id = %s', (qid,)).fetchone()
    
    if not question:
        conn.close()
        return jsonify({'error': 'Question not found'}), 404
    
    qd = dict(question)
    
    if qd['type'] == 'closed':
        answers = conn.execute(
            'SELECT * FROM answers WHERE question_id = %s ORDER BY sort_order',
            (qd['id'],)
        ).fetchall()
        qd['answers'] = [dict(a) for a in answers]
    else:
        oa = conn.execute(
            'SELECT * FROM open_answers WHERE question_id = %s',
            (qd['id'],)
        ).fetchone()
        qd['sample_answer'] = dict(oa)['sample_answer'] if oa else ''
    
    stats = conn.execute('''
        SELECT COUNT(*) as total,
               SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
        FROM user_answers WHERE question_id = %s
    ''', (qd['id'],)).fetchone()
    qd['stats'] = {'total': stats['total'], 'correct': stats['correct'] or 0}
    
    conn.close()
    return jsonify(qd)

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
    frontend_paths = [
        '../frontend/public/index.html',
        'frontend/public/index.html',
        '/var/task/frontend/public/index.html'
    ]
    
    for path in frontend_paths:
        if os.path.exists(path.replace('/index.html', '')):
            return send_from_directory(path.replace('/index.html', ''), 'index.html')
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fotograf App</title>
        <meta charset="utf-8">
    </head>
    <body>
        <h1>Fotograf App</h1>
        <p>Frontend files not found. API is working.</p>
        <p><a href="/api/chapters">View API Chapters</a></p>
    </body>
    </html>
    '''

@app.route('/admin')
def admin():
    frontend_paths = [
        '../frontend/public/admin.html',
        'frontend/public/admin.html',
        '/var/task/frontend/public/admin.html'
    ]
    
    for path in frontend_paths:
        if os.path.exists(path.replace('/admin.html', '')):
            return send_from_directory(path.replace('/admin.html', ''), 'admin.html')
    
    return "Admin page not found", 404

# Vercel serverless function handler
def handler(environ, start_response):
    return app(environ, start_response)

# Initialize database
if os.environ.get('VERCEL'):
    init_db()

if __name__ == '__main__':
    init_db()
    print("Fotograf Czeladnik — serwer startuje na http://localhost:5000")
    app.run(debug=False, port=5000, host='0.0.0.0')
