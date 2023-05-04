# Generated by Django 4.2 on 2023-05-04 13:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AlchemyApp', '0026_alter_client_state_alter_system_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='state',
            field=models.CharField(blank=True, choices=[('LA', 'Louisiana'), ('SD', 'South Dakota'), ('NM', 'New Mexico'), ('KS', 'Kansas'), ('ND', 'North Dakota'), ('NH', 'New Hampshire'), ('TX', 'Texas'), ('MS', 'Mississippi'), ('DE', 'Delaware'), ('MD', 'Maryland'), ('ME', 'Maine'), ('MO', 'Missouri'), ('WV', 'West Virginia'), ('CO', 'Colorado'), ('OK', 'Oklahoma'), ('NV', 'Nevada'), ('AS', 'American Samoa'), ('NY', 'New York'), ('FL', 'Florida'), ('IN', 'Indiana'), ('GA', 'Georgia'), ('OH', 'Ohio'), ('HI', 'Hawaii'), ('MT', 'Montana'), ('AK', 'Alaska'), ('WA', 'Washington'), ('WY', 'Wyoming'), ('TN', 'Tennessee'), ('NC', 'North Carolina'), ('PR', 'Puerto Rico'), ('AL', 'Alabama'), ('IL', 'Illinois'), ('PA', 'Pennsylvania'), ('MP', 'Northern Mariana Islands'), ('AR', 'Arkansas'), ('AZ', 'Arizona'), ('GU', 'Guam'), ('UT', 'Utah'), ('VT', 'Vermont'), ('MI', 'Michigan'), ('WI', 'Wisconsin'), ('MA', 'Massachusetts'), ('RI', 'Rhode Island'), ('CT', 'Connecticut'), ('VA', 'Virginia'), ('UM', 'United States Minor Outlying Islands'), ('DC', 'District of Columbia'), ('NE', 'Nebraska'), ('NJ', 'New Jersey'), ('MN', 'Minnesota'), ('SC', 'South Carolina'), ('IA', 'Iowa'), ('ID', 'Idaho'), ('KY', 'Kentucky'), ('CA', 'California'), ('VI', 'U.S. Virgin Islands'), ('OR', 'Oregon')], default=None, max_length=2, null=True, verbose_name='State'),
        ),
    ]
