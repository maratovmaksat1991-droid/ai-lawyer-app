import streamlit as st
from modules.analyzer import render_audio_analyzer
from modules.documents import render_doc_analyzer
from modules.simulator import render_court_simulator
from db import get_cases, get_case, delete_case

# --- НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(page_title="Legal OS Pro", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
    h1 { color: #1E3A8A; font-family: 'Helvetica Neue', sans-serif; }
    h2, h3 { color: #374151; }
    div.stButton > button:first-child {
        background-color: #2563EB;
        color: white;
        border-radius: 10px;
        height: 50px;
        font-size: 18px;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: all 0.3s;
    }
    div.stButton > button:first-child:hover {
        background-color: #1D4ED8;
        transform: translateY(-2px);
    }
    .stExpander { border: 1px solid #E5E7EB; border-radius: 8px; }
    .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)


# --- САЙДБАР ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2600/2600246.png", width=100)
st.sidebar.title("Legal OS")
st.sidebar.caption("v10.0 • KZ Edition")
st.sidebar.divider()

mode = st.sidebar.radio(
    "Навигация",
    ["Анализатор Дела", "Анализ Документов", "Судебный Тренажер"]
)

# --- ИСТОРИЯ ДЕЛ В САЙДБАРЕ ---
st.sidebar.divider()
st.sidebar.markdown("### История дел")

cases = get_cases(limit=20)
if cases:
    for case in cases:
        with st.sidebar.expander(f"{case['title']} ({case['created_at']})"):
            st.markdown(f"**Модуль:** {case['module']}")
            if st.button("Открыть", key=f"open_{case['id']}"):
                st.session_state['viewed_case'] = case
                st.rerun()
            if st.button("Удалить", key=f"del_{case['id']}"):
                delete_case(case['id'])
                st.rerun()
else:
    st.sidebar.caption("Пока нет сохранённых дел.")

st.sidebar.divider()
st.sidebar.warning(
    "Результаты носят информационный характер "
    "и не являются юридической консультацией. "
    "Всегда консультируйтесь с квалифицированным юристом."
)
st.sidebar.info("Система работает на базе Gemini 2.0 Flash.")

# --- ПРОСМОТР СОХРАНЁННОГО ДЕЛА ---
if 'viewed_case' in st.session_state and st.session_state.viewed_case:
    case = st.session_state.viewed_case
    st.markdown(f"## {case['title']}")
    st.caption(f"Модуль: {case['module']} | Дата: {case['created_at']}")
    st.markdown(case['content'])
    if st.button("Закрыть"):
        del st.session_state['viewed_case']
        st.rerun()
else:
    # --- ОСНОВНОЙ КОНТЕНТ ---
    if mode == "Анализатор Дела":
        render_audio_analyzer()
    elif mode == "Анализ Документов":
        render_doc_analyzer()
    elif mode == "Судебный Тренажер":
        render_court_simulator()
