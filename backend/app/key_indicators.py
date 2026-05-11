from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.engine import Connection


PERCENT_KEYWORDS = (
    "taux",
    "pourcentage",
    "proportion",
    "part ",
    "part du",
    "part de",
    "penetration",
    "satisfaction",
    "disponibilite",
    "couverture",
    "utilisation",
)
COUNT_KEYWORDS = ("nombre", "nbre", "nb ", "volume", "dossier", "patient", "texte")
PERIODICITY_ORDER = {"Mensuelle": 0, "Trimestrielle": 1, "Semestrielle": 2, "Annuelle": 3}
VALID_MONTHS = {
    "Mensuelle": set(range(1, 13)),
    "Trimestrielle": {3, 6, 9, 12},
    "Semestrielle": {6, 12},
    "Annuelle": {12},
}
TARGET_FIELD_BY_PERIODICITY = {
    "Mensuelle": "cible_mensuelle",
    "Trimestrielle": "cible_trimestrielle",
    "Semestrielle": "cible_semestrielle",
    "Annuelle": "cible_annuelle",
}
MONTH_LABELS = {
    1: "Janv.",
    2: "Fevr.",
    3: "Mars",
    4: "Avr.",
    5: "Mai",
    6: "Juin",
    7: "Juil.",
    8: "Aout",
    9: "Sept.",
    10: "Oct.",
    11: "Nov.",
    12: "Dec.",
}


def _to_float(value: Decimal | int | None) -> float:
    return float(value or 0)


def _to_int(value: Decimal | int | None) -> int:
    return int(value or 0)


def _to_iso(value: date | None) -> str | None:
    return value.isoformat() if value else None


def _rate(part: int, whole: int) -> float:
    return round((part / whole) * 100, 1) if whole else 0.0


def _normalize(value: str | None) -> str:
    return (
        str(value or "")
        .lower()
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
        .replace("â", "a")
        .replace("î", "i")
        .replace("ï", "i")
        .replace("ô", "o")
        .replace("ù", "u")
        .replace("û", "u")
        .replace("ç", "c")
        .replace("œ", "oe")
    )


def _value_format(label: str, history: list[dict[str, object]]) -> str:
    normalized_label = _normalize(label)
    max_abs_value = max(
        (abs(float(item["value"])) for item in history if item["value"] is not None),
        default=0.0,
    )

    if any(keyword in normalized_label for keyword in COUNT_KEYWORDS):
        return "number"

    if max_abs_value <= 1.2 or any(keyword in normalized_label for keyword in PERCENT_KEYWORDS):
        return "percent"

    return "number"


def _trend_tolerance(value_format: str, previous_value: float) -> float:
    base_value = abs(previous_value)

    if value_format == "percent":
        return max(base_value * 0.03, 0.015)

    return max(base_value * 0.03, 1.0)


def _resolve_trend(value_format: str, latest_value: float | None, previous_value: float | None) -> str:
    if latest_value is None or previous_value is None:
        return "initial"

    delta = latest_value - previous_value
    tolerance = _trend_tolerance(value_format, previous_value)

    if delta > tolerance:
        return "up"

    if delta < -tolerance:
        return "down"

    return "stable"


def _build_period_label(periodicity: str, period_value: date) -> str:
    year = period_value.year
    month = period_value.month

    if periodicity == "Mensuelle":
        return f"{MONTH_LABELS.get(month, month)} {year}"

    if periodicity == "Trimestrielle":
        return f"T{month // 3} {year}"

    if periodicity == "Semestrielle":
        return f"S{1 if month == 6 else 2} {year}"

    return str(year)


def _is_valid_period(periodicity: str, period_value: date) -> bool:
    return period_value.month in VALID_MONTHS.get(periodicity, set(range(1, 13)))


