import streamlit as st
import requests
import os
import io
import contextlib

# CONFIGURATION
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:7860")

def check_backend():
    try:
        # Increased timeout to handle initial container spin-up
        requests.get(f"{BACKEND_URL}/state", timeout=5)
        return True
    except:
        return False

if "task_data" not in st.session_state:
    st.session_state.task_data = None

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(
    page_title="AI Code Review Assistant",
    page_icon="[BOT]",
    layout="wide",
)

# -------------------------------
# Dual-Layer Cyber-Engine Background
# -------------------------------
st.markdown("""
<div id="bg-container">
    <div id="gradient-wave"></div>
    <canvas id="particle-network"></canvas>
</div>

<style>
    :root {
        --deep-indigo: #0a0e1b;
        --royal-purple: #1e1b4b;
        --neon-cyan: #00f2ff;
    }

    #bg-container {
        position: fixed;
        top: 0; left: 0;
        width: 100vw; height: 100vh;
        z-index: -1;
        overflow: hidden;
        background-color: var(--deep-indigo);
    }

    #gradient-wave {
        position: absolute;
        width: 200%; height: 200%;
        top: -50%; left: -50%;
        background: radial-gradient(circle at center, var(--royal-purple) 0%, var(--deep-indigo) 70%);
        animation: wave-animation 20s infinite alternate ease-in-out;
        z-index: -2;
    }

    @keyframes wave-animation {
        0% { transform: scale(1) rotate(0deg); opacity: 0.8; }
        50% { transform: scale(1.1) rotate(2deg); opacity: 1; }
        100% { transform: scale(1) rotate(0deg); opacity: 0.8; }
    }

    canvas#particle-network {
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 100%;
        z-index: -1;
    }

    /* Glassmorphism Overrides */
    .stApp { background: transparent !important; }
</style>

<script>
    const canvas = document.getElementById('particle-network');
    const ctx = canvas.getContext('2d');
    
    let particles = [];
    const count = 40;

    function init() {
        if (!canvas) return;
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        particles = [];
        for (let i = 0; i < count; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.4,
                vy: (Math.random() - 0.5) * 0.4,
                size: Math.random() * 2 + 1
            });
        }
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = 'rgba(0, 242, 255, 0.4)';
        ctx.strokeStyle = 'rgba(0, 242, 255, 0.1)';

        for (let i = 0; i < count; i++) {
            let p = particles[i];
            p.x += p.vx;
            p.y += p.vy;

            if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
            if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fill();

            for (let j = i + 1; j < count; j++) {
                let p2 = particles[j];
                let dist = Math.sqrt((p.x - p2.x)**2 + (p.y - p2.y)**2);
                if (dist < 150) {
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(animate);
    }

    window.addEventListener('resize', init);
    init();
    animate();
</script>
""", unsafe_allow_html=True)

