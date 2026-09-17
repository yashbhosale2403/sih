# SecureDocs — Secure Digital Document Management System

**SIH26190 Prototype** | Sponsor: Ministry of Home Affairs | Category: Software

SecureDocs provides legal and investigation agencies with a tamper-proof document management system anchored by a SHA-256 Merkle chain-of-custody ledger, explainable audit dashboard, proactive anomaly detection, and offline sync capability.

---

## Technical Stack & Dependencies
- **Python:** 3.11+
- **Framework:** Django 5.0.x & Django REST Framework 3.15.x
- **Token Auth:** `djangorestframework-simplejwt`
- **Asynchronous & Scheduled Tasks:** Celery 5.4.x + Redis 7.x
- **Encryption:** `cryptography` (AES-256-GCM / Fernet key derivation)
- **Frontend:** Django Templates + HTMX + Alpine.js + PWA Service Worker / IndexedDB
- **PDF Generation:** ReportLab / WeasyPrint

---

## Setup & Running Locally

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Migrations:**
   ```bash
   python manage.py migrate
   ```

3. **Run Dev Server:**
   ```bash
   python manage.py runserver
   ```

4. **Run Tests:**
   ```bash
   pytest
   ```

---

## Database Immutability Note
PostgreSQL 16 is recommended for production. In PostgreSQL, `REVOKE UPDATE, DELETE ON ledger_ledgerentry FROM ledger_writer` guarantees database-level append-only immutability.
In dev mode with SQLite 3, database grants are gracefully skipped and immutability is enforced via Django model `save()` & `delete()` method overrides.
