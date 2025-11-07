# combustion_app/models.py
from django.db import models

class Fuel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    # Ultimate Analysis
    C = models.FloatField(default=0.35, verbose_name="Carbon (C) %")
    H = models.FloatField(default=0.04, verbose_name="Hydrogen (H) %")
    O = models.FloatField(default=0.40, verbose_name="Oxygen (O) %")
    N = models.FloatField(default=0.005, verbose_name="Nitrogen (N) %")
    S = models.FloatField(default=0.005, verbose_name="Sulfur (S) %")
    Ash = models.FloatField(default=0.20, verbose_name="Ash %")
    
    # Properties
    hhv_mj_kg = models.FloatField(default=16.0, verbose_name="HHV (MJ/kg)")
    cost_per_tonne = models.FloatField(default=50.0, verbose_name="Cost (₹/tonne)") # <-- NEW

    def __str__(self):
        return self.name

    def get_analysis_dict(self):
        return {
            'C': self.C, 'H': self.H, 'O': self.O, 
            'N': self.N, 'S': self.S, 'Ash': self.Ash
        }


class FurnaceRun(models.Model):
    name = models.CharField(max_length=100, default="Simulation Run")
    run_date = models.DateTimeField(auto_now_add=True)
    
    # --- Input Parameters ---
    fuel = models.ForeignKey(Fuel, on_delete=models.SET_NULL, null=True)
    moisture_percent = models.FloatField(default=10.0, verbose_name="Moisture (%)")
    excess_air_percent = models.FloatField(default=30.0, verbose_name="Excess Air (%)")
    furnace_load_gj_hour = models.FloatField(default=1.0, verbose_name="Furnace Load (GJ/hr)") 
    
    # --- Calculated Results ---
    calculated_efficiency = models.FloatField(null=True, blank=True, verbose_name="Efficiency (%)")
    exhaust_temp_c = models.FloatField(null=True, blank=True, verbose_name="Exhaust Temp (°C)")
    flue_gas_co2_percent = models.FloatField(null=True, blank=True, verbose_name="Flue Gas CO2 (%)")
    t_adiabatic_c = models.FloatField(null=True, blank=True, verbose_name="Adiabatic Temp (°C)")
    cost_per_gj = models.FloatField(null=True, blank=True, verbose_name="Cost (₹/GJ)") 
    cost_per_hour = models.FloatField(null=True, blank=True, verbose_name="Cost (₹/hr)") 
    emissions_co_ppm = models.FloatField(null=True, blank=True, verbose_name="CO (ppm)") 
    emissions_nox_ppm = models.FloatField(null=True, blank=True, verbose_name="NOx (ppm)") 

    def __str__(self):
        return f"{self.name} - {self.run_date.strftime('%Y-%m-%d %H:%M')}"

    # Method to run the simulation and save results
    def run_and_save_simulation(self):
        if not self.fuel:
            return None
            
        from .furnace_model import run_combustion_model
        
        # 1. Run the core model
        results = run_combustion_model(
            self.fuel,
            self.moisture_percent, 
            self.excess_air_percent,
            self.furnace_load_gj_hour # Pass new input
        )
        
        # 2. Update and save results
        self.calculated_efficiency = results['efficiency']
        self.exhaust_temp_c = results['exhaust_temp_c']
        self.flue_gas_co2_percent = results['flue_gas_co2_percent']
        self.t_adiabatic_c = results['t_adiabatic_c']
        self.cost_per_gj = results['cost_per_gj']
        self.cost_per_hour = results['cost_per_hour']
        self.emissions_co_ppm = results['emissions_co_ppm']
        self.emissions_nox_ppm = results['emissions_nox_ppm']
        
        # 3. Save the model instance
        self.save() 
        return results