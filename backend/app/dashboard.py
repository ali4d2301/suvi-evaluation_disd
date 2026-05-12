from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import text

from app.database import engine
from app.key_indicators import build_key_indicators_payload


RAW_COMPLETED_STATUSES = {"Terminée", "Réalisée"}
DISPLAY_COMPLETED_STATUS = "Réalisée"
STATUS_ORDER = [DISPLAY_COMPLETED_STATUS, "En cours", "Non démarrée", "Suspendue", "Annulée"]


def _to_float(value: Decimal | int | None) -> float:
    return float(value or 0)


def _to_int(value: Decimal | int | None) -> int:
    return int(value or 0)


def _to_iso(value: date | datetime | None) -> str | None:
    return value.isoformat() if value else None


def _display_status(value: str | None) -> str:
    if value in RAW_COMPLETED_STATUSES:
        return DISPLAY_COMPLETED_STATUS
    return str(value or "")


def _rate(part: int, whole: int) -> float:
    return round((part / whole) * 100, 1) if whole else 0.0


def _build_spotlight(summary: dict[str, int | float]) -> dict[str, str]:
    if summary["startedActivities"] == 0:
        return {
            "title": "",
            "message": f"{summary['notStartedActivities']} activités sont enregistrées sans démarrage effectif.",
        }

    if summary["overdueActivities"] > 0:
        return {
            "title": "",
            "message": f"{summary['overdueActivities']} activités dépassent leur horizon planifié.",
        }

    return {
        "title": "",
        "message": (
            f"{summary['startedActivities']} activités ont déjà démarré. "
            f"{summary['coveredAxes']} axes et {summary['coveredProjects']} projets sont couverts."
        ),
    }


