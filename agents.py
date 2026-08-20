# AI SQL Agent - LangGraph Agent with Natural Language to SQL Capabilities
import os
import sys
import time
import uuid
import threading
from dotenv import load_dotenv
from sql_validator import validate_sql, is_query
from database import (
    get_db_connection,
    check_db_health,
    seed_database,
    get_db_schema,
    execute_query
)
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

# Rich terminal formatting for an enhanced CLI experience
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.markdown import Markdown
    from rich.table import Table
    from rich.prompt import Prompt
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# Global Checkpointer for Multi-Turn Agent Memory
_global_checkpointer = MemorySaver()

# Thread-safe execution store to capture tool outputs and prevent duplicate database queries
_execution_lock = threading.Lock()
_execution_store = {}


# ==========================================
# 1. Define LangGraph Tools
# ==========================================

@tool
def fetch_schema() -> str:
    """Fetch the database schema including table names, column names, and data types from PostgreSQL."""
    return get_db_schema()


@tool
def run_sql_query(query: str, config: RunnableConfig = None) -> str:
    """Validate and execute a single read-only SQL query against PostgreSQL. Returns fetched records or an error."""
    clean_query = query.strip()
    if not clean_query.endswith(";"):
        clean_query += ";"

    thread_id = "default_session"
    if config and "configurable" in config:
        thread_id = config["configurable"].get("thread_id", "default_session")

    # 1. Application-level AST & Security validation
    is_valid, val_reason = validate_sql(clean_query)
    if not is_valid:
        with _execution_lock:
            _execution_store[thread_id] = {
                "sql_query": clean_query,
                "rows": [],
                "columns": [],
                "row_count": 0,
                "execution_time_ms": 0.0,
                "error": val_reason,
                "validation_passed": False
            }
        return f"SECURITY ERROR: Query rejected by validator. {val_reason}"

    # 2. Execute SQL query ONCE against PostgreSQL using read-only connection
    try:
        start_time = time.time()
        results = execute_query(clean_query, readonly=True)
        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Store single execution result for UI / caller reuse (eliminates duplicate DB query)
        columns = list(results[0].keys()) if results else []
        with _execution_lock:
            _execution_store[thread_id] = {
                "sql_query": clean_query,
                "rows": results,
                "columns": columns,
                "row_count": len(results),
                "execution_time_ms": duration_ms,
                "error": None,
                "validation_passed": True
            }

        if not results:
            return "Query executed successfully. Result: 0 rows returned."

        # Format output string for LLM reasoning
        if len(results) <= 50:
            return str(results)
        else:
            return f"Retrieved {len(results)} rows. First 50 rows: {str(results[:50])}"

    except Exception as error:
        error_msg = str(error)
        with _execution_lock:
            _execution_store[thread_id] = {
                "sql_query": clean_query,
                "rows": [],
                "columns": [],
                "row_count": 0,
                "execution_time_ms": 0.0,
                "error": error_msg,
                "validation_passed": True
            }
        return f"Database Execution Error: {error_msg}"


# ==========================================
# 2. List of Tools
# ==========================================
tools = [fetch_schema, run_sql_query]