def _build_valid_history(
    periodicity: str,
    raw_history: list[dict[str, object]],
) -> tuple[list[dict[str, object]], int]:
    valid_history = []
    ignored_points = 0

    for entry in raw_history:
        period_value = entry["periodDate"]

        if not isinstance(period_value, date):
            continue

        if not _is_valid_period(periodicity, period_value):
            ignored_points += 1
            continue

        valid_history.append(
            {
                "period": _to_iso(period_value),
                "periodLabel": _build_period_label(periodicity, period_value),
                "periodDate": period_value,
                "value": entry["value"],
            }
        )

    return valid_history, ignored_points


def _resolve_target_value(periodicity: str, row: dict[str, object]) -> float | None:
    field_name = TARGET_FIELD_BY_PERIODICITY[periodicity]
    value = _to_float(row[field_name])

    if value == 0:
        return None

    return value


def _resolve_period_target_value(
    indicator_code: str,
    periodicity: str,
    period_value: date,
    targets_by_indicator_year: dict[str, dict[int, dict[str, object]]],
    fallback_row: dict[str, object],
) -> float | None:
    indicator_targets = targets_by_indicator_year.get(indicator_code, {})
    target_row = indicator_targets.get(period_value.year)

    if target_row is not None:
        return _resolve_target_value(periodicity, target_row)

    # Backward compatibility: only use the legacy target columns when no
    # historized targets exist for this indicator at all. Missing years must
    # stay explicit to avoid biasing retrospective analysis.
    if indicator_targets:
        return None

    return _resolve_target_value(periodicity, fallback_row)


def _build_year_targets(
    periodicity: str,
    targets_by_year: dict[int, dict[str, object]],
) -> list[dict[str, object]]:
    return [
        {
            "year": year,
            "targetValue": _resolve_target_value(periodicity, row),
        }
        for year, row in sorted(targets_by_year.items())
    ]


def _attach_history_targets(
    indicator_code: str,
    periodicity: str,
    history: list[dict[str, object]],
    targets_by_indicator_year: dict[str, dict[int, dict[str, object]]],
    fallback_row: dict[str, object],
) -> list[dict[str, object]]:
    enriched_history = []

    for entry in history:
        period_value = entry["periodDate"]

        if not isinstance(period_value, date):
            enriched_history.append(entry)
            continue

        value = float(entry["value"]) if entry["value"] is not None else None
        target_value = _resolve_period_target_value(
            indicator_code,
            periodicity,
            period_value,
            targets_by_indicator_year,
            fallback_row,
        )

        enriched_history.append(
            {
                **entry,
                "targetValue": target_value,
                "targetStatus": _resolve_target_status(value, target_value),
                "targetGap": _target_gap_value(value, target_value),
                "targetGapRatio": _target_gap_ratio(value, target_value),
                "attainmentRate": _attainment_rate(value, target_value),
            }
        )

    return enriched_history


def _resolve_target_status(latest_value: float | None, target_value: float | None) -> str:
    if latest_value is None or target_value is None:
        return "no_target"

    if latest_value >= target_value:
        return "on_target"

    return "below_target"


def _target_gap_value(latest_value: float | None, target_value: float | None) -> float | None:
    if latest_value is None or target_value is None:
        return None

    return round(latest_value - target_value, 4)


def _target_gap_ratio(latest_value: float | None, target_value: float | None) -> float | None:
    if latest_value is None or target_value in (None, 0):
        return None

    return round(((latest_value / target_value) - 1) * 100, 1)


def _attainment_rate(latest_value: float | None, target_value: float | None) -> float | None:
    if latest_value is None or target_value in (None, 0):
        return None

    return round(min((latest_value / target_value) * 100, 100.0), 1)


def _attainment_bucket(attainment_rate: float | None) -> str:
    if attainment_rate is None:
        return "no_target"

    if attainment_rate >= 100:
        return "attained"

    if attainment_rate >= 80:
        return "on_track"

    if attainment_rate >= 50:
        return "watch"

    return "alert"


def _pressure_rank(item: dict[str, object]) -> tuple[int, int, float, int, str]:
    return (
        1 if item["targetStatus"] == "below_target" else 0,
        1 if item["trend"] == "down" else 0,
        abs(float(item["targetGapRatio"] or 0)),
        int(item["validHistoryCount"]),
        str(item["label"]),
    )


