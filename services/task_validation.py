"""Validation rules shared by planner create and edit forms."""

from datetime import date


MODULES = (
    "Working with Data",
    "Maths for Data Science",
    "Digital Circuits and Logic Design",
    "Computer Programming",
    "Introduction to AI",
    "Personal",
)
PRIORITIES = ("Low", "Medium", "High")


def validate_task_form(form) -> tuple[dict, dict]:
    values = {
        "title": form.get("title", "").strip(),
        "description": form.get("description", "").strip(),
        "module": form.get("module", ""),
        "due_date": form.get("due_date", ""),
        "priority": form.get("priority", ""),
    }
    errors = {}
    if not values["title"]:
        errors["title"] = "Add a short assessment title."
    elif len(values["title"]) > 120:
        errors["title"] = "Keep the title to 120 characters or fewer."
    if len(values["description"]) > 1000:
        errors["description"] = "Keep the description to 1,000 characters or fewer."
    if values["module"] not in MODULES:
        errors["module"] = "Choose one of the listed modules."
    try:
        date.fromisoformat(values["due_date"])
    except ValueError:
        errors["due_date"] = "Choose a valid due date."
    if values["priority"] not in PRIORITIES:
        errors["priority"] = "Choose Low, Medium, or High priority."
    return values, errors
