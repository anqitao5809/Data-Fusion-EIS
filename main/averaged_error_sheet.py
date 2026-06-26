import os
import pandas as pd
import re
import numpy as np

def process_eis_averages_with_min_max(root_folder, output_filename="EIS_Averages_MinMax_Trial1.xlsx"):
    # get subfolders and sort them by the temperature in their name
    subfolders = [d for d in os.listdir(root_folder) if os.path.isdir(os.path.join(root_folder, d))]
    
    def extract_temp_val(name):
        match = re.search(r'(\d+)', name)
        return int(match.group(1)) if match else 999
    
    subfolders.sort(key=extract_temp_val)

    all_temp_blocks = []

    # iterate through each temperature folder
    for folder in subfolders:
        folder_path = os.path.join(root_folder, folder)
        temp_val = extract_temp_val(folder)
        
        # Filter for EIS, skip "OCP"
        files = [f for f in os.listdir(folder_path) if f.upper().endswith('.DTA')]
        eis_files = [f for f in files if '_EIS' in f.upper() and '_OCP' not in f.upper()]
        
        if not eis_files:
            continue

        temp_data_list = []

        for file_name in eis_files:
            file_path = os.path.join(folder_path, file_name)
            
            # find Z curve
            data_start_idx = -1
            with open(file_path, 'r', encoding='latin-1') as f:
                for i, line in enumerate(f):
                    if "ZCURVE" in line:
                        data_start_idx = i + 1
                        break
            
            if data_start_idx == -1: continue

            # read data and clean headers
            df = pd.read_csv(file_path, sep='\t', skiprows=data_start_idx, encoding='latin-1')
            df = df.iloc[1:].reset_index(drop=True)
            df.columns = [col.split()[0].strip() for col in df.columns]
            
            # Extract only the needed columns
            subset = df[['Freq', 'Zmod', 'Zphz']].apply(pd.to_numeric, errors='coerce')
            temp_data_list.append(subset)

        if not temp_data_list: continue

        # combine trials and calculate statistics per Frequency point
        combined_trials = pd.concat(temp_data_list)
        stats = combined_trials.groupby('Freq').agg({
            'Zmod': ['mean', 'min', 'max'],
            'Zphz': ['mean', 'min', 'max']
        }).reset_index()

        # Flatten multi-index columns: ['Freq', 'Zmod_mean', 'Zmod_min'...]
        stats.columns = ['Freq', 'Zmod_Avg', 'Zmod_Min', 'Zmod_Max', 'Zphz_Avg', 'Zphz_Min', 'Zphz_Max']
        
        # Sort by frequency descending (standard EIS)
        stats = stats.sort_values(by='Freq', ascending=False).reset_index(drop=True)

        # 4. Create the 8-column block for this temperature
        block = pd.DataFrame({
            f"Temp_{temp_val}C": [temp_val] + [np.nan] * (len(stats)-1),
            "Freq": stats['Freq'],
            "Zmod_Avg": stats['Zmod_Avg'],
            "Zmod_Min": stats['Zmod_Min'],
            "Zmod_Max": stats['Zmod_Max'],
            "Zphz_Avg": stats['Zphz_Avg'],
            "Zphz_Min": stats['Zphz_Min'],
            "Zphz_Max": stats['Zphz_Max']
        })
        
        all_temp_blocks.append(block)

    if not all_temp_blocks:
        print("No valid EIS data found in subfolders.")
        return

    # 5. Concatenate all temperature blocks side-by-side
    final_df = pd.concat(all_temp_blocks, axis=1)

    # 6. Export with XlsxWriter for scientific notation
    writer = pd.ExcelWriter(output_filename, engine='xlsxwriter')
    final_df.to_excel(writer, index=False, sheet_name='Averages')

    workbook = writer.book
    worksheet = writer.sheets['Averages']
    
    # Formats
    sci_format = workbook.add_format({'num_format': '0.00E+00'})
    header_format = workbook.add_format({'bold': True, 'bg_color': '#EFEFEF', 'border': 1})

    for col_num, col_name in enumerate(final_df.columns):
        # Apply scientific notation to all numeric columns (skip Temp)
        if "Temp" not in str(col_name):
            worksheet.set_column(col_num, col_num, 12, sci_format)
        else:
            worksheet.set_column(col_num, col_num, 12)
        
        # Rewrite the header with formatting
        worksheet.write(0, col_num, col_name, header_format)

    writer.close()
    print(f"Success! Averaged data with Min/Max saved to {output_filename}")

# --- UPDATE YOUR ROOT FOLDER PATH HERE ---
root_path = r'C:\Users\taq58\Downloads\0.200mol%Be'
process_eis_averages_with_min_max(root_path)
