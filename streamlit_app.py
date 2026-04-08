import streamlit as st
import requests

BACKEND_URL = "http://127.0.0.1:8000"

# ---------------------------
# Supported Languages
# ---------------------------
LANGUAGE_EXTENSIONS = {
    "python": [".py"],
    "cpp": [".cpp", ".cxx", ".cc", ".hpp", ".h"],
    "c": [".c", ".h"],
    "java": [".java"],
    "typescript": [".ts", ".tsx"],
    "rust": [".rs"],
    "go": [".go"],
    "csharp": [".cs"],
    "php": [".php"],
    "ruby": [".rb"],
    "swift": [".swift"],
    "kotlin": [".kt", ".kts"]
}

def get_language(filename: str) -> str:
    for lang, exts in LANGUAGE_EXTENSIONS.items():
        if any(filename.endswith(ext) for ext in exts):
            return lang
    return "python"

# ---------------------------
# UI Layout
# ---------------------------
st.set_page_config(page_title="AI Code Review Assistant", page_icon="", layout="wide")

st.title(" AI Code Review Assistant")
st.markdown("---")

st.sidebar.header("Simulation Controls")
filename = st.sidebar.text_input("Enter filename to analyze", value="main.py", help="e.g., main.cpp, HelloWorld.java")
task_description = st.sidebar.text_area("Task Context / Description (Optional)", value="", help="Explain what the code is supposed to do.")

st.info("Paste your code below and click ** Analyze Code** to receive a professional AI-driven code review.")

# CODE EDITOR
code_input = st.text_area("Code Editor", height=350, placeholder="Paste your code here...", value='print("Hello BugHunter!")')

if st.button(" Analyze Code"):
    if code_input.strip() == "":
        st.warning("Please enter some code to analyze.")
    else:
        with st.spinner("Performing real-time execution and AI review..."):
            action = {
                "filename": filename,
                "action_type": "read_file",
                "code": code_input,
                "task_description": task_description
            }
            try:
                response = requests.post(f"{BACKEND_URL}/step", json=action)
                if response.status_code == 200:
                    data = response.json()
                    
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.subheader(" Metrics")
                        st.metric("Step Reward", data['reward'])
                        st.metric("Total Score", data['total_score'])
                        st.write(f"**Feedback:** {data['feedback']}")
                    
                    with col2:
                        language = get_language(filename)
                        st.subheader(f" {language.capitalize()} Analysis")
                        
                        st.code(data['runtime_trace'], language="python" if language == "python" else None)

                    st.markdown("---")
                    
                    # AI Review Output
                    st.header(" AI Review Summary")
                    c1, c2, c3 = st.columns(3)
                    
                    with c1:
                        st.error(" ISSUES")
                        st.write(data.get("issues", "No issues detected."))
                    
                    with c2:
                        st.warning(" IMPACT")
                        st.write(data.get("impact", "No impact detected."))
                    
                    with c3:
                        st.success(" RECOMMENDED FIX")
                        st.write(data.get("fix", "No fix suggested."))
                        
                else:
                    st.error(f"Error analyzing the file. Backend returned status code {response.status_code}")
            except Exception as e:
                st.error(f"Failed to connect to backend: {str(e)}")

st.markdown("---")
st.caption("Powered by BugHunter AI Engine | Local Runtime Trace + AI Verification")
