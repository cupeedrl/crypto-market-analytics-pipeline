import logging
from typing import Any, Dict

import requests

from src.utils.config import Config

logger = logging.getLogger(__name__)


def send_failure_alert(context: Dict[str, Any]) -> None:
    """Send Discord alert when a DAG or task fails."""
    if not Config.DISCORD_WEBHOOK_URL:
        logger.warning("Discord webhook URL not configured, skipping alert")
        return

    dag = context.get("dag")
    dag_id = dag.dag_id if dag else "unknown"

    task_instance = context.get("task_instance")
    task_id = task_instance.task_id if task_instance else "DAG"

    execution_date = str(context.get("execution_date", "unknown"))

    dag_run = context.get("dag_run")
    run_id = dag_run.run_id if dag_run else "unknown"

    exception = context.get("exception")
    error_msg = str(exception) if exception else "Unknown error"

    payload = {
        "embeds": [
            {
                "title": "Airflow DAG Failed",
                "description": f"**DAG**: `{dag_id}`\n**Task**: `{task_id}`",
                "color": 16711680,
                "fields": [
                    {
                        "name": "Execution Date",
                        "value": execution_date,
                        "inline": True,
                    },
                    {
                        "name": "Run ID",
                        "value": run_id,
                        "inline": True,
                    },
                    {
                        "name": "Error",
                        "value": f"```{error_msg[:500]}```",
                        "inline": False,
                    },
                ],
                "footer": {"text": "Crypto Analytics Pipeline"},
            }
        ]
    }

    try:
        response = requests.post(
            Config.DISCORD_WEBHOOK_URL,
            json=payload,
            timeout=10,
        )
        logger.info(f"Discord alert sent. Status: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send Discord alert: {e}")


def send_success_alert(context: Dict[str, Any]) -> None:
    """Send Discord alert when a DAG succeeds."""
    if not Config.DISCORD_WEBHOOK_URL:
        return

    dag = context.get("dag")
    dag_id = dag.dag_id if dag else "unknown"

    execution_date = str(context.get("execution_date", "unknown"))

    payload = {
        "embeds": [
            {
                "title": "Airflow DAG Success",
                "description": f"**DAG**: `{dag_id}` completed successfully",
                "color": 65280,
                "fields": [
                    {
                        "name": "Execution Date",
                        "value": execution_date,
                        "inline": True,
                    }
                ],
                "footer": {"text": "Crypto Analytics Pipeline"},
            }
        ]
    }

    try:
        response = requests.post(
            Config.DISCORD_WEBHOOK_URL,
            json=payload,
            timeout=10,
        )
        logger.info(f"Success alert sent to Discord. Status: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send success alert: {e}")
