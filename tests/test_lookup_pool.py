"""CHG-TW-004 lookup-pool scoring: unknown dates never score young (synthetic records, invented names only)."""
import datetime as dt

import pytest

from tw.lookup_pool import (
    batch_sort_key,
    award_id_sort_key,
    earliest_known,
    is_young,
    parse_known_date,
    score_entities,
)


def _ent(name, *, first_seen, earliest_award, value=1000.0, n=1, link="Reported", tid="A-1"):
    # `name` is invented and only labels the synthetic record; scoring never reads it.
    return {
        "name": name,
        "value": value,
        "n": n,
        "link": link,
        "first_seen": parse_known_date(first_seen),
        "earliest_award": parse_known_date(earliest_award),
        "tiebreak_id": tid,
    }


@pytest.mark.parametrize("raw", [None, "", "   ", "9999-12-31", "9999-12-31T00:00:00Z", "1900-01-01",
                                 "1970-01-01", "0001-01-01", "not a date", "2150-01-01", "1985-05-05", 20240101])
def test_placeholders_and_missing_are_unknown(raw) -> None:
    assert parse_known_date(raw) is None


def test_real_date_is_known() -> None:
    assert parse_known_date("2024-03-12T10:00:00Z") == dt.date(2024, 3, 12)


def test_earliest_known_has_no_fill_value() -> None:
    assert earliest_known([None, "", "9999-12-31"]) is None
    assert earliest_known(["9999-12-31", "2024-05-01", "2023-02-01"]) == dt.date(2023, 2, 1)


@pytest.mark.parametrize("first_seen,award", [
    (None, "2024-01-10"),
    ("", "2024-01-10"),
    ("9999-12-31", "2024-01-10"),
    ("1900-01-01", "2024-01-10"),
    ("2023-06-01", None),
    ("2023-06-01", "9999-12-31"),
    (None, None),
])
def test_missing_date_never_scores_young(first_seen, award) -> None:
    ents = score_entities([_ent("Qwertane Widget Supplies (Pty) Ltd", first_seen=first_seen, earliest_award=award)])
    assert ents[0]["young"] is False
    assert ents[0]["score"] == ents[0]["value_points"] + 1  # Reported link only, no young points


def test_known_dates_inside_window_are_young() -> None:
    assert is_young(dt.date(2023, 6, 1), dt.date(2024, 5, 30)) is True
    assert is_young(dt.date(2023, 6, 1), dt.date(2023, 6, 1)) is True


def test_window_edges_and_negative_gap() -> None:
    assert is_young(dt.date(2023, 6, 1), dt.date(2024, 5, 31)) is True   # 365 days
    assert is_young(dt.date(2023, 6, 1), dt.date(2024, 6, 1)) is False   # 366 days
    assert is_young(dt.date(2024, 6, 1), dt.date(2024, 1, 1)) is False   # first seen after the award
    assert is_young(dt.date(2022, 5, 31), dt.date(2022, 7, 1)) is False  # before 2022-06-01


def test_unknown_award_date_sorts_last_deterministically() -> None:
    ents = [
        _ent("Zephyra Holdings (Pty) Ltd", first_seen="2021-01-01", earliest_award=None, tid="A-1"),
        _ent("Testburg and Sons (Pty) Ltd", first_seen="2021-01-01", earliest_award="2024-02-02", tid="A-9"),
        _ent("Acme Widgets CC", first_seen="2021-01-01", earliest_award="9999-12-31", tid="A-0"),
    ]
    order = [e["name"] for e in score_entities(ents)]
    assert order == ["Testburg and Sons (Pty) Ltd", "Acme Widgets CC", "Zephyra Holdings (Pty) Ltd"]
    again = [e["name"] for e in score_entities(list(reversed(ents)))]
    assert again == order


def test_unknown_tiebreak_id_sorts_last() -> None:
    a = _ent("Qwertane Widget Supplies (Pty) Ltd", first_seen=None, earliest_award="2024-01-01", tid=None)
    b = _ent("Testburg and Sons (Pty) Ltd", first_seen=None, earliest_award="2024-01-01", tid="B-1")
    for e in (a, b):
        e.update(score=1)
    assert sorted([a, b], key=batch_sort_key)[0] is b


def test_quartile_bands_use_ascending_lower_nearest_rank() -> None:
    vals = [10.0, 20.0, 30.0, 40.0, 50.0]  # V ascending; Q50 = V[2] = 30, Q75 = V[3] = 40
    ents = [_ent(f"Invented Supplier {i} (Pty) Ltd", first_seen=None, earliest_award="2024-01-01", value=v, tid=str(i))
            for i, v in enumerate(vals)] + [_ent("Invented Zero (Pty) Ltd", first_seen=None, earliest_award="2024-01-01", value=0.0, tid="z")]
    pts = {e["value"]: e["value_points"] for e in score_entities(ents)}
    assert pts == {10.0: 1, 20.0: 1, 30.0: 2, 40.0: 3, 50.0: 3, 0.0: 0}


@pytest.mark.parametrize("raw", ["20240101", "2024-W01-1", "2024-08-30garbage", "2024-02-30",
                                 "2024-08-30T25:00:00Z", "2024-08-30T10:00:00+24:00", " 2024-08-30",
                                 "2024-08-30 10:00:00", "2024-08-30T10:00:00+0200"])
def test_strict_parser_rejects_loose_shapes(raw) -> None:
    assert parse_known_date(raw) is None


def test_plain_date_keeps_its_date() -> None:
    assert parse_known_date("2024-08-30") == dt.date(2024, 8, 30)


def test_z_time_keeps_its_date() -> None:
    assert parse_known_date("2024-08-30T23:59:59Z") == dt.date(2024, 8, 30)
    assert parse_known_date("2024-08-30T00:00:00.123Z") == dt.date(2024, 8, 30)


def test_plus_two_just_after_midnight_rolls_back_a_day() -> None:
    assert parse_known_date("2024-08-30T00:30:00+02:00") == dt.date(2024, 8, 29)


def test_minus_five_late_evening_rolls_forward_a_day() -> None:
    assert parse_known_date("2024-08-30T21:00:00-05:00") == dt.date(2024, 8, 31)


def test_bare_time_keeps_written_date() -> None:
    assert parse_known_date("2024-08-30T23:30:00") == dt.date(2024, 8, 30)


def test_etenders_release_date_shape_parses() -> None:
    # The only release-date shape in the pinned eTenders file: YYYY-MM-DDTHH:MM:SSZ
    assert parse_known_date("2023-11-07T08:15:42Z") == dt.date(2023, 11, 7)


def test_numeric_award_ids_compare_numerically() -> None:
    ids = ["10", "9", "x-2", None, "100", "x-10"]
    assert sorted(ids, key=award_id_sort_key) == ["9", "10", "100", "x-10", "x-2", None]
    assert min(["10", "9"], key=award_id_sort_key) == "9"


def test_numeric_tiebreak_in_batch_order() -> None:
    a = _ent("Qwertane Widget Supplies (Pty) Ltd", first_seen=None, earliest_award="2024-01-01", tid="10")
    b = _ent("Testburg and Sons (Pty) Ltd", first_seen=None, earliest_award="2024-01-01", tid="9")
    assert [e["name"] for e in score_entities([a, b])] == ["Testburg and Sons (Pty) Ltd", "Qwertane Widget Supplies (Pty) Ltd"]
