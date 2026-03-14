import streamlit as st

from utils import get_model, extract_text_from_file, transcribe_audio, create_docx
from db import save_case


def render_court_simulator():
    st.markdown("## Судебный Тренажер")
    st.caption("Симуляция заседания с Судьей и Оппонентом. Проверьте свою позицию.")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "sim_active" not in st.session_state:
        st.session_state.sim_active = False
    if "turn_count" not in st.session_state:
        st.session_state.turn_count = 0
    if "sim_analysis" not in st.session_state:
        st.session_state.sim_analysis = None

    # НАСТРОЙКИ
    if not st.session_state.sim_active and not st.session_state.sim_analysis:
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 1. Ваша роль")
                user_role = st.selectbox("Кого представляете?", ["Истец", "Ответчик"], index=0)
            with col2:
                st.markdown("### 2. Материалы")
                sim_files = st.file_uploader(
                    "Загрузите дело",
                    type=['pdf', 'docx', 'txt'],
                    accept_multiple_files=True
                )

            st.markdown("---")
            if st.button("Открыть заседание", use_container_width=True, type="primary"):
                if sim_files:
                    # Валидация файлов
                    ctx = ""
                    for f in sim_files:
                        text = extract_text_from_file(f)
                        if text and "Файл пуст" not in text:
                            ctx += text + "\n"

                    if not ctx.strip():
                        st.error("Не удалось прочитать загруженные файлы.")
                        return

                    if user_role == "Истец":
                        ai_roles = "Роли ИИ: 1. СУДЬЯ. 2. АДВОКАТ ОТВЕТЧИКА."
                        absent = "Ответчик"
                    else:
                        ai_roles = "Роли ИИ: 1. СУДЬЯ. 2. АДВОКАТ ИСТЦА."
                        absent = "Истец"

                    try:
                        model = get_model()
                        prompt = f"""
                        {ai_roles}
                        Пользователь: {user_role}. ВНИМАНИЕ: {absent} отсутствует, говори ТОЛЬКО с пользователем.
                        Контекст: ГПК РК. Материалы: {ctx[:30000]}
                        Начни заседание. Представься как СУДЬЯ и задай первый вопрос.
                        """
                        res = model.generate_content(prompt)
                        st.session_state.messages = [{"role": "assistant", "content": res.text}]
                        st.session_state.sim_active = True
                        st.session_state.user_role = user_role
                        st.session_state.ai_roles = ai_roles
                        st.session_state.absent = absent
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ошибка при запуске симуляции: {e}")
                else:
                    st.error("Без документов суд не начнется!")

    # ПРОЦЕСС
    if st.session_state.sim_active:
        for msg in st.session_state.messages:
            avatar = "⚖️" if msg["role"] == "assistant" else "👤"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

        st.write("")
        with st.container(border=True):
            st.markdown("**Ваш ответ суду:**")
            key = f"court_mic_{st.session_state.turn_count}"
            user_audio = st.audio_input("Запись голоса", key=key)

            if user_audio:
                with st.spinner("Суд слушает..."):
                    try:
                        user_text = transcribe_audio(user_audio)
                        if not user_text:
                            st.error("Не удалось распознать речь.")
                            return

                        st.session_state.messages.append({"role": "user", "content": user_text})

                        model = get_model()
                        hist = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])

                        prompt = f"""
                        {st.session_state.ai_roles}
                        Правило: ИГНОРИРУЙ отсутствующего {st.session_state.absent}. Говори только с Пользователем.
                        История: {hist}
                        Ответ: "{user_text}"
                        Задача: Кто говорит сейчас (Судья или Оппонент)? Оцени ответ. Задай СЛЕДУЮЩИЙ вопрос.
                        """
                        res = model.generate_content(prompt)
                        st.session_state.messages.append({"role": "assistant", "content": res.text})
                        st.session_state.turn_count += 1
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ошибка: {e}")

        col_end, _ = st.columns([1, 2])
        with col_end:
            if st.button("Закончить прения", use_container_width=True):
                with st.spinner("Подготовка разбора..."):
                    try:
                        model = get_model()
                        hist = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                        res = model.generate_content(
                            f"Разбор судебной симуляции по законам РК.\n"
                            f"Роль пользователя: {st.session_state.user_role}.\n"
                            f"История: {hist}\n\n"
                            f"Составь отчет:\n"
                            f"1. Контекст дела\n"
                            f"2. Сильные стороны выступления\n"
                            f"3. Слабые стороны и ошибки\n"
                            f"4. Итоговая оценка"
                        )
                        st.session_state.sim_analysis = res.text
                        st.session_state.sim_active = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ошибка при анализе: {e}")

    # РАЗБОР
    if st.session_state.sim_analysis:
        with st.container(border=True):
            st.markdown("## Результаты симуляции")
            st.markdown(st.session_state.sim_analysis)
            st.markdown("---")

            col_save, col_download, col_restart = st.columns(3)
            with col_download:
                docx = create_docx(st.session_state.sim_analysis, "Разбор (РК)")
                st.download_button(
                    "Скачать Разбор (.docx)", docx,
                    "Debrief.docx", use_container_width=True
                )
            with col_save:
                if st.button("Сохранить в историю", use_container_width=True, key="save_sim"):
                    save_case(
                        title=f"Симуляция ({st.session_state.get('user_role', 'N/A')})",
                        module="Тренажер",
                        content=st.session_state.sim_analysis
                    )
                    st.toast("Сохранено в историю!")
            with col_restart:
                if st.button("Начать заново", use_container_width=True):
                    st.session_state.messages = []
                    st.session_state.sim_analysis = None
                    st.session_state.turn_count = 0
                    st.rerun()
