import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from impedance.models.circuits import CustomCircuit
from impedance.validation import linKK
import builtins

# Fix for internal impedance library calls
builtins.np = np 

# --- 1. LOAD AND CLEAN DATA ---
file_path = 'EIS_Compiled_Data.xlsx'
df = pd.read_excel(file_path)

# Data Cleaning
df.iloc[:, 0] = df.iloc[:, 0].ffill()
df = df.dropna(subset=[df.columns[1], df.columns[2]])

# Filter for 500C - REMOVED the 10kHz cap to include all frequencies
target_temp = 500.0
mask = (df.iloc[:, 0] == target_temp)
df_filtered = df[mask].sort_values(by=df.columns[1], ascending=False)

freq = df_filtered.iloc[:, 1].values 
z_mod = df_filtered.iloc[:, 2].values 
z_phz = df_filtered.iloc[:, 4].values

# --- 2. COMPLEX CONSTRUCTION ---
# We use -z_phz because EIS systems usually export phase as positive 
# for capacitive lag, but math requires a negative imaginary part.
z_complex = z_mod * np.exp(1j * np.deg2rad(-z_phz))

# --- 3. KK VALIDATION ---
try:
    # Unpacking all 5 values for impedance 1.7.1
    f_kk, z_kk, r_real, r_imag, mu = linKK(freq, z_complex, c=0.5)
    kk_score = np.mean(np.abs(r_real) + np.abs(r_imag))
    print(f"KK Validation Score: {kk_score:.4f}")
except Exception as e:
    print(f"KK Test Error: {e}")
    r_real, r_imag, kk_score = np.zeros_like(freq), np.zeros_like(freq), 999

# --- 4. CIRCUIT FITTING ---
# L0: Lead Inductance (common at >10kHz)
# R0: Solution Resistance
# p(R1, CPE1): Charge transfer resistance and Double Layer
model_str = "L0-R0-p(R1,CPE1)"

# Guesses: [L0, R0, R1, CPE1_Q, CPE1_alpha]
guess = [1e-7, 2.0, 1000.0, 1e-4, 0.8]
lower_b = [1e-10, 0.1, 1.0, 1e-8, 0.5]
upper_b = [1e-4, 100.0, 1e6, 0.1, 1.0]

try:
    circ = CustomCircuit(model_str, initial_guess=guess)
    circ.fit(freq, z_complex, bounds=(lower_b, upper_b))
    print("\n--- FIT PARAMETERS ---")
    print(circ)
    z_fit = circ.predict(freq)
except Exception as e:
    print(f"Circuit Fit failed: {e}")
    z_fit = None

# --- 5. PLOTTING ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))

# Nyquist Plot (Better for seeing the "Legit" shape)
ax_nyq = fig.add_axes([0.6, 0.65, 0.25, 0.2]) # Inset Nyquist
ax_nyq.scatter(z_complex.real, -z_complex.imag, s=10, c='blue')
if z_fit is not None:
    ax_nyq.plot(z_fit.real, -z_fit.imag, 'r-')
ax_nyq.set_title("Nyquist Shape")
ax_nyq.set_xlabel("Z'")
ax_nyq.set_ylabel("-Z''")

# Bode Magnitude Plot
ax1.loglog(freq, z_mod, 'bo', label='Experimental Data', alpha=0.6)
if z_fit is not None:
    f_smooth = np.logspace(np.log10(freq.min()), np.log10(freq.max()), 200)
    z_smooth = circ.predict(f_smooth)
    ax1.loglog(f_smooth, np.abs(z_smooth), 'r-', lw=2, label='Fit (L-R-p(R,CPE))')

ax1.set_title(f"Bode Analysis (Full Range) | KK Score: {kk_score:.4f}")
ax1.set_ylabel("Magnitude |Z| (Ohm)")
ax1.grid(True, which="both", ls="-", alpha=0.3)
ax1.legend()

# KK Residuals Plot
ax2.plot(freq, r_real * 100, 'g-o', label='Real Residual %', markersize=3)
ax2.plot(freq, r_imag * 100, 'm-s', label='Imag Residual %', markersize=3)
ax2.set_xscale('log')
ax2.axhline(0, color='black', lw=1)
ax2.set_ylim(-10, 10) # Zoom in on the error
ax2.set_ylabel("KK Normalized Error %")
ax2.set_xlabel("Frequency (Hz)")
ax2.legend()

plt.tight_layout()
plt.show()