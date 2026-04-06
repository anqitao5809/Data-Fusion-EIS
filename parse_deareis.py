import pandas as pd
import numpy as np
import os

# Configuration
input_file = 'EIS_Averages_MinMax.xlsx'  # Your source file
sheet_name = 'Averages'                  # The data sheet
output_folder = 'DEAREIS_Outputs'         # The folder for your filtered CSVs
max_frequency = 10000                   # Filter limit: 1*10^5 Hz

def convert_xlsx_to_dearis_filtered(filename, sheet, folder, limit_f):
    # Create the output directory if it doesn't exist
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"Created folder: {folder}")
    
    # Load the Excel data
    print(f"Reading {filename}...")
    df = pd.read_excel(filename, sheet_name=sheet)
    
    # Each temperature block is 8 columns wide
    cols_per_block = 8
    num_blocks = len(df.columns) // cols_per_block
    
    for i in range(num_blocks):
        start_col = i * cols_per_block
        block = df.iloc[:, start_col : start_col + cols_per_block]
        
        # Identify Temperature (header of first column in block)
        temp_label = block.columns[0]
        
        # Extract Frequency, Magnitude (Avg), and Phase (Avg)
        freq = block.iloc[:, 1]
        z_mod = block.iloc[:, 2]
        z_phz = block.iloc[:, 5]
        
        # Remove empty rows
        valid_mask = freq.notna()
        freq, z_mod, z_phz = freq[valid_mask], z_mod[valid_mask], z_phz[valid_mask]
        
        # Calculate Real and Imaginary components
        phi_rad = np.radians(z_phz)
        z_real = z_mod * np.cos(phi_rad)
        z_imag = z_mod * np.sin(phi_rad)
        
        # Create DataFrame
        dearis_df = pd.DataFrame({
            'Frequency (Hz)': freq,
            "Z' (Ohm)": z_real,
            "Z'' (Ohm)": z_imag
        })
        
        # --- FILTER: Keep only rows where Frequency <= 1*10^5 ---
        dearis_df = dearis_df[dearis_df['Frequency (Hz)'] <= limit_f]
        
        # Save to the specific output folder
        output_name = f"{temp_label}_DEARIS_Filtered.csv"
        output_path = os.path.join(folder, output_name)
        dearis_df.to_csv(output_path, index=False)
        print(f"  - Saved to folder: {output_name} (Max Freq in file: {dearis_df['Frequency (Hz)'].max() if not dearis_df.empty else 'N/A'})")

if __name__ == "__main__":
    if os.path.exists(input_file):
        convert_xlsx_to_dearis_filtered(input_file, sheet_name, output_folder, max_frequency)
        print("\nSuccess! All files are filtered and saved in the folder.")
    else:
        print(f"Error: File '{input_file}' not found.")