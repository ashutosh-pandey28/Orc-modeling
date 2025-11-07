# combustion_app/forms.py
from django import forms
from .models import FurnaceRun, Fuel

class FurnaceRunForm(forms.ModelForm):
    fuel = forms.ModelChoiceField(queryset=Fuel.objects.all(), 
                                  empty_label="--- Select a Fuel ---",
                                  widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = FurnaceRun
        fields = ['name', 'fuel', 'moisture_percent', 'excess_air_percent', 'furnace_load_gj_hour'] # <-- UPDATED
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g., Test Run 1'}),
            'moisture_percent': forms.NumberInput(attrs={'step': 1, 'min': 1, 'max': 50}),
            'excess_air_percent': forms.NumberInput(attrs={'step': 5, 'min': 10, 'max': 200}),
            'furnace_load_gj_hour': forms.NumberInput(attrs={'step': 0.1, 'min': 0.1, 'max': 100}), # <-- NEW
        }


# --- NEW FORM FOR ANALYSIS PAGE ---
class AnalysisForm(forms.Form):
    fuel = forms.ModelChoiceField(queryset=Fuel.objects.all(), 
                                  empty_label="--- Select a Fuel ---",
                                  widget=forms.Select(attrs={'class': 'form-control'}))
    
    VARIABLE_CHOICES = [
        ('moisture_percent', 'Moisture Content'),
        ('excess_air_percent', 'Excess Air'),
    ]
    variable_to_sweep = forms.ChoiceField(choices=VARIABLE_CHOICES, label="Variable to Sweep")
    
    start_value = forms.FloatField(initial=10, min_value=1)
    end_value = forms.FloatField(initial=50, min_value=1)
    steps = forms.IntegerField(initial=10, min_value=2, max_value=50, label="Number of Steps")
    
    # Constant values for the simulation
    constant_moisture = forms.FloatField(initial=10, label="Constant Moisture (%)")
    constant_excess_air = forms.FloatField(initial=40, label="Constant Excess Air (%)")
    constant_load = forms.FloatField(initial=1, label="Constant Furnace Load (GJ/hr)")