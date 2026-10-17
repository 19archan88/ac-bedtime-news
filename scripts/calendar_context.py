#!/usr/bin/env python3
"""Read-only Friday-anchored periods and child context. Python standard library only."""

import argparse
import calendar
from datetime import date, timedelta
import json
from pathlib import Path
import re
import sys


def parse_date(value):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Date must use YYYY-MM-DD")
    return date.fromisoformat(value)


def add_months(start, months):
    total = start.year * 12 + start.month - 1 + months
    year, month0 = divmod(total, 12)
    month = month0 + 1
    return date(year, month, min(start.day, calendar.monthrange(year, month)[1]))


def elapsed(start, end):
    if end < start:
        raise ValueError("End date precedes start date")
    months = (end.year - start.year) * 12 + end.month - start.month
    if add_months(start, months) > end:
        months -= 1
    anniversary = add_months(start, months)
    return {"years": months // 12, "months": months % 12,
            "total_months": months, "days": (end - anniversary).days,
            "total_days": (end - start).days}


def week_context(day):
    anchor = day + timedelta(days=(4 - day.weekday()) % 7)
    start = anchor - timedelta(days=6)
    iso_year, iso_week, _ = anchor.isocalendar()
    key = f"{iso_year:04d}-W{iso_week:02d}"
    return {"start": start.isoformat(), "end": anchor.isoformat(),
            "anchor_friday": anchor.isoformat(), "weekly_key": key,
            "report_id": f"W-{key}", "belongs_to_month": anchor.strftime("%Y-%m"),
            "belongs_to_year": f"{anchor.year:04d}",
            "daily_dates": [(start + timedelta(days=i)).isoformat() for i in range(7)]}


def month_context(value):
    if not re.fullmatch(r"\d{4}-\d{2}", value):
        raise ValueError("Month must use YYYY-MM")
    first = date.fromisoformat(value + "-01")
    last = calendar.monthrange(first.year, first.month)[1]
    weeks = [week_context(date(first.year, first.month, n))
             for n in range(1, last + 1)
             if date(first.year, first.month, n).weekday() == 4]
    return {"monthly_key": value, "report_id": f"M-{value}",
            "start": weeks[0]["start"], "end": weeks[-1]["end"],
            "last_anchor_friday": weeks[-1]["anchor_friday"],
            "expected_weekly_keys": [w["weekly_key"] for w in weeks], "weeks": weeks}


def year_context(value):
    if not re.fullmatch(r"\d{4}", value) or not 2 <= int(value) <= 9998:
        raise ValueError("Year must be four digits in 0002..9998")
    months = [month_context(f"{value}-{n:02d}") for n in range(1, 13)]
    return {"yearly_key": value, "report_id": f"Y-{value}",
            "start": months[0]["start"], "end": months[-1]["end"],
            "expected_monthly_keys": [m["monthly_key"] for m in months],
            "months": [{k: m[k] for k in ("monthly_key", "start", "end",
                        "last_anchor_friday", "expected_weekly_keys")} for m in months]}


def grade_context(day, baselines):
    """Use the latest confirmed baseline, preserving earlier school history."""
    if not baselines:
        return None
    applicable = []
    seen = set()
    for baseline in baselines:
        effective = parse_date(baseline['effective_date'])
        if effective in seen:
            raise ValueError('Duplicate school baseline date')
        seen.add(effective)
        index = baseline['grade_index']
        if type(index) is not int or index < 1:
            raise ValueError('grade_index must be a positive integer')
        promotion = baseline['promotion_day']
        if not re.fullmatch(r'\d{2}-\d{2}', promotion):
            raise ValueError('promotion_day must use MM-DD')
        boundary = parse_date('2001-' + promotion)  # Must exist every year.
        stages = baseline['stages']
        if not stages or any(not s['name'] or type(s['years']) is not int or s['years'] < 1 for s in stages):
            raise ValueError('Each school stage needs a name and positive years')
        if index > sum(s['years'] for s in stages):
            raise ValueError('Baseline grade exceeds configured school stages')
        if effective <= day:
            applicable.append((effective, baseline, boundary))
    if not applicable:
        return None
    effective, baseline, boundary = max(applicable, key=lambda item: item[0])
    mmdd = (boundary.month, boundary.day)
    academic = lambda d: d.year - ((d.month, d.day) < mmdd)
    index = baseline['grade_index'] + academic(day) - academic(effective)
    remaining = index
    label = None
    for stage in baseline['stages']:
        if remaining <= stage['years']:
            label = f"{stage['name']}{remaining}年级"
            break
        remaining -= stage['years']
    return {'grade': label, 'school_year_index': index,
            'baseline_date': effective.isoformat(),
            'status': 'projected' if label else 'beyond_configured_stages',
            'notice': '依据家长确认的学籍基准和升年级规则推算；实际学籍变动以家长校正为准。'}


