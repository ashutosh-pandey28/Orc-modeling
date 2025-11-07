# combustion_app/admin.py
from django.contrib import admin
from .models import FurnaceRun, Fuel

class FuelAdmin(admin.ModelAdmin):
    list_display = ('name', 'hhv_mj_kg', 'cost_per_tonne', 'C', 'H', 'O', 'Ash')

# Register your models here.
admin.site.register(Fuel, FuelAdmin)
admin.site.register(FurnaceRun)