import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_READONLY_URL = os.getenv("DATABASE_READONLY_URL", DATABASE_URL)
DATABASE_ADMIN_URL = os.getenv("DATABASE_ADMIN_URL", DATABASE_URL)


def _resolve_connection_url(admin: bool = False) -> str:
    """
    Resolves the target database connection URL from environment variables.
    Supports DATABASE_ADMIN_URL / DATABASE_READONLY_URL / DATABASE_URL
    as well as discrete DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD variables.
    """
    if admin:
        url = os.getenv("DATABASE_ADMIN_URL") or os.getenv("DATABASE_URL") or DATABASE_ADMIN_URL or DATABASE_URL
    else:
        url = os.getenv("DATABASE_READONLY_URL") or os.getenv("DATABASE_URL") or DATABASE_READONLY_URL or DATABASE_URL

    if not url:
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT", "5432")
        name = os.getenv("DB_NAME")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        if host and name:
            import urllib.parse
            encoded_pass = urllib.parse.quote(password or "", safe="")
            auth = f"{user}:{encoded_pass}@" if user else ""
            url = f"postgresql://{auth}{host}:{port}/{name}"

    return url or ""


def get_readonly_db_connection():
    """
    Establishes and returns a dedicated read-only connection for the AI SQL Agent.
    Uses dict_row to return query results as dictionaries.
    Strictly enforces transaction read-only mode at the connection level.
    """
    target_url = _resolve_connection_url(admin=False)
    if not target_url:
        raise ValueError("DATABASE_URL / DATABASE_READONLY_URL is not set in the environment variables (.env).")
    try:
        conn = psycopg.connect(
            target_url,
            row_factory=dict_row
        )
        conn.read_only = True
        return conn
    except Exception as error:
        raise ConnectionError(f"Unable to connect to PostgreSQL (Read-Only). Error: {str(error)}")


def get_admin_db_connection():
    """
    Establishes and returns a write-capable connection for backend administrative
    operations (such as database seeding and future dataset ingestion).
    Uses dict_row to return query results as dictionaries.
    IMPORTANT: This connection must NOT be exposed to the AI Agent.
    """
    target_url = _resolve_connection_url(admin=True)
    if not target_url:
        raise ValueError("DATABASE_URL / DATABASE_ADMIN_URL is not set in the environment variables (.env).")
    try:
        conn = psycopg.connect(
            target_url,
            row_factory=dict_row
        )
        return conn
    except Exception as error:
        raise ConnectionError(f"Unable to connect to PostgreSQL (Admin). Error: {str(error)}")


def get_db_connection(readonly: bool = False):
    """
    Backward-compatible connection factory.
    - If readonly is True: returns a read-only connection (for AI Agent / safe queries).
    - If readonly is False: returns a write-enabled connection (for admin / seeding).
    """
    if readonly:
        return get_readonly_db_connection()
    else:
        return get_admin_db_connection()


