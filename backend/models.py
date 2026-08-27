from database import get_connection, export_to_csv

def create_url(original_url, short_code, created_at):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO urls
            (original_url, short_code, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (original_url, short_code, created_at, created_at)
        )
        conn.commit()
        row_id = cursor.lastrowid
    export_to_csv()
    return row_id

def get_by_code(short_code):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM urls WHERE short_code = ?",
            (short_code,)
        ).fetchone()

def get_by_id(url_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM urls WHERE id = ?",
            (url_id,)
        ).fetchone()

def get_all(search=""):
    with get_connection() as conn:
        if search:
            pattern = f"%{search}%"
            return conn.execute(
                """
                SELECT * FROM urls
                WHERE original_url LIKE ? OR short_code LIKE ?
                ORDER BY id DESC
                """,
                (pattern, pattern)
            ).fetchall()

        return conn.execute(
            "SELECT * FROM urls ORDER BY id DESC"
        ).fetchall()

def update_url(url_id, original_url, updated_at):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE urls
            SET original_url = ?, updated_at = ?
            WHERE id = ?
            """,
            (original_url, updated_at, url_id)
        )
        conn.commit()
        rowcount = cursor.rowcount
    export_to_csv()
    return rowcount

def delete_url(url_id):
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM urls WHERE id = ?",
            (url_id,)
        )
        conn.commit()
        rowcount = cursor.rowcount
    export_to_csv()
    return rowcount

def clear_history():
    with get_connection() as conn:
        conn.execute("DELETE FROM urls")
        conn.commit()
    export_to_csv()

def increment_clicks(short_code):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE urls
            SET click_count = click_count + 1
            WHERE short_code = ?
            """,
            (short_code,)
        )
        conn.commit()
    export_to_csv()


def get_stats():
    with get_connection() as conn:
        total_urls = conn.execute(
            "SELECT COUNT(*) AS count FROM urls"
        ).fetchone()["count"]

        total_clicks = conn.execute(
            "SELECT COALESCE(SUM(click_count), 0) AS count FROM urls"
        ).fetchone()["count"]

        return {
            "total_urls": total_urls,
            "total_clicks": total_clicks
        }
