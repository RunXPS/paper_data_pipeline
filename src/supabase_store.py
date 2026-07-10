import os
from datetime import datetime

import psycopg2
from psycopg2.extras import Json, RealDictCursor, execute_values

TABLE_NAME = "accumulated_papers"


def _get_db_url() -> str:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is missing. Cannot connect to Supabase.")
    return db_url


def get_week_key() -> str:
    """Return ISO week key (e.g. 2026-W28) for grouping papers before Sunday email."""
    return datetime.today().strftime("%G-W%V")


def _row_to_paper(row: dict) -> dict:
    return {
        "title": row["title"],
        "published": row["published"],
        "summary": row["summary"],
        "link": row["link"],
        "screener_reason": row["screener_reason"],
        "deep_analysis": row["deep_analysis"],
    }


def load_accumulated_papers(week_key: str) -> list[dict]:
    query = f"""
        SELECT title, published, summary, link, screener_reason, deep_analysis
        FROM {TABLE_NAME}
        WHERE week_key = %s
    """
    with psycopg2.connect(_get_db_url()) as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (week_key,))
            rows = cursor.fetchall()
    return [_row_to_paper(row) for row in rows]


def save_papers(papers: list[dict], week_key: str) -> None:
    if not papers:
        return

    records = [
        (
            week_key,
            paper["title"],
            paper.get("published"),
            paper.get("summary"),
            paper.get("link"),
            paper.get("screener_reason"),
            Json(paper.get("deep_analysis")),
        )
        for paper in papers
    ]

    insert_sql = f"""
        INSERT INTO {TABLE_NAME}
            (week_key, title, published, summary, link, screener_reason, deep_analysis)
        VALUES %s
    """

    with psycopg2.connect(_get_db_url()) as connection:
        with connection.cursor() as cursor:
            execute_values(cursor, insert_sql, records, page_size=100)
        connection.commit()

    print(f"Saved {len(records)} paper(s) to Supabase for week {week_key}.")


def clear_week(week_key: str) -> None:
    with psycopg2.connect(_get_db_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE week_key = %s", (week_key,))
        connection.commit()
    print(f"Cleared accumulated papers for week {week_key}.")
