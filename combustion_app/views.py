# combustion_app/views.py
import json
import numpy as np
import csv 
import io  
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string

from .forms import FurnaceRunForm, AnalysisForm, ValidationForm
from .models import FurnaceRun
from .furnace_model import run_combustion_model

def simulation_input(request):
    
    # --- THIS IS THE POST (FORM SUBMIT) LOGIC ---
    if request.method == 'POST':
        form = FurnaceRunForm(request.POST)
        
        if form.is_valid():
            furnace_run = form.save(commit=False)
            furnace_run.save() # Save the run *first*
            
            # Now run the simulation, which saves the results
            results = furnace_run.run_and_save_simulation()
            
            if results is None:
                messages.error(request, 'Could not run simulation. Please check fuel selection.')
                # If it fails, redirect back to the (GET) page
                return redirect('simulation_input')
            
            # Success! Redirect to the new results page
            return redirect('simulation_results', run_id=furnace_run.id)
        
        else:
            # Form is invalid. We must re-render the page,
            # but we MUST include the history and the invalid form (to show errors).
            history_runs = FurnaceRun.objects.all().order_by('-run_date')[:10]
            context = {
                'form': form, # Pass the invalid form back
                'title': 'Furnace Model Input',
                'history_runs': history_runs
            }
            messages.error(request, 'Please correct the errors in the form.')
            return render(request, 'combustion_app/input_form.html', context)
    
    # --- THIS IS THE GET (PAGE LOAD) LOGIC ---
    # If the request is not POST, it must be GET.
    form = FurnaceRunForm()
    # Fetches the 10 most recent runs
    history_runs = FurnaceRun.objects.all().order_by('-run_date')[:10]
    
    context = {
        'form': form, 
        'title': 'Furnace Model Input',
        'history_runs': history_runs # Pass history to template
    }
    return render(request, 'combustion_app/input_form.html', context)


# --- (Rest of your views.py file) ---

def simulation_results(request, run_id):
    run = get_object_or_404(FurnaceRun, id=run_id)
    
    if not run.fuel:
        messages.error(request, f"Cannot display results for Run ID {run.id}. This run has no associated fuel. Please run a new simulation.")
        return redirect('simulation_input')
        
    try:
        results = run_combustion_model(run.fuel, run.moisture_percent, run.excess_air_percent, run.furnace_load_gj_hour)
        validation_data = results['validation_data']
    except Exception as e:
        messages.error(request, f"Error calculating results: {e}")
        return redirect('simulation_input')
        
    chart_data = {
        'labels': validation_data['excess_air_points'],
        'model_data': validation_data['model_efficiency'],
        'actual_data': validation_data['actual_efficiency'],
        'current_run': {'x': run.excess_air_percent, 'y': run.calculated_efficiency}
    }
    
    context = {
        'run': run,
        'title': 'Simulation Results & Validation',
        'chart_data': json.dumps(chart_data)
    }
    return render(request, 'combustion_app/results.html', context)


def analysis_view(request):
    form = AnalysisForm()
    chart_data = None

    if request.method == 'POST':
        form = AnalysisForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            x_values = np.linspace(data['start_value'], data['end_value'], data['steps'])
            
            results_efficiency = []
            results_cost = []
            results_co = []
            
            for x_val in x_values:
                if data['variable_to_sweep'] == 'moisture_percent':
                    moisture = x_val
                    excess_air = data['constant_excess_air']
                else:
                    moisture = data['constant_moisture']
                    excess_air = x_val
                
                sim_results = run_combustion_model(
                    data['fuel'], moisture, excess_air, data['constant_load']
                )
                
                results_efficiency.append(sim_results['efficiency'])
                results_cost.append(sim_results['cost_per_gj'])
                results_co.append(sim_results['emissions_co_ppm'])
            
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


def compare_view(request):
    run_ids = request.GET.getlist('run_ids')
    
    if not run_ids or len(run_ids) < 2:
        messages.error(request, "You must select at least two runs to compare.")
        return redirect('simulation_input')
        
    runs = FurnaceRun.objects.filter(id__in=run_ids).order_by('run_date')
    
    context = {
        'title': 'Comparison Results',
        'runs': runs
    }
    return render(request, 'combustion_app/compare_results.html', context)


def validation_view(request):
    form = ValidationForm()
    chart_data = None

    if request.method == 'POST':
        form = ValidationForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            csv_file = data['validation_file']
            
            try:
                decoded_file = csv_file.read().decode('utf-8')
                io_string = io.StringIO(decoded_file)
                
                reader = csv.DictReader(io_string)
                
                actual_x_data = []
                actual_y_data = []
                model_y_data = []
                
                X_HEADER = 'excess_air'
                Y_HEADER = 'measured_efficiency'

                if X_HEADER not in reader.fieldnames or Y_HEADER not in reader.fieldnames:
                    messages.error(request, f"CSV file must contain columns named '{X_HEADER}' and '{Y_HEADER}'.")
                    return redirect('validation_view')

                for row in reader:
                    try:
                        x_val = float(row[X_HEADER])
                        y_val_actual = float(row[Y_HEADER])
                        
                        sim_results = run_combustion_model(
                            data['fuel'],
                            data['constant_moisture'],
                            x_val,
                            data['constant_load']
                        )
                        
                        actual_x_data.append(x_val)
                        actual_y_data.append(y_val_actual)
                        model_y_data.append(sim_results['efficiency'])
                        
                    except (ValueError, TypeError):
                        pass
                
                chart_data = json.dumps({
                    'labels': actual_x_data,
                    'model_data': model_y_data,
                    'actual_data': actual_y_data,
                    'x_axis_label': X_HEADER,
                    'y_axis_label': 'Efficiency (%)'
                })

            except Exception as e:
                messages.error(request, f"An error occurred processing the file: {e}")
            
    context = {
        'title': 'Model Validation',
        'form': form,
        'chart_data': chart_data
    }
    return render(request, 'combustion_app/validation.html', context)