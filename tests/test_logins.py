import pytest

from sync.logins import MAX_LENGTH, make_login, normalize


def test_normalize_polskie_znaki():
    assert normalize("Łukasz") == "lukasz"
    assert normalize("Żółkiewski") == "zolkiewski"
    assert normalize("Nowak-Kowalska") == "nowakkowalska"


def test_login_podstawowy():
    assert make_login("Jan", "Kowalski", set()) == "jkowalski"


def test_login_zajety_dostaje_numer():
    assert make_login("Jan", "Kowalski", {"jkowalski"}) == "jkowalski2"
    assert make_login("Jan", "Kowalski", {"jkowalski", "jkowalski2"}) == "jkowalski3"


def test_login_ma_maksymalna_dlugosc():
    login = make_login("Jan", "Konstantynopolitanczykiewicz", set())
    assert len(login) == MAX_LENGTH
    numbered = make_login("Jan", "Konstantynopolitanczykiewicz", {login})
    assert len(numbered) == MAX_LENGTH
    assert numbered.endswith("2")


def test_login_bez_liter():
    with pytest.raises(ValueError):
        make_login("123", "Kowalski", set())
