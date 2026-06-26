import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib.ticker as ticker

def plot_first_temp_set(file_path, output_folder="EIS_Results"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 1. Load and Clean Data
    df = pd.read_excel(file_path)
    temp_val = df.iloc[0, 0]
    
    # Selecting Freq, Zmod_Avg, and Zphz_Avg
    data_subset = df.iloc[:, [1, 2, 5]].copy()
    data_subset.columns = ['Freq', 'Zmod', 'Zphz']
    
    for col in data_subset.columns:
        data_subset[col] = pd.to_numeric(data_subset[col], errors='coerce')
    
    data_subset = data_subset.dropna().sort_values(by='Freq')

    # 2. Create Plot
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # --- Magnitude Plot (Left Y - Log Scale) ---
    color_mod = 'tab:blue'
    ax1.loglog(data_subset['Freq'], data_subset['Zmod'], 'o-', 
               markersize=5, color=color_mod, label='Magnitude $|Z|$', linewidth=1.5)
    
    ax1.set_xlabel('Frequency (Hz)', fontsize=12, fontweight='bold')
    ax1.set_ylabel(r'$|Z|$ ($\Omega$)', color=color_mod, fontsize=12, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor=color_mod)

    # --- Phase Plot (Right Y - Linear Scale) ---
    ax2 = ax1.twinx()
    color_phz = 'tab:red'
    ax2.semilogx(data_subset['Freq'], data_subset['Zphz'], 's-', 
                 markersize=5, color=color_phz, label='Phase', linewidth=1.5)
    
    ax2.set_ylabel(r'Phase Angle ($^{\circ}$)', color=color_phz, fontsize=12, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor=color_phz)

    # 3. AUTO-ADJUST GRID AND SCALE
    # This ensures the grid hits "nice" numbers (multiples of 10 or 45 degrees) 
    # while still auto-scaling to your data.
    ax1.xaxis.set_major_locator(ticker.LogLocator(base=10.0, numticks=15))
    ax2.yaxis.set_major_locator(ticker.MaxNLocator(nbins=10, steps=[1, 2, 5, 10]))
    
    # Force the grid lines to be "even" by only showing Major lines
    # Minor log lines are what make it look "crowded/uneven"
    ax1.grid(True, which="major", axis='both', linestyle='-', alpha=0.5)
    ax1.set_axisbelow(True)

    # 4. Title & Legend
    plt.title(f'Bode Plot - {temp_val}°C', fontsize=14, fontweight='bold')
    
    # Merge legends into one box
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc='best', framealpha=0.9)

    fig.tight_layout()

    # 5. Save
    save_path = os.path.join(output_folder, f"Bode_{temp_val}C_Auto.png")
    plt.savefig(save_path, dpi=300)
    plt.close(fig)
    
    print(f"Plot saved with auto-scaling: {save_path}")

plot_first_temp_set('EIS_Averages_MinMax.xlsx')