import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from impedance.models.circuits import CustomCircuit
from impedance.validation import linKK
import builtins

builtins.np = np 

# 1. LOAD DATA
df = pd.read_excel('EIS_Averages_MinMax.xlsx', usecols=[1, 2, 5])
freq_raw = df.iloc[:, 0].values  
z_mod_raw = df.iloc[:, 1].values 
z_phz_raw = df.iloc[:, 2].values 

# 2. CROP THE DATA (Remove top and bottom ends)
trim_percent = 10  # Adjust this to crop more or less
n_total = len(freq_raw)
start_idx = int(n_total * (trim_percent / 100))
end_idx = n_total - start_idx

freq = freq_raw[start_idx:end_idx]
z_mod = z_mod_raw[start_idx:end_idx]
z_phz = z_phz_raw[start_idx:end_idx]
z_complex = z_mod * np.exp(1j * np.deg2rad(z_phz))

print(f"Original points: {n_total} | Cropped points: {len(freq)}")

# 3. KK VALIDATION (On Cropped Data)
print("Running KK on cropped data...")
kk_output = linKK(freq, z_complex, c=0.5)

# Handle the v1.7.1 tuple/array return
if isinstance(kk_output, tuple):
    z_kk = np.array(kk_output[1]) if len(kk_output) > 1 else np.array(kk_output[0])
else:
    z_kk = np.array(kk_output)

z_kk = z_kk.astype(complex)
res_real = (z_complex.real - z_kk.real) / np.abs(z_complex)
res_imag = (z_complex.imag - z_kk.imag) / np.abs(z_complex)
kk_score = np.mean(np.abs(res_real) + np.abs(res_imag))

# 4. FIT WINNING MODEL (CPE-Interface)
wire_L, wire_R, salt_R = 4.46e-07, 5.96, 0.739
model_str = "p(L1,R2)-R3-CPE4-p(R5,C6)"
guess = [wire_L, wire_R, salt_R, 1.4e-5, 0.9, 54.7, 1.4e-5]

try:
    circ = CustomCircuit(model_str, initial_guess=guess)
    circ.fit(freq, z_complex)
    z_fit = circ.predict(freq)
    print("Fit successful on cropped data.")
except Exception as e:
    print(f"Fit failed: {e}")
    z_fit = None

# 5. PLOTTING
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

# Magnitude Plot
ax1.loglog(freq_raw, z_mod_raw, 'k.', alpha=0.2, label='Excluded Data')
ax1.loglog(freq, z_mod, 'bo', markersize=5, label='Cropped Data')
if z_fit is not None:
    ax1.loglog(freq, np.abs(z_fit), 'r-', linewidth=2, label='Model Fit')

ax1.set_title(f"Cropped Analysis (Trim: {trim_percent}%) | KK Score: {kk_score:.4f}")
ax1.set_ylabel("Magnitude |Z|")
ax1.legend()

# Residuals Plot (Is the data now physical?)
ax2.plot(freq, res_real * 100, 'g-', label='Real Res %')
ax2.plot(freq, res_imag * 100, 'm-', label='Imag Res %')
ax2.set_xscale('log')
ax2.axhline(0, color='black', lw=1)
ax2.set_ylabel("KK Error %")
ax2.set_xlabel("Frequency (Hz)")
ax2.legend()

plt.tight_layout()
plt.show()

if z_fit is not None:
    print("\n--- NEW PARAMETERS (CROPPED) ---")
    print(circ)