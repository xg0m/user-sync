"""Raport planu synchronizacji w formacie Markdown."""
from .plan import summary


def _format(value):
    if isinstance(value, list):
        return ", ".join(value) if value else "(brak)"
    return str(value)


def describe(action):
    """Opis akcji do jednej komórki tabeli."""
    details = [action.reason] if action.reason else []
    if action.changes:
        for name, (old, new) in action.changes.items():
            details.append(f"{name}: {_format(old)} -> {_format(new)}")
    elif action.record:
        details.append("grupy: " + _format(action.record["groups"]))
    return "; ".join(details).replace("|", "/")


def render_report(actions):
    lines = ["# Plan synchronizacji kont", "", "| Akcja | Liczba |", "|---|---|"]
    lines += [f"| {kind} | {count} |" for kind, count in summary(actions).items()]
    lines += ["", "| Akcja | ID pracownika | Login | Szczegóły |", "|---|---|---|---|"]
    for action in actions:
        lines.append(f"| {action.kind} | {action.employee_id} | {action.login} | {describe(action)} |")
    return "\n".join(lines) + "\n"