# -------------------------------
# Professional Theme CSS
# -------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;700;900&family=Orbitron:wght@400;700;900&display=swap');
    
    .stApp { background-color: #0a0e1b; color: #ffffff; font-family: 'Outfit', sans-serif; }
    h1, h2, h3 { font-family: 'Orbitron', sans-serif; text-transform: uppercase; letter-spacing: 1px; }
    
    [data-testid="stSidebar"] { background-color: #0e1117 !important; border-right: 1px solid #1f2937; }
    
    .stMetric { background-color: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(0, 242, 255, 0.1); }
    [data-testid="stMetricValue"] { color: #00f2ff !important; font-family: 'Orbitron', sans-serif; text-shadow: 0 0 10px rgba(0, 242, 255, 0.5); }
    
    .stTextArea > div { background-color: #1a1f2e !important; color: #ffffff !important; border: 1px solid #374151 !important; }
    
    .stButton > button {
        background: linear-gradient(45deg, #00f2ff, #2563eb) !important;
        color: white !important;
        border: none !important;
        font-family: 'Orbitron', sans-serif;
        font-weight: 700;
        transition: 0.3s all ease;
    }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0, 242, 255, 0.4); }
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Sidebar
# -------------------------------
with st.sidebar:
    st.title("AI CODE REVIEW ASSISTANT")
    st.markdown("""
        **Features:**
        - Multi-language support
        - Structured AI code reviews
        - NEW: Manual Language Selection
        - NEW: Configuration Sidebar
    """)
    st.markdown("---")
    
    with st.expander("Advanced Settings", expanded=False):
        user_api_key = st.text_input("HF_TOKEN / OpenAI API Key", type="password")
    
    st.markdown("---")
    st.subheader("HACKATHON ENV MODE")
    st.write("Play as the AI Agent manually!")
    task_sel = st.selectbox("Load OpenEnv Task:", ["None", "task_1", "task_2", "task_3"])
    if st.button("Load Task"):
        if task_sel != "None":
            res = requests.post(f"{BACKEND_URL}/reset?task_id={task_sel}")
            if res.status_code == 200:
                st.session_state.task_data = res.json()
                st.rerun()

# -------------------------------
# Main Content
# -------------------------------
st.markdown("<h1 style='text-align:center;'>AI Code Review Dashboard</h1>", unsafe_allow_html=True)

if not check_backend():
    st.warning("ENGINE WARMING UP: The backend AI service is starting. Please wait 5-10 seconds...")
    st.stop()

st.markdown("<hr>", unsafe_allow_html=True)

if st.session_state.task_data:
    data = st.session_state.task_data
    st.markdown(f"## TASK: {data['pr_details']['title']}")
    
    c1, c2 = st.columns([1, 2])
    with c1:
        file_to_read = st.selectbox("Files in PR:", data["files"])
        if st.button("Read File", use_container_width=True):
            res = requests.post(f"{BACKEND_URL}/step", json={"command": "read_file", "filename": file_to_read}).json()
            st.session_state.task_data = res["observation"]
            st.rerun()
            
    with c2:
        if data.get("current_file_content"):
            st.code(data["current_file_content"])
            cmt = st.text_input("Identify Bug or Add Comment:")
            if st.button("Post Review Comment"):
                res = requests.post(f"{BACKEND_URL}/step", json={"command": "add_comment", "filename": data["current_file_name"], "content": cmt}).json()
                st.session_state.task_data = res["observation"]
                st.success(f"Reward updated: {res['reward']}")

    st.markdown("---")
    res_c1, res_c2 = st.columns(2)
    with res_c1:
        if st.button("Reject PR (Request Changes)", type="primary"):
            res = requests.post(f"{BACKEND_URL}/step", json={"command": "request_changes"}).json()
            st.success(f"Final Score: {res['reward']} / 1.0")
            st.session_state.task_data = None
    with res_c2:
        if st.button("Approve PR"):
            res = requests.post(f"{BACKEND_URL}/step", json={"command": "approve"}).json()
            st.success(f"Final Score: {res['reward']} / 1.0")
            st.session_state.task_data = None

else:
    st.markdown("### SANDBOX: PASTE YOUR CODE SNIPPET")
    pasted_code = st.text_area("Code Editor", height=300, value='print("Logic Lords Online")')

    col_a, col_b = st.columns([3, 1])
    with col_a:
        sel_lang = st.selectbox("Select Programming Language:", ["python", "cpp", "java", "javascript"])
    with col_b:
        st.write("") # Spacer
        st.write("") # Spacer
        analyze_button = st.button("Analyze Snippet", use_container_width=True)

    if analyze_button:
        with st.spinner("Analyzing..."):
            # Execute for trace
            f = io.StringIO()
            try:
                with contextlib.redirect_stdout(f):
                    exec(pasted_code, {})
                trace = f.getvalue()
            except Exception as e:
                trace = str(e)
            
            # API Call with Retry Logic
            payload = {"code": pasted_code, "action_type": "paste_code", "language": sel_lang}
            res = None
            for _ in range(3):
                try:
                    res_raw = requests.post(f"{BACKEND_URL}/frontend_step", json=payload, timeout=5)
                    res = res_raw.json()
                    break
                except:
                    import time
                    time.sleep(1)
            
            if not res:
                st.error("Backend connection timeout. Please try again in 5 seconds.")
                st.stop()
            
            st.markdown("---")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Reward", res.get("reward", 0))
            m2.metric("Total Score", 10)
            
            rank = res.get("rank", "5/10")
            color = "#00f2ff" if "10" in rank else "#f59e0b"
            m3.markdown(f"**Code Quality Rank:** <h2 style='color:{color};margin:0;'>{rank}</h2>", unsafe_allow_html=True)
            m4.metric("Language Detected", sel_lang.capitalize())
            
            st.markdown("---")
            st.markdown("### RUNTIME / EXECUTION TRACE")
            st.code(trace if trace else "Code executed successfully.")
            
            t1, t2, t3 = st.tabs(["ISSUES", "IMPACT", "FIX"])
            t1.info(res.get("issues", "No major issues."))
            t2.warning(res.get("impact", "Maintainability verified."))
            t3.success(res.get("fix", "Review complete."))
