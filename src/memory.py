from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from collections.abc import Iterator
from typing import Any


def _database_path() -> Path:
    return Path.home() / ".wayfarer" / "travel_memory.sqlite3"


def _supabase_client() -> Any | None:
    url = os.getenv("SUPABASE_URL")
    secret_key = os.getenv("SUPABASE_SECRET_KEY")
    if not url and not secret_key:
        return None
    if not url or not secret_key:
        raise RuntimeError(
            "Supabase is only partially configured. Set both SUPABASE_URL and "
            "SUPABASE_SECRET_KEY, or remove both to use local SQLite."
        )

    from supabase import create_client

    return create_client(url, secret_key)


def _connect() -> sqlite3.Connection:
    path = _database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS travel_memory (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            summary TEXT NOT NULL DEFAULT '',
            preferences TEXT NOT NULL DEFAULT '{}'
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS saved_trips (
            id TEXT PRIMARY KEY,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            travel_date TEXT NOT NULL,
            preferences TEXT NOT NULL,
            itinerary TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        "INSERT OR IGNORE INTO travel_memory (id, summary, preferences) VALUES (1, '', '{}')"
    )
    connection.commit()
    return connection


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    connection = _connect()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def load_memory() -> dict[str, Any]:
    client = _supabase_client()
    if client:
        row = (
            client.table("travel_memory")
            .select("summary, preferences")
            .eq("id", 1)
            .maybe_single()
            .execute()
            .data
        )
        if not row:
            return {"summary": "", "preferences": {}}
        preferences = row.get("preferences", {})
        return {
            "summary": row.get("summary", ""),
            "preferences": preferences if isinstance(preferences, dict) else {},
        }

    with _connection() as connection:
        row = connection.execute(
            "SELECT summary, preferences FROM travel_memory WHERE id = 1"
        ).fetchone()
    if row is None:
        return {"summary": "", "preferences": {}}
    try:
        preferences = json.loads(row["preferences"])
    except json.JSONDecodeError:
        preferences = {}
    if not isinstance(preferences, dict):
        preferences = {}
    return {"summary": row["summary"], "preferences": preferences}


def save_preferences(preferences: dict[str, Any], summary: str) -> None:
    client = _supabase_client()
    if client:
        client.table("travel_memory").upsert(
            {"id": 1, "summary": summary, "preferences": preferences}
        ).execute()
        return

    serialized = json.dumps(preferences, ensure_ascii=True)
    with _connection() as connection:
        connection.execute(
            "UPDATE travel_memory SET summary = ?, preferences = ? WHERE id = 1",
            (summary, serialized),
        )


def clear_memory() -> None:
    client = _supabase_client()
    if client:
        client.table("travel_memory").upsert(
            {"id": 1, "summary": "", "preferences": {}}
        ).execute()
        return

    with _connection() as connection:
        connection.execute(
            "UPDATE travel_memory SET summary = '', preferences = '{}' WHERE id = 1"
        )


def save_trip(
    origin: str,
    destination: str,
    travel_date: str,
    preferences: dict[str, Any],
    itinerary: list[dict[str, str]],
) -> str:
    trip_id = str(uuid.uuid4())
    trip = {
        "id": trip_id,
        "origin": origin,
        "destination": destination,
        "travel_date": travel_date,
        "preferences": preferences,
        "itinerary": itinerary,
    }
    client = _supabase_client()
    if client:
        client.table("saved_trips").insert(trip).execute()
        return trip_id

    with _connection() as connection:
        connection.execute(
            """
            INSERT INTO saved_trips
                (id, origin, destination, travel_date, preferences, itinerary)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                trip_id,
                origin,
                destination,
                travel_date,
                json.dumps(preferences, ensure_ascii=True),
                json.dumps(itinerary, ensure_ascii=True),
            ),
        )
    return trip_id


def list_saved_trips() -> list[dict[str, Any]]:
    client = _supabase_client()
    if client:
        response = (
            client.table("saved_trips")
            .select("id, origin, destination, travel_date, preferences, itinerary, created_at")
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []

    with _connection() as connection:
        rows = connection.execute(
            """
            SELECT id, origin, destination, travel_date, preferences, itinerary, created_at
            FROM saved_trips ORDER BY created_at DESC, rowid DESC
            """
        ).fetchall()
    return [
        {
            **dict(row),
            "preferences": json.loads(row["preferences"]),
            "itinerary": json.loads(row["itinerary"]),
        }
        for row in rows
    ]


def delete_saved_trip(trip_id: str) -> None:
    client = _supabase_client()
    if client:
        client.table("saved_trips").delete().eq("id", trip_id).execute()
        return

    with _connection() as connection:
        connection.execute("DELETE FROM saved_trips WHERE id = ?", (trip_id,))
