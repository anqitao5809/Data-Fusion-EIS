import os
import pandas as pd
import re

def process_dta_to_formatted_excel(input_folder, output_filename="EIS_Final_Formatted.xlsx"):
    files = [f for f in os.listdir(input_folder) if f.upper().endswith('.DTA')]
    if not files:
        print("No .DTA files found.")
        return

    all_blocks = []

    for file_name in files:
        file_path = os.path.join(input_folder, file_name)
        
        # Extract temp from filename
        temp_match = re.search(r'_(\d+)C_', file_name)
        temp_val = int(temp_match.group(1)) if temp_match else 0

        # Find ZCURVE
        data_start_idx = 0
        with open(file_path, 'r', encoding='latin-1') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if "ZCURVE" in line:
                    data_start_idx = i + 1
                    break
        
        # Read and clean
        df_raw = pd.read_csv(file_path, sep='\t', skiprows=data_start_idx, encoding='latin-1')
        df_raw = df_raw.iloc[1:].reset_index(drop=True) # Drop units row
        df_raw.columns = [col.split()[0].strip() for col in df_raw.columns]

        # Create the 5-column block (matches your image structure)
        # Column 1 header is the Temp value, and we fill it with NaN below the first row
        block = pd.DataFrame({
            "temp.": [temp_val] + [float('nan')] * (len(df_raw)-1),
            "Freq": pd.to_numeric(df_raw['Freq'], errors='coerce'),
            "Zmod": pd.to_numeric(df_raw['Zmod'], errors='coerce'),
            "Freq_Copy": pd.to_numeric(df_raw['Freq'], errors='coerce'),
            "Zphz": pd.to_numeric(df_raw['Zphz'], errors='coerce')
        })
        
        # Add a blank spacer column between trials
        block[' '] = "" 
        all_blocks.append(block)

    # Merge all trials side-by-side
    final_df = pd.concat(all_blocks, axis=1)

    # Use XlsxWriter to force Scientific Notation
    writer = pd.ExcelWriter(output_filename, engine='xlsxwriter')
    # We write without the index and handle the headers carefully
    final_df.to_excel(writer, index=False, sheet_name='Sheet1')

    workbook  = writer.book
    worksheet = writer.sheets['Sheet1']

    # Define the 1.00E+01 format
    sci_format = workbook.add_format({'num_format': '0.00E+00'})

    # Apply formatting to the data area (starting from row 2 down)
    # worksheet.set_column(column_index, column_index, width, format)
    # We apply it to columns B, C, D, E, G, H, I, J... skipping the temp columns
    total_cols = len(final_df.columns)
    for col_num in range(total_cols):
        # Check if the column name is one of the data columns
        col_header = str(final_df.columns[col_num])
        if col_header in ['Freq', 'Zmod', 'Freq_Copy', 'Zphz']:
            worksheet.set_column(col_num, col_num, 12, sci_format)
        else:
            worksheet.set_column(col_num, col_num, 10)

    writer.close()
    print(f"Success! Processed {len(files)} files into {output_filename}")

# Change this to your actual folder path
process_dta_to_formatted_excel(r'C:\Users\taq58\Downloads\sample')