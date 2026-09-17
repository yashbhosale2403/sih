# SecureDocs Security & Threat Model Specification

**Problem Statement SIH26190** — Secure Digital Document Management System

---

## 1. Threat Model & Mitigations

### Threat 1: Insider Tampering via Direct Database Access
- **Attack Scenario:** A corrupt DB admin or insider attempts to alter stored document version hashes or past ledger logs directly inside PostgreSQL.
- **Mitigation:**
  - **Merkle Hash Chain:** Each `LedgerEntry` stores `entry_hash = SHA256(document_hash + prev_entry_hash + action + actor.id + server_timestamp + case.id)`. Any direct DB manipulation breaks the forward hash chain and is immediately flagged by `verify_case_integrity(case_id)`.
  - **Database Immutability Grants (PostgreSQL):**
    ```sql
    CREATE ROLE ledger_writer;
    GRANT INSERT, SELECT ON ledger_ledgerentry TO ledger_writer;
    REVOKE UPDATE, DELETE ON ledger_ledgerentry FROM ledger_writer;
    ```
  - **Application-Level Defense-in-Depth:** In `LedgerEntry.save()`, any attempt to update an existing primary key or delete an entry raises an explicit `PermissionError`.

### Threat 2: Offline Device Theft or Compromised Cache
- **Attack Scenario:** A field officer's mobile device/laptop is stolen while containing cached sensitive case files.
- **Mitigation:**
  - Documents on disk are encrypted using **AES-256-GCM / Fernet** deriving keys using `MASTER_KEY`.
  - Offline IndexedDB payloads in browser contain SHA-256 hash assertions verified upon server sync.

### Threat 3: Credential Stuffing & Brute Force Attacks
- **Attack Scenario:** Automated attacker attempts dictionary attacks against user badge IDs or login endpoints.
- **Mitigation:**
  - Synchronous failure tracking at login time (`failed_login_count`).
  - After `MAX_FAILED_LOGINS` (default: 5) consecutive failures:
    - User status automatically set to `is_locked = True`.
    - High-severity `FAILED_LOGIN_LOCKOUT` Alert created.
    - All future login attempts blocked until an `ADMIN` unlocks the user account.

### Threat 4: Unauthorized Case Access & Privilege Escalation
- **Attack Scenario:** An authenticated officer attempts to inspect cases outside their assignment or scope.
- **Mitigation:**
  - Attribute-Based Access Control (**ABAC**): Single permission function `can_access(user, case)` enforces role checks AND active `CaseAssignment` check (`active=True`).
  - **Audit Logging:** Every denied access attempt logs an `AccessLog` row (`result=DENIED`), feeding the anomaly detection engine.

---

## 2. Dev Fallback Note (SQLite vs PostgreSQL)
In SQLite local development mode, PostgreSQL role grants (`REVOKE UPDATE, DELETE`) cannot be executed by SQLite engine.
However, application-level immutability override (`LedgerEntry.save()`) enforces append-only immutability in both SQLite and PostgreSQL.
When deployed on PostgreSQL 16, migration `ledger/migrations/0002_ledger_immutability_grants.py` applies PostgreSQL role grants automatically.
