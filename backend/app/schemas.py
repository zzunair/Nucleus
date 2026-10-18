from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Clients
class ClientBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: str | None = None
    phone: str | None = None
    notes: str | None = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    email: str | None = None
    phone: str | None = None
    notes: str | None = None


class ClientOut(ClientBase, ORM):
    id: int
    created_at: datetime


# --- Projects
ProjectStatus = Literal["active", "on_hold", "done", "archived"]


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    client_id: int | None = None
    description: str | None = None
    status: ProjectStatus = "active"
    deadline: datetime | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    client_id: int | None = None
    description: str | None = None
    status: ProjectStatus | None = None
    deadline: datetime | None = None


class ProjectOut(ProjectBase, ORM):
    id: int
    created_at: datetime


# --- Tasks
TaskStatus = Literal["todo", "doing", "done", "cancelled"]


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    project_id: int | None = None
    description: str | None = None
    status: TaskStatus = "todo"
    priority: int = Field(default=2, ge=1, le=3)
    due_at: datetime | None = None
    remind_at: datetime | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    project_id: int | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: int | None = Field(default=None, ge=1, le=3)
    due_at: datetime | None = None
    remind_at: datetime | None = None


class TaskOut(TaskBase, ORM):
    id: int
    completed_at: datetime | None
    created_at: datetime


# --- Journal
class JournalBase(BaseModel):
    content: str = Field(min_length=1)
    entry_date: date | None = None
    mood: int | None = Field(default=None, ge=1, le=5)


class JournalCreate(JournalBase):
    pass


class JournalUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1)
    entry_date: date | None = None
    mood: int | None = Field(default=None, ge=1, le=5)


class JournalOut(ORM):
    id: int
    content: str
    entry_date: date
    mood: int | None
    created_at: datetime


# --- Finance
Kind = Literal["income", "expense"]


class FinanceBase(BaseModel):
    kind: Kind
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    occurred_on: date | None = None
    category: str | None = None
    description: str | None = None
    client_id: int | None = None
    project_id: int | None = None


class FinanceCreate(FinanceBase):
    pass


class FinanceUpdate(BaseModel):
    kind: Kind | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    occurred_on: date | None = None
    category: str | None = None
    description: str | None = None
    client_id: int | None = None
    project_id: int | None = None


class FinanceOut(ORM):
    id: int
    kind: Kind
    amount: Decimal
    currency: str
    occurred_on: date
    category: str | None
    description: str | None
    client_id: int | None
    project_id: int | None
    created_at: datetime


# --- Parse jobs
class ParseRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)
    source: Literal["text", "voice"] = "text"


class ParseJobOut(ORM):
    id: int
    status: str
    source: str
    input_text: str
    result: dict | None
    error: str | None
    created_at: datetime
