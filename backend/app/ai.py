"""Turn raw text into structured tasks / finance entries / journal entries via local Ollama."""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from zoneinfo import ZoneInfo

import httpx
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app import models
from app.config import APP_TIMEZONE, OLLAMA_MODEL, OLLAMA_URL


class ParsedTask(BaseModel):
    title: str
    description: str | None = None
    due_at: datetime | None = Field(default=None, description="Local ISO 8601, e.g. 2026-10-20T17:00:00")
    priority: int = Field(default=2, ge=1, le=3)


class ParsedFinance(BaseModel):
    kind: Literal["income", "expense"]
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = "USD"
    category: str | None = None
    description: str | None = None
    occurred_on: date | None = None


class ParsedJournal(BaseModel):
    content: str
    mood: int | None = Field(default=None, ge=1, le=5)


class ParsedOutput(BaseModel):
    tasks: list[ParsedTask] = []
    finance: list[ParsedFinance] = []
    journal: list[ParsedJournal] = []


SYSTEM_PROMPT = """You extract structured data from a person's casual notes.
Current local date/time: {now} ({tz}).
Return JSON with three lists: tasks, finance, journal. Any list may be empty.
- tasks: things to do or remember. Resolve relative dates ("tomorrow 5pm", "next Friday") to a local ISO 8601 due_at. priority 1=high, 2=normal, 3=low.
- finance: money spent or received. amount is a positive number; kind is "expense" or "income". Do not invent amounts.
- journal: reflections or feelings worth recording. mood is 1 (awful) to 5 (great) only if clearly implied.
Only extract what is actually stated. Do not invent items."""


async def call_ollama(text: str) -> ParsedOutput:
    tz = ZoneInfo(APP_TIMEZONE)
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "format": ParsedOutput.model_json_schema(),  # constrains output to our schema
        "options": {"temperature": 0},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT.format(
                now=datetime.now(tz).strftime("%A %Y-%m-%d %H:%M"), tz=APP_TIMEZONE)},
            {"role": "user", "content": text},
        ],
    }
    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
        resp.raise_for_status()
    return ParsedOutput.model_validate_json(resp.json()["message"]["content"])


def save_parsed(db: Session, parsed: ParsedOutput) -> dict[str, list[int]]:
    """Persist parsed items; returns the created ids per type. Caller commits."""
    tz = ZoneInfo(APP_TIMEZONE)
    created: dict[str, list[int]] = {"tasks": [], "finance": [], "journal": []}

    def add(kind: str, obj):
        db.add(obj)
        db.flush()
        created[kind].append(obj.id)

    for t in parsed.tasks:
        due = t.due_at.replace(tzinfo=tz) if t.due_at and t.due_at.tzinfo is None else t.due_at
        add("tasks", models.Task(title=t.title, description=t.description, due_at=due, priority=t.priority))
    for f in parsed.finance:
        add("finance", models.FinanceTransaction(
            kind=f.kind, amount=f.amount, currency=f.currency.upper()[:3], category=f.category,
            description=f.description, occurred_on=f.occurred_on or datetime.now(tz).date()))
    for j in parsed.journal:
        add("journal", models.JournalEntry(content=j.content, mood=j.mood))
    return created
