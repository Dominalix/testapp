from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
from datetime import datetime
import random
import math

# Import pytań - na górze żeby Vercel bundlował plik
from seed_data import CHAPTERS, QUESTIONS

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# ─── In-memory storage ───────────────────────────────────────────────────────
# Pytania i rozdziały są statyczne (z seed_data.py)
# Sesje i odpowiedzi użytkownika są efemeryczne (w pamięci lambdy)

_questions = {q['id']: q for q in QUESTIONS}
_chapters  = {c['id']: c for c in CHAPTERS}
_sessions  = {}   # session_id -> session dict
_user_ans  = []   # lista odpowiedzi użytkownika

# ─── Debug ───────────────────────────────────────────────────────────────────

@app.route('/api/debug', methods=['GET'])
def debug_info():
    return jsonify({
        'chapters': len(_chapters),
        'questions': len(_questions),
        'sessions': len(_sessions),
        'user_answers': len(_user_ans),
        'source': 'seed_data.py (in-memory)',
        'VERCEL': os.environ.get('VERCEL', 'nie'),
    })

# ─── Chapters ────────────────────────────────────────────────────────────────

@app.route('/api/chapters', methods=['GET'])
def get_chapters():
    result = []
    for c in CHAPTERS:
        cc = dict(c)
        cc['question_count'] = sum(1 for q in _questions.values() if q['chapter_id'] == c['id'])
        result.append(cc)
    return jsonify(result)

# ─── Questions ───────────────────────────────────────────────────────────────

@app.route('/api/questions', methods=['GET'])
def get_questions():
    chapter_id = request.args.get('chapter_id')
    qs = list(_questions.values())
    if chapter_id:
        qs = [q for q in qs if str(q['chapter_id']) == str(chapter_id)]

    result = []
    for q in qs:
        qc = dict(q)
        ans = [ua for ua in _user_ans if ua['question_id'] == q['id']]
        qc['stats'] = {'total': len(ans), 'correct': sum(1 for a in ans if a.get('is_correct') == 1)}
        result.append(qc)
    return jsonify(result)

@app.route('/api/questions', methods=['POST'])
def create_question():
    data = request.json
    qid = str(uuid.uuid4())
    q = {
        'id': qid,
        'chapter_id': data['chapter_id'],
        'text': data['text'],
        'type': data['type'],
        'created_at': datetime.now().isoformat(),
    }
    if data['type'] == 'closed':
        q['answers'] = [
            {'id': str(uuid.uuid4()), 'text': a['text'],
             'is_correct': 1 if a.get('is_correct') else 0, 'sort_order': i}
            for i, a in enumerate(data.get('answers', []))
        ]
    else:
        q['sample_answer'] = data.get('sample_answer', '')
    _questions[qid] = q
    return jsonify(q), 201

@app.route('/api/questions/<qid>', methods=['PUT'])
def update_question(qid):
    if qid not in _questions:
        return jsonify({'error': 'not found'}), 404
    data = request.json
    q = _questions[qid]
    q.update({'chapter_id': data['chapter_id'], 'text': data['text'], 'type': data['type']})
    if data['type'] == 'closed':
        q['answers'] = [
            {'id': str(uuid.uuid4()), 'text': a['text'],
             'is_correct': 1 if a.get('is_correct') else 0, 'sort_order': i}
            for i, a in enumerate(data.get('answers', []))
        ]
    else:
        q['sample_answer'] = data.get('sample_answer', '')
    return jsonify({'ok': True})

@app.route('/api/questions/<qid>', methods=['DELETE'])
def delete_question(qid):
    _questions.pop(qid, None)
    return jsonify({'ok': True})

@app.route('/api/question/<qid>', methods=['GET'])
def get_question_by_id(qid):
    q = _questions.get(qid)
    if not q:
        return jsonify({'error': 'not found'}), 404
    qc = dict(q)
    ans = [ua for ua in _user_ans if ua['question_id'] == qid]
    qc['stats'] = {'total': len(ans), 'correct': sum(1 for a in ans if a.get('is_correct') == 1)}
    return jsonify(qc)

# ─── Test / Sessions ─────────────────────────────────────────────────────────

