from django.db import migrations

def apply_postgres_grants(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'ledger_writer') THEN
                    CREATE ROLE ledger_writer;
                END IF;
            END
            $$;
            GRANT INSERT, SELECT ON ledger_ledgerentry TO ledger_writer;
            REVOKE UPDATE, DELETE ON ledger_ledgerentry FROM ledger_writer;
        """)

def reverse_postgres_grants(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute("""
            GRANT UPDATE, DELETE ON ledger_ledgerentry TO ledger_writer;
        """)

class Migration(migrations.Migration):

    dependencies = [
        ('ledger', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(apply_postgres_grants, reverse_code=reverse_postgres_grants),
    ]
