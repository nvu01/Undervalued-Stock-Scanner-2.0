import glob
import os
from io import StringIO
from SCRIPTS.etl import get_files, data_cleaning, get_grouped_stats
import pandas as pd
from datetime import datetime

def get_current_pos():
    '''
    Retrieve and process the CSV file in "Position Statement" folder
    Return a dataframe that lists all the active stocks
    '''
    # Get absolute path to the file relative to project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    folder_path = os.path.join(project_root, 'Position Statement')
    files = glob.glob(os.path.join(folder_path, "*"))
    filepath = max(files, key=os.path.getmtime)

    with open(filepath) as f:
        lines = f.readlines()

    # Identify the location of the table
    start_indx = None
    for i, line in enumerate(lines):
        if 'Group "Undervalued"' in line:
            start_indx = i + 3
            break

    end_indx = None
    for j in range(start_indx + 1, len(lines)):
        if lines[j].strip() == '':
            end_indx = j - 1
            break

    # Extract the table
    data = ''.join(lines[start_indx:end_indx])
    df = pd.read_csv(StringIO(data))

    # Transform the dataframe
    df.dropna(subset=['BP Effect'], inplace=True)
    df.reset_index(drop=True, inplace=True)
    df = df[['Instrument']]
    df.rename(columns={'Instrument': 'Symbol'}, inplace=True)

    return df

def get_all_stock_data(all_files, metric_cols, pos):
    '''
    Apply data_cleaning() function from etl.py to process all the files in "Downloaded CSV Files" folder
    Apply get_grouped_stats() function from etl.py to generate stats columns
    Filter only for stocks in current position statement
    '''
    # Get all stock data and stats
    dfs = []
    for i, file in enumerate(all_files):
        df = data_cleaning(file)
        _, df_with_stats = get_grouped_stats(df, metric_cols)
        dfs.append(df_with_stats)

    full_df = pd.concat(dfs, ignore_index=True)
    full_df.drop(columns=full_df.filter(like='_std').columns, axis=1, inplace=True)     # Remove std columns

    # Filter for current positions
    merged_df = pd.merge(pos, full_df, how='left', on='Symbol')

    return merged_df

def scan(df):
    '''
    Scan for stocks that have exit signals
    - Define overvaluation and bad quality signals
    - Create columns that count overvaluation and bad quality signals
    - Select only stocks that have at least one signal
    '''
    # Scan for active stocks that are no longer in the scanner due to their Market Cap being out of range (250M - 2B)
    out_of_scanner = df.loc[df['Market Cap Group'].isna(), 'Symbol']

    scanned_df = df.loc[~df['Market Cap Group'].isna(), :].copy()

    # Create "Overvaluation" column
    scanned_df['Overvaluation'] = 0
    scanned_df.loc[scanned_df['P/FCF'] >= scanned_df['P/FCF_mean'], 'Overvaluation'] += 1
    scanned_df.loc[scanned_df['P/B'] >= scanned_df['P/B_mean'], 'Overvaluation'] += 1
    scanned_df.loc[scanned_df['P/E'] >= scanned_df['P/E_mean'], 'Overvaluation'] += 1

    # Create "Bad Quality" column
    scanned_df['Bad Quality'] = 0
    scanned_df.loc[scanned_df['ROE'] < 10, 'Bad Quality'] += 1
    scanned_df.loc[scanned_df['ROA'] < 5, 'Bad Quality'] += 1
    scanned_df.loc[scanned_df['ROE'] < scanned_df['ROE_mean'], 'Bad Quality'] += 1
    scanned_df.loc[scanned_df['ROA'] < scanned_df['ROA_mean'], 'Bad Quality'] += 1
    scanned_df.loc[scanned_df['P/FCF'] <= 0, 'Bad Quality'] += 1
    scanned_df.loc[scanned_df['P/E'] <= 0, 'Bad Quality'] += 1

    # Scan for all conditions
    scanned_df = scanned_df.loc[(scanned_df['Overvaluation'] >= 1) | (scanned_df['Bad Quality'] >= 1), :]

    # Rearrange columns and round numbers
    scanned_df = scanned_df[['Symbol', 'Industry', 'Overvaluation', 'Bad Quality', 'P/FCF', 'P/FCF_mean', 'P/B', 'P/B_mean', 'P/E',
         'P/E_mean', 'ROE', 'ROE_mean', 'ROA', 'ROA_mean', 'A/E', 'A/E_mean']]

    scanned_df = scanned_df.round(2)

    return out_of_scanner, scanned_df

