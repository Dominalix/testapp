from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
from datetime import datetime
import random
import math

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# Simple in-memory storage for debugging
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
    # For now, just use memory store to test basic functionality
    print("🔍 DEBUG: Using memory store")
    return memory_store

def save_app_data(data):
    print("🔍 DEBUG: Saving to memory store")
    global memory_store
    memory_store = data
    return True

# ─── DEBUG ENDPOINT ────────────────────────────────────────────────────────────────

@app.route('/api/debug', methods=['GET'])
def debug_info():
    """Debug endpoint to check environment and data"""
    debug_info = {
        "environment": {
            "EDGE_DB": os.environ.get('EDGE_DB', 'NOT_SET'),
            "VERCEL": os.environ.get('VERCEL', 'NOT_SET'),
            "NODE_ENV": os.environ.get('NODE_ENV', 'NOT_SET')
        },
        "data_status": {
            "chapters_count": len(memory_store['chapters']),
            "questions_count": len(memory_store['questions']),
            "user_answers_count": len(memory_store['user_answers']),
            "sessions_count": len(memory_store['sessions'])
        },
        "sample_data": {
            "chapters": memory_store['chapters'][:1]  # First chapter only
        }
    }
    return jsonify(debug_info)

@app.route('/api/add-sample-questions', methods=['POST'])
def add_sample_questions():
    """Add sample questions for testing"""
    try:
        print("🔍 DEBUG: Adding sample questions")
        
        sample_questions = [
            {
                'id': str(uuid.uuid4()),
                'chapter_id': 1,
                'text': 'Jaki jest podstawowy czas naświetlania w fotografii czarno-białej?',
                'type': 'closed',
                'created_at': datetime.now().isoformat(),
                'answers': [
                    {'id': str(uuid.uuid4()), 'text': '1/125 sekundy', 'is_correct': 1, 'sort_order': 0},
                    {'id': str(uuid.uuid4()), 'text': '1/60 sekundy', 'is_correct': 0, 'sort_order': 1},
                    {'id': str(uuid.uuid4()), 'text': '1/30 sekundy', 'is_correct': 0, 'sort_order': 2},
                    {'id': str(uuid.uuid4()), 'text': '1/15 sekundy', 'is_correct': 0, 'sort_order': 3}
                ]
            },
            {
                'id': str(uuid.uuid4()),
                'chapter_id': 1,
                'text': 'Opisz proces wywoływania fotografii czarno-białej.',
                'type': 'open',
                'created_at': datetime.now().isoformat(),
                'sample_answer': 'Wywoływanie to proces chemiczny, w którym naświetlony materiał światłoczuły jest poddawany działaniu wywoływacza, co powoduje zamianę niewidocznego obrazu utajonego w emulsji na obraz widoczny.'
            },
            {
                'id': str(uuid.uuid4()),
                'chapter_id': 2,
                'text': 'Co oznacza skrót "aparat" w terminologii fotograficznej?',
                'type': 'closed',
                'created_at': datetime.now().isoformat(),
                'answers': [
                    {'id': str(uuid.uuid4()), 'text': 'Aparat fotograficzny', 'is_correct': 1, 'sort_order': 0},
                    {'id': str(uuid.uuid4()), 'text': 'Obiektyw fotograficzny', 'is_correct': 0, 'sort_order': 1},
                    {'id': str(uuid.uuid4()), 'text': 'Lampa błyskowa', 'is_correct': 0, 'sort_order': 2},
                    {'id': str(uuid.uuid4()), 'text': 'Statyw', 'is_correct': 0, 'sort_order': 3}
                ]
            },
            {
                'id': str(uuid.uuid4()),
                'chapter_id': 3,
                'text': 'Jakie są podstawowe rodzaje materiałów światłoczułych?',
                'type': 'closed',
                'created_at': datetime.now().isoformat(),
                'answers': [
                    {'id': str(uuid.uuid4()), 'text': 'Srebrowe i bromkowe', 'is_correct': 1, 'sort_order': 0},
                    {'id': str(uuid.uuid4()), 'text': 'Cyjanowe i azotowe', 'is_correct': 0, 'sort_order': 1},
                    {'id': str(uuid.uuid4()), 'text': 'Tlenowe i chlorowe', 'is_correct': 0, 'sort_order': 2},
                    {'id': str(uuid.uuid4()), 'text': 'Kolorowe i czarno-białe', 'is_correct': 0, 'sort_order': 3}
                ]
            }
        ]
        
        memory_store['questions'].extend(sample_questions)
        print(f"🔍 DEBUG: Added {len(sample_questions)} sample questions")
        
        return jsonify({
            'message': f'Added {len(sample_questions)} sample questions',
            'total_questions': len(memory_store['questions'])
        })
    except Exception as e:
        print(f"🔍 DEBUG: Error adding sample questions: {e}")
        return jsonify({'error': str(e)}), 500