def _weight(q):
    ans = [ua for ua in _user_ans if ua['question_id'] == q['id']]
    total = len(ans)
    if total == 0:
        return 3.0
    correct = sum(1 for a in ans if a.get('is_correct') == 1)
    return 1.0 + (1.0 - correct / total) * 2.0

def _weighted_sample(pool, n):
    if len(pool) <= n:
        return pool[:]
    weights = [_weight(q) for q in pool]
    total_w = sum(weights)
    probs = [w / total_w for w in weights]
    chosen, chosen_ids = [], set()
    attempts = 0
    while len(chosen) < n and attempts < 1000:
        attempts += 1
        r, cumulative = random.random(), 0
        for i, p in enumerate(probs):
            cumulative += p
            if r <= cumulative:
                if pool[i]['id'] not in chosen_ids:
                    chosen.append(pool[i])
                    chosen_ids.add(pool[i]['id'])
                break
    remaining = [q for q in pool if q['id'] not in chosen_ids]
    random.shuffle(remaining)
    chosen.extend(remaining[:n - len(chosen)])
    return chosen

@app.route('/api/test/generate', methods=['POST'])
def generate_test():
    data = request.json
    chapter_id = data.get('chapter_id')
    question_count = data.get('question_count', 15)

    qs = list(_questions.values())
    if chapter_id:
        qs = [q for q in qs if str(q['chapter_id']) == str(chapter_id)]

    closed_qs = [q for q in qs if q['type'] == 'closed']
    open_qs   = [q for q in qs if q['type'] == 'open']

    open_count   = math.ceil(question_count / 6)
    closed_count = question_count - open_count
    if closed_count == 0 and question_count > 0:
        closed_count, open_count = 1, min(open_count, question_count - 1)

    selected = _weighted_sample(closed_qs, closed_count) + _weighted_sample(open_qs, open_count)
    random.shuffle(selected)

    result = []
    for q in selected:
        qc = dict(q)
        if qc['type'] == 'closed':
            answers = list(qc.get('answers', []))
            random.shuffle(answers)
            qc['answers'] = answers
        result.append(qc)

    sid = str(uuid.uuid4())
    _sessions[sid] = {
        'id': sid, 'chapter_id': chapter_id,
        'started_at': datetime.now().isoformat(),
        'finished_at': None, 'score': None, 'total': len(result)
    }
    return jsonify({'session_id': sid, 'questions': result})

@app.route('/api/test/answer', methods=['POST'])
def record_answer():
    data = request.json
    _user_ans.append({
        'id': str(uuid.uuid4()),
        'question_id': data['question_id'],
        'session_id': data.get('session_id'),
        'answer_id': data.get('answer_id'),
        'open_text': data.get('open_text'),
        'is_correct': data.get('is_correct'),
        'answered_at': datetime.now().isoformat()
    })
    return jsonify({'ok': True})

@app.route('/api/test/finish', methods=['POST'])
def finish_test():
    data = request.json
    sid = data.get('session_id')
    if sid in _sessions:
        _sessions[sid].update({
            'finished_at': datetime.now().isoformat(),
            'score': data.get('score', 0),
            'total': data.get('total', 0)
        })
    return jsonify({'ok': True})

# ─── Stats ───────────────────────────────────────────────────────────────────