def out_put(scanned_df, output_path):
    '''
    Output scanned dataframe to .xlsx file with conditional format to highlight signals
    '''
    row_count = len(scanned_df)
    # Save dataframe as .xlsx with clean layout and conditional format
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        scanned_df.to_excel(writer, index=False, sheet_name='Data')

        workbook = writer.book
        worksheet = writer.sheets['Data']

        # Create formats
        bg_red = workbook.add_format({'bg_color': '#F2DCDB'})
        font_red = workbook.add_format({'font_color': '#C00000'})
        bg_yellow = workbook.add_format({'bg_color': '#F0E199'})
        font_bg_red_bold = workbook.add_format({'font_color': '#C00000', 'bg_color': '#F2DCDB', 'bold': True})

        # Apply conditional formatting
        # Overvaluation
        worksheet.conditional_format(1, 4, row_count, 4,  # P/FCF >= Mean
                                     {'type': 'formula',
                                      'criteria': '=$E2>=$F2',
                                      'format': bg_yellow})

        worksheet.conditional_format(1, 6, row_count, 6,  # P/B >= Mean
                                     {'type': 'formula',
                                      'criteria': '=$G2>=$H2',
                                      'format': bg_yellow})

        worksheet.conditional_format(1, 8, row_count, 8,  # P/E >= Mean
                                     {'type': 'formula',
                                      'criteria': '=$I2>=$J2',
                                      'format': bg_yellow})

        # Bad quality
        worksheet.conditional_format(1, 10, row_count, 10,  # ROE < 10
                                     {'type': 'cell',
                                      'criteria': '<',
                                      'value': 10,
                                      'format': bg_red})

        worksheet.conditional_format(1, 12, row_count, 12,  # ROA < 5
                                     {'type': 'cell',
                                      'criteria': '<',
                                      'value': 5,
                                      'format': bg_red})

        worksheet.conditional_format(1, 10, row_count, 10,  # ROE < Mean
                                     {'type': 'formula',
                                      'criteria': '=$K2<$L2',
                                      'format': font_red})

        worksheet.conditional_format(1, 12, row_count, 12,  # ROA < Mean
                                     {'type': 'formula',
                                      'criteria': '=$M2<$N2',
                                      'format': font_red})

        # Severe deterioration
        worksheet.conditional_format(1, 4, row_count, 4,  # P/FCF <= 0
                                     {'type': 'cell',
                                      'criteria': '<=',
                                      'value': 0,
                                      'format': font_bg_red_bold})

        worksheet.conditional_format(1, 8, row_count, 8,  # P/E <= 0
                                     {'type': 'cell',
                                      'criteria': '<=',
                                      'value': 0,
                                      'format': font_bg_red_bold})

        worksheet.conditional_format(1, 10, row_count, 10,  # ROE < 0
                                     {'type': 'cell',
                                      'criteria': '<',
                                      'value': 0,
                                      'format': bg_red})

        worksheet.conditional_format(1, 12, row_count, 12,  # ROA < 0
                                     {'type': 'cell',
                                      'criteria': '<',
                                      'value': 0,
                                      'format': bg_red})

        # Legend for all formats
        worksheet.write("V1", "Severe")
        worksheet.write("V2", "P/FCF <= 0", font_bg_red_bold)
        worksheet.write("V3", "P/E <= 0", font_bg_red_bold)
        worksheet.write("V4", "ROE < 0", font_bg_red_bold)
        worksheet.write("V5", "ROA < 0", font_bg_red_bold)

        worksheet.write("V8", "Overvaluation")
        worksheet.write("V9", "P/FCF >= Mean", bg_yellow)
        worksheet.write("V10", "P/B >= Mean", bg_yellow)
        worksheet.write("V11", "P/E >= Mean", bg_yellow)

        worksheet.write("V13", "Bad Quality")
        worksheet.write("V14", "ROE < 10 (non-REITs)", bg_red)
        worksheet.write("V15", "ROA < 5", bg_red)
        worksheet.write("V16", "ROE < Mean", font_red)
        worksheet.write("V17", "ROA < Mean", font_red)

def main():
    '''
    Create a pipeline to process raw data
    '''
    metric_cols = ['P/FCF', 'P/B', 'ROE', 'ROA', 'A/E', 'P/E']
    all_files, _, project_root = get_files()
    pos = get_current_pos()
    df = get_all_stock_data(all_files, metric_cols, pos)
    out_of_scanner, scanned_df = scan(df)

    # Save files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    unscannable_folder = os.path.join(project_root, 'Exit Signals', 'Unscannable', f'{timestamp}_OutOfScanner.xlsx')
    out_of_scanner.to_excel(unscannable_folder, index=False)

    scannable_path = os.path.join(project_root, 'Exit Signals', 'Scannable', f'{timestamp}_ExitSignals.xlsx')
    out_put(scanned_df, scannable_path)

    print('File processing completed')

if __name__ == "__main__":
    main()