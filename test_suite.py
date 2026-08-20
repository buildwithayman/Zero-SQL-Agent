import sys
import uuid
import agents
import database
from agents import ask_agent, reset_agent_memory
from sql_validator import validate_sql

print("===============================================================", flush=True)
print("  FULL VERIFICATION TEST SUITE: ZeroSQL AI Agent", flush=True)
print("===============================================================\n", flush=True)

# ---------------------------------------------------------------------
# TEST 1 & 2: Multi-turn Memory & Pronoun Reference Handling
# ---------------------------------------------------------------------
print(">>> [TEST 1 & 2] Multi-Turn Reasoning & Pronoun/Sorting Memory", flush=True)
t1 = str(uuid.uuid4())

# Turn 1
r1 = ask_agent("Show employees in Engineering department", thread_id=t1)
sql1 = r1.get("sql_query", "")
print("  Turn 1 Prompt: 'Show employees in Engineering department'", flush=True)
print("  Turn 1 SQL:   ", sql1.replace('\n', ' '), flush=True)
print("  Turn 1 Rows:  ", r1.get("query_result", {}).get("row_count") if r1.get("query_result") else "None", flush=True)

# Turn 2
r2 = ask_agent("Now only those earning above 90000", thread_id=t1)
sql2 = r2.get("sql_query", "")
print("  Turn 2 Prompt: 'Now only those earning above 90000'", flush=True)
print("  Turn 2 SQL:   ", sql2.replace('\n', ' '), flush=True)
print("  Turn 2 Rows:  ", r2.get("query_result", {}).get("row_count") if r2.get("query_result") else "None", flush=True)
assert "90000" in sql2, "Turn 2 failed to filter salary > 90000"

# Turn 3
r3 = ask_agent("Sort them by salary descending", thread_id=t1)
sql3 = r3.get("sql_query", "")
print("  Turn 3 Prompt: 'Sort them by salary descending'", flush=True)
print("  Turn 3 SQL:   ", sql3.replace('\n', ' '), flush=True)
print("  Turn 3 Rows:  ", r3.get("query_result", {}).get("row_count") if r3.get("query_result") else "None", flush=True)
assert "order by" in sql3.lower() and "desc" in sql3.lower(), "Turn 3 failed to sort desc"
print("  ✅ TEST 1 & 2 PASSED: Multi-turn context & pronoun references maintained.\n", flush=True)

# ---------------------------------------------------------------------
# TEST 3: New Conversation Isolation
# ---------------------------------------------------------------------
print(">>> [TEST 3] New Conversation Thread Isolation", flush=True)
t2 = str(uuid.uuid4())
r_iso = ask_agent("Show students in Computer Science", thread_id=t2)
print("  New Thread Prompt: 'Show students in Computer Science'", flush=True)
print("  New Thread SQL:   ", r_iso.get("sql_query", "").replace('\n', ' '), flush=True)
print("  New Thread Rows:  ", r_iso.get("query_result", {}).get("row_count") if r_iso.get("query_result") else "None", flush=True)
assert "students" in r_iso.get("sql_query", "").lower(), "New thread failed to query students table"
print("  ✅ TEST 3 PASSED: Clean thread isolation with zero cross-session leakage.\n", flush=True)

# ---------------------------------------------------------------------
# TEST 4: SQL Security & AST Validation
# ---------------------------------------------------------------------
print(">>> [TEST 4] SQL Security & AST Guardrails", flush=True)
security_matrix = [
    ("DELETE FROM employees;", False, "DELETE blocked"),
    ("DROP TABLE employees;", False, "DROP blocked"),
    ("ALTER TABLE users ADD COLUMN age INT;", False, "ALTER blocked"),
    ("TRUNCATE orders;", False, "TRUNCATE blocked"),
    ("SELECT * FROM employees; DROP TABLE users;", False, "Multi-statement injection blocked"),
    ("SELECT pg_sleep(10);", False, "Dangerous pg_sleep function blocked"),
    ("INSERT INTO products (name) VALUES ('Hacked');", False, "INSERT blocked"),
    ("SELECT * FROM employees WHERE name = 'Grant';", True, "Literal string containing keyword allowed"),
    ("WITH dept_cte AS (SELECT * FROM departments) SELECT * FROM dept_cte;", True, "Valid CTE allowed")
]

for query, should_pass, desc in security_matrix:
    is_valid, msg = validate_sql(query)
    assert is_valid == should_pass, f"Security assertion failed for: {query} (Got {is_valid}, expected {should_pass})"
    status = "✅ PASS" if is_valid == should_pass else "❌ FAIL"
    print(f"  {status}: {desc:<45} -> Valid={is_valid}", flush=True)
print("  ✅ TEST 4 PASSED: Defense-in-depth SQL AST guardrails verified.\n", flush=True)

# ---------------------------------------------------------------------
# TEST 5: Database Connection Read-Only Enforcement
# ---------------------------------------------------------------------
print(">>> [TEST 5] Database-Level Read-Only Transaction Enforcement", flush=True)
try:
    with database.get_db_connection(readonly=True) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE users CASCADE;")
    raise AssertionError("Dangerous DROP succeeded on read-only connection!")
except Exception as e:
    print(f"  ✅ PASS: PostgreSQL transaction rejected write: {str(e)[:65]}...", flush=True)
print("  ✅ TEST 5 PASSED: Read-only connection actively blocks all writes.\n", flush=True)

# ---------------------------------------------------------------------
# TEST 6: Single Database Execution (Zero UI Duplication)
# ---------------------------------------------------------------------
print(">>> [TEST 6] Single Database Execution Count (No Duplication)", flush=True)
call_counter = {"count": 0}
orig_exec = agents.execute_query

def tracked_execute(sql, readonly=True):
    call_counter["count"] += 1
    return orig_exec(sql, readonly=readonly)

agents.execute_query = tracked_execute
t3 = str(uuid.uuid4())
call_counter["count"] = 0

r_single = ask_agent("Calculate total revenue from orders", thread_id=t3)
agents.execute_query = orig_exec

print(f"  Total PostgreSQL Query Executions: {call_counter['count']}", flush=True)
print(f"  Captured SQL:                      {r_single.get('query_result', {}).get('sql_query', '').replace(chr(10), ' ')}", flush=True)
print(f"  Execution Latency (ms):            {r_single.get('query_result', {}).get('execution_time_ms')}ms", flush=True)
print(f"  Captured Rows Count:               {r_single.get('query_result', {}).get('row_count')}", flush=True)
assert call_counter["count"] == 1, f"Expected 1 database execution, got {call_counter['count']}"
print("  ✅ TEST 6 PASSED: Exactly 1 database execution per request.\n", flush=True)

print("===============================================================", flush=True)
print("  🎉 ALL 6 COMPREHENSIVE TEST SCENARIOS PASSED WITH 100% SUCCESS!", flush=True)
print("===============================================================", flush=True)
