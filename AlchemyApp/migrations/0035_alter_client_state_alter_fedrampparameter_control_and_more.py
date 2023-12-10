# Generated by Django 4.2 on 2023-07-16 22:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('AlchemyApp', '0034_nistcontrol_related_controls_alter_client_state'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='state',
            field=models.CharField(blank=True, choices=[('VA', 'Virginia'), ('IL', 'Illinois'), ('MI', 'Michigan'), ('WI', 'Wisconsin'), ('NY', 'New York'), ('DE', 'Delaware'), ('DC', 'District of Columbia'), ('UM', 'United States Minor Outlying Islands'), ('AK', 'Alaska'), ('AS', 'American Samoa'), ('UT', 'Utah'), ('ID', 'Idaho'), ('WY', 'Wyoming'), ('CO', 'Colorado'), ('IA', 'Iowa'), ('MA', 'Massachusetts'), ('ND', 'North Dakota'), ('SC', 'South Carolina'), ('OK', 'Oklahoma'), ('FL', 'Florida'), ('RI', 'Rhode Island'), ('NE', 'Nebraska'), ('AL', 'Alabama'), ('LA', 'Louisiana'), ('PR', 'Puerto Rico'), ('AZ', 'Arizona'), ('MD', 'Maryland'), ('AR', 'Arkansas'), ('NH', 'New Hampshire'), ('HI', 'Hawaii'), ('WV', 'West Virginia'), ('VI', 'U.S. Virgin Islands'), ('OR', 'Oregon'), ('KS', 'Kansas'), ('NV', 'Nevada'), ('VT', 'Vermont'), ('NC', 'North Carolina'), ('MN', 'Minnesota'), ('ME', 'Maine'), ('MS', 'Mississippi'), ('TN', 'Tennessee'), ('MT', 'Montana'), ('CT', 'Connecticut'), ('KY', 'Kentucky'), ('WA', 'Washington'), ('CA', 'California'), ('TX', 'Texas'), ('MO', 'Missouri'), ('PA', 'Pennsylvania'), ('NJ', 'New Jersey'), ('IN', 'Indiana'), ('GU', 'Guam'), ('GA', 'Georgia'), ('OH', 'Ohio'), ('MP', 'Northern Mariana Islands'), ('SD', 'South Dakota'), ('NM', 'New Mexico')], default=None, max_length=2, null=True, verbose_name='State'),
        ),
        migrations.AlterField(
            model_name='fedrampparameter',
            name='control',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='FedRAMP_parameters', to='AlchemyApp.nistcontrol'),
        ),
        migrations.AlterField(
            model_name='fedrampparameter',
            name='element',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='FedRAMP_parameters', to='AlchemyApp.nistcontrolelement'),
        ),
        migrations.AlterField(
            model_name='system',
            name='environment',
            field=models.CharField(blank=True, choices=[('On-Premises', 'On-Premises'), ('Cloud-Based', 'Cloud-Based'), ('Hybrid', 'Hybrid')], default='Cloud-Based', max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='system',
            name='fedramp_compliance_status',
            field=models.CharField(blank=True, choices=[('Not Started', 'Not Started'), ('In Progress', 'In Progress'), ('Authorized', 'Authorized')], default='Not Started', max_length=20, null=True),
        ),
    ]