// Main JavaScript for AI Interview System

// Interview state management
const InterviewState = {
    currentInterviewId: null,
    currentQuestionNum: 1,
    nextQuestion: null,
    nextQuestionNum: null
};

let codeEditor = null; // Global editor instance

// Initialize CodeMirror on load
window.addEventListener('load', () => {
    const editorElement = document.getElementById('code-editor');
    if (editorElement) {
        codeEditor = CodeMirror(editorElement, {
            mode: "python",
            theme: "monokai",
            lineNumbers: true,
            autoCloseBrackets: true,
            indentUnit: 4,
            viewportMargin: Infinity
        });
        
        // Set default value
        codeEditor.setValue("# 여기에 코드를 작성하세요\nprint('Hello, Interview!')");
    }
});

// Tab Switching
window.switchTab = function(tab) {
    const textSection = document.getElementById('text-answer-section');
    const codeSection = document.getElementById('code-answer-section');
    const tabs = document.querySelectorAll('.tab-btn');
    
    if (tab === 'text') {
        textSection.style.display = 'block';
        codeSection.style.display = 'none';
        tabs[0].classList.add('active');
        tabs[1].classList.remove('active');
    } else {
        textSection.style.display = 'none';
        codeSection.style.display = 'block';
        tabs[0].classList.remove('active');
        tabs[1].classList.add('active');
        // Refresh editor to fix rendering issues when hidden
        if (codeEditor) {
            setTimeout(() => codeEditor.refresh(), 10);
        }
    }
};

// Language Selection
const langSelect = document.getElementById('language-select');
if (langSelect) {
    langSelect.addEventListener('change', (e) => {
        const lang = e.target.value;
        if (codeEditor) {
            if (lang === 'python') {
                codeEditor.setOption("mode", "python");
                codeEditor.setValue("# Python Code\n");
            } else if (lang === 'javascript') {
                codeEditor.setOption("mode", "javascript");
                codeEditor.setValue("// JavaScript Code\n");
            }
        }
    });
}

// Run Code
const runBtn = document.getElementById('run-code-btn');
if (runBtn) {
    runBtn.addEventListener('click', async () => {
        if (!codeEditor) return;
        
        const code = codeEditor.getValue();
        const language = document.getElementById('language-select').value;
        const outputElem = document.getElementById('code-output');
        
        outputElem.textContent = "실행 중...";
        runBtn.disabled = true;
        
        try {
            const response = await fetch('/run_code', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code, language })
            });
            
            const data = await response.json();
            
            if (data.run) {
                // Piston API format
                const output = data.run.output;
                outputElem.textContent = output || "(출력이 없습니다)";
            } else if (data.error) {
                outputElem.textContent = "Error: " + data.error;
            } else {
                outputElem.textContent = JSON.stringify(data, null, 2);
            }
        } catch (error) {
            outputElem.textContent = "System Error: " + error.message;
        } finally {
            runBtn.disabled = false;
        }
    });
}

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
    
    // Get code data
    let code = null;
    let language = null;
    let codeOutput = null;
    
    if (codeEditor) {
        // If code tab is active or code has been modified, include it?
        // Let's include if it's not the default empty state or user is on code tab.
        // For simplicity, always send if not empty
        const editorContent = codeEditor.getValue();
        if (editorContent && editorContent.length > 20) { // arbitrary length check
             code = editorContent;
             language = document.getElementById('language-select').value;
             codeOutput = document.getElementById('code-output').textContent;
             if (codeOutput === '실행 결과가 여기에 표시됩니다...') codeOutput = '';
        }
    }

    if (!answer && !code) {
        alert('답변 또는 코드를 입력해주세요.');
        return;
    }
    
    // Show loading
    document.getElementById('submit-answer').disabled = true;
    document.getElementById('loading').style.display = 'block';
    document.getElementById('feedback-section').style.display = 'none';
    
    try {
        const payload = { answer };
        if (code) {
            payload.code = code;
            payload.language = language;
            payload.code_output = codeOutput;
        }

        const response = await fetch('/submit_answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
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
       Clear code editor
    if (codeEditor) {
        codeEditor.setValue(document.getElementById('language-select').value === 'python' ? "# 여기에 코드를 작성하세요" : "// 여기에 코드를 작성하세요");
        document.getElementById('code-output').textContent = '실행 결과가 여기에 표시됩니다...';
    }
    
    // Switch back to text tab by default
    switchTab('text');
    
    //          document.getElementById('view-results').style.display = 'inline-block';
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
