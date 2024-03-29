# Generated by Django 4.2 on 2023-05-30 17:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AlchemyApp', '0015_alter_client_state'),
    ]

    operations = [
        migrations.AlterField(
            model_name='client',
            name='state',
            field=models.CharField(blank=True, choices=[('AZ', 'Arizona'), ('NH', 'New Hampshire'), ('VT', 'Vermont'), ('NE', 'Nebraska'), ('PA', 'Pennsylvania'), ('WI', 'Wisconsin'), ('AL', 'Alabama'), ('RI', 'Rhode Island'), ('MP', 'Northern Mariana Islands'), ('GU', 'Guam'), ('NM', 'New Mexico'), ('WY', 'Wyoming'), ('AS', 'American Samoa'), ('WA', 'Washington'), ('IL', 'Illinois'), ('CT', 'Connecticut'), ('SC', 'South Carolina'), ('NC', 'North Carolina'), ('ND', 'North Dakota'), ('IA', 'Iowa'), ('MS', 'Mississippi'), ('MO', 'Missouri'), ('NV', 'Nevada'), ('TX', 'Texas'), ('OK', 'Oklahoma'), ('CO', 'Colorado'), ('SD', 'South Dakota'), ('WV', 'West Virginia'), ('MT', 'Montana'), ('UM', 'United States Minor Outlying Islands'), ('NY', 'New York'), ('OR', 'Oregon'), ('UT', 'Utah'), ('ME', 'Maine'), ('PR', 'Puerto Rico'), ('MA', 'Massachusetts'), ('HI', 'Hawaii'), ('TN', 'Tennessee'), ('AK', 'Alaska'), ('LA', 'Louisiana'), ('GA', 'Georgia'), ('NJ', 'New Jersey'), ('MD', 'Maryland'), ('KY', 'Kentucky'), ('IN', 'Indiana'), ('ID', 'Idaho'), ('MN', 'Minnesota'), ('VI', 'U.S. Virgin Islands'), ('AR', 'Arkansas'), ('FL', 'Florida'), ('VA', 'Virginia'), ('DC', 'District of Columbia'), ('OH', 'Ohio'), ('DE', 'Delaware'), ('KS', 'Kansas'), ('MI', 'Michigan'), ('CA', 'California')], default=None, max_length=2, null=True, verbose_name='State'),
        ),
    ]
