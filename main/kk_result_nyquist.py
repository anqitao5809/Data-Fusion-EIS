import numpy as np
import matplotlib.pyplot as plt
import os

# 1. Setup the workspace
output_folder = "kk_results_025mol"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

def perform_lin_kk(f, Z, M=25):
    """Calculates Linear KK fit and consistency (mu) using RC elements."""
    omega = 2 * np.pi * f
    tau = np.logspace(np.log10(1/np.max(omega)), np.log10(1/np.min(omega)), M)
    A_re, A_im = np.zeros((len(f), M + 1)), np.zeros((len(f), M + 1))
    A_re[:, 0] = 1.0 
    for k in range(M):
        den = 1.0 + (omega * tau[k])**2
        A_re[:, k+1], A_im[:, k+1] = 1.0 / den, - (omega * tau[k]) / den
    
    # Linear Least Squares Fit
    A = np.vstack([A_re, A_im])
    b = np.concatenate([Z.real, Z.imag])
    R_params, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
    
    Z_fit = (A_re @ R_params) + 1j * (A_im @ R_params)
    R_k = R_params[1:]
    mu = 1 - (np.sum(np.abs(R_k[R_k < 0])) / np.sum(np.abs(R_k[R_k >= 0])))
    res = (Z - Z_fit) / np.abs(Z) * 100
    return Z_fit, mu, res

# 2. Define temperatures (replace with your actual data keys/files)
temperatures = [400, 450, 500, 550, 600]
freqs = np.logspace(-1, 5, 50)

print(f"{'Temp':<8} | {'Score (mu)':<12} | {'Status':<10}")
print("-" * 35)

for temp in temperatures:
    # --- DATA LOADING PLACEHOLDER ---
    # In your real setup, replace this with your CSV loading logic:
    # df = pd.read_csv(f"025mol_{temp}C_trial1.csv")
    # f, Z = df['freq'], df['real'] + 1j*df['imag']
    
    # Simulating data for the example:
    R_total = 100 * (400/temp)**1.5  # Resistance drops with temp
    Z_data = R_total / (1 + (1j * 2 * np.pi * freqs * 1e-3)**0.85)
    # Add a bit of 'experimental' noise
    Z_data += (np.random.randn(len(freqs)) + 1j*np.random.randn(len(freqs))) * (R_total * 0.005)

    # 3. Perform KK Validation
    Z_fit, mu, res = perform_lin_kk(freqs, Z_data)
    
    # Classification Logic
    status = "PASS" if mu > 0.98 else "MARGINAL" if mu > 0.88 else "FAIL"
    print(f"{temp:03}°C     | {mu:10.4f}   | {status}")

    # 4. Generate and save the plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot 1: Nyquist Fit
    ax1.plot(Z_data.real, -Z_data.imag, 'bo', label='Experimental Trial 1')
    ax1.plot(Z_fit.real, -Z_fit.imag, 'r-', linewidth=2, label='Lin-KK Fit')
    ax1.set_title(f"Nyquist Plot: 0.25 mol @ {temp}°C\n({status})")
    ax1.set_xlabel("Z' (Ω)")
    ax1.set_ylabel("-Z'' (Ω)")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: KK Residuals
    ax2.semilogx(freqs, res.real, 'b-o', label='Real Residual %')
    ax2.semilogx(freqs, res.imag, 'r-o', label='Imag Residual %')
    ax2.axhline(0, color='black', linestyle='--')
    ax2.set_title(f"KK Residuals (Consistency mu = {mu:.4f})")
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("Error (%)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f"{output_folder}/KK_Result_{temp}C.png")
    plt.close() # Free up memory

print(f"\nDone! All plots saved to the '{output_folder}' folder.")