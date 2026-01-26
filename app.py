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

# LangChain Imports
from langchain_openai import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain

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

# Initialize LangChain ChatOpenAI
llm = ChatOpenAI(api_key=api_key, model="gpt-3.5-turbo", temperature=0.7)

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
            'started_at': datetime.now().isoformat(),
            'chat_history': ConversationBufferMemory(return_messages=True) # Initialize LangChain memory
        }
        
        # Generate first question
        question = generate_question_langchain(interview_id, data.position, data.level, 1)
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

        # Update Memory with User Answer
        if interview.get('chat_history'):
             # Add the last question asked by AI and the answer given by user to memory
             # We need to retrieve the last question.
             # current_q index points to the question index in 'questions' list.
             # Note that 'questions' list has questions: [Q1, Q2, ...]
             # The user is submitting answer for 'questions[current_q-1] if we incremented? 
             # Wait, logic in start_interview: current_question = 0. Append Q1.
             # So Q1 is at index 0. user submits. current_question is 0.
             last_question = interview['questions'][current_q]
             interview['chat_history'].save_context({"input": last_question}, {"output": data.answer})
        
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
        
        # Check if interview should continue (5 regular questions + 1 coding test)
        if interview['current_question'] <= 5:
            # If we just finished 5th question (index 4), now generate 6th item (index 5) 
            
            is_coding_test = False
            if interview['current_question'] == 5:
                next_question = generate_coding_test(
                    interview['position'], 
                    interview['level']
                )
                is_coding_test = True
            else:
                next_question = generate_question_langchain(
                    interview_id,
                    interview['position'], 
                    interview['level'], 
                    interview['current_question'] + 1'],
                    interview['answers']
                )

            interview['questions'].append(next_question)
            
            return {
                'success': True,
                'feedback': feedback,
                'next_question': next_question,
                'question_number': interview['current_question'] + 1,
                'is_coding_test': is_coding_test,
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
    """Show interview_langchain(interview_id, position, level, question_number):
    """Generate interview question using LangChain with Memory"""
    try:
        current_memory = interviews[interview_id].get('chat_history')
        if not current_memory:
             # Fallback if memory is lost (shouldn't happen with in-memory dict)
             current_memory = ConversationBufferMemory(return_messages=True)

        prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(
                    f"You are an expert technical interviewer for a {level} {position} role. "
                    "Your goal is to assess the candidate's technical skills, problem-solving abilities, and cultural fit. "
                    f"This is question number {question_number} out of 5."
                ),
                # The `variable_name` here depends on what `ConversationBufferMemory` outputs.
                # Default is usually "history" or "chat_history". We will use MessagesPlaceholder.
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template(
                    "Based on the candidate's previous answers (if any), generate the next interview question. "
                    "If the previous answer was interesting or lacked detail, ask a follow-up question. "
                    "Otherwise, move to a new relevant technical topic.\n\n"
                    "The question should be:\n"
                    "- Relevant to the position\n"
                    "- Appropriate for the experience level\n"
                    "- Clear and concise\n"
                    "- Technical but fair\n\n"
                    "Return ONLY the question text."
                )
            ]
        )
        
        conversation = LLMChain(
            llm=llm,
            prompt=prompt,
            verbose=True,
            memory=current_memory
        )
        
        # In LLMChain with memory, we often just pass an empty input if the prompt relies on history + system prompt
        # But we need to trigger it. We can pass a dummy input or structure the prompt to take an input.
        # Let's adjust the prompt to take a "trigger" or just run it.
        # Actually, since we are manually saving context to memory in `submit_answer`, 
        # we can just ask it to "Generate next question".
        
        response = conversation.invokeb({"input": "Generate the next question."})
        # Note: LLMChain.run or invoke might differ by version. invoke returns dict 'text'.
        # Using `predict` is often easier for simple string output.
        
        question = response['text'].strip()
        return question

    except Exception as e:
        print(f"Error generating question with LangChain: {str(e)}")
        # Fallback to old method or hardcoded
        return generate_question(position, level, question_number)

def generate_question(position, level, question_number, previous_questions=None, previous_answers=None):
    """Generate interview question using OpenAI (Legacy/Fallback)ew_id')
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
            model="gpt-4o",
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

def generate_coding_test(position, level):
    """Generate a coding challenge using OpenAI"""
    try:
        prompt = f"""You are an expert technical interviewer. Generate a practical coding challenge 
for a {level} level {position} position.

The challenge should:
1. Be solvable within 10-15 minutes.
2. Require writing a specific function or small script.
3. Test algorithmic thinking or API usage relevant to the role.
4. Include 2-3 specific test cases in the description.

Return ONLY the problem description. Do not include the solution."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert technical interviewer. You create clear, solvable coding challenges."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating coding test: {str(e)}")
        return f"Write a function to reverse a string in Python, but without using the slicing syntax [::-1]. Explain your approach."

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

Keep the feedback concise and professional (max 200 words)."""

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
