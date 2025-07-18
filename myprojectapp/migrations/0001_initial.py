# Generated by Django 5.1.4 on 2024-12-14 15:42

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Product Name')),
                ('price', models.FloatField(verbose_name='Product Price')),
                ('pdetails', models.CharField(max_length=100)),
                ('cat', models.IntegerField(choices=[(1, 'T-Shirts'), (2, 'Shirts'), (3, 'Jeans'), (4, 'Trousers'), (5, 'Boxers')], verbose_name='Product Category')),
                ('size', models.IntegerField(choices=[(1, 'S'), (2, 'M'), (3, 'L'), (4, 'XL'), (5, 'XXL')], verbose_name='Size')),
                ('is_active', models.BooleanField(default=True, verbose_name='Available')),
                ('pimage', models.ImageField(upload_to='image')),
            ],
        ),
        migrations.CreateModel(
            name='orders',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.CharField(max_length=50)),
                ('qty', models.IntegerField(default=1)),
                ('uid', models.ForeignKey(db_column='uid', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('pid', models.ForeignKey(db_column='pid', on_delete=django.db.models.deletion.CASCADE, to='myprojectapp.product')),
            ],
        ),
        migrations.CreateModel(
            name='cart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('qty', models.IntegerField(default=1)),
                ('uid', models.ForeignKey(db_column='uid', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('pid', models.ForeignKey(db_column='pid', on_delete=django.db.models.deletion.CASCADE, to='myprojectapp.product')),
            ],
        ),
    ]
