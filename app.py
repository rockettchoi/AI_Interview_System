from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
import uuid
import uvicorn
import requests
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Add Session Middleware
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Templates
templates = Jinja2Templates(directory="templates")

# Initialize OpenAI client
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("Warning: OPENAI_API_KEY not found in environment variables. OpenAI features will fail.")
client = OpenAI(api_key=api_key)

# Store interview data (NOTE: In-memory storage - not for production use!)
interviews = {}

# Pydantic models for request bodies
class StartInterviewRequest(BaseModel):
    position: str = 'Software Engineer'
    level: str = 'Junior'

class RunCodeRequest(BaseModel):
    code: str
    language: str

class SubmitAnswerRequest(BaseModel):
    answer: str
    code: str = None
    language: str = None
    code_output: str = None

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Main page - Interview start"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/start_interview")
def start_interview(request: Request, data: StartInterviewRequest):
    """Start a new interview session"""
    try:
        # Generate secure interview ID using UUID
        interview_id = str(uuid.uuid4())
        request.session['interview_id'] = interview_id
        
        # Initialize interview data
        interviews[interview_id] = {
            'position': data.position,
            'level': data.level,
            'questions': [],
            'answers': [],
            'feedback': [],
            'current_question': 0,
            'started_at': datetime.now().isoformat()
        }
        
        # Generate first question
        question = generate_question(data.position, data.level, 1)
        interviews[interview_id]['questions'].append(question)
        
        return {
            'success': True,
            'interview_id': interview_id,
            'question': question
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={'success': False, 'error': str(e)})

@app.post("/run_code")
def run_code(data: RunCodeRequest):
    """Execute code using Piston API"""
    try:
        # Piston API execution
        piston_lang = data.language
        version = "*"
        if piston_lang == "python": 
            version = "3.10.0"
        elif piston_lang == "javascript":
            version = "18.15.0"

        response = requests.post("https://emkc.org/api/v2/piston/execute", json={
            "language": piston_lang,
            "version": version,
            "files": [{"content": data.code}]
        })
        
        if response.status_code == 200:
            return response.json()
        else:
            return JSONResponse(status_code=response.status_code, content={"error": "Execution failed"})
            
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})

@app.post("/submit_answer")
def submit_answer(request: Request, data: SubmitAnswerRequest):
    """Submit an answer and get feedback"""
    try:
        interview_id = request.session.get('interview_id')
        
        if not interview_id or interview_id not in interviews:
            return JSONResponse(status_code=400, content={'success': False, 'error': 'Invalid interview session'})
        
        interview = interviews[interview_id]
        current_q = interview['current_question']
        question = interview['questions'][current_q]
        
        # Store answer
        interview['answers'].append(data.answer)
        
        # Get AI feedback
        feedback = evaluate_answer(
            question, 
            data.answer, 
            interview['position'], 
            interview['level'],
            data.code,
            data.code_output
        )
        interview['feedback'].append(feedback)
        
        # Move to next question
        interview['current_question'] += 1
        
        # Check if interview should continue (max 5 questions)
        if interview['current_question'] < 5:
            next_question = generate_question(
                interview['position'], 
                interview['level'], 
                interview['current_question'] + 1,
                interview['questions'],
                interview['answers']
            )
            interview['questions'].append(next_question)
            
            return {
                'success': True,
                'feedback': feedback,
                'next_question': next_question,
                'question_number': interview['current_question'] + 1,
                'completed': False
            }
        else:
            # Interview completed
            return {
                'success': True,
                'feedback': feedback,
                'completed': True,
                'total_questions': len(interview['questions'])
            }
    except Exception as e:
        return JSONResponse(status_code=500, content={'success': False, 'error': str(e)})

@app.get("/results", response_class=HTMLResponse)
def results(request: Request):
    """Show interview results"""
    interview_id = request.session.get('interview_id')
    if not interview_id or interview_id not in interviews:
        return templates.TemplateResponse("error.html", {"request": request, "message": "Interview session not found"})
    
    interview = interviews[interview_id]
    return templates.TemplateResponse("results.html", {"request": request, "interview": interview})

def generate_question(position, level, question_number, previous_questions=None, previous_answers=None):
    """Generate interview question using OpenAI"""
    try:
        context = ""
        if previous_questions and previous_answers:
            context = "\n\nPrevious context:\n"
            for q, a in zip(previous_questions, previous_answers):
                context += f"Q: {q}\nA: {a}\n"

        prompt = f"""You are an expert technical interviewer. Generate a {level} level interview question 
for a {position} position. This is question number {question_number} out of 5.{context}

If there is previous context, try to make the new question flow naturally from the previous topic or dig deeper into the candidate's answer if appropriate. Otherwise, switch to a new relevant technical topic.

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
        # Use modulo to prevent IndexError if question_number exceeds fallback list length
        safe_index = (question_number - 1) % len(fallback_questions)
        return fallback_questions[safe_index]

def evaluate_answer(question, answer, position, level, code=None, code_output=None):
    """Evaluate answer using OpenAI"""
    try:
        code_context = ""
        if code:
            code_context = f"""
Candidate also submitted the following code:
```
{code}
```
Code Execution Output:
```
{code_output}
```

Please evaluate the code quality, including:
- Correctness (does it solve the problem if applicable)
- Time and Space Complexity analysis
- Code Style and Pythonic/Idiomatic usage
- Presence and quality of comments
"""

        prompt = f"""You are an expert interviewer evaluating a candidate's answer.

Position: {position}
Level: {level}
Question: {question}
Answer: {answer}
{code_context}

Provide constructive feedback on the answer (and code if provided). Include:
1. Strengths of the answer/code
2. Areas for improvement
3. Overall assessment (Good/Average/Needs Improvement)

Keep the feedback concise and professional (max 20

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
        return "Thank you for your answer. Your response has been recorded."

if __name__ == '__main__':
    # Use reload=True equal to Flask's debug=True
    uvicorn.run("app:app", host='0.0.0.0', port=8000, reload=True)
