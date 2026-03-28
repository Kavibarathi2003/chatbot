import streamlit as st
import pandas as pd
from groq import Groq
import pdfplumber

# ─────────────────────────────────────────────
# 🔐 API KEY (Use secrets in production)
# ─────────────────────────────────────────────
client = Groq(api_key="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")

def llm(prompt):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# ─────────────────────────────────────────────
# 🎨 PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(page_title="AI Data Assistant", layout="wide")

# ─────────────────────────────────────────────
# 🎨 PREMIUM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #020617, #0f172a);
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617, #0f172a) !important;
    color: white !important;
}

/* Chat bubbles */
.user-msg {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    padding: 12px;
    border-radius: 16px;
    color: white;
    text-align: right;
    margin: 8px 0;
}

.bot-msg {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(12px);
    padding: 12px;
    border-radius: 16px;
    margin: 8px 0;
}

/* Code */
.code-box {
    background: #111827;
    padding: 10px;
    border-radius: 10px;
    color: #38bdf8;
    font-size: 13px;
}

/* Result */
.result-box {
    background: #020617;
    border-left: 4px solid #38bdf8;
    padding: 10px;
    border-radius: 10px;
}

/* Upload box */
.upload-box {
    border: 2px dashed #38bdf8;
    padding: 25px;
    border-radius: 12px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 🧠 SESSION STATE
# ─────────────────────────────────────────────
if "chat" not in st.session_state:
    st.session_state.chat = []

# ─────────────────────────────────────────────
# 📂 SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📂 Upload Files")

    uploaded_files = st.file_uploader(
        "Upload Excel / CSV / PDF",
        type=["xlsx", "csv", "pdf"],
        accept_multiple_files=True
    )

    st.markdown("---")
    st.markdown("💡 Try asking:")
    st.write("- Average price")
    st.write("- Top 5 records")
    st.write("- Summarize PDF")

# ─────────────────────────────────────────────
# 🎯 HEADER
# ─────────────────────────────────────────────
st.markdown("## 🤖 AI Data Assistant")
st.caption("Upload multiple files and get insights ✨")

dfs = []
texts = []

# ─────────────────────────────────────────────
# 📂 FILE PROCESSING
# ─────────────────────────────────────────────
if uploaded_files:

    for file in uploaded_files:
        file_type = file.name.split(".")[-1]

        if file_type == "xlsx":
            dfs.append(pd.read_excel(file))

        elif file_type == "csv":
            dfs.append(pd.read_csv(file))

        elif file_type == "pdf":
            with pdfplumber.open(file) as pdf:
                pages = [p.extract_text() for p in pdf.pages]
                texts.append("\n".join([p for p in pages if p]))

    st.success(f"✅ {len(uploaded_files)} file(s) loaded")

# Combine data
df = pd.concat(dfs, ignore_index=True) if dfs else None
text_data = "\n".join(texts) if texts else None

# ─────────────────────────────────────────────
# 💬 CHAT DISPLAY
# ─────────────────────────────────────────────
for role, msg in st.session_state.chat:
    if role == "user":
        st.markdown(f"<div class='user-msg'>👤 {msg}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='bot-msg'>{msg}</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 📊 DATA MODE
# ─────────────────────────────────────────────
if df is not None:

    df.columns = [c.strip().replace(" ", "_") for c in df.columns]

    with st.expander("📊 Preview Combined Data"):
        st.dataframe(df.head())

    def generate_code(q):
        prompt = f"""
DataFrame: df
Columns: {list(df.columns)}

Convert question into pandas code only.

Question: {q}
"""
        return llm(prompt)

    def run_code(code):
        try:
            return eval(code), None
        except Exception as e:
            return None, str(e)

    user_q = st.chat_input("Ask about your data...")

    if user_q:
        st.session_state.chat.append(("user", user_q))

        code = generate_code(user_q)
        result, err = run_code(code)

        if err:
            response = f"❌ {err}"
        else:
            response = f"""
<div class='code-box'>⚙️ {code}</div>
<br>
<div class='result-box'>
📊 <b>Result:</b><br>{result}
</div>
"""

        st.session_state.chat.append(("bot", response))
        st.rerun()

# ─────────────────────────────────────────────
# 📄 PDF MODE
# ─────────────────────────────────────────────
elif text_data:

    user_q = st.chat_input("Ask about documents...")

    if user_q:
        st.session_state.chat.append(("user", user_q))

        prompt = f"""
Documents:
{text_data[:4000]}

Question: {user_q}
"""
        answer = llm(prompt)

        st.session_state.chat.append(("bot", answer))
        st.rerun()

# ─────────────────────────────────────────────
# ❗ EMPTY STATE
# ─────────────────────────────────────────────
else:
    st.markdown("""
    <div class='upload-box'>
        📂 Upload one or more files to begin<br><br>
        Supports Excel, CSV, PDF
    </div>
    """, unsafe_allow_html=True)