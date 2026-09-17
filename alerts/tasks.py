from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from celery import shared_task
from alerts.models import AccessLog, AccessResult, Alert, AlertType, AlertSeverity, AlertStatus
from accounts.models import User

@shared_task
def scan_access_patterns():
    """
    Celery Beat periodic task (Section 6):
    Scans AccessLog records against ANOMALY_RULES every 2 minutes.
    """
    now = timezone.now()
    rules = getattr(settings, 'ANOMALY_RULES', {})
    dedup_minutes = rules.get('DEDUP_MINUTES', 30)

    # 1. BULK_DOWNLOAD Rule
    bulk_rule = rules.get('BULK_DOWNLOAD', {})
    if bulk_rule.get('ENABLED', True):
        threshold = bulk_rule.get('THRESHOLD', 5)
        window = bulk_rule.get('WINDOW_MINUTES', 10)
        since_time = now - timedelta(minutes=window)

        for user in User.objects.filter(is_active=True):
            downloads = AccessLog.objects.filter(
                user=user,
                action="DOWNLOAD",
                result=AccessResult.ALLOWED,
                timestamp__gte=since_time
            )
            if downloads.count() >= threshold:
                # Check dedup cooldown
                recent_alert = Alert.objects.filter(
                    user=user,
                    alert_type=AlertType.BULK_DOWNLOAD,
                    status=AlertStatus.OPEN,
                    created_at__gte=now - timedelta(minutes=dedup_minutes)
                ).exists()

                if not recent_alert:
                    alert = Alert.objects.create(
                        alert_type=AlertType.BULK_DOWNLOAD,
                        severity=AlertSeverity.HIGH,
                        user=user,
                        case=downloads.first().case if downloads.first() else None,
                        description=f"User {user.username} downloaded {downloads.count()} files within {window} minutes."
                    )
                    alert.triggering_logs.set(downloads)

    # 2. OFF_HOURS_ACCESS Rule
    off_hours_rule = rules.get('OFF_HOURS_ACCESS', {})
    if off_hours_rule.get('ENABLED', True):
        start_hour = int(off_hours_rule.get('START_HOUR', '08:00').split(':')[0])
        end_hour = int(off_hours_rule.get('END_HOUR', '20:00').split(':')[0])

        current_hour = now.hour
        if current_hour < start_hour or current_hour >= end_hour:
            recent_logs = AccessLog.objects.filter(
                result=AccessResult.ALLOWED,
                timestamp__gte=now - timedelta(minutes=10)
            )
            for log in recent_logs:
                recent_alert = Alert.objects.filter(
                    user=log.user,
                    alert_type=AlertType.OFF_HOURS_ACCESS,
                    status=AlertStatus.OPEN,
                    created_at__gte=now - timedelta(minutes=dedup_minutes)
                ).exists()

                if not recent_alert:
                    alert = Alert.objects.create(
                        alert_type=AlertType.OFF_HOURS_ACCESS,
                        severity=AlertSeverity.MEDIUM,
                        user=log.user,
                        case=log.case,
                        description=f"User {log.user.username} performed off-hours action '{log.action}' at {now.strftime('%H:%M UTC')}."
                    )
                    alert.triggering_logs.add(log)

    # 3. UNAUTHORIZED_ATTEMPTS Rule
    unauth_rule = rules.get('UNAUTHORIZED_ATTEMPTS', {})
    if unauth_rule.get('ENABLED', True):
        threshold = unauth_rule.get('THRESHOLD', 3)
        window = unauth_rule.get('WINDOW_MINUTES', 15)
        since_time = now - timedelta(minutes=window)

        for user in User.objects.filter(is_active=True):
            denied_logs = AccessLog.objects.filter(
                user=user,
                result=AccessResult.DENIED,
                timestamp__gte=since_time
            )
            if denied_logs.count() >= threshold:
                recent_alert = Alert.objects.filter(
                    user=user,
                    alert_type=AlertType.UNAUTHORIZED_ATTEMPTS,
                    status=AlertStatus.OPEN,
                    created_at__gte=now - timedelta(minutes=dedup_minutes)
                ).exists()

                if not recent_alert:
                    alert = Alert.objects.create(
                        alert_type=AlertType.UNAUTHORIZED_ATTEMPTS,
                        severity=AlertSeverity.HIGH,
                        user=user,
                        case=denied_logs.first().case if denied_logs.first() else None,
                        description=f"User {user.username} had {denied_logs.count()} denied access attempts in {window} minutes."
                    )
                    alert.triggering_logs.set(denied_logs)

    return "Access pattern scan completed."
