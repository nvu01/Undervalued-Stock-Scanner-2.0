import pandas as pd
import os
from SCRIPTS.etl import get_files, data_cleaning, get_grouped_stats
from datetime import datetime

# Apply functions from etl.py to get all the stock data
metric_cols = ['P/FCF', 'P/B', 'ROE', 'ROA', 'A/E', 'P/E']
dfs = []

all_files, _, project_root = get_files()

for file in all_files:
    df = data_cleaning(file)
    _, df_with_stats = get_grouped_stats(df, metric_cols)
    dfs.append(df_with_stats)

full_df = pd.concat(dfs, ignore_index=True)

full_df.drop(columns=full_df.filter(like='_std').columns, axis=1, inplace=True)  # Remove _std columns

# Get a list of selected stocks from user input
print("Paste stock symbols below and press Enter.")
print("When done, press Enter again.")

symbol = []
while True:
    line = input()
    if not line:
        break
    symbol.append(line)

# Filter stock data for just selected stocks
df = full_df.loc[full_df['Symbol'].isin(symbol),:]

# Save files
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

file_path = os.path.join(project_root, 'Selected Stock Snapshots', f'{timestamp}_snapshot.xlsx')

df.to_excel(file_path, index=False)

print('Snapshot created')





