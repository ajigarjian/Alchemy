# Generated by Django 4.2 on 2023-06-13 02:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AlchemyApp', '0022_alter_client_state_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='state',
            field=models.CharField(blank=True, choices=[('AZ', 'Arizona'), ('OR', 'Oregon'), ('WV', 'West Virginia'), ('MD', 'Maryland'), ('MA', 'Massachusetts'), ('AL', 'Alabama'), ('MS', 'Mississippi'), ('MT', 'Montana'), ('ME', 'Maine'), ('SC', 'South Carolina'), ('NJ', 'New Jersey'), ('TN', 'Tennessee'), ('IN', 'Indiana'), ('PR', 'Puerto Rico'), ('DC', 'District of Columbia'), ('IL', 'Illinois'), ('ND', 'North Dakota'), ('KS', 'Kansas'), ('OH', 'Ohio'), ('WA', 'Washington'), ('NE', 'Nebraska'), ('VA', 'Virginia'), ('CT', 'Connecticut'), ('OK', 'Oklahoma'), ('IA', 'Iowa'), ('CO', 'Colorado'), ('UT', 'Utah'), ('FL', 'Florida'), ('NM', 'New Mexico'), ('WY', 'Wyoming'), ('NV', 'Nevada'), ('UM', 'United States Minor Outlying Islands'), ('AR', 'Arkansas'), ('VT', 'Vermont'), ('RI', 'Rhode Island'), ('CA', 'California'), ('DE', 'Delaware'), ('NY', 'New York'), ('GU', 'Guam'), ('VI', 'U.S. Virgin Islands'), ('MP', 'Northern Mariana Islands'), ('KY', 'Kentucky'), ('HI', 'Hawaii'), ('MI', 'Michigan'), ('LA', 'Louisiana'), ('GA', 'Georgia'), ('WI', 'Wisconsin'), ('SD', 'South Dakota'), ('TX', 'Texas'), ('PA', 'Pennsylvania'), ('NC', 'North Carolina'), ('NH', 'New Hampshire'), ('MN', 'Minnesota'), ('AS', 'American Samoa'), ('AK', 'Alaska'), ('MO', 'Missouri'), ('ID', 'Idaho')], default=None, max_length=2, null=True, verbose_name='State'),
        ),
        migrations.AlterField(
            model_name='controlimplementation',
            name='statement',
            field=models.TextField(blank=True, default=''),
        ),
    ]
