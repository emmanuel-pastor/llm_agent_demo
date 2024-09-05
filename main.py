import PyPDF2
import streamlit as st
import anthropic

api_key = "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"

def extract_text_from_pdf(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ''
    for page in reader.pages:
        text += page.extract_text()
    return text

def file_to_text(file):
    if file.name.endswith('.pdf'):
        return extract_text_from_pdf(file)
    else:
        return file.read().decode()

with st.sidebar:
    anthropic_api_key = st.text_input("Anthropic API Key", key="file_qa_api_key", type="password")
    "[View the source code](https://github.com/streamlit/llm-examples/blob/main/pages/1_File_Q%26A.py)"
    "[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/streamlit/llm-examples?quickstart=1)"

st.title("📝 File Q&A with Anthropic")

uploaded_file = st.file_uploader("Upload an article", type=("txt", "md", "pdf"))

question = st.text_input(
    "Ask something about the article",
    placeholder="Can you give me a short summary?",
    disabled=not uploaded_file,
)

if uploaded_file and question and not anthropic_api_key:
    st.info("Please add your Anthropic API key to continue.")

if uploaded_file and question and anthropic_api_key:
    article = file_to_text(uploaded_file)
    prompt = f"""{anthropic.HUMAN_PROMPT} Here's an article:\n\n
    {article}\n\n\n\n{question}{anthropic.AI_PROMPT}"""

    client = anthropic.Client(api_key=anthropic_api_key)
    response = client.completions.create(
        prompt=prompt,
        stop_sequences=[anthropic.HUMAN_PROMPT],
        model="claude-2.1", #"claude-2" for Claude 2 model
        max_tokens_to_sample=1000,
    )
    st.write("### Answer")
    st.write(response.completion)