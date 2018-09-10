from django.contrib.postgres.fields import ArrayField
from django.db import migrations, models


def convert_reimbursement_numbers_to_array(apps, schema_editor):
    Reimbursement = apps.get_model("chamber_of_deputies", "Reimbursement")
    for record in Reimbursement.objects.all():
        record.numbers = record.reimbursement_numbers.split(", ")
        record.save()


def convert_reimbursement_numbers_to_array_rollback(apps, schema_editor):
    Reimbursement = apps.get_model("chamber_of_deputies", "Reimbursement")
    for record in Reimbursement.objects.all():
        record.reimbursement_numbers = ", ".join(record.numbers)
        record.save()


class Migration(migrations.Migration):

    dependencies = [
        ("chamber_of_deputies", "0003_remove_available_in_latest_dataset_field")
    ]

    operations = [
        migrations.AlterField(
            model_name="reimbursement",
            name="document_id",
            field=models.IntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name="reimbursement",
            name="supplier",
            field=models.CharField(max_length=256),
        ),
        migrations.AlterField(
            model_name="reimbursement",
            name="issue_date",
            field=models.DateField(null=True),
        ),
        migrations.RenameField(
            model_name="reimbursement",
            old_name="total_reimbursement_value",
            new_name="total_value",
        ),
        migrations.RenameField(
            model_name="reimbursement",
            old_name="subquota_id",
            new_name="subquota_number",
        ),
        migrations.AddField(
            model_name="reimbursement",
            name="numbers",
            field=ArrayField(models.CharField(max_length=128), default=list),
        ),
        migrations.RunPython(
            convert_reimbursement_numbers_to_array,
            convert_reimbursement_numbers_to_array_rollback,
        ),
        migrations.RemoveField(model_name="reimbursement", name="net_values"),
        migrations.RemoveField(
            model_name="reimbursement", name="reimbursement_numbers"
        ),
        migrations.RemoveField(model_name="reimbursement", name="reimbursement_values"),
    ]
