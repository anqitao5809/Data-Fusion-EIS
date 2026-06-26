import os
import pandas as pd
import re

def process_dta_to_multi_column(input_folder, output_filename="EIS_Combined_Trials.xlsx"):
    # Filter for .DTA files
    files = [f for f in os.listdir(input_folder) if f.upper().endswith('.DTA')]
    if not files:
        print("No .DTA files found.")
        return

    all_blocks = []

    for file_name in files:
        file_path = os.path.join(input_folder, file_name)
        
        # Extract temp from filename (looks for _25C_ or similar)
        temp_match = re.search(r'_(\d+)C_', file_name)
        temp_val = int(temp_match.group(1)) if temp_match else "N/A"

        # Locate the data start point (ZCURVE)
        data_start_idx = -1
        with open(file_path, 'r', encoding='latin-1') as f:
            for i, line in enumerate(f):
                if "ZCURVE" in line:
                    data_start_idx = i + 1
                    break
        
        if data_start_idx == -1:
            print(f"Skipping {file_name}: 'ZCURVE' not found.")
            continue

        # Read the data, skipping the units row (the row immediately after ZCURVE)
        df_raw = pd.read_csv(file_path, sep='\t', skiprows=data_start_idx, encoding='latin-1')
        df_raw = df_raw.iloc[1:].reset_index(drop=True)
        
        # Clean column names (removes trailing units/spaces)
        df_raw.columns = [col.split()[0].strip() for col in df_raw.columns]

        # Create the 5-column unit
        # Trial structure: [Temp, Freq, Zmod, Freq, Zphz]
        block = pd.DataFrame({
            "Temp": [temp_val] + [float('nan')] * (len(df_raw)-1),
            "Freq": pd.to_numeric(df_raw['Freq'], errors='coerce'),
            "Zmod": pd.to_numeric(df_raw['Zmod'], errors='coerce'),
            "Freq_alt": pd.to_numeric(df_raw['Freq'], errors='coerce'),
            "Zphz": pd.to_numeric(df_raw['Zphz'], errors='coerce')
        })
        
        all_blocks.append(block)

    if not all_blocks:
        return

    # Concatenate side-by-side
    final_df = pd.concat(all_blocks, axis=1)

    # Export with XlsxWriter for formatting
    writer = pd.ExcelWriter(output_filename, engine='xlsxwriter')
    final_df.to_excel(writer, index=False, sheet_name='Data')

    workbook  = writer.book
    worksheet = writer.sheets['Data']

    # Define scientific notation format
    sci_format = workbook.add_format({'num_format': '0.00E+00'})
    # Define header format (optional, makes it look professional)
    header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})

    # Apply formatting across all columns
    for col_num, col_name in enumerate(final_df.columns):
        # Apply scientific notation to everything EXCEPT Temperature columns
        if "Temp" not in str(col_name):
            worksheet.set_column(col_num, col_num, 12, sci_format)
        else:
            worksheet.set_column(col_num, col_num, 10)
        
        # Re-write headers with bold format
        worksheet.write(0, col_num, col_name, header_format)

    writer.close()
    print(f"Success! Processed {len(files)} trials into {output_filename}")

# Run the script
folder_path = r'C:\Users\taq58\Downloads\sample'
process_dta_to_multi_column(folder_path)