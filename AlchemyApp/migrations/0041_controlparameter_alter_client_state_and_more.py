# Generated by Django 4.2 on 2023-08-20 18:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('AlchemyApp', '0040_nistcontrolparameter_alter_client_state_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ControlParameter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('control', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='parameters', to='AlchemyApp.nistcontrol')),
                ('element', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='parameters', to='AlchemyApp.nistcontrolelement')),
            ],
            options={
                'verbose_name': 'Parameter',
                'verbose_name_plural': 'Parameters',
            },
        ),
        migrations.AlterField(
            model_name='client',
            name='state',
            field=models.CharField(blank=True, choices=[('DC', 'District of Columbia'), ('AS', 'American Samoa'), ('GA', 'Georgia'), ('RI', 'Rhode Island'), ('ME', 'Maine'), ('ND', 'North Dakota'), ('AL', 'Alabama'), ('MD', 'Maryland'), ('MI', 'Michigan'), ('NC', 'North Carolina'), ('UM', 'United States Minor Outlying Islands'), ('AR', 'Arkansas'), ('PA', 'Pennsylvania'), ('NM', 'New Mexico'), ('WY', 'Wyoming'), ('MN', 'Minnesota'), ('AZ', 'Arizona'), ('CA', 'California'), ('KS', 'Kansas'), ('SD', 'South Dakota'), ('WI', 'Wisconsin'), ('MO', 'Missouri'), ('UT', 'Utah'), ('PR', 'Puerto Rico'), ('OR', 'Oregon'), ('SC', 'South Carolina'), ('KY', 'Kentucky'), ('NJ', 'New Jersey'), ('IN', 'Indiana'), ('DE', 'Delaware'), ('NH', 'New Hampshire'), ('OH', 'Ohio'), ('WA', 'Washington'), ('GU', 'Guam'), ('VT', 'Vermont'), ('MA', 'Massachusetts'), ('TN', 'Tennessee'), ('MP', 'Northern Mariana Islands'), ('NY', 'New York'), ('FL', 'Florida'), ('WV', 'West Virginia'), ('IL', 'Illinois'), ('MT', 'Montana'), ('AK', 'Alaska'), ('MS', 'Mississippi'), ('VI', 'U.S. Virgin Islands'), ('HI', 'Hawaii'), ('LA', 'Louisiana'), ('IA', 'Iowa'), ('NE', 'Nebraska'), ('TX', 'Texas'), ('CO', 'Colorado'), ('ID', 'Idaho'), ('NV', 'Nevada'), ('VA', 'Virginia'), ('CT', 'Connecticut'), ('OK', 'Oklahoma')], default=None, max_length=2, null=True, verbose_name='State'),
        ),
        migrations.DeleteModel(
            name='NISTControlParameter',
        ),
    ]