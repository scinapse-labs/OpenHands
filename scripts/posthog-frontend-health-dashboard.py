#!/usr/bin/env python3
"""Create a PostHog 'Frontend Health' dashboard with web vitals and error tracking tiles.

Requires environment variables:
  POSTHOG_API_KEY      -- PostHog personal API key (phx_...)
  POSTHOG_PROJECT_ID   -- PostHog project ID (e.g. 163845 for staging)

Idempotent: if a dashboard named "Frontend Health" already exists, prints its URL and exits.
"""

import os
import sys

import requests

POSTHOG_BASE = "https://us.posthog.com"
DASHBOARD_NAME = "Frontend Health"
DASHBOARD_DESCRIPTION = "Web vitals trends and JavaScript error tracking"


def get_env_or_exit(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"Error: {name} environment variable is not set", file=sys.stderr)
        sys.exit(1)
    return value


def api_headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def dashboard_url(project_id: str, dashboard_id: int) -> str:
    return f"{POSTHOG_BASE}/project/{project_id}/dashboard/{dashboard_id}"


def find_existing_dashboard(
    project_id: str, headers: dict
) -> int | None:
    """Return the ID of an existing 'Frontend Health' dashboard, or None."""
    url = f"{POSTHOG_BASE}/api/projects/{project_id}/dashboards/"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    for dash in resp.json().get("results", []):
        if dash.get("name") == DASHBOARD_NAME and not dash.get("deleted"):
            return dash["id"]
    return None


def create_dashboard(project_id: str, headers: dict) -> int:
    """Create the Frontend Health dashboard and return its ID."""
    url = f"{POSTHOG_BASE}/api/projects/{project_id}/dashboards/"
    payload = {
        "name": DASHBOARD_NAME,
        "description": DASHBOARD_DESCRIPTION,
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()["id"]


def web_vitals_insight(
    metric_name: str, metric_label: str, value_property: str, event_property: str
) -> dict:
    """Build insight payload for a web vitals trend line."""
    return {
        "name": f"Web Vitals -- {metric_label}",
        "query": {
            "kind": "TrendsQuery",
            "series": [
                {
                    "event": "$web_vitals",
                    "kind": "EventsNode",
                    "math": "avg",
                    "math_property": value_property,
                    "properties": [
                        {
                            "key": event_property,
                            "type": "event",
                            "operator": "is_set",
                        }
                    ],
                }
            ],
            "interval": "day",
            "dateRange": {
                "date_from": "-30d",
            },
            "trendsFilter": {
                "display": "ActionsLineGraph",
            },
        },
    }


def js_error_rate_insight() -> dict:
    """Build insight payload for daily JS error count."""
    return {
        "name": "JS Error Rate (daily count)",
        "query": {
            "kind": "TrendsQuery",
            "series": [
                {
                    "event": "$exception",
                    "kind": "EventsNode",
                    "math": "total",
                }
            ],
            "interval": "day",
            "dateRange": {
                "date_from": "-30d",
            },
            "trendsFilter": {
                "display": "ActionsLineGraph",
            },
        },
    }


def top_js_errors_insight() -> dict:
    """Build insight payload for top JS errors by exception type."""
    return {
        "name": "Top JS Errors (by exception type)",
        "query": {
            "kind": "TrendsQuery",
            "series": [
                {
                    "event": "$exception",
                    "kind": "EventsNode",
                    "math": "total",
                }
            ],
            "dateRange": {
                "date_from": "-30d",
            },
            "breakdownFilter": {
                "breakdowns": [
                    {
                        "property": "$exception_type",
                        "type": "event",
                    }
                ],
            },
            "trendsFilter": {
                "display": "ActionsTable",
            },
        },
    }


def create_insight(
    project_id: str, headers: dict, dashboard_id: int, insight_payload: dict
) -> None:
    """Create an insight and attach it to the dashboard."""
    url = f"{POSTHOG_BASE}/api/projects/{project_id}/insights/"
    payload = {
        **insight_payload,
        "dashboards": [dashboard_id],
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    print(f"  Created: {insight_payload['name']}")


def main() -> None:
    api_key = get_env_or_exit("POSTHOG_API_KEY")
    project_id = get_env_or_exit("POSTHOG_PROJECT_ID")
    headers = api_headers(api_key)

    # Check for existing dashboard (idempotent)
    existing_id = find_existing_dashboard(project_id, headers)
    if existing_id is not None:
        url = dashboard_url(project_id, existing_id)
        print(f"Dashboard '{DASHBOARD_NAME}' already exists: {url}")
        sys.exit(0)

    # Create dashboard
    print(f"Creating '{DASHBOARD_NAME}' dashboard...")
    dash_id = create_dashboard(project_id, headers)

    # Define all 6 insight tiles
    insights = [
        web_vitals_insight(
            "LCP",
            "LCP (Largest Contentful Paint)",
            "$web_vitals_LCP_value",
            "$web_vitals_LCP_event",
        ),
        web_vitals_insight(
            "FCP",
            "FCP (First Contentful Paint)",
            "$web_vitals_FCP_value",
            "$web_vitals_FCP_event",
        ),
        web_vitals_insight(
            "INP",
            "INP (Interaction to Next Paint)",
            "$web_vitals_INP_value",
            "$web_vitals_INP_event",
        ),
        web_vitals_insight(
            "CLS",
            "CLS (Cumulative Layout Shift)",
            "$web_vitals_CLS_value",
            "$web_vitals_CLS_event",
        ),
        js_error_rate_insight(),
        top_js_errors_insight(),
    ]

    # Create each insight on the dashboard
    for insight in insights:
        create_insight(project_id, headers, dash_id, insight)

    url = dashboard_url(project_id, dash_id)
    print(f"\nDashboard created successfully: {url}")


if __name__ == "__main__":
    main()
