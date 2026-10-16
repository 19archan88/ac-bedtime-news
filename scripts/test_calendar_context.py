"""Boundary and partition tests for the reusable calendar helper."""

from datetime import date, timedelta
import unittest

from calendar_context import child_context, date_context, elapsed, month_context, week_context, year_context


class CalendarTests(unittest.TestCase):
    def test_source_example(self):
        result = date_context("2026-08-29")
        self.assertEqual(result["week"]["report_id"], "W-2026-W36")
        self.assertEqual(result["week"]["end"], "2026-09-04")
        self.assertEqual(result["week"]["belongs_to_month"], "2026-09")

    def test_cross_year_iso_identity_is_separate_from_ownership(self):
        result = week_context(date(2026, 12, 26))
        self.assertEqual(result["weekly_key"], "2026-W53")
        self.assertEqual(result["belongs_to_year"], "2027")
        self.assertEqual(result["belongs_to_month"], "2027-01")
        self.assertEqual(month_context("2027-01")["expected_weekly_keys"],
                         ["2026-W53", "2027-W01", "2027-W02", "2027-W03", "2027-W04"])

    def test_optional_family_profile(self):
        self.assertIsNone(date_context("2015-01-01")["child"]["age"])
        self.assertIsNone(date_context("2030-01-01")["child"]["school"])
        birth = date(2018, 4, 12)  # Fictional test profile, never a default.
        entry = date(2024, 8, 20)
        self.assertEqual(date_context("2024-04-11", birth)["child"]["age_label"], "5岁11个月")
        self.assertEqual(date_context("2024-04-12", birth)["child"]["age_label"], "6岁0个月")
        self.assertFalse(child_context(date(2024, 8, 19), birth, entry)["school"]["enrolled"])
        start = child_context(entry, birth, entry)["school"]
        self.assertIsNone(start["grade"])
        self.assertEqual(start["elapsed"]["total_days"], 0)
        partial = child_context(date(2024, 9, 1), school_start=entry)
        self.assertIsNone(partial["age"])
        self.assertEqual(partial["school"]["elapsed"]["total_days"], 12)
        with self.assertRaises(ValueError):
            child_context(date(2024, 1, 1), birth, date(2017, 1, 1))
        with self.assertRaises(ValueError):
            date_context("2017-01-01", birth)

    def test_month_and_year_trigger_boundaries(self):
        self.assertFalse(date_context("2026-09-24")["calendar_conditions_only"]["is_anchor_friday"])
        self.assertTrue(date_context("2026-09-25")["calendar_conditions_only"]["is_last_anchor_friday_of_month"])
        self.assertFalse(date_context("2026-09-26")["calendar_conditions_only"]["is_last_anchor_friday_of_month"])
        self.assertTrue(date_context("2026-12-25")["calendar_conditions_only"]["is_last_anchor_friday_of_year"])
        self.assertEqual(year_context("2026")["end"], "2026-12-25")
        self.assertEqual(year_context("2027")["start"], "2026-12-26")

    def test_calendar_partitions_twenty_years(self):
        cursor = date(2020, 1, 1)
        while cursor < date(2040, 1, 1):
            week = week_context(cursor)
            start, end = date.fromisoformat(week["start"]), date.fromisoformat(week["end"])
            self.assertEqual(start.weekday(), 5)
            self.assertEqual(end.weekday(), 4)
            self.assertLessEqual(start, cursor)
            self.assertGreaterEqual(end, cursor)
            self.assertEqual((end - start).days, 6)
            cursor += timedelta(days=1)
        for year in range(2020, 2040):
            weeks = [w for m in range(1, 13) for w in month_context(f"{year}-{m:02d}")["weeks"]]
            self.assertEqual(len({w["weekly_key"] for w in weeks}), len(weeks))
            self.assertIn(len(weeks), (52, 53))
            for previous, current in zip(weeks, weeks[1:]):
                self.assertEqual(date.fromisoformat(previous["end"]) + timedelta(days=1),
                                 date.fromisoformat(current["start"]))

    def test_leap_day_and_corrected_profile(self):
        self.assertEqual(elapsed(date(2020, 2, 29), date(2021, 2, 28))["years"], 1)
        result = child_context(date(2027, 9, 1), date(2021, 4, 12), date(2027, 9, 1))
        self.assertEqual(result["age_label"], "6岁4个月")
        self.assertIsNone(result["school"]["grade"])

    def test_invalid_dates(self):
        for value in ("2026-2-1", "2026-02-30"):
            with self.assertRaises(ValueError):
                date_context(value)
        with self.assertRaises(ValueError):
            month_context("2026-13")
        with self.assertRaises(ValueError):
            year_context("26")


if __name__ == "__main__":
    unittest.main()