def check_db_health() -> bool:
    """
    Checks whether the database connection is active and responding.
    Returns True if healthy, False otherwise.
    """
    try:
        with get_db_connection(readonly=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1;")
                return True
    except Exception:
        return False


def get_db_schema() -> str:
    """
    Retrieves and formats the complete database schema for all public tables,
    including table names, columns, and data types.
    """
    try:
        with get_db_connection(readonly=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        table_name, 
                        column_name, 
                        data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    ORDER BY table_name, ordinal_position;
                """)
                rows = cursor.fetchall()
                if not rows:
                    return "No tables found in the public schema of the database."

                schema_map = {}
                for row in rows:
                    table = row["table_name"]
                    col_info = f"{row['column_name']} ({row['data_type']})"
                    schema_map.setdefault(table, []).append(col_info)

                formatted = []
                for table, columns in schema_map.items():
                    formatted.append(f"Table '{table}':\n  - " + "\n  - ".join(columns))

                return "\n\n".join(formatted)
    except Exception as error:
        return f"Error fetching database schema: {str(error)}"


def execute_query(sql_query: str, readonly: bool = True) -> list[dict]:
    """
    Executes a SQL query against PostgreSQL and returns the rows as a list of dicts.
    By default, uses a read-only connection to guarantee no state-modifying operations occur.
    """
    try:
        with get_db_connection(readonly=readonly) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_query)
                # If query returns rows (e.g. SELECT, WITH)
                if cursor.description is not None:
                    return cursor.fetchall()
                if not readonly:
                    conn.commit()
                return []
    except Exception as error:
        raise RuntimeError(f"Database query execution failed: {str(error)}")


def seed_database() -> tuple[bool, str]:
    """
    Seeds the PostgreSQL database with sample tables (departments, employees,
    students, users, products, orders) and initial records.
    Uses a write-enabled connection.
    """
    sql_statements = [
        # Drop existing tables cleanly
        "DROP TABLE IF EXISTS orders CASCADE;",
        "DROP TABLE IF EXISTS products CASCADE;",
        "DROP TABLE IF EXISTS users CASCADE;",
        "DROP TABLE IF EXISTS students CASCADE;",
        "DROP TABLE IF EXISTS employees CASCADE;",
        "DROP TABLE IF EXISTS departments CASCADE;",

        # 1. Departments Table
        """
        CREATE TABLE departments (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            location VARCHAR(100),
            budget NUMERIC(12, 2)
        );
        """,
        """
        INSERT INTO departments (name, location, budget) VALUES
        ('Engineering', 'San Francisco', 1500000.00),
        ('Marketing', 'New York', 800000.00),
        ('Human Resources', 'Chicago', 400000.00),
        ('Sales', 'Austin', 1200000.00),
        ('Finance', 'New York', 900000.00);
        """,

        # 2. Employees Table
        """
        CREATE TABLE employees (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE,
            salary NUMERIC(10, 2),
            department_id INT REFERENCES departments(id),
            hire_date DATE
        );
        """,
        """
        INSERT INTO employees (name, email, salary, department_id, hire_date) VALUES
        ('Rahul Verma', 'rahul@example.com', 95000.00, 1, '2021-03-15'),
        ('Aman Sharma', 'aman@example.com', 88000.00, 1, '2022-01-10'),
        ('Priya Patel', 'priya@example.com', 92000.00, 1, '2020-06-20'),
        ('Neha Gupta', 'neha@example.com', 75000.00, 2, '2021-09-01'),
        ('Vikram Singh', 'vikram@example.com', 72000.00, 2, '2022-05-12'),
        ('Ananya Roy', 'ananya@example.com', 68000.00, 3, '2019-11-05'),
        ('Rohan Mehta', 'rohan@example.com', 85000.00, 4, '2021-02-28'),
        ('Kavya Nair', 'kavya@example.com', 90000.00, 4, '2020-08-14'),
        ('Siddharth Kumar', 'siddharth@example.com', 98000.00, 5, '2018-04-01'),
        ('Deepak Joshi', 'deepak@example.com', 65000.00, 3, '2023-02-10');
        """,

        # 3. Students Table
        """
        CREATE TABLE students (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE,
            course VARCHAR(100),
            marks INT,
            enrollment_date DATE
        );
        """,
        """
        INSERT INTO students (name, email, course, marks, enrollment_date) VALUES
        ('Rahul Sharma', 'rahul.s@example.com', 'Computer Science', 98, '2023-08-01'),
        ('Aman Verma', 'aman.v@example.com', 'Computer Science', 95, '2023-08-01'),
        ('Priya Singh', 'priya.s@example.com', 'Data Science', 94, '2023-08-01'),
        ('Neha Agarwal', 'neha.a@example.com', 'Data Science', 91, '2023-08-01'),
        ('Karan Malhotra', 'karan.m@example.com', 'AI', 89, '2023-08-01'),
        ('Simran Kaur', 'simran.k@example.com', 'Computer Science', 87, '2023-08-01'),
        ('Arjun Reddy', 'arjun.r@example.com', 'Cybersecurity', 85, '2023-08-01'),
        ('Ishaan Iyer', 'ishaan.i@example.com', 'AI', 82, '2023-08-01'),
        ('Tanya Sen', 'tanya.s@example.com', 'Cybersecurity', 78, '2023-08-01'),
        ('Varun Rao', 'varun.r@example.com', 'Data Science', 72, '2023-08-01');
        """,

        # 4. Users Table
        """
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE,
            city VARCHAR(50)
        );
        """,
        """
        INSERT INTO users (name, email, city) VALUES
        ('Aarav Mehta', 'aarav@gmail.com', 'Delhi'),
        ('Diya Kapoor', 'diya@gmail.com', 'Mumbai'),
        ('Kabir Das', 'kabir@yahoo.com', 'Delhi'),
        ('Myra Joshi', 'myra@hotmail.com', 'Bangalore'),
        ('Vihaan Trivedi', 'vihaan@gmail.com', 'Hyderabad'),
        ('Aditi Rao', 'aditi@gmail.com', 'Delhi'),
        ('Reyansh Bhatia', 'reyansh@gmail.com', 'Chennai');
        """,

        # 5. Products Table
        """
        CREATE TABLE products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            category VARCHAR(50),
            price NUMERIC(10, 2),
            stock_quantity INT
        );
        """,
        """
        INSERT INTO products (name, category, price, stock_quantity) VALUES
        ('MacBook Pro M3', 'Electronics', 1999.99, 25),
        ('iPhone 15 Pro', 'Electronics', 1199.99, 50),
        ('Dell XPS 15', 'Electronics', 1499.99, 15),
        ('Ergonomic Chair', 'Furniture', 299.99, 40),
        ('Standing Desk', 'Furniture', 499.99, 20),
        ('Mechanical Keyboard', 'Accessories', 129.99, 100),
        ('Noise Cancelling Headphones', 'Accessories', 249.99, 60);
        """,

        # 6. Orders Table
        """
        CREATE TABLE orders (
            id SERIAL PRIMARY KEY,
            user_id INT REFERENCES users(id),
            product_id INT REFERENCES products(id),
            quantity INT,
            total_amount NUMERIC(10, 2),
            order_date DATE
        );
        """,
        """
        INSERT INTO orders (user_id, product_id, quantity, total_amount, order_date) VALUES
        (1, 1, 1, 1999.99, '2024-01-15'),
        (1, 6, 2, 259.98, '2024-01-16'),
        (2, 2, 1, 1199.99, '2024-01-20'),
        (3, 4, 2, 599.98, '2024-02-01'),
        (4, 5, 1, 499.99, '2024-02-05'),
        (5, 3, 1, 1499.99, '2024-02-15'),
        (6, 7, 1, 249.99, '2024-03-01');
        """
    ]
    try:
        with get_db_connection(readonly=False) as conn:
            with conn.cursor() as cursor:
                for statement in sql_statements:
                    cursor.execute(statement)
            conn.commit()
        return True, "Database seeded successfully!"
    except Exception as error:
        return False, f"Failed to seed database: {str(error)}"


def get_tables_list() -> list[str]:
    """Returns a list of all table names in the public schema."""
    try:
        with get_db_connection(readonly=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                """)
                rows = cursor.fetchall()
                return [row["table_name"] for row in rows]
    except Exception:
        return []


