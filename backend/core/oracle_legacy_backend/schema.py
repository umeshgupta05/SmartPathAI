import hashlib

from django.db import DatabaseError
from django.db.models import AutoField, BigAutoField, SmallAutoField
from django.db.backends.oracle.schema import DatabaseSchemaEditor as OracleSchemaEditor


class DatabaseSchemaEditor(OracleSchemaEditor):
    def _is_identity_column(self, table_name, column_name):
        try:
            return super()._is_identity_column(table_name, column_name)
        except DatabaseError:
            return False

    def _sequence_and_trigger_names(self, table_name, column_name):
        seed = f"{table_name}:{column_name}".encode("utf-8")
        suffix = hashlib.md5(seed).hexdigest()[:10].upper()
        sequence_name = f"SQ_{suffix}"
        trigger_name = f"TR_{suffix}"
        return sequence_name, trigger_name

    def create_model(self, model):
        super().create_model(model)

        for field in model._meta.local_fields:
            if isinstance(field, (AutoField, BigAutoField, SmallAutoField)):
                self._create_legacy_autoincrement(model._meta.db_table, field.column)

    def delete_model(self, model):
        for field in model._meta.local_fields:
            if isinstance(field, (AutoField, BigAutoField, SmallAutoField)):
                self._drop_legacy_autoincrement(model._meta.db_table, field.column)
        super().delete_model(model)

    def _create_legacy_autoincrement(self, table_name, column_name):
        sequence_name, trigger_name = self._sequence_and_trigger_names(table_name, column_name)
        quoted_sequence = self.quote_name(sequence_name)
        quoted_trigger = self.quote_name(trigger_name)
        quoted_table = self.quote_name(table_name)
        quoted_column = self.quote_name(column_name)

        self.execute(
            f"""
            DECLARE
                seq_count INTEGER;
            BEGIN
                SELECT COUNT(1) INTO seq_count FROM USER_SEQUENCES WHERE SEQUENCE_NAME = '{sequence_name}';
                IF seq_count = 0 THEN
                    EXECUTE IMMEDIATE 'CREATE SEQUENCE {quoted_sequence} START WITH 1 INCREMENT BY 1 NOCACHE';
                END IF;
            END;
            """
        )

        self.execute(
            f"""
            CREATE OR REPLACE TRIGGER {quoted_trigger}
            BEFORE INSERT ON {quoted_table}
            FOR EACH ROW
            WHEN (new.{column_name} IS NULL)
            BEGIN
                SELECT {quoted_sequence}.NEXTVAL INTO :new.{quoted_column} FROM dual;
            END;
            """
        )

    def _drop_legacy_autoincrement(self, table_name, column_name):
        sequence_name, trigger_name = self._sequence_and_trigger_names(table_name, column_name)
        quoted_trigger = self.quote_name(trigger_name)
        quoted_sequence = self.quote_name(sequence_name)

        self.execute(
            f"""
            BEGIN
                EXECUTE IMMEDIATE 'DROP TRIGGER {quoted_trigger}';
            EXCEPTION
                WHEN OTHERS THEN
                    IF SQLCODE != -4080 THEN
                        RAISE;
                    END IF;
            END;
            """
        )

        self.execute(
            f"""
            BEGIN
                EXECUTE IMMEDIATE 'DROP SEQUENCE {quoted_sequence}';
            EXCEPTION
                WHEN OTHERS THEN
                    IF SQLCODE != -2289 THEN
                        RAISE;
                    END IF;
            END;
            """
        )
