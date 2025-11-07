# combustion_app/views.py
import json
import numpy as np
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import FurnaceRunForm, AnalysisForm
from .models import FurnaceRun
from .furnace_model import run_combustion_model

def simulation_input(request):
    if request.method == 'POST':
        form = FurnaceRunForm(request.POST)
        if form.is_valid():
            furnace_run = form.save(commit=False)
            furnace_run.save() 
            results = furnace_run.run_and_save_simulation()
            
            if results is None:
                messages.error(request, 'Please select a valid fuel.')
                return render(request, 'combustion_app/input_form.html', {'form': form, 'title': 'Furnace Model Input'})

            return redirect('simulation_results', run_id=furnace_run.id)
    else:
        form = FurnaceRunForm()
        
    return render(request, 'combustion_app/input_form.html', {'form': form, 'title': 'Furnace Model Input'})

def simulation_results(request, run_id):
    run = get_object_or_404(FurnaceRun, id=run_id)
    
    if not run.fuel:
        messages.error(request, f"Cannot display results for Run ID {run.id}. This run has no associated fuel. Please run a new simulation.")
        return redirect('simulation_input')
        
    # Re-run model to get validation data
    try:
        results = run_combustion_model(run.fuel, run.moisture_percent, run.excess_air_percent, run.furnace_load_gj_hour)
        validation_data = results['validation_data']
    except Exception as e:
        messages.error(request, f"Error calculating results: {e}")
        return redirect('simulation_input')
        
    # Prepare data for Chart.js
    chart_data = {
        'labels': validation_data['excess_air_points'],
        'model_data': validation_data['model_efficiency'],
        'actual_data': validation_data['actual_efficiency'],
        'current_run': {
            'x': run.excess_air_percent,
            'y': run.calculated_efficiency
        }
    }
    
    context = {
        'run': run,
        'title': 'Simulation Results & Validation',
        'chart_data': json.dumps(chart_data)
    }
    return render(request, 'combustion_app/results.html', context)


# --- NEW VIEW FOR ANALYSIS PAGE ---
def analysis_view(request):
    form = AnalysisForm()
    chart_data = None

    if request.method == 'POST':
        form = AnalysisForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            # Create the array for the x-axis
            x_values = np.linspace(data['start_value'], data['end_value'], data['steps'])
            
            # Prepare lists for results
            results_efficiency = []
            results_cost = []
            results_co = []
            
            # Loop and run the model for each value
            for x_val in x_values:
                if data['variable_to_sweep'] == 'moisture_percent':
                    moisture = x_val
                    excess_air = data['constant_excess_air']
                else: # excess_air_percent
                    moisture = data['constant_moisture']
                    excess_air = x_val
                
                # Run the model
                sim_results = run_combustion_model(
                    data['fuel'],
                    moisture,
                    excess_air,
                    data['constant_load']
                )
                
                # Store results
                results_efficiency.append(sim_results['efficiency'])
                results_cost.append(sim_results['cost_per_gj'])
                results_co.append(sim_results['emissions_co_ppm'])
            
            # Package for Chart.js
            chart_data = json.dumps({
                'labels': list(x_values),
                'efficiency_data': results_efficiency,
                'cost_data': results_cost,
                'co_data': results_co,
                'x_axis_label': dict(form.fields['variable_to_sweep'].choices)[data['variable_to_sweep']]
            })

    context = {
        'title': 'Parametric Analysis',
        'form': form,
        'chart_data': chart_data
    }
    return render(request, 'combustion_app/analysis.html', context)