import os, json, re, random
from io import BytesIO
import requests
import streamlit as st
from pypdf import PdfReader
from dotenv import load_dotenv
load_dotenv()
st.set_page_config(page_title='Binary Brads | Student Super Assistant', page_icon='🚀', layout='wide')
st.markdown('''<style>.stApp{background:linear-gradient(135deg,#0b1020,#15152f);color:#f0f3ff}div[data-testid="stMetric"]{background:#202441;border-radius:15px;padding:15px}.stButton>button{border-radius:12px}h1,h2,h3{color:#c4b5fd}</style>''',unsafe_allow_html=True)
MODES={
'💬 General AI':'You are Binary Brads, a helpful, accurate AI assistant. State uncertainty clearly.',
'📚 Study Tutor':'Explain topics in easy steps, with examples, exam-friendly key points and mini exercises.',
'🧠 Quiz Maker':'Create 8 varied multiple-choice questions, four options each, and an answer key with explanations.',
'🗂️ Flashcards':'Create 12 concise question-and-answer flashcards formatted as a numbered list.',
'📝 Notes Generator':'Generate organized revision notes with headings, definitions, examples and a recap.',
'💻 Code Mentor':'Help debug and write readable working code, explain dependencies and show tests.',
'🎯 Interview Coach':'Conduct interview preparation, give model answers and practical feedback.',
'📄 Resume Reviewer':'Review supplied resume text for clarity, impact, ATS keywords and truthful improvements. Do not invent achievements.',
'✉️ Writing Studio':'Draft or improve emails, letters, descriptions and professional writing.',
'🌍 Translator':'Translate text into the requested language while preserving meaning and tone.',
'🎨 Idea Lab':'Brainstorm original project ideas, creative concepts, event plans and extracurricular activities.',
'🗓️ Productivity Planner':'Create actionable schedules, to-do lists, milestones and priorities.',
'😊 Sentiment Explorer':'Analyze the tone of provided text, give nuanced evidence and avoid claiming clinical diagnosis.',
'📑 Document Q&A':'Answer only from the provided document context; when absent, say it is not found.'}

def config(name, default=''):
    return st.secrets.get(name, os.getenv(name, default))

def call_ai(messages,provider,model):
    if provider=='Groq':
        key=str(config('GROQ_API_KEY')).strip()
        if not key: raise RuntimeError('GROQ_API_KEY missing. Configure GROQ_API_KEY in Streamlit Cloud app secrets.')
        r=requests.post('https://api.groq.com/openai/v1/chat/completions',headers={'Authorization':f'Bearer {key}'},json={'model':model,'messages':messages,'temperature':0.5},timeout=90)
        if not r.ok: raise RuntimeError(f'Groq API error {r.status_code}: {r.text[:350]}')
        return r.json()['choices'][0]['message']['content']
    url=os.getenv('OLLAMA_URL','http://localhost:11434').rstrip('/')
    r=requests.post(url+'/api/chat',json={'model':model,'messages':messages,'stream':False},timeout=180)
    if not r.ok: raise RuntimeError(f'Ollama error {r.status_code}: {r.text[:350]}')
    return r.json()['message']['content']

def pdf_text(files):
    pieces=[]
    for file in files:
        try:
            reader=PdfReader(BytesIO(file.getvalue()))
            text='\n'.join((p.extract_text() or '') for p in reader.pages)
            pieces.append((file.name,text))
        except Exception as e: st.warning(f'Cannot read {file.name}: {e}')
    return pieces

def select_context(question,docs,max_chars=14000):
    chunks=[]
    for name,txt in docs:
        for i in range(0,len(txt),1300): chunks.append((name,txt[i:i+1500]))
    terms=set(re.findall(r'\w{3,}',question.lower()))
    ranked=sorted(chunks,key=lambda item:sum(item[1].lower().count(t) for t in terms),reverse=True)
    return '\n\n'.join(f'[Source: {name}]\n{chunk}' for name,chunk in ranked[:9])[:max_chars]

if 'history' not in st.session_state: st.session_state.history=[]
if 'tasks' not in st.session_state: st.session_state.tasks=[]
with st.sidebar:
    st.title('🚀 Binary Brads')
    st.caption('Your intelligent student super assistant')
    provider=st.radio('AI engine',['Groq','Ollama (local, free)'],index=0)
    provider='Ollama' if provider.startswith('Ollama') else provider
    model=st.text_input('Model',value=os.getenv('OLLAMA_MODEL','llama3.2') if provider=='Ollama' else config('GROQ_MODEL','llama-3.3-70b-versatile'))
    mode=st.selectbox('Select your AI tool',list(MODES))
    if st.button('🧹 New conversation',use_container_width=True): st.session_state.history=[];st.rerun()
    st.caption('Privacy: conversations stay in this browser session. Files are sent to your chosen AI provider when used.')