def _support_rank(item: dict[str, object]) -> tuple[int, int, float, int, str]:
    return (
        1 if item["targetStatus"] == "on_target" else 0,
        1 if item["trend"] == "up" else 0,
        float(item["targetGapRatio"] or 0),
        int(item["validHistoryCount"]),
        str(item["label"]),
    )


def _trend_score(item: dict[str, object]) -> tuple[int, float, int]:
    trend_weight = {"up": 2, "stable": 1, "initial": 0, "down": -2}.get(str(item["trend"]), 0)
    target_weight = {"on_target": 2, "below_target": -2, "no_target": 0}.get(str(item["targetStatus"]), 0)

    return (
        trend_weight + target_weight,
        float(item["targetGapRatio"] or 0),
        int(item["validHistoryCount"]),
    )


def _pick_axis_highlight(
    items: list[dict[str, object]],
    direction: str,
) -> dict[str, object] | None:
    if direction == "pressure":
        candidates = [item for item in items if item["latestValue"] is not None]
        return max(candidates, key=_pressure_rank, default=None)

    candidates = [item for item in items if item["latestValue"] is not None]
    return max(candidates, key=_support_rank, default=None)


def build_key_indicators_payload(connection: Connection) -> dict[str, object]:
    axis_rows = connection.execute(
        text(
            """
            SELECT
                code_axe,
                axe
            FROM axes
            ORDER BY id ASC
            """
        )
    ).mappings().all()

    indicator_rows = connection.execute(
        text(
            """
            SELECT
                code_indicateur,
                axe,
                code_axe,
                indicateur,
                periodicite,
                cible_mensuelle,
                cible_trimestrielle,
                cible_semestrielle,
                cible_annuelle
            FROM indicateurs
            ORDER BY
                COALESCE(NULLIF(code_axe, ''), 'zzzz'),
                code_indicateur ASC
            """
        )
    ).mappings().all()

    value_rows = connection.execute(
        text(
            """
            SELECT
                id_indicateur,
                periode,
                valeur
            FROM valeurs_indicateurs
            ORDER BY
                id_indicateur ASC,
                periode ASC
            """
        )
    ).mappings().all()

    target_rows = connection.execute(
        text(
            """
            SELECT
                id_indicateur,
                CAST(annee AS UNSIGNED) AS annee,
                cible_mensuelle,
                cible_trimestrielle,
                cible_semestrielle,
                cible_annuelle
            FROM cibles_indicateurs
            ORDER BY
                id_indicateur ASC,
                annee ASC
            """
        )
    ).mappings().all()

    values_by_indicator: dict[str, list[dict[str, object]]] = defaultdict(list)
    targets_by_indicator_year: dict[str, dict[int, dict[str, object]]] = defaultdict(dict)

    for row in value_rows:
        values_by_indicator[str(row["id_indicateur"])].append(
            {
                "periodDate": row["periode"],
                "value": _to_float(row["valeur"]) if row["valeur"] is not None else None,
            }
        )

    for row in target_rows:
        targets_by_indicator_year[str(row["id_indicateur"])][int(row["annee"])] = dict(row)

    indicator_items: list[dict[str, object]] = []
    indicators_by_axis: dict[str, list[dict[str, object]]] = defaultdict(list)
    valid_periods: list[date] = []

    for row in indicator_rows:
        code = str(row["code_indicateur"])
        label = str(row["indicateur"])
        axis_label = str(row["axe"])
        axis_code = str(row["code_axe"])
        periodicity = str(row["periodicite"])
        raw_history = list(values_by_indicator.get(code, []))
        valid_history, ignored_points = _build_valid_history(periodicity, raw_history)
        year_targets = _build_year_targets(periodicity, targets_by_indicator_year.get(code, {}))
        valid_history = _attach_history_targets(
            code,
            periodicity,
            valid_history,
            targets_by_indicator_year,
            dict(row),
        )

        if valid_history:
            valid_periods.extend(
                entry["periodDate"] for entry in valid_history if isinstance(entry["periodDate"], date)
            )

        latest_entry = valid_history[-1] if valid_history else None
        previous_entry = valid_history[-2] if len(valid_history) > 1 else None
        value_format = _value_format(label, valid_history)
        latest_value = float(latest_entry["value"]) if latest_entry and latest_entry["value"] is not None else None
        previous_value = (
            float(previous_entry["value"])
            if previous_entry and previous_entry["value"] is not None
            else None
        )
        target_value = (
            latest_entry["targetValue"]
            if latest_entry and "targetValue" in latest_entry
            else _resolve_target_value(periodicity, row)
        )
        target_status = _resolve_target_status(latest_value, target_value)
        target_gap = _target_gap_value(latest_value, target_value)
        target_gap_ratio = _target_gap_ratio(latest_value, target_value)
        attainment_rate = _attainment_rate(latest_value, target_value)
        trend = _resolve_trend(value_format, latest_value, previous_value)
        delta = latest_value - previous_value if latest_value is not None and previous_value is not None else None
        delta_ratio = (
            round((delta / abs(previous_value)) * 100, 1)
            if delta is not None and previous_value not in (None, 0)
            else None
        )

        item = {
            "code": code,
            "label": label,
            "axisLabel": axis_label,
            "axisCode": axis_code,
            "periodicity": periodicity,
            "periodicityOrder": PERIODICITY_ORDER.get(periodicity, 99),
            "valueFormat": value_format,
            "latestPeriod": latest_entry["period"] if latest_entry else None,
            "latestPeriodLabel": latest_entry["periodLabel"] if latest_entry else None,
            "latestValue": latest_value,
            "previousPeriod": previous_entry["period"] if previous_entry else None,
            "previousPeriodLabel": previous_entry["periodLabel"] if previous_entry else None,
            "previousValue": previous_value,
            "delta": round(delta, 4) if delta is not None else None,
            "deltaRatio": delta_ratio,
            "trend": trend,
            "targetValue": target_value,
            "targetStatus": target_status,
            "targetGap": target_gap,
            "targetGapRatio": target_gap_ratio,
            "attainmentRate": attainment_rate,
            "validHistoryCount": len(valid_history),
            "ignoredPoints": ignored_points,
            "yearTargets": year_targets,
            "history": [
                {
                    "period": entry["period"],
                    "periodLabel": entry["periodLabel"],
                    "value": entry["value"],
                    "targetValue": entry.get("targetValue"),
                    "targetStatus": entry.get("targetStatus"),
                    "targetGap": entry.get("targetGap"),
                    "targetGapRatio": entry.get("targetGapRatio"),
                    "attainmentRate": entry.get("attainmentRate"),
                }
                for entry in valid_history
            ],
        }

        indicator_items.append(item)
        indicators_by_axis[axis_code].append(item)

    latest_valid_period = max(valid_periods) if valid_periods else None
    total_indicators = len(indicator_items)
    active_axes = sum(1 for items in indicators_by_axis.values() if items)
    targeted_indicators = sum(1 for item in indicator_items if item["targetValue"] is not None)
    on_target_indicators = sum(1 for item in indicator_items if item["targetStatus"] == "on_target")
    below_target_indicators = sum(1 for item in indicator_items if item["targetStatus"] == "below_target")
    no_target_indicators = sum(1 for item in indicator_items if item["targetStatus"] == "no_target")
    comparable_indicators = sum(1 for item in indicator_items if int(item["validHistoryCount"]) > 1)
    upward_indicators = sum(1 for item in indicator_items if item["trend"] == "up")
    downward_indicators = sum(1 for item in indicator_items if item["trend"] == "down")
    stable_indicators = sum(1 for item in indicator_items if item["trend"] == "stable")
    initial_indicators = sum(1 for item in indicator_items if item["trend"] == "initial")

    axis_performance = []
    for axis_row in axis_rows:
        axis_code = str(axis_row["code_axe"])
        axis_label = str(axis_row["axe"])
        axis_indicators = indicators_by_axis.get(axis_code, [])

        if not axis_indicators:
            continue

        targeted_count = sum(1 for item in axis_indicators if item["targetValue"] is not None)
        on_target_count = sum(1 for item in axis_indicators if item["targetStatus"] == "on_target")
        below_target_count = sum(1 for item in axis_indicators if item["targetStatus"] == "below_target")
        no_target_count = sum(1 for item in axis_indicators if item["targetStatus"] == "no_target")
        comparable_count = sum(1 for item in axis_indicators if int(item["validHistoryCount"]) > 1)
        up_count = sum(1 for item in axis_indicators if item["trend"] == "up")
        down_count = sum(1 for item in axis_indicators if item["trend"] == "down")
        stable_count = sum(1 for item in axis_indicators if item["trend"] == "stable")
        initial_count = sum(1 for item in axis_indicators if item["trend"] == "initial")
        support_signal = _pick_axis_highlight(axis_indicators, "support")
        pressure_signal = _pick_axis_highlight(axis_indicators, "pressure")

        axis_performance.append(
            {
                "code": axis_code,
                "label": axis_label,
                "totalIndicators": len(axis_indicators),
                "targetedIndicators": targeted_count,
                "onTargetCount": on_target_count,
                "belowTargetCount": below_target_count,
                "noTargetCount": no_target_count,
                "onTargetRate": _rate(on_target_count, targeted_count),
                "belowTargetRate": _rate(below_target_count, targeted_count),
                "targetBalance": on_target_count - below_target_count,
                "comparableIndicators": comparable_count,
                "upCount": up_count,
                "downCount": down_count,
                "stableCount": stable_count,
                "initialCount": initial_count,
                "trendBalance": up_count - down_count,
                "supportSignal": (
                    {
                        "label": str(support_signal["label"]),
                        "targetStatus": str(support_signal["targetStatus"]),
                        "trend": str(support_signal["trend"]),
                    }
                    if support_signal
                    else None
                ),
                "pressureSignal": (
                    {
                        "label": str(pressure_signal["label"]),
                        "targetStatus": str(pressure_signal["targetStatus"]),
                        "trend": str(pressure_signal["trend"]),
                    }
                    if pressure_signal
                    else None
                ),
            }
        )

    axis_performance.sort(
        key=lambda item: (
            -int(item["belowTargetCount"]),
            int(item["onTargetCount"]),
            -int(item["downCount"]),
            str(item["label"]),
        )
    )

    best_axis = max(
        axis_performance,
        key=lambda item: (
            int(item["onTargetCount"]),
            -int(item["belowTargetCount"]),
            int(item["trendBalance"]),
            str(item["label"]),
        ),
        default=None,
    )
    weakest_axis = max(
        axis_performance,
        key=lambda item: (
            int(item["belowTargetCount"]),
            -int(item["onTargetCount"]),
            -int(item["trendBalance"]),
            str(item["label"]),
        ),
        default=None,
    )

    positive_axes = sum(1 for item in axis_performance if int(item["targetBalance"]) > 0)
    negative_axes = sum(1 for item in axis_performance if int(item["targetBalance"]) < 0)
    balanced_axes = sum(1 for item in axis_performance if int(item["targetBalance"]) == 0)
    targeted_axes = sum(1 for item in axis_performance if int(item["targetedIndicators"]) > 0)

    pressure_pool = sorted(
        (item for item in indicator_items if item["latestValue"] is not None),
        key=_pressure_rank,
        reverse=True,
    )
    support_pool = sorted(
        (item for item in indicator_items if item["latestValue"] is not None),
        key=_support_rank,
        reverse=True,
    )

    selected_codes: set[str] = set()
    signals: list[dict[str, object]] = []

    for bucket in (pressure_pool[:4], support_pool[:4], pressure_pool, support_pool):
        for item in bucket:
            code = str(item["code"])

            if code in selected_codes:
                continue

            signals.append(item)
            selected_codes.add(code)

            if len(signals) == 6:
                break

        if len(signals) == 6:
            break

    signals.sort(
        key=lambda item: (
            item["targetStatus"] != "below_target",
            item["trend"] != "down",
            -abs(float(item["targetGapRatio"] or 0)),
            -_trend_score(item)[0],
            str(item["axisLabel"]),
            str(item["label"]),
        )
    )

    indicators = sorted(
        indicator_items,
        key=lambda item: (
            str(item["axisCode"]),
            str(item["code"]),
            str(item["label"]),
        ),
    )

    attainment_totals = {
        "attained": 0,
        "on_track": 0,
        "watch": 0,
        "alert": 0,
        "no_target": 0,
    }

    for item in indicators:
        attainment_totals[_attainment_bucket(item["attainmentRate"])] += 1

    targeted_total = max(targeted_indicators, 1)
    attainment_breakdown = [
        {
            "key": "attained",
            "label": "Atteints (>= 100%)",
            "total": attainment_totals["attained"],
            "percentage": _rate(attainment_totals["attained"], targeted_total),
        },
        {
            "key": "on_track",
            "label": "En bonne voie (80% - 99%)",
            "total": attainment_totals["on_track"],
            "percentage": _rate(attainment_totals["on_track"], targeted_total),
        },
        {
            "key": "watch",
            "label": "A surveiller (50% - 79%)",
            "total": attainment_totals["watch"],
            "percentage": _rate(attainment_totals["watch"], targeted_total),
        },
        {
            "key": "alert",
            "label": "En alerte (< 50%)",
            "total": attainment_totals["alert"],
            "percentage": _rate(attainment_totals["alert"], targeted_total),
        },
    ]

    timeline_totals: dict[str, dict[str, object]] = {}
    for item in indicators:
        for entry in item["history"]:
            period = str(entry["period"] or "")
            period_label = str(entry["periodLabel"] or "")
            rate = entry.get("attainmentRate")

            if not period or rate is None:
                continue

            aggregate = timeline_totals.setdefault(
                period,
                {
                    "period": period,
                    "periodLabel": period_label,
                    "rateTotal": 0.0,
                    "indicatorCount": 0,
                },
            )
            aggregate["rateTotal"] = float(aggregate["rateTotal"]) + float(rate)
            aggregate["indicatorCount"] = int(aggregate["indicatorCount"]) + 1

    attainment_timeline = [
        {
            "period": values["period"],
            "periodLabel": values["periodLabel"],
            "averageRate": round(float(values["rateTotal"]) / int(values["indicatorCount"]), 1),
            "indicatorCount": int(values["indicatorCount"]),
        }
        for _, values in sorted(timeline_totals.items())
        if int(values["indicatorCount"]) > 0
    ][-12:]

    return {
        "summary": {
            "totalIndicators": total_indicators,
            "activeAxes": active_axes,
            "registeredAxes": len(axis_rows),
            "targetedAxes": targeted_axes,
            "targetedIndicators": targeted_indicators,
            "onTargetIndicators": on_target_indicators,
            "belowTargetIndicators": below_target_indicators,
            "noTargetIndicators": no_target_indicators,
            "comparableIndicators": comparable_indicators,
            "upwardIndicators": upward_indicators,
            "downwardIndicators": downward_indicators,
            "stableIndicators": stable_indicators,
            "initialIndicators": initial_indicators,
            "positiveAxes": positive_axes,
            "negativeAxes": negative_axes,
            "balancedAxes": balanced_axes,
            "latestValidPeriod": _to_iso(latest_valid_period),
            "latestValidPeriodLabel": _build_period_label("Mensuelle", latest_valid_period)
            if latest_valid_period
            else None,
            "bestAxis": best_axis,
            "weakestAxis": weakest_axis,
        },
        "axisPerformance": axis_performance,
        "indicators": indicators,
        "signals": signals,
        "attainmentBreakdown": attainment_breakdown,
        "noTargetIndicators": attainment_totals["no_target"],
        "attainmentTimeline": attainment_timeline,
    }