# ─── Chapters ────────────────────────────────────────────────────────────────

@app.route('/api/chapters', methods=['GET'])
def get_chapters():
    try:
        print("🔍 DEBUG: /api/chapters called")
        data = get_app_data()
        
        # Add question counts
        chapters_with_counts = []
        for chapter in data['chapters']:
            question_count = len([q for q in data['questions'] if q['chapter_id'] == chapter['id']])
            chapter_copy = chapter.copy()
            chapter_copy['question_count'] = question_count
            chapters_with_counts.append(chapter_copy)
        
        print(f"🔍 DEBUG: Returning {len(chapters_with_counts)} chapters")
        return jsonify(chapters_with_counts)
    except Exception as e:
        print(f"🔍 DEBUG: Error in /api/chapters: {e}")
        return jsonify({'error': str(e)}), 500

# ─── Questions ────────────────────────────────────────────────────────────────

@app.route('/api/questions', methods=['GET'])
def get_questions():
    try:
        print("🔍 DEBUG: /api/questions called")
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
        
        print(f"🔍 DEBUG: Returning {len(result)} questions")
        return jsonify(result)
    except Exception as e:
        print(f"🔍 DEBUG: Error in /api/questions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/questions', methods=['POST'])
def create_question():
    try:
        print("🔍 DEBUG: POST /api/questions called")
        data = get_app_data()
        new_q = request.json
        print(f"🔍 DEBUG: New question data: {new_q}")
        
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
        
        print(f"🔍 DEBUG: Question created: {question['id']}")
        return jsonify(question), 201
    except Exception as e:
        print(f"🔍 DEBUG: Error in POST /api/questions: {e}")
        return jsonify({'error': str(e)}), 500

# ─── Stats ───────────────────────────────────────────────────────────────

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        print("🔍 DEBUG: /api/stats called")
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
        
        result = {
            'overall': overall,
            'by_chapter': by_chapter,
            'hardest': [],
            'all_sessions': []
        }
        
        print(f"🔍 DEBUG: Stats computed: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"🔍 DEBUG: Error in /api/stats: {e}")
        return jsonify({'error': str(e)}), 500

# ─── Serve Frontend ───────────────────────────────────────────────────────────

@app.route('/')
def index():
    try:
        print("🔍 DEBUG: / called")
        frontend_paths = [
            '../frontend/public/index.html',
            'frontend/public/index.html',
            '/var/task/frontend/public/index.html'
        ]
        
        for path in frontend_paths:
            if os.path.exists(path.replace('/index.html', '')):
                print(f"🔍 DEBUG: Serving frontend from {path}")
                return send_from_directory(path.replace('/index.html', ''), 'index.html')
        
        print("🔍 DEBUG: Frontend not found, returning fallback")
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Fotograf App - Debug</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>Fotograf App - Debug Mode</h1>
            <p>Frontend files not found. API is working.</p>
            <p><a href="/api/chapters">View API Chapters</a></p>
            <p><a href="/api/debug">Debug Info</a></p>
        </body>
        </html>
        '''
    except Exception as e:
        print(f"🔍 DEBUG: Error in /: {e}")
        return f"Error: {str(e)}", 500

@app.route('/admin')
def admin():
    try:
        print("🔍 DEBUG: /admin called")
        frontend_paths = [
            '../frontend/public/admin.html',
            'frontend/public/admin.html',
            '/var/task/frontend/public/admin.html'
        ]
        
        for path in frontend_paths:
            if os.path.exists(path.replace('/admin.html', '')):
                print(f"🔍 DEBUG: Serving admin from {path}")
                return send_from_directory(path.replace('/admin.html', ''), 'admin.html')
        
        print("🔍 DEBUG: Admin page not found")
        return "Admin page not found", 404
    except Exception as e:
        print(f"🔍 DEBUG: Error in /admin: {e}")
        return f"Error: {str(e)}", 500

# Vercel serverless function handler
def handler(environ, start_response):
    return app(environ, start_response)

if __name__ == '__main__':
    print("🔍 DEBUG: Fotograf Czeladnik — DEBUG MODE startuje na http://localhost:5000")
    app.run(debug=True, port=5000, host='0.0.0.0')