# ==========================================
# 3. Initialize LangGraph Agent
# ==========================================
def create_agent(model_name: str = None, temperature: float = 0.0, checkpointer=None):
    """Initializes and returns the LangGraph SQL ReAct Agent with Memory Checkpointer."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set. Please check your .env file.")

    effective_model = model_name if model_name else GROQ_MODEL
    effective_checkpointer = checkpointer if checkpointer is not None else _global_checkpointer

    llm = ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model_name=effective_model,
        temperature=temperature
    )

    system_prompt = (
        "You are an expert SQL assistant responsible for answering user questions using the connected PostgreSQL database.\n\n"
        "Strict Guidelines:\n"
        "1. You maintain conversation context across multiple turns. When a user asks follow-up questions referencing previous "
        "results (e.g. 'those employees', 'sort them by salary', 'now only IT department'), use the preceding conversation context to construct the query.\n"
        "2. If you do not know the database schema yet, invoke the `fetch_schema` tool first to inspect available tables, columns, and data types.\n"
        "3. Formulate only valid read-only PostgreSQL SELECT or WITH (CTE) queries based on the user's request. Never invent tables or columns.\n"
        "4. Always execute the SQL query using `run_sql_query` to verify and retrieve actual database results.\n"
        "5. If `run_sql_query` returns an error, analyze the error message, correct your query, and retry.\n"
        "6. Finally, present a clear, comprehensive, and friendly natural language response summarizing the findings for the user."
    )

    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
        checkpointer=effective_checkpointer
    )

    return agent


# Cache the default agent instance with global checkpointer
_cached_agent = None

def get_or_create_agent(model_name: str = None, temperature: float = 0.0):
    global _cached_agent
    if _cached_agent is None or model_name is not None or temperature != 0.0:
        _cached_agent = create_agent(model_name=model_name, temperature=temperature)
    return _cached_agent


def reset_agent_memory(thread_id: str = None):
    """Resets conversation memory and execution store for a given thread or all threads."""
    global _cached_agent, _global_checkpointer
    with _execution_lock:
        if thread_id:
            _execution_store.pop(thread_id, None)
        else:
            _execution_store.clear()
            _global_checkpointer = MemorySaver()
            _cached_agent = None


# ==========================================
# 4. Wrapper Function to Run Queries with Memory & Single Execution
# ==========================================
def ask_agent(
    user_question: str,
    thread_id: str = None,
    model_name: str = None,
    temperature: float = 0.0
) -> dict:
    """
    Invokes the LangGraph AI agent with the user question using thread-based conversation memory.
    Returns structured results including already-executed query data (eliminating duplicate DB calls).

    Returns:
        dict: {
            "answer": str,
            "sql_query": str or None,
            "validation_passed": bool,
            "tool_output": str,
            "messages": list,
            "query_result": dict or None,
            "thread_id": str
        }
    """
    effective_thread_id = thread_id if thread_id else "default_session"

    agent = get_or_create_agent(model_name=model_name, temperature=temperature)
    config = {"configurable": {"thread_id": effective_thread_id}}
    inputs = {"messages": [("user", user_question)]}

    response = agent.invoke(inputs, config=config)

    messages = response.get("messages", [])
    final_answer = messages[-1].content if messages else "No response generated."

    last_sql = None
    validation_passed = True
    tool_output = ""

    # Inspect messages from current/previous turns
    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc.get("name") == "run_sql_query":
                    last_sql = tc.get("args", {}).get("query")

        if getattr(msg, "type", "") == "tool":
            content_str = str(msg.content)
            tool_output += content_str + "\n"
            if "SECURITY ERROR" in content_str:
                validation_passed = False

    # Retrieve the single execution structured result from the tool
    with _execution_lock:
        query_result = _execution_store.get(effective_thread_id)

    # If query was generated, update last_sql and validation from structured result
    if query_result and query_result.get("sql_query"):
        last_sql = query_result["sql_query"]
        validation_passed = query_result.get("validation_passed", True)

    return {
        "answer": final_answer,
        "sql_query": last_sql,
        "validation_passed": validation_passed,
        "tool_output": tool_output,
        "messages": messages,
        "query_result": query_result,
        "thread_id": effective_thread_id
    }


# ==========================================
# 5. CLI (Command Line Interface) Mode
# ==========================================
def print_cli_banner():
    """Prints the startup banner for the CLI."""
    db_status = "Connected" if check_db_health() else "Disconnected (Check DATABASE_URL)"
    if RICH_AVAILABLE:
        banner_text = (
            f"[bold cyan]⚡ ZeroSQL AI[/bold cyan] - [dim]No SQL Required • Plain English to PostgreSQL Copilot[/dim]\n"
            f"[yellow]Database Status:[/yellow] [green]{db_status}[/green]  |  "
            f"[yellow]Model:[/yellow] [magenta]{GROQ_MODEL}[/magenta]\n\n"
            f"[bold]Commands:[/bold]\n"
            f"  • [green]schema[/green] : View database tables and columns\n"
            f"  • [green]seed[/green]   : Seed/reset database with sample data\n"
            f"  • [green]new[/green]    : Start a new conversation (reset memory)\n"
            f"  • [green]clear[/green]  : Clear terminal screen\n"
            f"  • [green]exit[/green]   : Exit the application\n"
            f"  • Or ask any plain English question about your data!"
        )
        console.print(Panel(banner_text, title="⚡ ZeroSQL AI", border_style="cyan", expand=False))
    else:
        print("=" * 60)
        print("⚡ ZeroSQL AI - No SQL Required • Plain English to PostgreSQL Copilot")
        print(f"Database Status: {db_status} | Model: {GROQ_MODEL}")
        print("Commands: 'schema', 'seed', 'new', 'clear', 'exit', or ask any question")
        print("=" * 60)


def show_schema_cli():
    """Displays the formatted schema in the CLI."""
    if RICH_AVAILABLE:
        with console.status("[bold green]Fetching database schema...[/bold green]"):
            schema_text = fetch_schema.invoke({})
        console.print(Panel(schema_text, title="📊 Database Schema", border_style="blue"))
    else:
        print("\n--- DATABASE SCHEMA ---")
        print(fetch_schema.invoke({}))
        print("-----------------------\n")


def seed_db_cli():
    """Seeds the database and prints the result in CLI."""
    if RICH_AVAILABLE:
        with console.status("[bold yellow]Seeding database...[/bold yellow]"):
            success, msg = seed_database()
        if success:
            console.print(f"[bold green]✓ {msg}[/bold green]")
        else:
            console.print(f"[bold red]✗ {msg}[/bold red]")
    else:
        success, msg = seed_database()
        print(f"[{'SUCCESS' if success else 'ERROR'}] {msg}")


def cli():
    """Interactive Command Line Interface for the AI SQL Agent with multi-turn memory."""
    print_cli_banner()
    cli_thread_id = str(uuid.uuid4())

    while True:
        try:
            if RICH_AVAILABLE:
                user_input = Prompt.ask("\n[bold cyan]ZeroSQL[/bold cyan]").strip()
            else:
                user_input = input("\nZeroSQL > ").strip()

            if not user_input:
                continue

            # Command routing
            lower_input = user_input.lower()
            if lower_input in ["exit", "quit", "q"]:
                if RICH_AVAILABLE:
                    console.print("[bold yellow]👋 Goodbye![/bold yellow]")
                else:
                    print("Goodbye!")
                break

            elif lower_input in ["new", "reset"]:
                cli_thread_id = str(uuid.uuid4())
                reset_agent_memory(cli_thread_id)
                if RICH_AVAILABLE:
                    console.print("[bold cyan]🔄 New conversation thread started. Memory cleared.[/bold cyan]")
                else:
                    print("New conversation thread started. Memory cleared.")
                continue

            elif lower_input in ["clear", "cls"]:
                os.system("clear" if os.name != "nt" else "cls")
                print_cli_banner()
                continue

            elif lower_input == "schema":
                show_schema_cli()
                continue

            elif lower_input == "seed":
                seed_db_cli()
                continue

            elif lower_input in ["help", "?"]:
                print_cli_banner()
                continue

            # Run agent query with multi-turn thread memory
            if RICH_AVAILABLE:
                with console.status("[bold green]Thinking & querying database...[/bold green]", spinner="dots"):
                    result = ask_agent(user_input, thread_id=cli_thread_id)

                # Show generated SQL query if any
                if result.get("sql_query"):
                    sql_code = result["sql_query"]
                    syntax = Syntax(sql_code, "sql", theme="monokai", line_numbers=False)
                    console.print(Panel(syntax, title="⚡ Generated SQL Query", border_style="yellow"))

                # Show validation warning if security error occurred
                if not result.get("validation_passed", True):
                    console.print(Panel("[bold red]⚠️ Security Alert: Destructive/forbidden query blocked![/bold red]", border_style="red"))

                # Show final answer
                console.print(Panel(Markdown(result["answer"]), title="💡 Answer", border_style="green"))

            else:
                print("\nThinking & querying database...")
                result = ask_agent(user_input, thread_id=cli_thread_id)

                if result.get("sql_query"):
                    print(f"\n[Generated SQL]:\n{result['sql_query']}\n")

                if not result.get("validation_passed", True):
                    print("[SECURITY WARNING]: Destructive or invalid query was blocked.")

                print(f"\n[Answer]:\n{result['answer']}\n")

        except KeyboardInterrupt:
            if RICH_AVAILABLE:
                console.print("\n[yellow]Session interrupted. Exiting...[/yellow]")
            else:
                print("\nSession interrupted. Exiting...")
            break
        except Exception as err:
            if RICH_AVAILABLE:
                console.print(f"[bold red]Error:[/bold red] {str(err)}")
            else:
                print(f"Error: {str(err)}")


if __name__ == "__main__":
    cli()
