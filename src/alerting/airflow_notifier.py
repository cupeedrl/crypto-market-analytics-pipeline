import logging
import requests
from typing import Dict, Any
from src.utils.config import Config

logger = logging.getLogger(__name__)


def send_failure_alert(context: Dict[str, Any]) -> None:
    """Send Discord alert when DAG or task fails using requests (no extra deps)"""
    if not Config.DISCORD_WEBHOOK_URL:
        logger.warning("Discord webhook URL not configured, skipping alert")
        return

    dag_id = context["dag"].dag_id
    task_id = (
        context["task_instance"].task_id if "task_instance" in context else "unknown"
    )
    execution_date = str(context.get("execution_date", "unknown"))
    run_id = context["dag_run"].run_id if "dag_run" in context else "unknown"

    exception = context.get("exception")
    error_msg = str(exception) if exception else "Unknown error"

    payload = {
        "embeds": [
            {
                "title": "❌ Airflow DAG Failed",
                "description": f"**DAG**: `{dag_id}`\n**Task**: `{task_id}`",
                "color": 16711680,
                "fields": [
                    {
                        "name": "📅 Execution Date",
                        "value": execution_date,
                        "inline": True,
                    },
                    {"name": "🔄 Run ID", "value": run_id, "inline": True},
                    {
                        "name": "❌ Error",
                        "value": f"```{error_msg[:500]}```",
                        "inline": False,
                    },
                ],
                "footer": {"text": "Crypto Analytics Pipeline"},
            }
        ]
    }

    try:
        response = requests.post(Config.DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        logger.info(f"Discord alert sent. Status: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send Discord alert: {str(e)}")


def send_success_alert(context: Dict[str, Any]) -> None:
    """Send Discord alert when DAG succeeds"""
    if not Config.DISCORD_WEBHOOK_URL:
        return

    dag_id = context["dag"].dag_id
    execution_date = str(context.get("execution_date", "unknown"))

    payload = {
        "embeds": [
            {
                "title": "✅ Airflow DAG Success",
                "description": f"**DAG**: `{dag_id}` completed successfully",
                "color": 65280,
                "fields": [
                    {
                        "name": "📅 Execution Date",
                        "value": execution_date,
                        "inline": True,
                    },
                ],
                "footer": {"text": "Crypto Analytics Pipeline"},
            }
        ]
    }

    try:
        requests.post(Config.DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        logger.info("Success alert sent to Discord")
    except Exception as e:
        logger.error(f"Failed to send success alert: {str(e)}")
