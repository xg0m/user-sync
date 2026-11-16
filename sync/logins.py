"""Tworzenie loginów kont na podstawie imienia i nazwiska."""

POLISH = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
MAX_LENGTH = 20


def normalize(text):
    """Zamienia polskie znaki na łacińskie i zostawia tylko małe litery a-z."""
    plain = text.translate(POLISH).lower()
    return "".join(char for char in plain if "a" <= char <= "z")


def make_login(first_name, last_name, taken):
    """Login to pierwsza litera imienia i nazwisko, np. jkowalski.

    Gdy login jest zajęty, dodaje kolejny numer: jkowalski2, jkowalski3.
    Zbiór taken obejmuje też konta wyłączone, bo loginów nie używa się ponownie.
    """
    first = normalize(first_name)
    last = normalize(last_name)
    if not first or not last:
        raise ValueError("Imię i nazwisko muszą zawierać litery")
    base = (first[0] + last)[:MAX_LENGTH]
    login = base
    number = 2
    while login in taken:
        suffix = str(number)
        login = base[: MAX_LENGTH - len(suffix)] + suffix
        number += 1
    return login
