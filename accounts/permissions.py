from accounts.models import UserRole, CaseAssignment
from alerts.models import AccessLog, AccessResult

def get_client_ip(request):
    if not request:
        return "127.0.0.1"
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')

def _log_denied(user, case, action, request):
    ip = get_client_ip(request)
    AccessLog.objects.create(
        user=user,
        case=case,
        action=action,
        result=AccessResult.DENIED,
        ip_address=ip
    )

def can_access(user, case, action="ACCESS", request=None) -> bool:
    """
    ABAC & RBAC Shared Permission check:
    - ADMIN role has global access to all cases and all operations.
    - Other roles require an active CaseAssignment (active=True) AND role permission for specific actions.
    - Every denied attempt creates an AccessLog row with result=DENIED.
    """
    if not user or not user.is_authenticated or user.is_locked:
        return False

    # 1. Action-level Role-Based Access Control (RBAC)
    if case and case.status == 'CLOSED' and user.role in [UserRole.INVESTIGATING_OFFICER, UserRole.VIEWER]:
        _log_denied(user, case, action, request)
        return False

    if user.role == UserRole.INVESTIGATING_OFFICER:
        if action in ["EXPORT_AUDIT_PDF", "REDACT_DOCUMENT"]:
            _log_denied(user, case, action, request)
            return False
    elif user.role == UserRole.LEGAL_REVIEWER:
        if action in ["UPLOAD_DOCUMENT", "NEW_DOCUMENT_VERSION", "REDACT_DOCUMENT"]:
            _log_denied(user, case, action, request)
            return False
    elif user.role == UserRole.VIEWER:
        if action in ["UPLOAD_DOCUMENT", "NEW_DOCUMENT_VERSION", "REDACT_DOCUMENT", "EXPORT_AUDIT_PDF"]:
            _log_denied(user, case, action, request)
            return False

    # 2. Case-level Attribute-Based Access Control (ABAC)
    allowed = False
    if user.role == UserRole.ADMIN or user.is_superuser:
        allowed = True
    elif case and CaseAssignment.objects.filter(user=user, case=case, active=True).exists():
        allowed = True

    if not allowed and user.is_authenticated:
        _log_denied(user, case, action, request)

    return allowed