@app.route('/api/stats', methods=['GET'])
def get_stats():
    total_answers  = len(_user_ans)
    total_correct  = sum(1 for a in _user_ans if a.get('is_correct') == 1)
    total_sessions = sum(1 for s in _sessions.values() if s.get('finished_at'))

    by_chapter = []
    for c in CHAPTERS:
        c_qs  = [q for q in _questions.values() if q['chapter_id'] == c['id']]
        c_qids = {q['id'] for q in c_qs}
        c_ans  = [a for a in _user_ans if a['question_id'] in c_qids]
        c_sess = sum(1 for s in _sessions.values() if s.get('chapter_id') == c['id'] and s.get('finished_at'))
        by_chapter.append({
            'name': c['name'], 'id': c['id'],
            'test_count': c_sess,
            'answer_count': len(c_ans),
            'correct_count': sum(1 for a in c_ans if a.get('is_correct') == 1)
        })

    # Hardest questions
    q_stats = {}
    for ua in _user_ans:
        qid = ua['question_id']
        if qid not in q_stats:
            q_stats[qid] = {'total': 0, 'correct': 0}
        q_stats[qid]['total'] += 1
        if ua.get('is_correct') == 1:
            q_stats[qid]['correct'] += 1
    hardest = []
    for qid, st in q_stats.items():
        if st['total'] >= 2 and qid in _questions:
            q = _questions[qid]
            c = _chapters.get(q['chapter_id'], {})
            hardest.append({
                'id': qid, 'text': q['text'], 'type': q['type'],
                'chapter_id': q['chapter_id'], 'chapter_name': c.get('name', ''),
                'attempts': st['total'], 'correct': st['correct'],
                'rate': st['correct'] / st['total']
            })
    hardest.sort(key=lambda x: x['rate'])

    all_sessions = []
    for s in _sessions.values():
        if s.get('finished_at'):
            sc = dict(s)
            sc['chapter_name'] = _chapters.get(s.get('chapter_id'), {}).get('name', '')
            all_sessions.append(sc)
    all_sessions.sort(key=lambda x: x.get('finished_at', ''), reverse=True)

    return jsonify({
        'overall': {'total_answers': total_answers, 'total_correct': total_correct, 'total_sessions': total_sessions},
        'by_chapter': by_chapter,
        'hardest': hardest[:5],
        'all_sessions': all_sessions
    })

@app.route('/api/session/<sid>/details', methods=['GET'])
def session_details(sid):
    s = _sessions.get(sid)
    if not s:
        return jsonify({'error': 'not found'}), 404
    sc = dict(s)
    sc['chapter_name'] = _chapters.get(s.get('chapter_id'), {}).get('name', '')
    ans = [ua for ua in _user_ans if ua['session_id'] == sid]
    formatted = []
    for ua in ans:
        q = _questions.get(ua['question_id'])
        if q:
            given = ''
            correct = ''
            if ua.get('answer_id') and q['type'] == 'closed':
                a = next((a for a in q.get('answers', []) if a['id'] == ua['answer_id']), None)
                if a:
                    given = a['text']
                correct = next((a['text'] for a in q.get('answers', []) if a.get('is_correct') == 1), '')
            elif ua.get('open_text'):
                given = ua['open_text']
            formatted.append({
                'id': ua['id'], 'question_id': ua['question_id'],
                'question_text': q['text'], 'type': q['type'],
                'given_answer': given, 'correct_answer': correct,
                'is_correct': ua.get('is_correct'), 'answered_at': ua['answered_at']
            })
    return jsonify({'session': sc, 'answers': formatted})

@app.route('/api/question/<qid>/history', methods=['GET'])
def question_history(qid):
    q = _questions.get(qid)
    if not q:
        return jsonify([])
    history = []
    for ua in sorted([a for a in _user_ans if a['question_id'] == qid],
                     key=lambda x: x.get('answered_at', ''), reverse=True)[:20]:
        given = ''
        if ua.get('answer_id') and q['type'] == 'closed':
            a = next((a for a in q.get('answers', []) if a['id'] == ua['answer_id']), None)
            if a:
                given = a['text']
        elif ua.get('open_text'):
            given = ua['open_text']
        history.append({'id': ua['id'], 'given_answer': given,
                        'is_correct': ua.get('is_correct'), 'answered_at': ua['answered_at']})
    return jsonify(history)

@app.route('/api/reset', methods=['POST'])
def reset_progress():
    if request.json.get('secret') != 'RESETASTER2137':
        return jsonify({'error': 'forbidden'}), 403
    _user_ans.clear()
    _sessions.clear()
    return jsonify({'ok': True})

# ─── Frontend ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    for base in ['../frontend/public', 'frontend/public', '/var/task/frontend/public']:
        if os.path.exists(base):
            return send_from_directory(base, 'index.html')
    return '<h1>API działa</h1><p><a href="/api/chapters">/api/chapters</a></p>'

@app.route('/admin')
def admin():
    for base in ['../frontend/public', 'frontend/public', '/var/task/frontend/public']:
        if os.path.exists(base):
            return send_from_directory(base, 'admin.html')
    return 'Admin not found', 404

def handler(environ, start_response):
    return app(environ, start_response)

if __name__ == '__main__':
    print(f'Fotograf — {len(QUESTIONS)} pytań załadowanych')
    app.run(debug=True, port=5000, host='0.0.0.0')