def child_context(day, birth=None, school_start=None, profile=None):
    profile = profile or {}
    if birth is not None and school_start is not None and school_start < birth:
        raise ValueError("School start precedes birth")
    age = elapsed(birth, day) if birth is not None else None
    age_label = f"{age['years']}岁{age['months']}个月" if age is not None else None
    age_precision = 'birth_date' if age is not None else None
    reference = profile.get('age_reference')
    if age is None and reference:
        reference_day = parse_date(reference['as_of'])
        years, months = reference['years'], reference.get('months')
        if type(years) is not int or years < 0 or (months is not None and (type(months) is not int or not 0 <= months < 12)):
            raise ValueError('Age reference needs nonnegative years and months in 0..11')
        if day >= reference_day and months is None:
            age_label = f"截至{reference_day.isoformat()}为{years}岁（月数未知）；当前精确年龄待确认"
            age_precision = 'years_only_reference'
        elif day >= reference_day:
            total = years * 12 + months + elapsed(reference_day, day)['total_months']
            age = {'years': total // 12, 'months': total % 12, 'total_months': total}
            age_label = f"约{age['years']}岁{age['months']}个月"
            age_precision = 'approximate_reference'
    school = None
    if school_start is not None:
        if day < school_start:
            school = {"enrolled": False, "grade": None,
                      "days_until_start": (school_start - day).days}
        else:
            school = {"enrolled": True, "grade": None,
                      "elapsed": elapsed(school_start, day),
                      "elapsed_day_convention": "入学当日已过0天；不含起始日"}
    grade = grade_context(day, profile.get('school_baselines'))
    if grade is not None:
        if school_start is not None and day < school_start:
            raise ValueError('School baseline conflicts with school entry date')
        school = school or {'enrolled': True, 'elapsed': None}
        school.update(grade)
    observation = profile.get('school_observation')
    if observation and parse_date(observation['as_of']) <= day:
        school = school or {'enrolled': None, 'grade': None}
        school['confirmed_observation'] = observation
        if observation['as_of'] == day.isoformat():
            school.update(grade=observation['label'], status='confirmed_on_report_date')
    return {"birth_date": birth.isoformat() if birth is not None else None,
            "age": age,
            "age_label": age_label, "age_precision": age_precision,
            "school_start": school_start.isoformat() if school_start is not None else None,
            "school": school}


def date_context(value, birth=None, school_start=None, profile=None):
    day = parse_date(value)
    if not 2 <= day.year <= 9998:
        raise ValueError("Date year must be in 0002..9998")
    week = week_context(day)
    anchor = parse_date(week["anchor_friday"])
    month = month_context(week["belongs_to_month"])
    last_friday = anchor.isoformat() == month["last_anchor_friday"]
    return {"date": value, "daily_key": value, "report_id": f"D-{value}",
            "prompt_version": "v2.0", "week": week,
            "child": child_context(day, birth, school_start, profile),
            "calendar_conditions_only": {
                "is_anchor_friday": day == anchor,
                "is_last_anchor_friday_of_month": day == anchor and last_friday,
                "is_last_anchor_friday_of_year": day == anchor and last_friday and anchor.month == 12},
            "notice": "日历条件不等于报告完成、材料齐全或家长授权；必须另行检查。"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("date", "month", "year"))
    parser.add_argument("value")
    parser.add_argument("--birth-date", help="Optional confirmed birth date (YYYY-MM-DD)")
    parser.add_argument("--school-start", help="Optional confirmed school entry date (YYYY-MM-DD)")
    parser.add_argument('--profile', help='Private FAMILY-profile.json path')
    parser.add_argument('--child-id', help='Required when the family profile contains multiple children')
    args = parser.parse_args(argv)
    try:
        if args.mode == "date":
            profile = {}
            if args.profile:
                family = json.loads(Path(args.profile).read_text(encoding='utf-8-sig'))
                children = family['children']
                ids = [c['id'] for c in children]
                if len(ids) != len(set(ids)):
                    raise ValueError('Child IDs must be unique')
                matches = [c for c in children if c['id'] == args.child_id] if args.child_id else children
                if len(matches) != 1:
                    raise ValueError('Select exactly one child with --child-id')
                profile = matches[0]
            elif args.child_id:
                raise ValueError('--child-id requires --profile')
            birth = args.birth_date or profile.get('birth_date')
            school_start = args.school_start or profile.get('school_start')
            result = date_context(args.value, parse_date(birth) if birth else None,
                                  parse_date(school_start) if school_start else None, profile)
        elif args.mode == "month":
            result = month_context(args.value)
        else:
            result = year_context(args.value)
        if args.mode != 'date' and (args.profile or args.birth_date or args.school_start or args.child_id):
            profile = {}
            if args.profile:
                family = json.loads(Path(args.profile).read_text(encoding='utf-8-sig'))
                children = family['children']
                ids = [c['id'] for c in children]
                if len(ids) != len(set(ids)):
                    raise ValueError('Child IDs must be unique')
                matches = [c for c in children if c['id'] == args.child_id] if args.child_id else children
                if len(matches) != 1:
                    raise ValueError('Select exactly one child with --child-id')
                profile = matches[0]
            elif args.child_id:
                raise ValueError('--child-id requires --profile')
            birth = args.birth_date or profile.get('birth_date')
            school_start = args.school_start or profile.get('school_start')
            result['child_context_date'] = result['end']
            result['child'] = child_context(parse_date(result['end']),
                parse_date(birth) if birth else None,
                parse_date(school_start) if school_start else None, profile)
    except (ValueError, OverflowError, OSError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
