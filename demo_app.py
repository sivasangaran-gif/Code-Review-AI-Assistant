from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from openai import OpenAI
import os
import markdown
import subprocess
import sys
import tempfile

app = FastAPI(title="BugHunter AI")

# Configuration
API_KEY = os.getenv("API_KEY", os.getenv("OPENAI_API_KEY", "")) 
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

def run_code_safely(code: str) -> str:
    """Executes the code in a subprocess and captures output/errors."""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w', encoding='utf-8') as tmp:
        tmp.write(code)
        tmp_path = tmp.name
    
    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=3
        )
        output = result.stdout
        error = result.stderr
        
        if error:
            return f" RUNTIME ERROR DETECTED:\n\n{error}"
        return f" EXECUTION SUCCESSFUL:\n\n{output if output else '[No output produced]'}"
    except subprocess.TimeoutExpired:
        return " ERROR: Execution timed out (potential infinite loop). Please check your loops or input() calls."
    except Exception as e:
        return f" SYSTEM ERROR: {str(e)}"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def auto_fix_code(code: str, error_type: str, error_line_num: int) -> str:
    """Attempts smart auto-correction of common Python errors."""
    try:
        code_lines = code.split('\n')
        fixed_lines = code_lines[:]

        if 'SyntaxError' in error_type and error_line_num:
            idx = error_line_num - 1
            if 0 <= idx < len(fixed_lines):
                line = fixed_lines[idx]
                stripped = line.rstrip()
                # Fix missing colon on def/class/if/else/elif/for/while/with/try/except/finally
                if any(stripped.startswith(kw) for kw in ['def ', 'class ', 'if ', 'elif ', 'else', 'for ', 'while ', 'with ', 'try', 'except', 'finally']):
                    if not stripped.endswith(':'):
                        fixed_lines[idx] = stripped + ':'

        elif 'ZeroDivisionError' in error_type:
            # Wrap problematic division in try-except
            new_lines = []
            for l in fixed_lines:
                if '/' in l and not l.strip().startswith('#'):
                    indent = len(l) - len(l.lstrip())
                    pad = ' ' * indent
                    new_lines.append(f"{pad}try:")
                    new_lines.append(f"{pad}    {l.strip()}")
                    new_lines.append(f"{pad}except ZeroDivisionError:")
                    new_lines.append(f"{pad}    print('Error: Cannot divide by zero.')")
                else:
                    new_lines.append(l)
            fixed_lines = new_lines

        elif 'TypeError' in error_type:
            # Add type conversion hint as comment
            if error_line_num:
                idx = error_line_num - 1
                if 0 <= idx < len(fixed_lines):
                    fixed_lines[idx] = fixed_lines[idx] + '  # TODO: Ensure matching types (e.g. int(), str())'

        fixed = '\n'.join(fixed_lines)
        # Only return fix if something changed
        if fixed != code:
            return fixed
        return code
    except Exception:
        return code


