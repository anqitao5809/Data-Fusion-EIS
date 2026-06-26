import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from impedance.models.circuits import CustomCircuit

# 1. Load Data
df = pd.read_excel('EIS_Averages_MinMax.xlsx')
freq = df['Freq'].values
z_mod = df['Zmod_Avg'].values
z_phz = df['Zphz_Avg'].values
temp_val = df.iloc[0, 0]

# Convert to complex
z_complex = z_mod * np.exp(1j * np.deg2rad(z_phz))

# 2. Circuit & Corrected Parameters
circuit_string = 'p(L1,R2)-R3-CPE4-p(R5,C6)'
param_names = ['L1', 'R2', 'R3', 'Yo4', 'a5', 'R5', 'C6']

# This matches the values you just provided:
initial_guess = [
    4.46e-07, # L1
    5.96e+00, # R2
    7.39e-01, # R3 (Salt)
    1.40e-05, # Yo4 (CPE Magnitude)
    9.25e-01, # a5  (CPE Alpha)
    5.47e+01, # R5  (Particle Resistance)
    1.42e-05  # C6  (Particle Capacitance)
]

# 3. FIXED BOUNDS
# We must ensure lower_bounds <= initial_guess <= upper_bounds
# Adjusted R2 upper bound from 1e-3 to 10 to accommodate your 5.96 guess.
lower_bounds = [0,      0,      0.01,   1e-9,   0.2,    1,      1e-12]
upper_bounds = [1e-1,   20,     100,    1e-1,   1.0,    1000,   1e-1]

circuit = CustomCircuit(circuit_string, initial_guess=initial_guess)

# 4. Fit
# If it still struggles, global_opt=True can be added here
circuit.fit(freq, z_complex, bounds=(lower_bounds, upper_bounds))
z_fit = circuit.predict(freq)

# 5. PRINT FINAL RESULTS
print("\n" + "="*60)
print(f"FINAL FIT RESULTS FOR {temp_val}°C")
print("="*60)
print(f"{'Parameter':<12} | {'Initial':<12} | {'Fitted':<12} | {'Change %'}")
print("-" * 60)

for name, start, final in zip(param_names, initial_guess, circuit.parameters_):
    diff = ((final - start) / start) * 100 if start != 0 else 0
    print(f"{name:<12} | {start:<12.2e} | {final:<12.2e} | {diff:>+8.1f}%")

print("-" * 60)
print(circuit)
print("="*60 + "\n")

# 6. Plotting
fig, ax1 = plt.subplots(figsize=(10, 6))

# Magnitude
color_mod = 'tab:blue'
ax1.loglog(freq, z_mod, 'o', color=color_mod, alpha=0.4, label='Data $|Z|$')
ax1.loglog(freq, np.abs(z_fit), '-', color=color_mod, linewidth=2, label='Fit $|Z|$')
ax1.set_ylabel(r'$|Z|$ ($\Omega$)', color=color_mod, fontsize=12, fontweight='bold')
ax1.set_xlabel('Frequency (Hz)', fontsize=12, fontweight='bold')
ax1.tick_params(axis='y', labelcolor=color_mod)

# Phase
ax2 = ax1.twinx()
color_phz = 'tab:red'
ax2.semilogx(freq, z_phz, 's', color=color_phz, alpha=0.4, label='Data Phase')
ax2.semilogx(freq, np.angle(z_fit, deg=True), '--', color=color_phz, linewidth=2, label='Fit Phase')
ax2.set_ylabel(r'Phase ($^{\circ}$)', color=color_phz, fontsize=12, fontweight='bold')
ax2.tick_params(axis='y', labelcolor=color_phz)

# Layout
ax1.grid(True, which="major", alpha=0.3)
title_line1 = f'Bode Plot Fit - {temp_val}°C'
title_line2 = rf'$R_3 = {circuit.parameters_[2]:.3f} \Omega$ | $a_5 = {circuit.parameters_[4]:.3f}$'
plt.title(title_line1 + '\n' + title_line2, fontweight='bold', fontsize=13)

lines, labels = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines + lines2, labels + labels2, loc='best')

fig.tight_layout()
plt.show()