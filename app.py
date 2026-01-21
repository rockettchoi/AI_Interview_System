from flask import Flask, render_template, request, jsonify, session
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import uuid
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Store interview data (NOTE: In-memory storage - not for production use!)
# For production, implement proper database persistence (e.g., PostgreSQL, MongoDB)
# and secure session management
interviews = {}

@app.route('/')
def index():
    """Main page - Interview start"""
    return render_template('index.html')

@app.route('/start_interview', methods=['POST'])
def start_interview():
    """Start a new interview session"""
    try:
        data = request.get_json()
        position = data.get('position', 'Software Engineer')
        level = data.get('level', 'Junior')
        
        # Generate secure interview ID using UUID
        interview_id = str(uuid.uuid4())
        session['interview_id'] = interview_id
        
        # Initialize interview data
        interviews[interview_id] = {
            'position': position,
            'level': level,
            'questions': [],
            'answers': [],
            'feedback': [],
            'current_question': 0,
            'started_at': datetime.now().isoformat()
        }
        
        # Generate first question
        question = generate_question(position, level, 1)
        interviews[interview_id]['questions'].append(question)
        
        return jsonify({
            'success': True,
            'interview_id': interview_id,
            'question': question
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    """Submit an answer and get feedback"""
    try:
        data = request.get_json()
        interview_id = session.get('interview_id')
        answer = data.get('answer', '')
        
        if not interview_id or interview_id not in interviews:
            return jsonify({'success': False, 'error': 'Invalid interview session'}), 400
        
        interview = interviews[interview_id]
        current_q = interview['current_question']
        question = interview['questions'][current_q]
        
        # Store answer
        interview['answers'].append(answer)
        
        # Get AI feedback
        feedback = evaluate_answer(question, answer, interview['position'], interview['level'])
        interview['feedback'].append(feedback)
        
        # Move to next question
        interview['current_question'] += 1
        
        # Check if interview should continue (max 5 questions)
        if interview['current_question'] < 5:
            next_question = generate_question(
                interview['position'], 
                interview['level'], 
                interview['current_question'] + 1
            )
            interview['questions'].append(next_question)
            
            return jsonify({
                'success': True,
                'feedback': feedback,
                'next_question': next_question,
                'question_number': interview['current_question'] + 1,
                'completed': False
            })
        else:
            # Interview completed
            return jsonify({
                'success': True,
                'feedback': feedback,
                'completed': True,
                'total_questions': len(interview['questions'])
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/results')
def results():
    """Show interview results"""
    interview_id = session.get('interview_id')
    if not interview_id or interview_id not in interviews:
        return render_template('error.html', message='Interview session not found')
    
    interview = interviews[interview_id]
    return render_template('results.html', interview=interview)

def generate_question(position, level, question_number):
    """Generate interview question using OpenAI"""
    try:
        prompt = f"""You are an expert technical interviewer. Generate a {level} level interview question 
for a {position} position. This is question number {question_number} out of 5.

The question should be:
- Relevant to the position
- Appropriate for the experience level
- Clear and concise
- Technical but fair

Return only the question text, no additional formatting or explanation."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert technical interviewer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        question = response.choices[0].message.content.strip()
        return question
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Error generating question: {type(e).__name__}: {str(e)}")
        # Fallback questions if API fails
        fallback_questions = [
            f"Tell me about your experience with {position} role.",
            f"What are the key skills needed for a {level} {position}?",
            "Describe a challenging project you've worked on.",
            "How do you approach problem-solving in your work?",
            "What are your career goals for the next few years?"
        ]
        return fallback_questions[question_number - 1]

def evaluate_answer(question, answer, position, level):
    """Evaluate answer using OpenAI"""
    try:
        prompt = f"""You are an expert interviewer evaluating a candidate's answer.

Position: {position}
Level: {level}
Question: {question}
Answer: {answer}

Provide constructive feedback on the answer. Include:
1. Strengths of the answer
2. Areas for improvement
3. Overall assessment (Good/Average/Needs Improvement)

Keep the feedback concise and professional (max 150 words)."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert interviewer providing feedback."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=250,
            temperature=0.7
        )
        
        feedback = response.choices[0].message.content.strip()
        return feedback
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Error evaluating answer: {type(e).__name__}: {str(e)}")
        return f"Thank you for your answer. Your response has been recorded."

if __name__ == '__main__':
    # Use debug mode only in development, disable in production
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
