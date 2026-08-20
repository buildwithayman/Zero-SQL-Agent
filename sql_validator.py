
"""
SQL Security Validator for AI SQL Agent
Defense-in-depth SQL parsing, AST inspection, multi-statement rejection,
and dangerous function blocking.
"""

import sqlparse
from sqlparse.tokens import Literal, Keyword, DML, DDL

# Forbidden SQL keywords (DML, DDL, DCL, TCL, administration)
FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "COPY",
    "VACUUM", "REINDEX", "COMMENT", "CLUSTER", "REFRESH", "ANALYZE",
    "BEGIN", "COMMIT", "ROLLBACK", "SAVEPOINT", "SET", "SHOW",
    "CALL", "DO", "LOCK", "DISCARD", "LISTEN", "NOTIFY", "RESET"
]

# Dangerous PostgreSQL functions and system commands that could cause side-effects
DANGEROUS_FUNCTIONS = [
    "pg_sleep", "pg_terminate_backend", "pg_cancel_backend",
    "pg_reload_conf", "pg_read_file", "pg_write_file",
    "pg_read_binary_file", "lo_import", "lo_export",
    "dblink", "dblink_exec", "pg_exec", "current_setting", "set_config"
]

FORBIDDEN_KEYWORDS_SET = set(FORBIDDEN_KEYWORDS)
DANGEROUS_FUNCTIONS_SET = set(DANGEROUS_FUNCTIONS)


def validate_sql(sql_query: str) -> tuple[bool, str]:
    """
    Validates that a SQL query is strictly a single, read-only SELECT or WITH statement.
    Uses sqlparse for AST/token stream inspection to prevent keyword-in-string false positives
    and block multi-statement injection attacks.

    Returns:
        tuple[bool, str]: (is_valid, validation_message_or_error)
    """
    if not sql_query or not sql_query.strip():
        return False, "Security Error: Empty SQL query."

    raw_query = sql_query.strip()

    # 1. Strip comments (single-line -- and multi-line /* */) to prevent comment-based evasion
    cleaned_query = sqlparse.format(raw_query, strip_comments=True).strip()
    if not cleaned_query:
        return False, "Security Error: Query contains only comments or whitespace."

    # 2. Check for multiple statements
    statements = sqlparse.parse(cleaned_query)
    non_empty_statements = [s for s in statements if str(s).strip().strip(";")]

    if len(non_empty_statements) == 0:
        return False, "Security Error: No executable SQL statement found."

    if len(non_empty_statements) > 1:
        return False, f"Security Error: Multiple SQL statements ({len(non_empty_statements)}) detected. Only single queries are allowed."

    stmt = non_empty_statements[0]

    # 3. Verify the root statement starts with SELECT or WITH (CTE)
    first_token = None
    for token in stmt.tokens:
        if not token.is_whitespace:
            first_token = token
            break

    if not first_token:
        return False, "Security Error: Statement contains no tokens."

    first_word = first_token.value.upper()
    if first_word not in ("SELECT", "WITH"):
        return False, f"Security Error: Statement type '{first_word}' is forbidden. Only SELECT and WITH statements are allowed."

    # 4. Recursively inspect all tokens in the AST
    def inspect_token(token) -> tuple[bool, str]:
        # Allow string literals and numeric literals without inspecting their content as keywords
        # (e.g. WHERE name = 'Grant' or WHERE status = 'Delete')
        if token.ttype in (Literal.String.Single, Literal.String.Symbol, Literal.Number.Integer, Literal.Number.Float):
            return True, ""

        token_str = token.value.upper() if token.value else ""
        clean_token = token_str.strip("();,\'\" ")

        # Check forbidden keywords
        if clean_token in FORBIDDEN_KEYWORDS_SET:
            return False, f"Security Error: Forbidden keyword '{clean_token}' detected."

        # Check dangerous functions
        if clean_token.lower() in DANGEROUS_FUNCTIONS_SET:
            return False, f"Security Error: Dangerous function '{clean_token.lower()}' detected."

        # Recursively inspect sub-tokens for compound structures (functions, parenthesized queries, etc.)
        if hasattr(token, "tokens"):
            for sub_token in token.tokens:
                is_ok, reason = inspect_token(sub_token)
                if not is_ok:
                    return False, reason

        return True, ""

    for token in stmt.tokens:
        is_ok, reason = inspect_token(token)
        if not is_ok:
            return False, reason

    return True, "Validation passed."


def is_query(sql_query: str) -> bool:
    """
    Backward-compatible boolean validator.
    Returns True if query passes all security and read-only checks, False otherwise.
    """
    is_valid, _ = validate_sql(sql_query)
    return is_valid


if __name__ == "__main__":
    test_queries = [
        ("SELECT * FROM employees WHERE name = 'Grant';", True),
        ("SELECT 1; DROP TABLE users;", False),
        ("WITH active AS (SELECT * FROM users) SELECT * FROM active;", True),
        ("INSERT INTO employees (name) VALUES ('Test');", False),
        ("UPDATE employees SET salary = 100000;", False),
        ("DELETE FROM orders;", False),
        ("SELECT pg_sleep(5);", False),
        ("SELECT * FROM employees -- comment\n WHERE salary > 50000;", True),
        ("SELECT 1; SELECT 2;", False),
    ]

    print("Running SQL Validator Tests:")
    for query, expected in test_queries:
        valid, msg = validate_sql(query)
        status = "✓ PASS" if valid == expected else "✗ FAIL"
        print(f"[{status}] {query[:40]:<40} -> Valid: {valid} ({msg})")
