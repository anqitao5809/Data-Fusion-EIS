import os
import pandas as pd
import re

def process_nested_eis_folders(root_folder, output_filename="EIS_Compiled_Data_Trial1.xlsx"):
    # get subfolders and sort by temperature
    subfolders = [d for d in os.listdir(root_folder) if os.path.isdir(os.path.join(root_folder, d))]
    
    def extract_temp_from_str(name):
        match = re.search(r'(\d+)', name)
        return int(match.group(1)) if match else 999
    
    subfolders.sort(key=extract_temp_from_str)

    all_blocks = []

    # go through each temperature folder
    for folder in subfolders:
        folder_path = os.path.join(root_folder, folder)
        
        # filters out name with "OCP"
        files = [f for f in os.listdir(folder_path) if f.upper().endswith('.DTA')]
        eis_files = [f for f in files if '_EIS' in f.upper() and '_OCP' not in f.upper()]
        
        # sort files in trial number order
        eis_files.sort()

        for file_name in eis_files:
            file_path = os.path.join(folder_path, file_name)
            
            temp_match = re.search(r'_(\d+)C_', file_name)
            trial_match = re.search(r'_(\d+)_EIS', file_name, re.IGNORECASE)
            
            temp_val = temp_match.group(1) if temp_match else "Unknown"
            trial_val = trial_match.group(1) if trial_match else "X"

            # find zcurve data
            data_start_idx = -1
            with open(file_path, 'r', encoding='latin-1') as f:
                for i, line in enumerate(f):
                    if "ZCURVE" in line:
                        data_start_idx = i + 1
                        break
            
            if data_start_idx == -1:
                continue

            df_raw = pd.read_csv(file_path, sep='\t', skiprows=data_start_idx, encoding='latin-1')
            df_raw = df_raw.iloc[1:].reset_index(drop=True)
            df_raw.columns = [col.split()[0].strip() for col in df_raw.columns]

            # 5-column unit
            # Header format: Temp_500C_T1 ( T1 for trial 1)
            temp_header = f"Temp_{temp_val}C_T{trial_val}"
            
            block = pd.DataFrame({
                temp_header: [temp_val] + [float('nan')] * (len(df_raw)-1),
                "Freq": pd.to_numeric(df_raw['Freq'], errors='coerce'),
                "Zmod": pd.to_numeric(df_raw['Zmod'], errors='coerce'),
                "Freq_alt": pd.to_numeric(df_raw['Freq'], errors='coerce'),
                "Zphz": pd.to_numeric(df_raw['Zphz'], errors='coerce')
            })
            all_blocks.append(block)

    if not all_blocks:
        print("No matching EIS files found.")
        return

    # Merge side-by-side
    final_df = pd.concat(all_blocks, axis=1)

    # Excel Formatting
    writer = pd.ExcelWriter(output_filename, engine='xlsxwriter')
    final_df.to_excel(writer, index=False, sheet_name='EIS_Data')

    workbook  = writer.book
    worksheet = writer.sheets['EIS_Data']
    
    sci_format = workbook.add_format({'num_format': '0.00E+00'})
    header_format = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3', 'border': 1})

    for col_num, col_name in enumerate(final_df.columns):
        # scientific notation to data columns
        if "Temp" not in str(col_name):
            worksheet.set_column(col_num, col_num, 12, sci_format)
        else:
            worksheet.set_column(col_num, col_num, 15)
        
        # headers with formatting
        worksheet.write(0, col_num, col_name, header_format)

    writer.close()
    print(f"Success! Compiled {len(all_blocks)} EIS trials into {output_filename}")

# function calling
root_path = r'C:\Users\taq58\Downloads\0.200mol%Be' 
process_nested_eis_folders(root_path)