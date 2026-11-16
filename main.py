"""Synchronizacja kont z systemem kadrowym. Domyślnie tylko pokazuje plan (tryb podglądu)."""
import argparse
from pathlib import Path

from sync.plan import apply_plan, build_plan, disable_ratio, read_hr, read_json, summary, write_json
from sync.report import render_report

BASE_DIR = Path(__file__).resolve().parent


def build_parser():
    parser = argparse.ArgumentParser(description="Synchronizacja kont użytkowników z eksportem kadrowym.")
    parser.add_argument("--hr", default=str(BASE_DIR / "sample_data" / "hr_export.csv"), help="eksport z systemu kadrowego (CSV)")
    parser.add_argument("--directory", default=str(BASE_DIR / "sample_data" / "directory.json"), help="obecny stan katalogu kont (JSON)")
    parser.add_argument("--mapping", default=str(BASE_DIR / "config" / "mapping.json"), help="mapowanie jednostek na grupy")
    parser.add_argument("--report", default=str(BASE_DIR / "output" / "plan_synchronizacji.md"), help="raport planu (Markdown)")
    parser.add_argument("--apply", action="store_true", help="zapisz zmiany w katalogu")
    parser.add_argument("--output", help="plik wynikowy przy --apply (domyślnie nadpisuje --directory)")
    parser.add_argument("--max-disable", type=float, default=0.2, help="maksymalny odsetek wyłączanych kont (domyślnie 0.2)")
    parser.add_argument("--force", action="store_true", help="pomiń limit wyłączanych kont")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    mapping = read_json(args.mapping)
    directory = read_json(args.directory)
    actions = build_plan(read_hr(args.hr), directory, mapping)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(actions), encoding="utf-8")
    for kind, count in summary(actions).items():
        print(f"{kind}: {count}")
    print(f"Raport: {report_path}")
    if not args.apply:
        print("Tryb podglądu: niczego nie zmieniono. Aby zapisać zmiany, użyj --apply.")
        return 0
    ratio = disable_ratio(actions, directory)
    if ratio > args.max_disable and not args.force:
        print(f"Przerwano: plan wyłącza {ratio:.0%} aktywnych kont, a limit to {args.max_disable:.0%}.")
        print("Sprawdź, czy eksport z kadr jest kompletny. Jeśli tak, uruchom ponownie z --force.")
        return 2
    output = args.output or args.directory
    write_json(output, apply_plan(directory, actions))
    print(f"Zapisano katalog: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
