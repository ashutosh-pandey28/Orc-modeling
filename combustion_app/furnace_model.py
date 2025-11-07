# combustion_app/furnace_model.py
import math
import numpy as np

# --- 1. Fixed Constants ---
M = {'C': 12, 'H': 1, 'O': 16, 'N': 14, 'S': 32}
Cp_AIR = 1.006
Cp_FG_DRY = 1.05
Cp_WATER_VAPOR = 1.872
H_vap = 2257
T_ref_K = 298.15
T_EXHAUST_K_FIXED = 523.15 # 250°C

# --- 2. Core Combustion Model Function ---

def run_combustion_model(fuel, moisture_percent, excess_air_percent, furnace_load_gj_hour=1.0):
    """
    UPDATED model that takes a Fuel object and furnace load.
    Returns performance, cost, and emissions.
    """
    
    # --- Get Fuel Properties ---
    RH_ULTIMATE_ANALYSIS = fuel.get_analysis_dict()
    fuel_hhv_mj_kg = fuel.hhv_mj_kg
    fuel_cost_per_tonne = fuel.cost_per_tonne
    
    # Convert inputs
    M_f = moisture_percent / 100.0
    EA = excess_air_percent / 100.0
    HHV = fuel_hhv_mj_kg * 1000.0  # kJ/kg
    
    M_DF = 1.0 - M_f
    M_W = M_f
    
    # --- STEP A: Mass Balance ---
    try:
        A_stoich_kgDF = (11.5 * RH_ULTIMATE_ANALYSIS['C'] + 
                         34.5 * RH_ULTIMATE_ANALYSIS['H'] + 
                         4.3 * RH_ULTIMATE_ANALYSIS['S'] - 
                         4.3 * RH_ULTIMATE_ANALYSIS['O'])
    except TypeError: A_stoich_kgDF = 0
    
    A_stoich = A_stoich_kgDF * M_DF
    A_actual = A_stoich * (1.0 + EA)
    M_FG = M_DF + A_actual - (RH_ULTIMATE_ANALYSIS['Ash'] * M_DF)
    
    # --- STEP B: Energy Balance (T_ad & LHV) ---
    M_H2O_total = M_W + (RH_ULTIMATE_ANALYSIS['H'] * 9.0 * M_DF) 
    LHV = HHV - (M_H2O_total * H_vap) # kJ/kg-WF
    
    try:
        dry_gas_mass = M_FG - M_H2O_total
        if dry_gas_mass < 0: dry_gas_mass = 0
        cp_dry_gas_fraction = (dry_gas_mass * Cp_FG_DRY) / M_FG
        cp_h2o_fraction = (M_H2O_total * Cp_WATER_VAPOR) / M_FG
        Cp_FG_WET_MIX = cp_dry_gas_fraction + cp_h2o_fraction
    except ZeroDivisionError: Cp_FG_WET_MIX = 1.05
    
    if Cp_FG_WET_MIX < 0.1: Cp_FG_WET_MIX = 1.05
    
    try:
        T_ad_K = T_ref_K + LHV / (M_FG * Cp_FG_WET_MIX)
    except ZeroDivisionError: T_ad_K = T_ref_K

    # --- STEP C: Furnace Efficiency ---
    Q_loss_percent = 0.10
    Q_loss_kJ_per_kgWF = Q_loss_percent * LHV
    Q_exh_kJ_per_kgWF = M_FG * Cp_FG_WET_MIX * (T_EXHAUST_K_FIXED - T_ref_K)
    Q_recovered = LHV - Q_exh_kJ_per_kgWF - Q_loss_kJ_per_kgWF
    
    try:
        efficiency = (Q_recovered / LHV)
    except ZeroDivisionError: efficiency = 0.0

    # --- STEP D: Cost Analysis ---
    try:
        # LHV in GJ/kg = (LHV kJ/kg) / 1,000,000
        LHV_gj_kg = LHV / 1e6
        # Fuel needed (kg/hr) = (Load GJ/hr) / (LHV GJ/kg * efficiency)
        fuel_kg_hr = furnace_load_gj_hour / (LHV_gj_kg * efficiency)
        # Cost ($/hr) = (Fuel kg/hr / 1000 kg/tonne) * Cost $/tonne
        cost_per_hour = (fuel_kg_hr / 1000.0) * fuel_cost_per_tonne
        # Cost ($/GJ) = Cost $/hr / Load GJ/hr
        cost_per_gj = cost_per_hour / furnace_load_gj_hour
    except ZeroDivisionError:
        fuel_kg_hr = 0
        cost_per_hour = 0
        cost_per_gj = 0

    # --- STEP E: Emissions (Simple Estimation) ---
    # CO (ppm) - rises sharply with low excess air
    emissions_co_ppm = 50 + (1000 * math.exp(-EA / 0.1))
    
    # NOx (ppm) - rises with temperature (using T_ad as proxy)
    T_ad_C = T_ad_K - 273.15
    emissions_nox_ppm = 10 * math.exp((T_ad_C - 1000) / 500)
    
    # --- STEP F: Validation Data (Placeholder) ---
    validation_data = {
        'excess_air_points': [10, 20, 30, 40, 50, 60],
        'model_efficiency': [78.5, 75.1, 72.0, 69.2, 66.8, 64.0],
        'actual_efficiency': [79.2, 75.0, 71.5, 68.4, 66.0, 64.1],
    }

    # --- G. Final Results Formatting ---
    return {
        'efficiency': max(0.0, min(100.0, efficiency * 100)),
        'exhaust_temp_c': T_EXHAUST_K_FIXED - 273.15,
        'flue_gas_co2_percent': max(0.0, 20.0 / (1.0 + EA * 1.5)),
        't_adiabatic_c': T_ad_K - 273.15,
        'validation_data': validation_data,
        'cost_per_gj': cost_per_gj,
        'cost_per_hour': cost_per_hour,
        'emissions_co_ppm': emissions_co_ppm,
        'emissions_nox_ppm': emissions_nox_ppm,
        'LHV': LHV_gj_kg * 1000 # LHV in MJ/kg
    }