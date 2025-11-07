# combustion_app/migrations/0004_initial_fuels.py

from django.db import migrations

def create_initial_fuels(apps, schema_editor):
    """
    This function will be run when we apply the migration.
    It gets the Fuel model and creates three default fuel objects.
    """
    # We must use apps.get_model() in migrations instead of a direct import.
    Fuel = apps.get_model('combustion_app', 'Fuel')

    # Fuel 1: Rice Husk
    Fuel.objects.create(
        name='Rice Husk',
        C=0.35,
        H=0.04,
        O=0.40,
        N=0.005,
        S=0.005,
        Ash=0.20,
        hhv_mj_kg=16.0,
        cost_per_tonne=50.0
    )

    # Fuel 2: Wood Chips
    Fuel.objects.create(
        name='Wood Chips',
        C=0.50,
        H=0.06,
        O=0.43,
        N=0.002,
        S=0.001,
        Ash=0.01,
        hhv_mj_kg=19.5,
        cost_per_tonne=50.0
    )
    
    # Fuel 3: Sugarcane Bagasse
    Fuel.objects.create(
        name='Sugarcane Bagasse',
        C=0.47,
        H=0.06,
        O=0.44,
        N=0.003,
        S=0.001,
        Ash=0.02,
        hhv_mj_kg=17.5,
        cost_per_tonne=50.0
    )

def remove_initial_fuels(apps, schema_editor):
    """
    This function is run if we ever "unmigrate" or reverse the migration.
    It safely deletes the fuels we created.
    """
    Fuel = apps.get_model('combustion_app', 'Fuel')
    Fuel.objects.filter(name__in=['Rice Husk', 'Wood Chips', 'Sugarcane Bagasse']).delete()


class Migration(migrations.Migration):

    dependencies = [
        # This should point to your PREVIOUS migration file.
        # Check your 'migrations' folder and update this if it's not '0003_...'.
        ('combustion_app', '0003_fuel_remove_furnacerun_fuel_hhv_mj_kg_and_more'), # <-- UPDATE THIS FILENAME
    ]

    operations = [
        # This tells Django to run our functions.
        migrations.RunPython(create_initial_fuels, reverse_code=remove_initial_fuels),
    ]