def review_code_with_ai(code: str, trace: str, language: str, task_description: str) -> str:
    if API_KEY and API_KEY != "your-api-key-here":
        prompt = f"""You are a Senior Software Engineer and Expert Code Reviewer with strong experience in debugging, optimization, and software security.

Your task is to carefully analyze the given code and produce a professional, structured code review.

Focus on:
1. Syntax Errors - Missing symbols, invalid syntax
2. Performance Issues - Inefficient loops, unnecessary computations, poor patterns
3. Security Vulnerabilities - SQL injection, unsafe string concatenation, improper input handling
4. Logical or Structural Problems - Incorrect logic, bad practices, maintainability issues

Output Format (STRICT):

ISSUES:
- [List each issue found with clear technical keywords]

IMPACT:
- [Explain why these issues matter - performance, security, or correctness impact]

FIX:
- [Provide clear, actionable solutions and corrected code approaches]

CORRECTED CODE:
- [Provide the full fixed code snippet properly wrapped in a markdown code block]

Keep responses concise, specific, and actionable. Focus on real issues only.

Analyze this {language} code.

Task Context: {task_description}"""
        full_input = f"Code:\n{code}\n\nExecution Trace:\n{trace}"
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": full_input}
                ],
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception:
            pass 
    
    if " EXECUTION SUCCESSFUL" in trace:
        output_content = trace.split(" EXECUTION SUCCESSFUL:\n\n")[-1] if " EXECUTION SUCCESSFUL:\n\n" in trace else "[No output produced]"
        return f"""###  Bug Summary
BugHunter AI Local Kernel analyzed your code. No runtime errors or exceptions were caught during execution!

###  Code Evaluation
- **Syntax:** Validated successfully.
- **Execution:** Ran to completion.
- **Output Captured:** Yes.

###  Program Output
```
{output_content}
```

###  Performance
- **Reliability:** 10/10 (Execution verified).
"""
    
    trace_lines = trace.split('\n')
    error_type = "Runtime Error"
    error_line_num = None
    error_line_desc = "an unknown line"

    for line in reversed(trace_lines):
        if "Error:" in line or "Exception:" in line:
            error_type = line.strip()
            break

    for line in reversed(trace_lines):
        if "line " in line and line.strip().startswith('File'):
            parts = line.split(',')
            if len(parts) >= 2:
                error_line_desc = parts[1].strip()
                try:
                    error_line_num = int(parts[1].strip().split()[-1])
                except Exception:
                    pass
            break

    corrected = auto_fix_code(code, error_type, error_line_num)
    corrected_block = f"\nCORRECTED PROGRAM:\n```python\n{corrected}\n```\n" if corrected and corrected != code else ""

    return f"""ISSUES:
- **Major Issue:** `{error_type}` detected at {error_line_desc}.
- **Violation:** Incompatible operations or malformed syntax.

IMPACT:
- **Immediate Crash:** Code execution is blocked until resolved.
- **Reliability Risk:** This will cause the application to fail in production.

FIX:
1. **Trace the Line:** Check the highlighted line in the execution trace below.
2. **Apply Update:** Replace the offending line with the corrected segment provided.
3. **Handle Errors:** Wrap risky logic in `try...except` blocks.
{corrected_block}"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BugHunter AI | Code Analysis</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-main: #0b0f19;
            --bg-sec: #1c2235;
            --bg-btn: #2a3143; 
            --primary: #6366f1;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #334155;
            --success: #10b981;
            --danger: #ef4444;
        }

        * { margin:0; padding:0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-main);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .header {
            display: flex;
            align-items: center;
            padding: 20px 30px;
            gap: 15px;
            font-size: 1.5rem;
            font-weight: 700;
        }
        .header i { color: var(--primary); font-size: 1.8rem; }
        
        .header-action-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 20px 30px;
            font-size: 1.2rem;
            font-weight: 600;
        }
        
        .header-action-bar .left { display: flex; align-items: center; gap: 15px; }

        .container {
            flex: 1;
            padding: 0 30px 40px;
            max-width: 1200px;
            margin: 0 auto;
            width: 100%;
        }

        .hidden { display: none !important; }

        /* Typography & Utils */
        .section-title { font-size: 0.85rem; font-weight: 500; color: var(--text-muted); margin-bottom: 12px; margin-top: 25px; }
        .view-title { font-size: 1.5rem; font-weight: 700; display: flex; align-items: center; gap: 10px; margin-bottom: 20px;}
        .icon-btn { background: none; border: none; color: var(--text-main); cursor: pointer; font-size: 1.2rem; transition: color 0.2s;}
        .icon-btn:hover { color: var(--primary); }
        .icon-btn.danger:hover { color: var(--danger); }

        /* Chips */
        .chip-group { display: flex; flex-wrap: wrap; gap: 10px; }
        .chip { background-color: var(--bg-btn); color: var(--text-muted); padding: 8px 16px; border-radius: 20px; font-size: 0.85rem; cursor: pointer; transition: all 0.2s; user-select: none; }
        .chip.active { background-color: var(--primary); color: white; font-weight: 500; }
        .lang-pill { background-color: var(--primary); color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; display: inline-block; }

        /* Inputs */
        textarea { width: 100%; background-color: var(--bg-sec); color: var(--text-main); border: 1px solid var(--bg-sec); border-radius: 8px; padding: 16px; font-family: 'JetBrains Mono', monospace; font-size: 0.95rem; outline: none; resize: vertical; }
        textarea:focus { border: 1px solid var(--border-color); }
        textarea::placeholder { color: #475569; }
        #codeInput { min-height: 300px; }
        #taskInput { min-height: 80px; }

        /* Buttons */
        .btn-primary { width: 100%; background-color: var(--primary); color: white; border: none; border-radius: 8px; padding: 18px; font-size: 1rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 10px; transition: opacity 0.2s; }
        .btn-primary:hover { opacity: 0.9; }
        
        .btn-hgroup { display: flex; gap: 15px; margin-top: 20px; }
        .btn-hgroup button { flex: 1; padding: 15px; border-radius: 8px; font-size: 0.95rem; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; transition: all 0.2s;}
        .btn-secondary { background-color: transparent; color: var(--text-muted); border: 1px solid var(--border-color); }
        .btn-secondary:hover { background-color: var(--bg-sec); color: white; }

        /* Bottom Nav */
        .bottom-nav { background-color: var(--bg-sec); border-top: 1px solid #141829; display: flex; justify-content: space-around; padding: 15px 0; margin-top: auto; }
        .nav-item { display: flex; align-items: center; gap: 8px; color: var(--text-muted); font-size: 0.9rem; cursor: pointer; }
        .nav-item.active { color: var(--primary); }
        .nav-item i { font-size: 1.1rem; }

        /* Markdown / Result Box */
        .result-box { background: var(--bg-sec); border-radius: 8px; padding: 25px; border: 1px solid var(--border-color); margin-top: 10px;}
        .markdown-body { font-size: 0.95rem; color: #cbd5e1; line-height: 1.6; font-family: 'Inter', sans-serif;}
        .markdown-body h3 { color: var(--primary); margin: 15px 0 10px; font-weight: 600;}
        .markdown-body p { margin-bottom: 10px; }
        .markdown-body ul { margin-left: 20px; margin-bottom: 10px; }
        .markdown-body code { background: rgba(0,0,0,0.3); padding: 2px 5px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;}
        .markdown-body pre { background: #0f111a; padding: 15px; border-radius: 8px; margin: 10px 0; border: 1px solid var(--border-color); overflow-x: auto;}
        .markdown-body pre code { font-weight: 500; }
        
        .code-box { background: var(--bg-sec); border-radius: 8px; padding: 15px; border: 1px solid var(--border-color); font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; font-weight: 500; color: #cbd5e1; white-space: pre-wrap; margin-top:5px; }
        .text-box { margin-top: 5px; color: white; font-size: 0.95rem; }

        /* History Cards */
        .history-list { display: flex; flex-direction: column; gap: 15px; }
        .history-card { background: var(--bg-sec); border: 1px solid var(--border-color); border-radius: 8px; padding: 20px; cursor: pointer; transition: border-color 0.2s; position: relative; }
        .history-card:hover { border-color: var(--primary); }
        .history-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .history-date { color: var(--text-muted); font-size: 0.8rem; }
        .history-snippet { font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #cbd5e1; white-space: pre; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; margin-right: 30px;}
        .history-arrow { position: absolute; right: 20px; top: 50%; transform: translateY(-50%); color: var(--primary); font-size: 1.2rem; }
        
        .trace-panel { margin-top: 20px; background: #0f111a; border: 1px solid var(--border-color); border-radius: 8px; padding: 15px; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; }
        .trace-header { color: var(--text-muted); font-size: 0.7rem; margin-bottom: 10px; text-transform: uppercase; }
        .error-text { color: #ef4444; }
        .success-text { color: #10b981; }

    </style>
</head>
<body>

    <!-- Main Header -->
    <div class="header" id="mainHeader">
        <i class="fa-solid fa-bug"></i>
        <span>Code Analysis</span>
    </div>

    <!-- Detail Header -->
    <div class="header-action-bar hidden" id="detailHeader">
        <div class="left">
            <button class="icon-btn" onclick="showHistoryList()"><i class="fa-solid fa-arrow-left"></i></button>
            <span>Review Details</span>
        </div>
        <button class="icon-btn danger" onclick="deleteCurrentDetail()"><i class="fa-solid fa-trash"></i></button>
    </div>

    <div class="container">
        <!-- VIEW 1: Input Form -->
        <div id="analyzeView">
            <div class="section-title">Programming Language</div>
            <div class="chip-group" id="langGroup">
                <div class="chip active" data-lang="Python">Python</div>
                <div class="chip" data-lang="JavaScript">JavaScript</div>
                <div class="chip" data-lang="TypeScript">TypeScript</div>
                <div class="chip" data-lang="Java">Java</div>
                <div class="chip" data-lang="C++">C++</div>
                <div class="chip" data-lang="C">C</div>
                <div class="chip" data-lang="C#">C#</div>
                <div class="chip" data-lang="Go">Go</div>
                <div class="chip" data-lang="Rust">Rust</div>
                <div class="chip" data-lang="PHP">PHP</div>
                <div class="chip" data-lang="Ruby">Ruby</div>
                <div class="chip" data-lang="Swift">Swift</div>
                <div class="chip" data-lang="Kotlin">Kotlin</div>
            </div>

            <div class="section-title">Code Snippet</div>
            <textarea id="codeInput" placeholder="Paste your code here..."></textarea>

            <div class="section-title">Task Description (Optional)</div>
            <textarea id="taskInput" placeholder="What should this code do?"></textarea>

            <button class="btn-primary" style="margin-top:25px;" id="analyzeBtn" onclick="runAnalysis()">
                <i class="fa-solid fa-magnifying-glass" id="btnIcon"></i>
                <span id="btnText">Analyze Code</span>
            </button>
        </div>

        <!-- VIEW 2: Analysis Complete Box -->
        <div id="resultView" class="hidden">
            <div class="view-title" style="margin-top:10px;">
                <i class="fa-solid fa-circle-check" style="color: var(--success);"></i>
                Analysis Complete
            </div>
            
            <div class="result-box">
                <div id="reportBox" class="markdown-body"></div>
                <div class="trace-panel">
                    <div class="trace-header">Runtime Execution Trace</div>
                    <div id="traceContent" style="color: #cbd5e1;"></div>
                </div>
            </div>

            <div class="btn-hgroup">
                <button class="btn-secondary" onclick="resetAnalysis()">
                    <i class="fa-solid fa-rotate-right"></i> New Analysis
                </button>
                <button class="btn-primary" onclick="showHistoryList()" style="margin-top:0;">
                    <i class="fa-solid fa-clock"></i> View History
                </button>
            </div>
        </div>

        <!-- VIEW 3: History List -->
        <div id="historyListView" class="hidden">
            <div class="view-title">
                <i class="fa-solid fa-clock" style="color: var(--primary);"></i>
                Review History
            </div>
            <div class="history-list" id="historyListContainer">
                <!-- Javascript will populate cards here -->
            </div>
        </div>

        <!-- VIEW 4: History Detail -->
        <div id="historyDetailView" class="hidden">
            <div class="section-title" style="margin-top:5px;">Language</div>
            <div class="text-box" id="detailLang" style="font-weight:600;"></div>

            <div class="section-title">Task Description</div>
            <div class="text-box" id="detailTask"></div>

            <div class="section-title">Code Snippet</div>
            <div class="code-box" id="detailCode"></div>

            <div class="section-title">Analysis Result</div>
            <div class="result-box markdown-body" id="detailReport" style="margin-top:5px;"></div>
            <div class="trace-panel" id="detailTracePanel">
                <div class="trace-header">Runtime Execution Trace</div>
                <div id="detailTrace" style="color: #cbd5e1;"></div>
            </div>
        </div>
    </div>

    <!-- Bottom Navigation -->
    <div class="bottom-nav">
        <div class="nav-item active" id="navAnalyze" onclick="resetAnalysis(); setActiveNav('navAnalyze');">
            <i class="fa-solid fa-code"></i>
            <span>Analyze</span>
        </div>
        <div class="nav-item" id="navHistory" onclick="showHistoryList(); setActiveNav('navHistory');">
            <i class="fa-solid fa-clock"></i>
            <span>History</span>
        </div>
        <div class="nav-item" id="navProfile" onclick="setActiveNav('navProfile');">
            <i class="fa-solid fa-user"></i>
            <span>Profile</span>
        </div>
    </div>

    <script>
        // State
        let selectedLang = "Python";
        let historyData = JSON.parse(localStorage.getItem('bughunter_history') || '[]');
        let currentDetailIndex = -1;

        // UI Elements
        const views = {
            analyze: document.getElementById('analyzeView'),
            result: document.getElementById('resultView'),
            historyList: document.getElementById('historyListView'),
            historyDetail: document.getElementById('historyDetailView')
        };
        const headers = {
            main: document.getElementById('mainHeader'),
            detail: document.getElementById('detailHeader')
        };

        // Chips Selection
        const chips = document.querySelectorAll('.chip');
        chips.forEach(chip => {
            chip.addEventListener('click', () => {
                chips.forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                selectedLang = chip.getAttribute('data-lang');
            });
        });

        // Functions
        function switchView(viewName) {
            Object.values(views).forEach(v => v.classList.add('hidden'));
            views[viewName].classList.remove('hidden');

            if(viewName === 'historyDetail') {
                headers.main.classList.add('hidden');
                headers.detail.classList.remove('hidden');
            } else {
                headers.main.classList.remove('hidden');
                headers.detail.classList.add('hidden');
            }
        }

        function setActiveNav(navId) {
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            document.getElementById(navId).classList.add('active');
        }

        function resetAnalysis() {
            document.getElementById('codeInput').value = '';
            document.getElementById('taskInput').value = '';
            switchView('analyze');
        }

        async function runAnalysis() {
            const code = document.getElementById('codeInput').value;
            if (!code.trim()) return;

            const task = document.getElementById('taskInput').value;
            const btnText = document.getElementById('btnText');
            const btnIcon = document.getElementById('btnIcon');
            const analyzeBtn = document.getElementById('analyzeBtn');

            btnText.innerText = 'Analyzing...';
            btnIcon.className = 'fa-solid fa-spinner fa-spin';
            analyzeBtn.style.opacity = '0.7';

            try {
                const formData = new URLSearchParams({ 
                    'code': code,
                    'language': selectedLang,
                    'task_description': task
                });

                const response = await fetch('/hunt', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: formData
                });
                const data = await response.json();
                
                // Show Result View
                switchView('result');
                document.getElementById('reportBox').innerHTML = data.ai_report;
                document.getElementById('traceContent').innerHTML = formatTrace(data.trace);

                // Save to History
                saveToHistory({
                    language: selectedLang,
                    code: code,
                    task: task,
                    report: data.ai_report,
                    trace: data.trace,
                    timestamp: new Date().toLocaleString()
                });

            } catch (err) {
                switchView('result');
                document.getElementById('reportBox').innerHTML = '<span class="error-text">Critical System Failure.</span>';
                document.getElementById('traceContent').innerText = 'Error connecting to backend.';
            } finally {
                btnText.innerText = 'Analyze Code';
                btnIcon.className = 'fa-solid fa-magnifying-glass';
                analyzeBtn.style.opacity = '1';
                window.scrollTo(0,0);
            }
        }

        function formatTrace(trace) {
            return trace.replace(/\\n/g, '<br>').replace('', '<span class="error-text">').replace('', '<span class="success-text">') + '</span>';
        }

        function saveToHistory(item) {
            historyData.unshift(item); // prepend
            localStorage.setItem('bughunter_history', JSON.stringify(historyData));
        }

        function showHistoryList() {
            setActiveNav('navHistory');
            switchView('historyList');
            
            const container = document.getElementById('historyListContainer');
            container.innerHTML = '';

            if(historyData.length === 0) {
                container.innerHTML = '<div style="text-align:center; color:#64748b; margin-top:40px;">No history available.</div>';
                return;
            }

            historyData.forEach((item, index) => {
                const card = document.createElement('div');
                card.className = 'history-card';
                card.onclick = () => showHistoryDetail(index);
                card.innerHTML = `
                    <div class="history-card-header">
                        <div class="lang-pill">${item.language.toLowerCase()}</div>
                        <div class="history-date">${item.timestamp}</div>
                    </div>
                    <div class="history-snippet">${escapeHtml(item.code)}</div>
                    <i class="fa-solid fa-chevron-right history-arrow"></i>
                `;
                container.appendChild(card);
            });
            window.scrollTo(0,0);
        }

        function showHistoryDetail(index) {
            currentDetailIndex = index;
            const item = historyData[index];
            switchView('historyDetail');

            document.getElementById('detailLang').innerText = item.language.toLowerCase();
            document.getElementById('detailTask').innerText = item.task || 'No description provided.';
            document.getElementById('detailCode').innerText = item.code;
            document.getElementById('detailReport').innerHTML = item.report;
            
            const tracePanel = document.getElementById('detailTracePanel');
            if (item.trace && item.trace.trim() !== '') {
                tracePanel.style.display = 'block';
                document.getElementById('detailTrace').innerHTML = formatTrace(item.trace);
            } else {
                tracePanel.style.display = 'none';
            }
            window.scrollTo(0,0);
        }

        function deleteCurrentDetail() {
            if(currentDetailIndex >= 0) {
                historyData.splice(currentDetailIndex, 1);
                localStorage.setItem('bughunter_history', JSON.stringify(historyData));
                showHistoryList();
            }
        }

        function escapeHtml(unsafe) {
            return unsafe.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }

    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_TEMPLATE

@app.post("/hunt")
async def handle_hunt(
    code: str = Form(...),
    language: str = Form("Python"),
    task_description: str = Form("")
):
    if language == "Python":
        trace = run_code_safely(code)
    else:
        trace = f" Execution for {language} is currently not supported. Skipping local runtime trace."
    
    ai_md = review_code_with_ai(code, trace, language, task_description)
    ai_html = markdown.markdown(ai_md, extensions=['fenced_code', 'tables', 'md_in_html'])
    
    return {
        "ai_report": ai_html,
        "trace": trace
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("demo_app:app", host="127.0.0.1", port=8000, reload=True)
