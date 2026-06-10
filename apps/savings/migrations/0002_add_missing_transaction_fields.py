from django.db import migrations


def add_missing_transaction_columns(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    cursor.execute("PRAGMA table_info('savings_savingstransaction')")
    existing_columns = {row[1] for row in cursor.fetchall()}

    if 'reversed_at' not in existing_columns:
        cursor.execute('ALTER TABLE savings_savingstransaction ADD COLUMN reversed_at datetime NULL')
    if 'is_reversed' not in existing_columns:
        cursor.execute('ALTER TABLE savings_savingstransaction ADD COLUMN is_reversed bool NOT NULL DEFAULT 0')
    if 'original_transaction_id' not in existing_columns:
        cursor.execute('ALTER TABLE savings_savingstransaction ADD COLUMN original_transaction_id bigint NULL')
    if 'reversed_by_id' not in existing_columns:
        cursor.execute('ALTER TABLE savings_savingstransaction ADD COLUMN reversed_by_id bigint NULL')


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('savings', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_missing_transaction_columns, noop_reverse),
    ]
