// Main JavaScript for AI Interview System

// Interview state management
const InterviewState = {
    currentInterviewId: null,
    currentQuestionNum: 1,
    nextQuestion: null,
    nextQuestionNum: null
};

// Start Interview
document.getElementById('interview-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const position = document.getElementById('position').value;
    const level = document.getElementById('level').value;
    
    try {
        const response = await fetch('/start_interview', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ position, level })
        });
        
        const data = await response.json();
        
        if (data.success) {
            InterviewState.currentInterviewId = data.interview_id;
            InterviewState.currentQuestionNum = 1;
            
            // Hide start section, show interview section
            document.getElementById('start-section').style.display = 'none';
            document.getElementById('interview-section').style.display = 'block';
            
            // Display first question
            document.getElementById('question-num').textContent = '1';
            document.getElementById('question-text').textContent = data.question;
        } else {
            alert('면접 시작에 실패했습니다: ' + data.error);
        }
    } catch (error) {
        alert('오류가 발생했습니다: ' + error.message);
    }
});

// Submit Answer
document.getElementById('submit-answer').addEventListener('click', async () => {
    const answer = document.getElementById('answer').value.trim();
    
    if (!answer) {
        alert('답변을 입력해주세요.');
        return;
    }
    
    // Show loading
    document.getElementById('submit-answer').disabled = true;
    document.getElementById('loading').style.display = 'block';
    document.getElementById('feedback-section').style.display = 'none';
    
    try {
        const response = await fetch('/submit_answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ answer })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Hide loading
            document.getElementById('loading').style.display = 'none';
            
            // Show feedback
            document.getElementById('feedback-text').textContent = data.feedback;
            document.getElementById('feedback-section').style.display = 'block';
            
            if (data.completed) {
                // Interview completed
                document.getElementById('next-question').style.display = 'none';
                document.getElementById('view-results').style.display = 'inline-block';
            } else {
                // Store next question
                InterviewState.nextQuestion = data.next_question;
                InterviewState.nextQuestionNum = data.question_number;
                document.getElementById('next-question').style.display = 'inline-block';
                document.getElementById('view-results').style.display = 'none';
            }
        } else {
            alert('답변 제출에 실패했습니다: ' + data.error);
            document.getElementById('loading').style.display = 'none';
            document.getElementById('submit-answer').disabled = false;
        }
    } catch (error) {
        alert('오류가 발생했습니다: ' + error.message);
        document.getElementById('loading').style.display = 'none';
        document.getElementById('submit-answer').disabled = false;
    }
});

// Next Question
document.getElementById('next-question').addEventListener('click', () => {
    // Clear previous answer
    document.getElementById('answer').value = '';
    
    // Update question
    document.getElementById('question-num').textContent = InterviewState.nextQuestionNum;
    document.getElementById('question-text').textContent = InterviewState.nextQuestion;
    
    // Hide feedback, enable submit
    document.getElementById('feedback-section').style.display = 'none';
    document.getElementById('submit-answer').disabled = false;
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// View Results
document.getElementById('view-results').addEventListener('click', () => {
    window.location.href = '/results';
});