def get_dashboard_payload() -> dict[str, object]:
    with engine.connect() as connection:
        key_indicators = build_key_indicators_payload(connection)
        last_data_update_row = connection.execute(
            text(
                """
                SELECT
                    MAX(last_updated_at) AS last_data_updated_at
                FROM (
                    SELECT MAX(COALESCE(updated_at, created_at)) AS last_updated_at FROM activite
                    UNION ALL
                    SELECT MAX(COALESCE(updated_at, created_at)) AS last_updated_at FROM projets
                    UNION ALL
                    SELECT MAX(COALESCE(updated_at, created_at)) AS last_updated_at FROM axes
                    UNION ALL
                    SELECT MAX(COALESCE(updated_at, created_at)) AS last_updated_at FROM indicateurs
                    UNION ALL
                    SELECT MAX(COALESCE(updated_at, created_at)) AS last_updated_at FROM valeurs_indicateurs
                    UNION ALL
                    SELECT MAX(COALESCE(updated_at, created_at)) AS last_updated_at FROM cibles_indicateurs
                ) AS updates
                """
            )
        ).mappings().one()

        summary_row = connection.execute(
            text(
                """
                SELECT
                    COUNT(*) AS total_activities,
                    COUNT(DISTINCT a.projet) AS covered_projects,
                    COALESCE((SELECT COUNT(*) FROM projets), 0) AS registered_projects,
                    COUNT(DISTINCT COALESCE(ax.axe, a.axe_strategique)) AS covered_axes,
                    COALESCE((SELECT COUNT(*) FROM axes), 0) AS registered_axes,
                    COUNT(DISTINCT NULLIF(TRIM(a.service_responsable), '')) AS services_in_charge,
                    SUM(CASE WHEN a.etat IN ('Terminée', 'Réalisée') THEN 1 ELSE 0 END) AS completed_activities,
                    SUM(CASE WHEN a.etat IN ('En cours', 'Terminée', 'Réalisée') THEN 1 ELSE 0 END) AS started_activities,
                    SUM(CASE WHEN a.etat = 'En cours' THEN 1 ELSE 0 END) AS in_progress_activities,
                    SUM(CASE WHEN a.etat = 'Non démarrée' THEN 1 ELSE 0 END) AS not_started_activities,
                    SUM(CASE WHEN a.etat = 'Suspendue' THEN 1 ELSE 0 END) AS suspended_activities,
                    SUM(CASE WHEN a.etat = 'Annulée' THEN 1 ELSE 0 END) AS cancelled_activities,
                    SUM(CASE WHEN a.date_fin_planifiee IS NULL THEN 1 ELSE 0 END) AS activities_without_end_date,
                    COALESCE(SUM(a.budget_previsionnel), 0) AS planned_budget,
                    COALESCE(SUM(a.montant_depense), 0) AS spent_budget,
                    SUM(
                        CASE
                            WHEN a.date_fin_planifiee IS NOT NULL
                                AND a.date_fin_planifiee < CURDATE()
                                AND a.etat NOT IN ('Terminée', 'Réalisée', 'Annulée')
                            THEN 1
                            ELSE 0
                        END
                    ) AS overdue_activities
                FROM activite a
                LEFT JOIN projets p ON p.projet = a.projet
                LEFT JOIN axes ax ON ax.id = p.id_axe
                """
            )
        ).mappings().one()

        status_rows = connection.execute(
            text(
                """
                SELECT
                    etat AS label,
                    COUNT(*) AS total
                FROM activite
                GROUP BY etat
                ORDER BY FIELD(etat, 'Réalisée', 'Terminée', 'En cours', 'Non démarrée', 'Suspendue', 'Annulée')
                """
            )
        ).mappings().all()

        axis_rows = connection.execute(
            text(
                """
                SELECT
                    COALESCE(ax.axe, a.axe_strategique) AS label,
                    COUNT(*) AS total
                FROM activite a
                LEFT JOIN projets p ON p.projet = a.projet
                LEFT JOIN axes ax ON ax.id = p.id_axe
                GROUP BY COALESCE(ax.axe, a.axe_strategique)
                ORDER BY total DESC, label ASC
                """
            )
        ).mappings().all()

        project_rows = connection.execute(
            text(
                """
                SELECT
                    a.projet AS label,
                    COALESCE(ax.axe, a.axe_strategique) AS axe_label,
                    COUNT(*) AS total
                FROM activite a
                LEFT JOIN projets p ON p.projet = a.projet
                LEFT JOIN axes ax ON ax.id = p.id_axe
                GROUP BY a.projet, COALESCE(ax.axe, a.axe_strategique)
                ORDER BY total DESC, label ASC
                LIMIT 6
                """
            )
        ).mappings().all()

        service_rows = connection.execute(
            text(
                """
                SELECT
                    COALESCE(NULLIF(TRIM(service_responsable), ''), 'Non renseigné') AS label,
                    COUNT(*) AS total
                FROM activite
                GROUP BY COALESCE(NULLIF(TRIM(service_responsable), ''), 'Non renseigné')
                ORDER BY total DESC, label ASC
                LIMIT 6
                """
            )
        ).mappings().all()

        service_status_rows = connection.execute(
            text(
                """
                SELECT
                    COALESCE(NULLIF(TRIM(service_responsable), ''), 'Non renseigné') AS service_label,
                    etat AS status_label,
                    COUNT(*) AS total
                FROM activite
                GROUP BY
                    COALESCE(NULLIF(TRIM(service_responsable), ''), 'Non renseigné'),
                    etat
                """
            )
        ).mappings().all()

        timeline_rows = connection.execute(
            text(
                """
                SELECT
                    DATE_FORMAT(date_debut_planifiee, '%Y-%m') AS month_key,
                    COUNT(*) AS total
                FROM activite
                WHERE date_debut_planifiee IS NOT NULL
                GROUP BY DATE_FORMAT(date_debut_planifiee, '%Y-%m')
                ORDER BY month_key ASC
                """
            )
        ).mappings().all()

        activity_rows = connection.execute(
            text(
                """
                SELECT
                    a.id,
                    COALESCE(ax.axe, a.axe_strategique) AS axe_label,
                    a.projet,
                    a.activite,
                    a.objectif_general,
                    COALESCE(NULLIF(TRIM(a.service_responsable), ''), 'Non renseigné') AS service_responsable,
                    COALESCE(NULLIF(TRIM(a.point_focal), ''), 'Non renseigné') AS point_focal,
                    a.observations,
                    a.date_debut_planifiee,
                    a.date_fin_planifiee,
                    a.date_debut_execution,
                    a.date_fin_execution,
                    a.etat,
                    a.budget_previsionnel,
                    a.montant_depense
                FROM activite a
                LEFT JOIN projets p ON p.projet = a.projet
                LEFT JOIN axes ax ON ax.id = p.id_axe
                ORDER BY
                    a.date_fin_planifiee IS NULL,
                    a.date_fin_planifiee ASC,
                    CASE a.etat
                        WHEN 'En cours' THEN 1
                        WHEN 'Non démarrée' THEN 2
                        WHEN 'Suspendue' THEN 3
                        WHEN 'Annulée' THEN 4
                        WHEN 'Réalisée' THEN 5
                        WHEN 'Terminée' THEN 5
                        ELSE 6
                    END,
                    a.date_debut_planifiee IS NULL,
                    a.date_debut_planifiee ASC,
                    a.id ASC
                """
            )
        ).mappings().all()

    total_activities = _to_int(summary_row["total_activities"])
    covered_projects = _to_int(summary_row["covered_projects"])
    registered_projects = _to_int(summary_row["registered_projects"])
    covered_axes = _to_int(summary_row["covered_axes"])
    registered_axes = _to_int(summary_row["registered_axes"])
    completed_activities = _to_int(summary_row["completed_activities"])
    started_activities = _to_int(summary_row["started_activities"])
    not_started_activities = _to_int(summary_row["not_started_activities"])
    planned_budget = _to_float(summary_row["planned_budget"])
    spent_budget = _to_float(summary_row["spent_budget"])
    activities_without_end_date = _to_int(summary_row["activities_without_end_date"])

    summary = {
        "totalActivities": total_activities,
        "coveredProjects": covered_projects,
        "registeredProjects": registered_projects,
        "coveredAxes": covered_axes,
        "registeredAxes": registered_axes,
        "servicesInCharge": _to_int(summary_row["services_in_charge"]),
        "completedActivities": completed_activities,
        "startedActivities": started_activities,
        "inProgressActivities": _to_int(summary_row["in_progress_activities"]),
        "notStartedActivities": not_started_activities,
        "suspendedActivities": _to_int(summary_row["suspended_activities"]),
        "cancelledActivities": _to_int(summary_row["cancelled_activities"]),
        "activitiesWithoutEndDate": activities_without_end_date,
        "plannedBudget": planned_budget,
        "spentBudget": spent_budget,
        "overdueActivities": _to_int(summary_row["overdue_activities"]),
        "completionRate": _rate(completed_activities, total_activities),
        "kickoffRate": _rate(started_activities, total_activities),
        "projectCoverageRate": _rate(covered_projects, registered_projects),
        "axisCoverageRate": _rate(covered_axes, registered_axes),
        "planningCompletenessRate": _rate(
            total_activities - activities_without_end_date,
            total_activities,
        ),
        "budgetConsumptionRate": round((spent_budget / planned_budget) * 100, 1)
        if planned_budget
        else 0.0,
    }

    status_totals: dict[str, int] = {}
    for row in status_rows:
        label = _display_status(row["label"])
        status_totals[label] = status_totals.get(label, 0) + _to_int(row["total"])
    status_breakdown = [
        {
            "label": status,
            "total": status_totals.get(status, 0),
            "percentage": _rate(status_totals.get(status, 0), total_activities),
        }
        for status in STATUS_ORDER
    ]

    axis_breakdown = [
        {
            "label": str(row["label"]),
            "total": _to_int(row["total"]),
            "percentage": _rate(_to_int(row["total"]), total_activities),
        }
        for row in axis_rows
    ]

    project_breakdown = [
        {
            "label": str(row["label"]),
            "axeLabel": str(row["axe_label"]),
            "total": _to_int(row["total"]),
            "share": _rate(_to_int(row["total"]), total_activities),
        }
        for row in project_rows
    ]

    service_breakdown = [
        {"label": str(row["label"]), "total": _to_int(row["total"])}
        for row in service_rows
    ]

    service_status_totals: dict[str, dict[str, int]] = {}
    for row in service_status_rows:
        service_label = str(row["service_label"])
        status_label = _display_status(row["status_label"])
        service_totals = service_status_totals.setdefault(service_label, {})
        service_totals[status_label] = service_totals.get(status_label, 0) + _to_int(row["total"])

    sorted_service_items = sorted(
        service_status_totals.items(),
        key=lambda item: (-sum(item[1].values()), item[0]),
    )

    service_status_breakdown = [
        {
            "label": service_label,
            "total": sum(status_totals.values()),
            "statuses": [
                {
                    "label": status,
                    "total": status_totals.get(status, 0),
                    "percentage": _rate(status_totals.get(status, 0), sum(status_totals.values())),
                }
                for status in STATUS_ORDER
            ],
        }
        for service_label, status_totals in sorted_service_items
    ]

    timeline = [
        {
            "monthKey": str(row["month_key"]),
            "total": _to_int(row["total"]),
        }
        for row in timeline_rows
    ]

    activities = [
        {
            "id": _to_int(row["id"]),
            "axeLabel": str(row["axe_label"]),
            "project": str(row["projet"]),
            "activity": str(row["activite"]),
            "generalObjective": str(row["objectif_general"] or "").strip(),
            "service": str(row["service_responsable"]),
            "pointFocal": str(row["point_focal"]),
            "observation": str(row["observations"] or "").strip(),
            "plannedStart": _to_iso(row["date_debut_planifiee"]),
            "plannedEnd": _to_iso(row["date_fin_planifiee"]),
            "executionStart": _to_iso(row["date_debut_execution"]),
            "executionEnd": _to_iso(row["date_fin_execution"]),
            "status": _display_status(row["etat"]),
            "plannedBudget": _to_float(row["budget_previsionnel"]),
            "spentBudget": _to_float(row["montant_depense"]),
        }
        for row in activity_rows
    ]

    return {
        "generatedAt": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "lastDataUpdatedAt": _to_iso(last_data_update_row["last_data_updated_at"]),
        "spotlight": _build_spotlight(summary),
        "summary": summary,
        "keyIndicators": key_indicators,
        "statusBreakdown": status_breakdown,
        "axisBreakdown": axis_breakdown,
        "projectBreakdown": project_breakdown,
        "serviceBreakdown": service_breakdown,
        "serviceStatusBreakdown": service_status_breakdown,
        "timeline": timeline,
        "activities": activities,
    }
