import streamlit as st
import google.generativeai as genai
import time
import os

from utils import get_model, upload_audio_to_gemini, create_docx, cleanup_temp_files, configure_genai
from db import save_case


def render_audio_analyzer():
    st.markdown("## Анализатор Дела")
    st.caption("Режим «Следователь»: Соберите улики, и ИИ составит полную картину.")

    if 'case_files' not in st.session_state:
        st.session_state.case_files = []
    if 'brief_text' not in st.session_state:
        st.session_state.brief_text = ""

    col_left, col_right = st.columns([1, 1.2], gap="large")

    with col_left:
        with st.container(border=True):
            st.markdown("### 1. Добавить материалы")
            st.info("Можно добавлять записи по очереди. Сводка будет обновляться.", icon="ℹ️")

            tab_mic, tab_file = st.tabs(["Записать голос", "Загрузить файл"])
            new_source = None

            with tab_mic:
                mic_val = st.audio_input("Нажмите для записи", key="an_mic")
                if mic_val:
                    new_source = mic_val
            with tab_file:
                file_val = st.file_uploader(
                    "Выберите аудио (MP3, WAV, OGG)",
                    type=["mp3", "wav", "ogg", "m4a"]
                )
                if file_val:
                    new_source = file_val

            st.markdown("---")

            if st.button("Добавить в дело", use_container_width=True):
                if new_source:
                    ext = new_source.name.split('.')[-1] if hasattr(new_source, 'name') else 'wav'
                    fname = f"evid_{int(time.time())}.{ext}"
                    with open(fname, "wb") as f:
                        f.write(new_source.getbuffer())

                    st.session_state.case_files.append(fname)
                    st.toast("Файл добавлен к делу!")

                    with st.spinner("ИИ анализирует материалы..."):
                        try:
                            configure_genai()
                            files_gemini = []
                            for p in st.session_state.case_files:
                                upl = upload_audio_to_gemini(p)
                                files_gemini.append(upl)

                            model = get_model()
                            prompt = """
                            Роль: Юрист Республики Казахстан.
                            Задача: Составь сводный отчет по всем записям.
                            Структура:
                            1. СУТЬ СИТУАЦИИ.
                            2. ФАКТЫ (Даты, Суммы, Имена).
                            3. ПРАВОВАЯ ОЦЕНКА (ссылки на ГК/ГПК РК).
                            4. ЧТО УТОЧНИТЬ У КЛИЕНТА.
                            5. ПЛАН ДЕЙСТВИЙ.
                            """
                            res = model.generate_content([prompt] + files_gemini)
                            st.session_state.brief_text = res.text
                        except Exception as e:
                            st.error(f"Ошибка при анализе: {e}")
                else:
                    st.warning("Сначала выберите файл или запишите голос.")

            if st.session_state.case_files:
                st.write(f"В деле файлов: **{len(st.session_state.case_files)}**")
                if st.button("Сбросить всё", type="secondary"):
                    cleanup_temp_files(st.session_state.case_files)
                    st.session_state.case_files = []
                    st.session_state.brief_text = ""
                    st.rerun()

    with col_right:
        with st.container(border=True):
            st.markdown("### 2. Сводка по делу")
            if st.session_state.brief_text:
                st.markdown(st.session_state.brief_text)
                st.markdown("---")

                col_save, col_download = st.columns(2)
                with col_download:
                    docx = create_docx(st.session_state.brief_text, "Сводка (РК)")
                    st.download_button(
                        "Скачать Сводку (.docx)", docx,
                        "Brief_KZ.docx", use_container_width=True
                    )
                with col_save:
                    if st.button("Сохранить в историю", use_container_width=True, key="save_analyzer"):
                        save_case(
                            title=f"Анализ дела ({len(st.session_state.case_files)} файлов)",
                            module="Анализатор",
                            content=st.session_state.brief_text
                        )
                        st.toast("Сохранено в историю!")
            else:
                st.markdown("*Здесь появится результат анализа...*")
