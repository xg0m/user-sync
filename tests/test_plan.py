import shutil
from pathlib import Path

import pytest

from main import main
from sync.plan import (
    CREATE,
    DISABLE,
    ENABLE,
    REVIEW,
    UPDATE,
    apply_plan,
    build_plan,
    disable_ratio,
    read_hr,
    read_json,
    summary,
)
from sync.report import render_report

BASE_DIR = Path(__file__).resolve().parent.parent
HR = BASE_DIR / "sample_data" / "hr_export.csv"
DIRECTORY = BASE_DIR / "sample_data" / "directory.json"
MAPPING = BASE_DIR / "config" / "mapping.json"


@pytest.fixture
def directory():
    return read_json(DIRECTORY)


@pytest.fixture
def actions(directory):
    return build_plan(read_hr(HR), directory, read_json(MAPPING))


def by_id(actions):
    return {action.employee_id: action for action in actions}


def test_akcje_dla_danych_przykladowych(actions):
    expected = [
        ("3", UPDATE),
        ("5", DISABLE),
        ("6", UPDATE),
        ("7", CREATE),
        ("8", CREATE),
        ("9", ENABLE),
        ("10", REVIEW),
        ("11", REVIEW),
        ("91", REVIEW),
    ]
    assert [(action.employee_id, action.kind) for action in actions] == expected


def test_podsumowanie(actions):
    assert summary(actions) == {CREATE: 2, UPDATE: 2, ENABLE: 1, DISABLE: 1, REVIEW: 3}


def test_nowe_konta_i_kolizja_loginu(actions):
    found = by_id(actions)
    assert found["7"].login == "jkowalski2"
    assert found["8"].login == "lzolkiewski"
    assert found["8"].record["groups"] == ["GRP_Pracownicy", "GRP_WM"]


def test_zmiany_atrybutow(actions):
    found = by_id(actions)
    assert set(found["3"].changes) == {"job_title", "groups"}
    assert found["3"].changes["groups"][1] == ["GRP_Kierownicy", "GRP_Pracownicy", "GRP_WI"]
    assert set(found["6"].changes) == {"unit", "groups"}


def test_ponowne_wlaczenie(actions):
    enable = by_id(actions)["9"]
    assert enable.changes["enabled"] == (False, True)
    assert enable.changes["groups"][1] == ["GRP_Finanse", "GRP_Pracownicy"]


def test_konto_techniczne_pominiete(actions):
    assert all(action.login != "svc_backup" for action in actions)


def test_konto_bez_rekordu_kadrowego_do_sprawdzenia(actions):
    orphan = by_id(actions)["91"]
    assert orphan.kind == REVIEW
    assert orphan.login == "agrabowski"


def test_wykonanie_planu(directory, actions):
    result = apply_plan(directory, actions)
    accounts = {account["login"]: account for account in result}
    assert len(result) == len(directory) + 2
    assert accounts["kkaminska"]["enabled"] is False
    assert accounts["kkaminska"]["groups"] == []
    assert accounts["ezielinska"]["enabled"] is True
    assert accounts["mwisniewska"]["job_title"] == "Profesor"
    assert accounts["tlewandowski"]["unit"] == "Dział IT"
    assert read_json(DIRECTORY) == directory


def test_plan_jest_idempotentny(directory, actions):
    synced = apply_plan(directory, actions)
    again = build_plan(read_hr(HR), synced, read_json(MAPPING))
    assert [(action.employee_id, action.kind) for action in again] == [("10", REVIEW), ("11", REVIEW), ("91", REVIEW)]


def test_odsetek_wylaczen(directory, actions):
    assert disable_ratio(actions, directory) == pytest.approx(1 / 7)


def test_raport(actions):
    report = render_report(actions)
    assert report.startswith("# Plan synchronizacji kont")
    assert "| UTWORZ | 7 | jkowalski2 |" in report


def run_main(tmp_path, *extra):
    directory_copy = tmp_path / "directory.json"
    shutil.copy(DIRECTORY, directory_copy)
    args = [
        "--hr", str(HR),
        "--directory", str(directory_copy),
        "--mapping", str(MAPPING),
        "--report", str(tmp_path / "plan.md"),
        *extra,
    ]
    return main(args), directory_copy


def test_tryb_podgladu_nie_zmienia_katalogu(tmp_path):
    code, directory_copy = run_main(tmp_path)
    assert code == 0
    assert read_json(directory_copy) == read_json(DIRECTORY)
    assert (tmp_path / "plan.md").exists()


def test_apply_zapisuje_zmiany(tmp_path):
    output = tmp_path / "wynik.json"
    code, _ = run_main(tmp_path, "--apply", "--output", str(output))
    assert code == 0
    assert len(read_json(output)) == len(read_json(DIRECTORY)) + 2


def test_limit_wylaczen_blokuje_zapis(tmp_path):
    code, directory_copy = run_main(tmp_path, "--apply", "--max-disable", "0.1")
    assert code == 2
    assert read_json(directory_copy) == read_json(DIRECTORY)


def test_force_omija_limit(tmp_path):
    code, directory_copy = run_main(tmp_path, "--apply", "--max-disable", "0.1", "--force")
    assert code == 0
    assert read_json(directory_copy) != read_json(DIRECTORY)
