"""
modules/automation.py
=======================================================
Automation
=======================================================
- Schedule tasks
- Send emails
- Create reminders
- Run scripts
- Generate reports
- Start applications automatically
"""

import smtplib
import subprocess
from email.mime.text import MIMEText
from apscheduler.schedulers.background import BackgroundScheduler
from config import Config
from core.memory import Memory
from utils.logger import get_logger

logger = get_logger("jarvis.automation")
memory = Memory()

scheduler = BackgroundScheduler()
scheduler.start()


# ---------- Scheduling ----------
def schedule_task(job_id: str, func, trigger: str = "interval", **trigger_args):
    """trigger: 'interval' (e.g. minutes=30) or 'cron' (e.g. hour=8, minute=0)."""
    scheduler.add_job(func, trigger, id=job_id, replace_existing=True, **trigger_args)
    logger.info(f"Scheduled job '{job_id}' ({trigger}: {trigger_args})")
    return job_id


def cancel_task(job_id: str):
    scheduler.remove_job(job_id)
    logger.info(f"Cancelled job '{job_id}'")


def list_scheduled_jobs():
    return [
        {"id": job.id, "next_run": str(job.next_run_time)}
        for job in scheduler.get_jobs()
    ]


# ---------- Reminders (persisted via Memory's task table) ----------
def create_reminder(title: str) -> int:
    task_id = memory.add_task(title)
    logger.info(f"Reminder created: [{task_id}] {title}")
    return task_id


def complete_reminder(task_id: int):
    memory.complete_task(task_id)


def list_reminders(status: str | None = None):
    return memory.list_tasks(status)


# ---------- Email ----------
def send_email(to_addr: str, subject: str, body: str) -> bool:
    if not (Config.SMTP_HOST and Config.SMTP_USER and Config.SMTP_PASS):
        logger.warning("SMTP not configured - email not sent.")
        return False
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = Config.SMTP_USER
    msg["To"] = to_addr
    try:
        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
            server.starttls()
            server.login(Config.SMTP_USER, Config.SMTP_PASS)
            server.sendmail(Config.SMTP_USER, [to_addr], msg.as_string())
        logger.info(f"Email sent to {to_addr}: {subject}")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error(f"send_email failed: {exc}")
        return False


# ---------- Scripts ----------
def run_script(path: str, args: list[str] | None = None, timeout: int = 30) -> dict:
    cmd = ["python", path] + (args or [])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Script timed out.", "returncode": -1}


# ---------- Reports ----------
def generate_daily_report() -> str:
    from modules import system_monitor
    snap = system_monitor.full_snapshot()
    reminders = list_reminders(status="pending")
    lines = [
        "=== JARVIS Daily Report ===",
        f"CPU: {snap['cpu']['percent']}%",
        f"Memory: {snap['memory']['percent']}%",
        f"Battery: {snap['battery']}",
        f"Pending reminders: {len(reminders)}",
    ]
    report = "\n".join(lines)
    logger.info("Generated daily report.")
    return report
