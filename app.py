import os
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()
# Streamlit Cloud stores credentials in st.secrets rather than a local .env file.
try:
    for secret_name in ("OPENAI_API_KEY", "OPENAI_MODEL"):
        if secret_name in st.secrets:
            os.environ[secret_name] = str(st.secrets[secret_name])
except Exception:
    pass

from database import (
    create_tables, get_all_books, add_book, search_books,
    update_book, delete_book, get_all_students, add_student,
    issue_book, return_book, get_issued_books
)
from ai_assistant import start_library_agent, resume_library_agent

create_tables()

st.set_page_config(
    page_title="Libra | Library Management",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root { --ink:#172033; --muted:#748094; --navy:#18243d; --blue:#526df5; --pale:#f4f6fb; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background:#f5f7fb; color:var(--ink); }
[data-testid="stSidebar"] { background:#17243d; }
[data-testid="stSidebar"] * { color:#eef2ff !important; }
[data-testid="stSidebar"] .stRadio label { padding:9px 12px; border-radius:10px; }
h1,h2,h3 { font-family:'Manrope',sans-serif; color:#172033; }
.hero { background:linear-gradient(115deg,#17243d 0%,#293e69 65%,#526df5 100%); padding:28px 32px; border-radius:20px; color:white; margin-bottom:22px; }
.hero h1 { color:white; font-size:30px; margin:0 0 7px 0; }
.hero p { color:#dce5ff; margin:0; font-size:14px; }
.eyebrow { text-transform:uppercase; letter-spacing:2px; font-size:11px; color:#aebeff; font-weight:700; margin-bottom:10px; }
.metric-card { background:white; border:1px solid #e8ecf4; border-radius:16px; padding:18px 20px; box-shadow:0 5px 18px rgba(23,32,51,.035); min-height:112px; }
.metric-label { color:#7a8598; font-size:13px; font-weight:600; margin-bottom:8px; }
.metric-value { color:#17243d; font-family:'Manrope',sans-serif; font-size:30px; font-weight:800; }
.metric-note { color:#8b95a6; font-size:11px; margin-top:3px; }
.section-head { display:flex; align-items:center; justify-content:space-between; margin:20px 0 12px; }
div[data-testid="stForm"] { background:white; border:1px solid #e8ecf4; border-radius:14px; padding:18px; }
.stButton>button, .stFormSubmitButton>button { border-radius:10px; font-weight:600; min-height:42px; }
.stButton>button[kind="primary"], .stFormSubmitButton>button[kind="primary"] { background:#526df5; border-color:#526df5; }
div[data-testid="stDataFrame"] { background:white; border-radius:14px; }
div[data-testid="stChatMessage"] { border-radius:14px; }
.small-muted { color:#7a8598; font-size:13px; }
</style>
""", unsafe_allow_html=True)

def hero(kicker, title, subtitle):
    st.markdown(
        f'<div class="hero"><div class="eyebrow">{kicker}</div>'
        f'<h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True
    )

def metric(label, value, note, emoji):
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{emoji} &nbsp;{label}</div>'
        f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
        unsafe_allow_html=True
    )

def flash(kind, message):
    getattr(st, kind)(message)

books = get_all_books()
students = get_all_students()
records = get_issued_books()
active_records = [r for r in records if str(r[5]).lower() == "issued"]
total_copies = sum(int(b[4]) for b in books) + len(active_records)
available_copies = sum(int(b[4]) for b in books)

with st.sidebar:
    st.markdown("## 📚 LIBRA")
    st.caption("SMART LIBRARY MANAGEMENT")
    st.divider()
    page = st.radio(
        "WORKSPACE",
        ["Overview", "Books", "Students", "Issue & Return", "AI Assistant"],
        label_visibility="visible"
    )
    st.divider()
    st.markdown("**Library status**")
    st.caption(f"{len(books)} book titles · {len(students)} students")
    st.caption("Powered by Python + Agentic AI")
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("Library Management System · v2.0")

if page == "Overview":
    hero("LIBRARY OVERVIEW", "Good day, Librarian 👋", "Here’s what’s happening in your library today.")
    c1,c2,c3,c4 = st.columns(4)
    with c1: metric("Book titles", len(books), "Unique titles in catalogue", "📚")
    with c2: metric("Available copies", available_copies, "Ready to be borrowed", "📖")
    with c3: metric("Registered students", len(students), "Library members", "🎓")
    with c4: metric("Currently issued", len(active_records), "Books with students", "↗️")

    left,right = st.columns([1.25,1])
    with left:
        st.subheader("Recently added books")
        if books:
            df = pd.DataFrame(books, columns=["Book ID","Title","Author","Category","Available"])
            st.dataframe(df.tail(6).iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info("Your catalogue is empty. Add your first book from the Books page.")
    with right:
        st.subheader("Catalogue by category")
        if books:
            cat = {}
            for b in books:
                cat[str(b[3])] = cat.get(str(b[3]),0) + 1
            chart_df = pd.DataFrame({"Category":list(cat.keys()),"Titles":list(cat.values())})
            fig = px.pie(chart_df, names="Category", values="Titles", hole=.62)
            fig.update_layout(margin=dict(t=10,b=10,l=5,r=5), legend_title_text="")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Category insights will appear when you add books.")
    st.subheader("Latest circulation activity")
    if records:
        recent = pd.DataFrame(records[:8], columns=["Issue ID","Book","Student","Issue date","Return date","Status"])
        st.dataframe(recent, use_container_width=True, hide_index=True)
    else:
        st.info("No issue records yet.")

elif page == "Books":
    hero("CATALOGUE", "Books collection", "Manage your library catalogue, track stock, and find titles quickly.")
    search_col, refresh_col = st.columns([4,1])
    with search_col:
        keyword = st.text_input("Search books", placeholder="Search by title, author, or category...")
    with refresh_col:
        st.write("")
        st.write("")
        if st.button("↻ Refresh", use_container_width=True):
            st.rerun()
    shown = search_books(keyword) if keyword.strip() else get_all_books()
    st.caption(f"{len(shown)} title(s) found")
    if shown:
        df = pd.DataFrame(shown, columns=["Book ID","Title","Author","Category","Available copies"])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No matching books found.")

    st.subheader("Add a new book")
    with st.form("add_book_form", clear_on_submit=True):
        a,b = st.columns(2)
        title = a.text_input("Book title *")
        author = b.text_input("Author *")
        category = a.text_input("Category *")
        quantity = b.number_input("Quantity *", min_value=0, step=1, value=1)
        submitted = st.form_submit_button("＋ Add book", type="primary")
        if submitted:
            if not title.strip() or not author.strip() or not category.strip():
                st.error("Please complete title, author, and category.")
            else:
                try:
                    add_book(title.strip(), author.strip(), category.strip(), int(quantity))
                    st.success("Book added successfully.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not add book: {exc}")

    st.subheader("Edit or remove a book")
    if books:
        book_map = {f"#{b[0]} · {b[1]}": b for b in books}
        selected_label = st.selectbox("Select a book", list(book_map.keys()))
        selected = book_map[selected_label]
        with st.form("edit_book_form"):
            x,y = st.columns(2)
            e_title = x.text_input("Title", value=selected[1])
            e_author = y.text_input("Author", value=selected[2])
            e_category = x.text_input("Category", value=selected[3])
            e_quantity = y.number_input("Available quantity", min_value=0, step=1, value=int(selected[4]))
            save, remove = st.columns(2)
            save_clicked = save.form_submit_button("Save changes", type="primary")
            delete_clicked = remove.form_submit_button("Delete selected book")
            if save_clicked:
                try:
                    update_book(int(selected[0]), e_title.strip(), e_author.strip(), e_category.strip(), int(e_quantity))
                    st.success("Book updated.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
            if delete_clicked:
                try:
                    delete_book(int(selected[0]))
                    st.success("Book deleted.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Cannot delete this book: {exc}")
    else:
        st.caption("Add a book to enable editing.")

elif page == "Students":
    hero("MEMBERS", "Student directory", "Register students and keep their library membership details organised.")
    if students:
        sdf = pd.DataFrame(students, columns=["Student ID","Name","Email"])
        st.dataframe(sdf, use_container_width=True, hide_index=True)
    else:
        st.info("No students registered yet.")
    st.subheader("Register a student")
    with st.form("student_form", clear_on_submit=True):
        name = st.text_input("Student name *")
        email = st.text_input("Email address")
        if st.form_submit_button("＋ Register student", type="primary"):
            if not name.strip():
                st.error("Student name is required.")
            else:
                try:
                    add_student(name.strip(), email.strip())
                    st.success("Student registered successfully.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

elif page == "Issue & Return":
    hero("CIRCULATION", "Issue & return desk", "Keep track of borrowed books and process returns.")
    available_books = [b for b in books if int(b[4]) > 0]
    l,r = st.columns(2)
    with l:
        st.subheader("Issue a book")
        if not available_books or not students:
            st.warning("You need at least one available book and one registered student.")
        else:
            book_options = {f"#{b[0]} · {b[1]} (available: {b[4]})":b[0] for b in available_books}
            student_options = {f"#{s[0]} · {s[1]}":s[0] for s in students}
            with st.form("issue_form"):
                b_choice = st.selectbox("Choose book", list(book_options))
                s_choice = st.selectbox("Choose student", list(student_options))
                if st.form_submit_button("Issue book", type="primary"):
                    try:
                        issue_id = issue_book(book_options[b_choice], student_options[s_choice])
                        st.success(f"Book issued. Record ID: {issue_id}")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
    with r:
        st.subheader("Return a book")
        if active_records:
            active_map = {f"#{r[0]} · {r[1]} — {r[2]}":r[0] for r in active_records}
            with st.form("return_form"):
                return_choice = st.selectbox("Select active issue", list(active_map))
                if st.form_submit_button("Mark as returned"):
                    try:
                        return_book(int(active_map[return_choice]))
                        st.success("Book returned successfully.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
        else:
            st.info("There are no books currently issued.")
    st.subheader("Circulation history")
    if records:
        rdf = pd.DataFrame(records, columns=["Issue ID","Book","Student","Issue date","Return date","Status"])
        st.dataframe(rdf, use_container_width=True, hide_index=True)
    else:
        st.info("No circulation records yet.")

elif page == "AI Assistant":
    hero("AGENTIC AI", "Your library copilot", "Ask questions about real library data. Database-changing actions require your approval.")
    if not os.getenv("OPENAI_API_KEY"):
        st.warning("Add your OpenAI API key as a Streamlit secret named OPENAI_API_KEY before using the assistant.")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [{
            "role":"assistant",
            "content":"Hello! I can search your books, list students, and review issue records. I will ask before issuing or returning a book."
        }]
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    pending = st.session_state.get("pending_agent_action")
    if pending:
        st.warning(f"The AI wants to perform **{pending['name']}** with arguments: `{pending['arguments']}`")
        approve_col, reject_col = st.columns(2)
        with approve_col:
            if st.button("Approve action", type="primary", use_container_width=True):
                try:
                    result = resume_library_agent(pending["state"], pending["interruption"], True)
                    st.session_state.pop("pending_agent_action", None)
                    if result["interruption"]:
                        st.session_state.pending_agent_action = result
                        st.info("Another approval is required before continuing.")
                    else:
                        st.session_state.chat_history.append({"role":"assistant","content":str(result["output"])})
                    st.rerun()
                except Exception as exc:
                    st.session_state.pop("pending_agent_action", None)
                    st.error(f"AI action failed: {exc}")
        with reject_col:
            if st.button("Reject action", use_container_width=True):
                try:
                    result = resume_library_agent(pending["state"], pending["interruption"], False)
                    st.session_state.pop("pending_agent_action", None)
                    if result["interruption"]:
                        st.session_state.pending_agent_action = result
                    else:
                        st.session_state.chat_history.append({"role":"assistant","content":str(result["output"])})
                    st.rerun()
                except Exception as exc:
                    st.session_state.pop("pending_agent_action", None)
                    st.error(f"Could not reject action: {exc}")

    prompt = st.chat_input("Ask about books, students, or issue records...", disabled=bool(pending))
    if prompt:
        st.session_state.chat_history.append({"role":"user","content":prompt})
        try:
            result = start_library_agent(prompt)
            if result["interruption"]:
                st.session_state.pending_agent_action = result
            else:
                st.session_state.chat_history.append({"role":"assistant","content":str(result["output"])})
        except Exception as exc:
            st.session_state.chat_history.append({"role":"assistant","content":f"Sorry, something went wrong: {exc}"})
        st.rerun()
