from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
from datetime import datetime
import random
import math
import json

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# Simple in-memory storage as fallback
# This will work for basic functionality without Edge Config
memory_store = {
    "chapters": [
        {
            "id": 1,
            "name": "Technologia",
            "description": "Procesy fotograficzne, techniki i metody pracy w fotografii"
        },
        {
            "id": 2,
            "name": "Maszynoznawstwo", 
            "description": "Aparaty fotograficzne, obiektywy, osprzęt i urządzenia"
        },
        {
            "id": 3,
            "name": "Materiałoznawstwo",
            "description": "Materiały światłoczułe, odczynniki chemiczne i nośniki"
        }
    ],
    "questions": [],
    "user_answers": [],
    "sessions": []
}

def get_app_data():
    # Try Edge Config first, fallback to memory
    try:
        edge_config_id = os.environ.get('EDGE_CONFIG_ID')
        if edge_config_id:
            # Try to use Edge Config if available
            import requests
            headers = {}
            edge_config_token = os.environ.get('EDGE_CONFIG_TOKEN')
            if edge_config_token:
                headers['Authorization'] = f'Bearer {edge_config_token}'
            
            url = f'https://api.vercel.com/v1/edge-config/{edge_config_id}/item/app_data'
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        print(f"Edge Config not available, using memory store: {e}")
    
    # Fallback to memory store
    return memory_store

def save_app_data(data):
    try:
        edge_config_id = os.environ.get('EDGE_CONFIG_ID')
        if edge_config_id:
            # Try to save to Edge Config
            import requests
            headers = {'Content-Type': 'application/json'}
            edge_config_token = os.environ.get('EDGE_CONFIG_TOKEN')
            if edge_config_token:
                headers['Authorization'] = f'Bearer {edge_config_token}'
            
            url = f'https://api.vercel.com/v1/edge-config/{edge_config_id}/item'
            response = requests.patch(url, headers=headers, json={'key': 'app_data', 'value': data})
            if response.status_code == 200:
                return True
    except Exception as e:
        print(f"Edge Config save failed, using memory store: {e}")
    
    # Fallback to memory store
    global memory_store
    memory_store = data
    return True

# ─── Chapters ────────────────────────────────────────────────────────────────

@app.route('/api/chapters', methods=['GET'])
def get_chapters():
    try:
        data = get_app_data()
        
        # Add question counts
        chapters_with_counts = []
        for chapter in data['chapters']:
            question_count = len([q for q in data['questions'] if q['chapter_id'] == chapter['id']])
            chapter_copy = chapter.copy()
            chapter_copy['question_count'] = question_count
            chapters_with_counts.append(chapter_copy)
        
        return jsonify(chapters_with_counts)
    except Exception as e:
        print(f"Error in /api/chapters: {e}")
        return jsonify({'error': str(e)}), 500

# ─── Questions ────────────────────────────────────────────────────────────────

