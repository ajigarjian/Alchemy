# Generated by Django 4.2 on 2023-06-11 19:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('AlchemyApp', '0021_alter_client_state_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='state',
            field=models.CharField(blank=True, choices=[('VA', 'Virginia'), ('AZ', 'Arizona'), ('GU', 'Guam'), ('CA', 'California'), ('VI', 'U.S. Virgin Islands'), ('AS', 'American Samoa'), ('MD', 'Maryland'), ('SC', 'South Carolina'), ('MI', 'Michigan'), ('OR', 'Oregon'), ('WA', 'Washington'), ('MA', 'Massachusetts'), ('SD', 'South Dakota'), ('DC', 'District of Columbia'), ('AK', 'Alaska'), ('UM', 'United States Minor Outlying Islands'), ('DE', 'Delaware'), ('AR', 'Arkansas'), ('NY', 'New York'), ('WI', 'Wisconsin'), ('RI', 'Rhode Island'), ('MP', 'Northern Mariana Islands'), ('MN', 'Minnesota'), ('IN', 'Indiana'), ('WV', 'West Virginia'), ('NE', 'Nebraska'), ('MO', 'Missouri'), ('NM', 'New Mexico'), ('HI', 'Hawaii'), ('IL', 'Illinois'), ('NV', 'Nevada'), ('KY', 'Kentucky'), ('NH', 'New Hampshire'), ('OK', 'Oklahoma'), ('ME', 'Maine'), ('NC', 'North Carolina'), ('CO', 'Colorado'), ('TN', 'Tennessee'), ('MS', 'Mississippi'), ('CT', 'Connecticut'), ('IA', 'Iowa'), ('ND', 'North Dakota'), ('MT', 'Montana'), ('OH', 'Ohio'), ('WY', 'Wyoming'), ('NJ', 'New Jersey'), ('FL', 'Florida'), ('UT', 'Utah'), ('PR', 'Puerto Rico'), ('VT', 'Vermont'), ('AL', 'Alabama'), ('KS', 'Kansas'), ('PA', 'Pennsylvania'), ('TX', 'Texas'), ('GA', 'Georgia'), ('LA', 'Louisiana'), ('ID', 'Idaho')], default=None, max_length=2, null=True, verbose_name='State'),
        ),
        migrations.AlterField(
            model_name='controlimplementation',
            name='control',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='control_implementations', to='AlchemyApp.nistcontrol'),
        ),
        migrations.AlterField(
            model_name='controlimplementationstatement',
            name='statement',
            field=models.TextField(blank=True, default=''),
        ),
    ]