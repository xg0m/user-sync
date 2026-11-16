"""Plan synchronizacji: porównanie eksportu kadrowego z katalogiem kont użytkowników."""
import copy
import csv
import json
from dataclasses import dataclass, field

from .logins import make_login

CREATE = "UTWORZ"
UPDATE = "ZMIEN"
ENABLE = "WLACZ"
DISABLE = "WYLACZ"
REVIEW = "SPRAWDZ"
KINDS = (CREATE, UPDATE, ENABLE, DISABLE, REVIEW)

ACTIVE = "aktywny"
TERMINATED = "zwolniony"
SYNCED_FIELDS = ("first_name", "last_name", "unit", "job_title", "groups")


@dataclass
class Action:
    """Jedna zmiana do wykonania w katalogu albo przypadek do ręcznego sprawdzenia."""

    kind: str
    employee_id: str
    login: str = ""
    changes: dict = field(default_factory=dict)
    reason: str = ""
    record: dict | None = None


def read_hr(path):
    """Czyta eksport z systemu kadrowego (CSV, separator średnik)."""
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        return [{key: (value or "").strip() for key, value in row.items()} for row in reader]


def read_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def _id_key(value):
    """Sortuje identyfikatory liczbowo, żeby 10 było po 9, a nie po 1."""
    return (0, int(value), "") if value.isdigit() else (1, 0, value)


def _current(account, name):
    value = account.get(name)
    return sorted(value or []) if name == "groups" else value


def compute_groups(row, mapping, manager_ids):
    """Grupy wynikają z mapowania: grupy bazowe, grupa jednostki i grupa kierowników."""
    groups = set(mapping["base_groups"])
    groups.add(mapping["units"][row["unit"]])
    if row["employee_id"] in manager_ids:
        groups.add(mapping["manager_group"])
    return sorted(groups)


def build_plan(hr_rows, directory, mapping):
    """Porównuje dane kadrowe z katalogiem i zwraca listę akcji. Nie zmienia katalogu.

    Konta bez employee_id (konta techniczne) są pomijane.
    Konto bez rekordu w kadrach nie jest wyłączane automatycznie, tylko trafia do sprawdzenia.
    """
    accounts = {account["employee_id"]: account for account in directory if account.get("employee_id")}
    taken = {account["login"] for account in directory}
    manager_ids = {row["manager_id"] for row in hr_rows if row["status"] == ACTIVE and row["manager_id"]}
    hr_ids = set()
    actions = []
    for row in sorted(hr_rows, key=lambda item: _id_key(item["employee_id"])):
        employee_id = row["employee_id"]
        hr_ids.add(employee_id)
        account = accounts.get(employee_id)
        login = account["login"] if account else ""
        status = row["status"]
        if status not in (ACTIVE, TERMINATED):
            actions.append(Action(REVIEW, employee_id, login, reason="Nieznany status w eksporcie: " + status))
            continue
        if status == TERMINATED:
            if account and account["enabled"]:
                actions.append(Action(DISABLE, employee_id, login, reason="Pracownik zwolniony"))
            continue
        if row["unit"] not in mapping["units"]:
            reason = "Jednostka bez mapowania na grupę: " + row["unit"]
            actions.append(Action(REVIEW, employee_id, login, reason=reason))
            continue
        desired = {
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "unit": row["unit"],
            "job_title": row["job_title"],
            "groups": compute_groups(row, mapping, manager_ids),
        }
        if account is None:
            try:
                new_login = make_login(row["first_name"], row["last_name"], taken)
            except ValueError as error:
                actions.append(Action(REVIEW, employee_id, reason=str(error)))
                continue
            taken.add(new_login)
            record = {"login": new_login, "employee_id": employee_id, **desired, "enabled": True}
            actions.append(Action(CREATE, employee_id, new_login, record=record))
            continue
        changes = {
            name: (_current(account, name), desired[name])
            for name in SYNCED_FIELDS
            if _current(account, name) != desired[name]
        }
        if not account["enabled"]:
            changes["enabled"] = (False, True)
            actions.append(Action(ENABLE, employee_id, login, changes=changes, reason="Pracownik ponownie aktywny"))
        elif changes:
            actions.append(Action(UPDATE, employee_id, login, changes=changes))
    for employee_id in sorted(accounts, key=_id_key):
        account = accounts[employee_id]
        if employee_id not in hr_ids and account["enabled"]:
            reason = "Aktywne konto bez rekordu w systemie kadrowym"
            actions.append(Action(REVIEW, employee_id, account["login"], reason=reason))
    return actions


def apply_plan(directory, actions):
    """Zwraca nowy katalog po wykonaniu akcji. Wejściowy katalog zostaje bez zmian."""
    result = copy.deepcopy(directory)
    by_id = {account["employee_id"]: account for account in result if account.get("employee_id")}
    for action in actions:
        if action.kind == CREATE:
            result.append(copy.deepcopy(action.record))
        elif action.kind in (UPDATE, ENABLE):
            account = by_id[action.employee_id]
            for name, (_, new_value) in action.changes.items():
                account[name] = new_value
        elif action.kind == DISABLE:
            account = by_id[action.employee_id]
            account["enabled"] = False
            account["groups"] = []
    return result


def summary(actions):
    counts = {kind: 0 for kind in KINDS}
    for action in actions:
        counts[action.kind] += 1
    return counts


def disable_ratio(actions, directory):
    """Jaki odsetek aktywnych kont pracowniczych plan wyłącza."""
    enabled = sum(1 for account in directory if account.get("employee_id") and account["enabled"])
    disabled = sum(1 for action in actions if action.kind == DISABLE)
    return disabled / enabled if enabled else 0.0
