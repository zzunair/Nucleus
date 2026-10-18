from app import models, schemas
from app.crud import make_crud_router

clients = make_crud_router("/clients", "Client", models.Client,
                           schemas.ClientCreate, schemas.ClientUpdate, schemas.ClientOut)
projects = make_crud_router("/projects", "Project", models.Project,
                            schemas.ProjectCreate, schemas.ProjectUpdate, schemas.ProjectOut)
tasks = make_crud_router("/tasks", "Task", models.Task,
                         schemas.TaskCreate, schemas.TaskUpdate, schemas.TaskOut)
journal = make_crud_router("/journal", "Journal", models.JournalEntry,
                           schemas.JournalCreate, schemas.JournalUpdate, schemas.JournalOut)
finance = make_crud_router("/finance", "Finance", models.FinanceTransaction,
                           schemas.FinanceCreate, schemas.FinanceUpdate, schemas.FinanceOut)
