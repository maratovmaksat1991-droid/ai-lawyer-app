import streamlit as st

from utils import get_model, extract_text_from_file, create_docx, transcribe_audio
from db import save_case


def render_doc_analyzer():
    st.markdown("## Анализ Документов")
    st.caption("Проверка договоров и исков на риски по законодательству РК.")

    with st.container(border=True):
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("#### Шаг 1. Контекст")
            ctx = st.audio_input("Скажите голосом: Чьи интересы защищаем?", key="doc_ctx")

        with col2:
            st.markdown("#### Шаг 2. Файлы")
            files = st.file_uploader(
                "Загрузите документы (PDF, Word)",
                type=['pdf', 'docx', 'txt'],
                accept_multiple_files=True
            )

    if 'doc_res' not in st.session_state:
        st.session_state.doc_res = None

    if files:
        # Валидация файлов
        valid_files = []
        for f in files:
            text = extract_text_from_file(f)
            if text and "Файл пуст" not in text and "Ошибка" not in text:
                valid_files.append((f, text))
            else:
                st.warning(f"Файл '{f.name}' пуст или не читается — пропущен.")

        if valid_files and st.button("Начать Анализ", use_container_width=True):
            with st.spinner("Читаю документы и сверяю с законами РК..."):
                try:
                    instr = "Общий анализ рисков."
                    if ctx:
                        instr = transcribe_audio(ctx)

                    full_text = ""
                    for f, text in valid_files:
                        full_text += f"\n--- {f.name} ---\n{text}\n"

                    model = get_model()
                    res = model.generate_content(
                        f"Инструкция: {instr}\n"
                        f"Документы:\n{full_text}\n\n"
                        f"Сделай анализ по законам РК:\n"
                        f"1. Сильные стороны документа\n"
                        f"2. Риски и слабые места\n"
                        f"3. Вывод и рекомендации"
                    )
                    st.session_state.doc_res = res.text
                except Exception as e:
                    st.error(f"Ошибка при анализе: {e}")

    if st.session_state.doc_res:
        with st.container(border=True):
            st.markdown("### Результат")
            st.markdown(st.session_state.doc_res)
            st.markdown("---")

            col_save, col_download = st.columns(2)
            with col_download:
                docx = create_docx(st.session_state.doc_res, "Анализ")
                st.download_button(
                    "Скачать Отчет (.docx)", docx,
                    "Doc_Analysis.docx", use_container_width=True
                )
            with col_save:
                if st.button("Сохранить в историю", use_container_width=True, key="save_docs"):
                    save_case(
                        title="Анализ документов",
                        module="Документы",
                        content=st.session_state.doc_res
                    )
                    st.toast("Сохранено в историю!")
