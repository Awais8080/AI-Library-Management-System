import os
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool
from database import get_all_books, get_all_students, get_issued_books, issue_book, return_book

load_dotenv()

@function_tool
def list_books() -> str:
    """Show all books in the library, including their available quantities."""
    books = get_all_books()
    if not books:
        return "There are no books in the library yet."
    return "\n".join(
        f"Book ID: {b[0]} | Title: {b[1]} | Author: {b[2]} | Category: {b[3]} | Available quantity: {b[4]}"
        for b in books
    )

@function_tool
def search_library_books(keyword: str) -> str:
    """Search books by a word in the title, author, or category."""
    from database import search_books
    books = search_books(keyword)
    if not books:
        return f"No books matched '{keyword}'."
    return "\n".join(
        f"Book ID: {b[0]} | Title: {b[1]} | Author: {b[2]} | Category: {b[3]} | Available quantity: {b[4]}"
        for b in books
    )

@function_tool
def list_students() -> str:
    """Show all registered students and their student IDs."""
    students = get_all_students()
    if not students:
        return "There are no registered students yet."
    return "\n".join(
        f"Student ID: {s[0]} | Name: {s[1]} | Email: {s[2] or 'Not provided'}"
        for s in students
    )

@function_tool
def list_issue_records() -> str:
    """Show all book issue and return records, including their current status."""
    records = get_issued_books()
    if not records:
        return "There are no issue records yet."
    return "\n".join(
        f"Issue ID: {r[0]} | Book: {r[1]} | Student: {r[2]} | Issue date: {r[3]} | Return date: {r[4] or 'Not returned'} | Status: {r[5]}"
        for r in records
    )

@function_tool(needs_approval=True)
def issue_library_book(book_id: int, student_id: int) -> str:
    """Issue a book to a student. This action always requires user approval."""
    new_issue_id = issue_book(book_id, student_id)
    return f"Book issued successfully. New issue record ID: {new_issue_id}."

@function_tool(needs_approval=True)
def return_library_book(issue_id: int) -> str:
    """Mark an issued book as returned. This action always requires user approval."""
    return_book(issue_id)
    return f"Issue record {issue_id} was marked as returned successfully."

library_agent = Agent(
    name="Library AI Assistant",
    model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
    instructions=(
        "You are the AI assistant for a Library Management System. Use tools for actual "
        "library books, students, availability, and issue records. Never invent records. "
        "Explain IDs clearly. Reading records does not need approval. Issuing or returning "
        "a book always requires explicit user approval. Never claim an operation succeeded "
        "unless the tool reports success. Ask for missing IDs or use read tools to identify them. "
        "Keep answers clear and concise."
    ),
    tools=[list_books, search_library_books, list_students, list_issue_records,
           issue_library_book, return_library_book],
)

def _pack_result(result):
    if result.interruptions:
        interruption = result.interruptions[0]
        return {
            "output": None,
            "state": result.to_state(),
            "interruption": interruption,
            "name": interruption.name or "Database action",
            "arguments": interruption.arguments or "{}",
        }
    return {"output": result.final_output, "state": None, "interruption": None}

def start_library_agent(user_message: str):
    result = Runner.run_sync(library_agent, user_message)
    return _pack_result(result)

def resume_library_agent(state, interruption, approved: bool):
    if approved:
        state.approve(interruption, always_approve=False)
    else:
        state.reject(interruption)
    result = Runner.run_sync(library_agent, state)
    return _pack_result(result)