def get_table_details(table_name: str) -> list[dict]:
    """Returns column information for a specific table."""
    try:
        with get_db_connection(readonly=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position;
                """, (table_name,))
                return cursor.fetchall()
    except Exception:
        return []


def get_table_row_counts() -> dict[str, int]:
    """Returns a mapping of table_name -> row_count for all public tables."""
    counts = {}
    tables = get_tables_list()
    if not tables:
        return counts
    try:
        with get_db_connection(readonly=True) as conn:
            with conn.cursor() as cursor:
                for table in tables:
                    cursor.execute(f'SELECT COUNT(*) as count FROM "{table}";')
                    res = cursor.fetchone()
                    counts[table] = res["count"] if res else 0
    except Exception:
        pass
    return counts


def get_db_server_info() -> dict:
    """Returns information about the connected PostgreSQL database server."""
    try:
        with get_db_connection(readonly=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT version() as version, current_database() as db_name, current_user as user_name;")
                row = cursor.fetchone()
                if row:
                    return {
                        "version": row.get("version", "Unknown"),
                        "database": row.get("db_name", "Unknown"),
                        "user": row.get("user_name", "Unknown"),
                        "status": "Connected"
                    }
    except Exception as e:
        return {
            "version": "Unavailable",
            "database": "Unknown",
            "user": "Unknown",
            "status": f"Error: {str(e)}"
        }
    return {"status": "Disconnected"}


if __name__ == "__main__":
    print("Testing Database Module with Read-Only Connections...")
    health = check_db_health()
    print(f"Health Status: {'Healthy' if health else 'Unhealthy'}")
    
    if health:
        print("\n--- Current Schema ---")
        print(get_db_schema())
        print("\n--- Server Info ---")
        print(get_db_server_info())