@app.route('/api/questions', methods=['GET'])
def get_questions():
    try:
        data = get_app_data()
        chapter_id = request.args.get('chapter_id')
        
        questions = data['questions']
        if chapter_id:
            questions = [q for q in questions if str(q['chapter_id']) == str(chapter_id)]
        
        # Add stats and answers
        result = []
        for q in questions:
            q_copy = q.copy()
            
            # Add answers for closed questions
            if q_copy['type'] == 'closed':
                q_copy['answers'] = q_copy.get('answers', [])
            else:
                q_copy['sample_answer'] = q_copy.get('sample_answer', '')
            
            # Calculate stats
            question_answers = [ua for ua in data['user_answers'] if ua['question_id'] == q_copy['id']]
            total_answers = len(question_answers)
            correct_answers = len([ua for ua in question_answers if ua.get('is_correct') == 1])
            
            q_copy['stats'] = {
                'total': total_answers,
                'correct': correct_answers
            }
            
            result.append(q_copy)
        
        return jsonify(result)
    except Exception as e:
        print(f"Error in /api/questions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/questions', methods=['POST'])
def create_question():
    try:
        data = get_app_data()
        new_q = request.json
        
        question = {
            'id': str(uuid.uuid4()),
            'chapter_id': new_q['chapter_id'],
            'text': new_q['text'],
            'type': new_q['type'],
            'created_at': datetime.now().isoformat()
        }
        
        if new_q['type'] == 'closed':
            question['answers'] = []
            for i, ans in enumerate(new_q.get('answers', [])):
                question['answers'].append({
                    'id': str(uuid.uuid4()),
                    'text': ans['text'],
                    'is_correct': 1 if ans.get('is_correct') else 0,
                    'sort_order': i
                })
        elif new_q['type'] == 'open':
            question['sample_answer'] = new_q.get('sample_answer', '')
        
        data['questions'].append(question)
        save_app_data(data)
        
        return jsonify(question), 201
    except Exception as e:
        print(f"Error in POST /api/questions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/questions/<qid>', methods=['PUT'])
def update_question(qid):
    try:
        data = get_app_data()
        update_data = request.json
        
        # Find and update question
        for i, q in enumerate(data['questions']):
            if q['id'] == qid:
                data['questions'][i] = {
                    'id': qid,
                    'chapter_id': update_data['chapter_id'],
                    'text': update_data['text'],
                    'type': update_data['type'],
                    'created_at': q.get('created_at', datetime.now().isoformat())
                }
                
                if update_data['type'] == 'closed':
                    answers = []
                    for i, ans in enumerate(update_data.get('answers', [])):
                        answers.append({
                            'id': str(uuid.uuid4()),
                            'text': ans['text'],
                            'is_correct': 1 if ans.get('is_correct') else 0,
                            'sort_order': i
                        })
                    data['questions'][i]['answers'] = answers
                elif update_data['type'] == 'open':
                    data['questions'][i]['sample_answer'] = update_data.get('sample_answer', '')
                
                break
        
        save_app_data(data)
        return jsonify({'ok': True})
    except Exception as e:
        print(f"Error in PUT /api/questions/{qid}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/questions/<qid>', methods=['DELETE'])
def delete_question(qid):
    try:
        data = get_app_data()
        
        # Remove question
        data['questions'] = [q for q in data['questions'] if q['id'] != qid]
        
        # Remove related user answers
        data['user_answers'] = [ua for ua in data['user_answers'] if ua['question_id'] != qid]
        
        save_app_data(data)
        return jsonify({'ok': True})
    except Exception as e:
        print(f"Error in DELETE /api/questions/{qid}: {e}")
        return jsonify({'error': str(e)}), 500

# ─── Tests / Sessions ─────────────────────────────────────────────────────────

@app.route('/api/test/generate', methods=['POST'])
def generate_test():
    try:
        data = get_app_data()
        request_data = request.json
        chapter_id = request_data.get('chapter_id')
        question_count = request_data.get('question_count', 15)
        
        # Filter questions
        questions = data['questions']
        if chapter_id:
            questions = [q for q in questions if str(q['chapter_id']) == str(chapter_id)]
        
        # Separate by type
        closed_qs = [q for q in questions if q['type'] == 'closed']
        open_qs = [q for q in questions if q['type'] == 'open']
        
        def weight(q):
            question_answers = [ua for ua in data['user_answers'] if ua['question_id'] == q['id']]
            total = len(question_answers)
            correct = len([ua for ua in question_answers if ua.get('is_correct') == 1])
            
            if total == 0:
                return 3.0
            rate = correct / total if total > 0 else 0
            return 1.0 + (1.0 - rate) * 2.0
        
        def weighted_sample(pool, n):
            if len(pool) <= n:
                return pool[:]
            weights = [weight(q) for q in pool]
            total_w = sum(weights)
            if total_w == 0:
                return random.sample(pool, min(n, len(pool)))
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
        
        # Prepare result with shuffled answers for closed questions
        result = []
        for q in selected:
            q_copy = q.copy()
            if q_copy['type'] == 'closed':
                answers = q_copy.get('answers', []).copy()
                random.shuffle(answers)
                q_copy['answers'] = answers
            else:
                q_copy['sample_answer'] = q_copy.get('sample_answer', '')
            result.append(q_copy)
        
        # Create session
        session = {
            'id': str(uuid.uuid4()),
            'chapter_id': chapter_id,
            'started_at': datetime.now().isoformat(),
            'finished_at': None,
            'score': None,
            'total': len(result)
        }
        
        data['sessions'].append(session)
        save_app_data(data)
        
        return jsonify({'session_id': session['id'], 'questions': result})
    except Exception as e:
        print(f"Error in /api/test/generate: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test/answer', methods=['POST'])
def record_answer():
    try:
        data = get_app_data()
        answer_data = request.json
        
        user_answer = {
            'id': str(uuid.uuid4()),
            'question_id': answer_data['question_id'],
            'session_id': answer_data.get('session_id'),
            'answer_id': answer_data.get('answer_id'),
            'open_text': answer_data.get('open_text'),
            'is_correct': answer_data.get('is_correct'),
            'answered_at': datetime.now().isoformat()
        }
        
        data['user_answers'].append(user_answer)
        save_app_data(data)
        
        return jsonify({'ok': True})
    except Exception as e:
        print(f"Error in /api/test/answer: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test/finish', methods=['POST'])
def finish_test():
    try:
        data = get_app_data()
        finish_data = request.json
        sid = finish_data.get('session_id')
        score = finish_data.get('score', 0)
        total = finish_data.get('total', 0)
        
        # Find and update session
        for session in data['sessions']:
            if session['id'] == sid:
                session['finished_at'] = datetime.now().isoformat()
                session['score'] = score
                session['total'] = total
                break
        
        save_app_data(data)
        return jsonify({'ok': True})
    except Exception as e:
        print(f"Error in /api/test/finish: {e}")
        return jsonify({'error': str(e)}), 500

# ─── Statistics ───────────────────────────────────────────────────────────────

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        data = get_app_data()
        
        # Overall stats
        total_answers = len(data['user_answers'])
        total_correct = len([ua for ua in data['user_answers'] if ua.get('is_correct') == 1])
        total_sessions = len([s for s in data['sessions'] if s.get('finished_at')])
        
        overall = {
            'total_answers': total_answers,
            'total_correct': total_correct,
            'total_sessions': total_sessions
        }
        
        # By chapter stats
        by_chapter = []
        for chapter in data['chapters']:
            chapter_questions = [q for q in data['questions'] if q['chapter_id'] == chapter['id']]
            chapter_sessions = [s for s in data['sessions'] if s['chapter_id'] == chapter['id'] and s.get('finished_at')]
            
            chapter_answers = []
            for q in chapter_questions:
                chapter_answers.extend([ua for ua in data['user_answers'] if ua['question_id'] == q['id']])
            
            correct_count = len([ua for ua in chapter_answers if ua.get('is_correct') == 1])
            
            by_chapter.append({
                'name': chapter['name'],
                'id': chapter['id'],
                'test_count': len(chapter_sessions),
                'answer_count': len(chapter_answers),
                'correct_count': correct_count
            })
        
        # Hardest questions
        question_stats = {}
        for q in data['questions']:
            q_answers = [ua for ua in data['user_answers'] if ua['question_id'] == q['id']]
            if len(q_answers) >= 2:
                correct = len([ua for ua in q_answers if ua.get('is_correct') == 1])
                rate = correct / len(q_answers)
                question_stats[q['id']] = {
                    'question': q,
                    'attempts': len(q_answers),
                    'correct': correct,
                    'rate': rate
                }
        
        hardest = sorted(question_stats.values(), key=lambda x: x['rate'])[:5]
        hardest_formatted = []
        for item in hardest:
            q = item['question']
            chapter = next((c for c in data['chapters'] if c['id'] == q['chapter_id']), None)
            hardest_formatted.append({
                'id': q['id'],
                'text': q['text'],
                'type': q['type'],
                'chapter_id': q['chapter_id'],
                'chapter_name': chapter['name'] if chapter else '',
                'attempts': item['attempts'],
                'correct': item['correct'],
                'rate': item['rate']
            })
        
        # All sessions
        all_sessions = []
        for session in data['sessions']:
            if session.get('finished_at'):
                chapter = next((c for c in data['chapters'] if c['id'] == session['chapter_id']), None)
                session_copy = session.copy()
                session_copy['chapter_name'] = chapter['name'] if chapter else ''
                all_sessions.append(session_copy)
        
        all_sessions.sort(key=lambda x: x.get('finished_at', ''), reverse=True)
        
        return jsonify({
            'overall': overall,
            'by_chapter': by_chapter,
            'hardest': hardest_formatted,
            'all_sessions': all_sessions
        })
    except Exception as e:
        print(f"Error in /api/stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/session/<sid>/details', methods=['GET'])
def session_details(sid):
    try:
        data = get_app_data()
        
        # Get session
        session = next((s for s in data['sessions'] if s['id'] == sid), None)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        chapter = next((c for c in data['chapters'] if c['id'] == session['chapter_id']), None)
        session_copy = session.copy()
        session_copy['chapter_name'] = chapter['name'] if chapter else ''
        
        # Get answers for this session
        session_answers = [ua for ua in data['user_answers'] if ua['session_id'] == sid]
        answers_formatted = []
        
        for ua in session_answers:
            question = next((q for q in data['questions'] if q['id'] == ua['question_id']), None)
            if question:
                given_answer = ''
                correct_answer = ''
                
                if ua.get('answer_id') and question['type'] == 'closed':
                    answer = next((a for a in question.get('answers', []) if a['id'] == ua['answer_id']), None)
                    if answer:
                        given_answer = answer['text']
                    correct_answer = next((a['text'] for a in question.get('answers', []) if a.get('is_correct') == 1), '')
                elif ua.get('open_text'):
                    given_answer = ua['open_text']
                
                answers_formatted.append({
                    'id': ua['id'],
                    'question_id': ua['question_id'],
                    'question_text': question['text'],
                    'type': question['type'],
                    'given_answer': given_answer,
                    'correct_answer': correct_answer,
                    'is_correct': ua.get('is_correct'),
                    'answered_at': ua['answered_at']
                })
        
        answers_formatted.sort(key=lambda x: x.get('answered_at', ''))
        
        return jsonify({
            'session': session_copy,
            'answers': answers_formatted
        })
    except Exception as e:
        print(f"Error in /api/session/{sid}/details: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/question/<qid>/history', methods=['GET'])
def question_history(qid):
    try:
        data = get_app_data()
        question = next((q for q in data['questions'] if q['id'] == qid), None)
        
        if not question:
            return jsonify([]), 404
        
        history = []
        question_answers = [ua for ua in data['user_answers'] if ua['question_id'] == qid]
        
        for ua in sorted(question_answers, key=lambda x: x.get('answered_at', ''), reverse=True)[:20]:
            given_answer = ''
            if ua.get('answer_id') and question['type'] == 'closed':
                answer = next((a for a in question.get('answers', []) if a['id'] == ua['answer_id']), None)
                if answer:
                    given_answer = answer['text']
            elif ua.get('open_text'):
                given_answer = ua['open_text']
            
            history.append({
                'id': ua['id'],
                'question_id': ua['question_id'],
                'given_answer': given_answer,
                'is_correct': ua.get('is_correct'),
                'answered_at': ua['answered_at']
            })
        
        return jsonify(history)
    except Exception as e:
        print(f"Error in /api/question/{qid}/history: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/question/<qid>', methods=['GET'])
def get_question_by_id(qid):
    try:
        data = get_app_data()
        question = next((q for q in data['questions'] if q['id'] == qid), None)
        
        if not question:
            return jsonify({'error': 'Question not found'}), 404
        
        q_copy = question.copy()
        
        if q_copy['type'] == 'closed':
            q_copy['answers'] = q_copy.get('answers', [])
        else:
            q_copy['sample_answer'] = q_copy.get('sample_answer', '')
        
        # Calculate stats
        question_answers = [ua for ua in data['user_answers'] if ua['question_id'] == qid]
        total_answers = len(question_answers)
        correct_answers = len([ua for ua in question_answers if ua.get('is_correct') == 1])
        
        q_copy['stats'] = {
            'total': total_answers,
            'correct': correct_answers
        }
        
        return jsonify(q_copy)
    except Exception as e:
        print(f"Error in /api/question/{qid}: {e}")
        return jsonify({'error': str(e)}), 500

# ─── Reset ────────────────────────────────────────────────────────────────────

@app.route('/api/reset', methods=['POST'])
def reset_progress():
    try:
        secret = request.json.get('secret')
        if secret != 'RESETASTER2137':
            return jsonify({'error': 'forbidden'}), 403
        
        data = get_app_data()
        data['user_answers'] = []
        data['sessions'] = []
        save_app_data(data)
        
        return jsonify({'ok': True})
    except Exception as e:
        print(f"Error in /api/reset: {e}")
        return jsonify({'error': str(e)}), 500

# ─── Serve Frontend ───────────────────────────────────────────────────────────

@app.route('/')
def index():
    try:
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
    except Exception as e:
        print(f"Error in /: {e}")
        return f"Error: {str(e)}", 500

@app.route('/admin')
def admin():
    try:
        frontend_paths = [
            '../frontend/public/admin.html',
            'frontend/public/admin.html',
            '/var/task/frontend/public/admin.html'
        ]
        
        for path in frontend_paths:
            if os.path.exists(path.replace('/admin.html', '')):
                return send_from_directory(path.replace('/admin.html', ''), 'admin.html')
        
        return "Admin page not found", 404
    except Exception as e:
        print(f"Error in /admin: {e}")
        return f"Error: {str(e)}", 500

# Vercel serverless function handler
def handler(environ, start_response):
    return app(environ, start_response)

if __name__ == '__main__':
    print("Fotograf Czeladnik — serwer startuje na http://localhost:5000")
    app.run(debug=False, port=5000, host='0.0.0.0')
