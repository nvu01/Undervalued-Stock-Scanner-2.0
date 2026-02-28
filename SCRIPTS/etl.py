import glob
import os
import pandas as pd
import numpy as np

def get_files():
    '''
    Retrieve all files in "Downloaded CSV Files" folder
    Return a list of file paths for 11 files
    Return the number files in the folder
    '''
    all_files = []

    # Get absolute path to the "Downloaded CSV Files" folder relative to project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    folder_path = os.path.join(project_root, 'Downloaded CSV Files')

    for root, dirs, files in os.walk(folder_path):
        files = glob.glob(os.path.join(root,'*.csv'))
        for f in files :
            all_files.append(os.path.abspath(f))

    # get total number of files found
    num_files = len(all_files)
    return all_files, num_files, project_root

def data_cleaning(file):
    '''
    Apply data cleaning to each file in "Downloaded CSV Files" folder
    '''
    df = pd.read_csv(file, skiprows=3)
    # Change column headers
    df.rename(columns={'Market Cap': 'Market Cap (M)', 'Last': 'Current Price',
                       'Free Cash Flow Per Share - Current (LTM)': 'Free CF',
                       'Book Value Per Share - Current (LTM)': 'BVPS',
                       'Earnings Per Share - TTM - Current (LTM)': 'EPS',
                       'Return on Equity (ROE) - Current (LTM)': 'ROE',
                       'Return on Assets (ROA) - Current (LTM)': 'ROA',
                       'Financial Leverage (Assets/Equity) - Current (LTM)': 'A/E'}, inplace=True)

    # Make sure Market Cap (M) column is in the right format before converting it to integer
    df['Market Cap (M)'] = df['Market Cap (M)'].str.split(' ').str[0]
    df['Market Cap (M)'] = df['Market Cap (M)'].str.replace(',', '')

    # Make sure metric columns are in the right format before converting them to float
    columns = ['Free CF', 'BVPS', 'EPS', 'ROE', 'ROA', 'A/E']
    for col in columns:
        if df[col].dtypes == 'object':
            df[col] = df[col].str.replace('[$),]', '', regex=True)
            df[col] = df[col].str.replace('(', '-', regex=False)
            df[col] = df[col].replace('<empty>', np.nan)
    # Convert numeric columns to the appropriate datatypes
    df = df.astype({'Market Cap (M)':'int64','Free CF':'float64', 'BVPS':'float64', 'EPS':'float64', 'ROE':'float64', 'ROA':'float64', 'A/E':'float64'})

    # Calculate new numeric columns
    df['P/FCF'] = df['Current Price'] / df['Free CF']
    df['P/B'] = df['Current Price'] / df['BVPS']
    df['P/E'] = df['Current Price'] / df['EPS']

    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    # Create Market Cap Group column
    df.loc[df['Market Cap (M)'] <= 2000, 'Market Cap Group'] = 'Small'
    df.loc[df['Market Cap (M)'].between(2000, 9999), 'Market Cap Group'] = 'Mid'
    df.loc[df['Market Cap (M)'] >= 10000, 'Market Cap Group'] = 'Large'

    # Keep only the important columns and rearrange column order
    df = df[['Market Cap Group', 'Industry', 'Symbol', 'Company Name', 'Market Cap (M)', 'Current Price', 'P/FCF', 'P/B', 'ROE', 'ROA', 'A/E', 'P/E']]

    return df

def mean_std(group):
    '''
    Calculates Q1, Q3, IQR, lower & upper bounds to filter out outliers
    Calculates the means and standard deviations of all metric columns within a specific Market Cap Group & Industry, excluding outliers and NA values
    Returns a pandas Series with indices showing types of statistical metric
    '''
    # Calculate Q1, Q3, IQR, lower & upper bounds
    q1 = group.quantile(0.25)
    q3 = group.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    filtered = group[(group >= lower) & (group <= upper)]   # Filter out outliers
    means = filtered.mean()   # Calculate the mean for each metric
    stds = filtered.std(ddof=0)   # Calculate the standard deviation for each metric
    result = pd.concat([means.add_suffix('_mean'), stds.add_suffix('_std')])
    return result

def get_grouped_stats(df, cols):
    '''
    Apply mean_std() function to each Market Cap Group and Industry
    Create new stats columns
    '''
    metrics_df = df.drop(columns=['Market Cap (M)', 'Current Price'])
    stats = metrics_df.groupby(['Market Cap Group', 'Industry'])[cols].apply(mean_std)

    df_with_stats = pd.merge(df, stats, on=['Market Cap Group', 'Industry'])
    return stats, df_with_stats

def scan(df):
    '''
    Apply preliminary conditions for scanning undervalued stocks
    Generate "EPSG" and "PEGY" columns
    '''
    # Apply the preliminary criteria
    conditions = [df['P/FCF'] > 0,
                  df['P/FCF'] < df['P/FCF_mean'],
                  df['P/B'] > 0,
                  df['P/B'] < df['P/B_mean'],
                  df['ROE'] > 10,
                  df['ROA'] > 5,
                  df['A/E'] > 1,
                  df['A/E'] < df['A/E_mean'],
                  df['P/E'] > 0]
    mask = np.logical_and.reduce(conditions)
    scanned_df = df[mask].copy()

    return scanned_df

def get_scores(df, cols):
    '''
    Calculate z-scores
    Calculate scores for additional criteria
    Return the scanned dataframe with scores
    '''
    for col in cols:
        df.loc[:, f'{col}_ZS'] = (df[col] - df[f'{col}_mean']) / df[f'{col}_std']

    df['Score'] = 0
    df.loc[df['P/B'] < 0.7 * df['P/B_mean'], 'Score'] += 1
    df.loc[df['ROE'] > df['ROE_mean'], 'Score'] += 1
    df.loc[df['ROA'] > df['ROA_mean'], 'Score'] += 1
    df.loc[df['P/E'] < df['P/E_mean'], 'Score'] += 1
    df.loc[df['P/E'].between(1, 25), 'Score'] += 1

    df.drop(columns=df.filter(like='_std').columns, axis=1, inplace=True)
    df.drop(columns=df.filter(like='_mean').columns, axis=1, inplace=True)
    return df

def main():
    '''
    The main pipeline incorporating other functions to process raw data
    '''
    all_files, num_files, project_root = get_files()
    print(f'{num_files} files found in "Downloaded CSV Files"')

    metric_cols = ['P/FCF', 'P/B', 'ROE', 'ROA', 'A/E', 'P/E']

    for i, file in enumerate(all_files):
        filename = os.path.splitext(os.path.basename(file))[0]
        df = data_cleaning(file)
        stats, df_with_stats = get_grouped_stats(df, metric_cols)
        scanned_df = scan(df_with_stats)
        scored_df = get_scores(scanned_df, metric_cols)
        stats.drop(columns=stats.filter(like='_std').columns, axis=1, inplace=True)

        result_path = os.path.join(project_root, 'Results', f'{filename}.xlsx')
        scored_df.to_excel(result_path, index=False)

        mean_path = os.path.join(project_root, 'Industry Means', f'{filename}.xlsx')
        stats.to_excel(mean_path, index=True)

        print(f'{filename} processed')


if __name__ == "__main__":
    main()