st.title('Binary Brads — Multi-Purpose Intelligent Assistant')
st.caption('Final-year project demo • Multiple specialized modes • Local or cloud LLM')
t1,t2,t3=st.tabs(['🤖 AI Workspace','📂 Document Lab','🛠️ Student Utilities'])
with t1:
    a,b,c=st.columns(3)
    a.metric('AI modes',len(MODES));b.metric('Messages',len(st.session_state.history));c.metric('AI providers',2)
    for m in st.session_state.history:
        with st.chat_message(m['role']): st.markdown(m['content'])
    prompt=st.chat_input('Ask Binary Brads anything...')
    if prompt:
        st.session_state.history.append({'role':'user','content':prompt})
        with st.chat_message('user'): st.markdown(prompt)
        with st.chat_message('assistant'):
            try:
                messages=[{'role':'system','content':MODES[mode]}]+st.session_state.history[-12:]
                with st.spinner('Thinking...'): answer=call_ai(messages,provider,model)
                st.markdown(answer)
                st.session_state.history.append({'role':'assistant','content':answer})
            except Exception as e: st.error(str(e))
    if st.session_state.history:
        st.download_button('⬇️ Export chat (JSON)',json.dumps(st.session_state.history,indent=2,ensure_ascii=False),file_name='binary_brads_chat.json',mime='application/json')
with t2:
    st.subheader('Ask questions about your PDFs')
    uploads=st.file_uploader('Upload PDF documents',type=['pdf'],accept_multiple_files=True)
    question=st.text_input('Question about the uploaded documents')
    if st.button('🔎 Analyze documents'):
        if not uploads or not question.strip(): st.warning('Upload a PDF and enter a question.')
        else:
            docs=pdf_text(uploads)
            context=select_context(question,docs)
            if not context.strip(): st.warning('No selectable text detected. Scanned PDFs need OCR.')
            else:
                try:
                    with st.spinner('Reading selected passages...'):
                        answer=call_ai([{'role':'system','content':MODES['📑 Document Q&A']+' Cite document filenames in your answer. Context:\n'+context},{'role':'user','content':question}],provider,model)
                    st.markdown(answer)
                    st.download_button('Download answer',answer,file_name='document_answer.txt')
                except Exception as e: st.error(str(e))
    st.caption('Uses keyword-ranked PDF passages, not vector embeddings. For a full RAG extension, add FAISS and an embedding model.')
with t3:
    left,right=st.columns(2)
    with left:
        st.subheader('📋 Personal task planner')
        new_task=st.text_input('New task')
        if st.button('Add task') and new_task.strip(): st.session_state.tasks.append({'task':new_task.strip(),'done':False})
        for i,item in enumerate(st.session_state.tasks):
            item['done']=st.checkbox(item['task'],value=item['done'],key=f'task_{i}')
        if st.session_state.tasks: st.download_button('Export tasks',json.dumps(st.session_state.tasks,indent=2),file_name='tasks.json')
    with right:
        st.subheader('🧮 Quick calculator')
        expression=st.text_input('Arithmetic expression (e.g. (12+8)*3/4)')
        if st.button('Calculate'):
            try:
                import ast,operator
                ops={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Pow:operator.pow,ast.Mod:operator.mod}
                def calc(node):
                    if isinstance(node,ast.Expression):return calc(node.body)
                    if isinstance(node,ast.Constant) and type(node.value) in (int,float):return node.value
                    if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.USub,ast.UAdd)):return -calc(node.operand) if isinstance(node.op,ast.USub) else calc(node.operand)
                    if isinstance(node,ast.BinOp) and type(node.op) in ops:
                        a,b=calc(node.left),calc(node.right)
                        if abs(a)>1e12 or abs(b)>1e12 or isinstance(node.op,ast.Pow) and abs(b)>12:raise ValueError('Expression too large')
                        return ops[type(node.op)](a,b)
                    raise ValueError('Only basic arithmetic is supported')
                st.success(str(calc(ast.parse(expression,mode='eval'))))
            except Exception as e: st.error(f'Invalid expression: {e}')
        st.subheader('🎲 Activity suggestion')
        if st.button('Surprise me'):
            st.info(random.choice(['Organize a campus hackathon','Host a technical quiz competition','Build an AI accessibility demo','Start a peer coding club','Run a science outreach event','Create a community volunteering campaign']))
