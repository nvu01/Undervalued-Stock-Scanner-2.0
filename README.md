# Undervalued Stock Scanner

### Disclaimer: This project is intended for educational and informational purposes only. The analysis, models, and methodologies used in this project are not intended to serve as financial or investment advice.The information presented should not be construed as a recommendation to buy, sell, or hold any securities or assets. Investing in the stock market carries inherent risks, and any decisions based on the content of this project are solely the responsibility of the individual. Always consult with a qualified financial advisor before making any investment decisions. 

## Project Overview
The Undervalued Stock Scanner identifies potentially undervalued stocks by analyzing key financial metrics across multiple sectors and market capitalization categories (Large Cap, Mid Cap, Small Cap).

The project applies structured financial screening rules combined with statistical methods (mean, standard deviation, quartiles, and z-scores) to evaluate company fundamentals relative to industry peers.

In addition to valuation screening, the project also identifies exit signals for currently held positions to help monitor potential overvaluation or quality deterioration.

Users can also generate Excel snapshots of the selected stocks and their metrics.

## Prerequisites

- Python libraries in `requirements.txt`
- Microsoft Excel
- Microsoft Power BI Desktop
- Optional: Thinkorswim app with active Charles Schwab account for data update/refresh.

## Framework Summary

For detailed methodology, refer to:
- `Conceptual Framework.pdf`
- `Exit Signals.pdf`

### Stock Fundamentals Screening

The evaluation is based on a series of criteria and statistical methods outlined in the `Conceptual Framework` document.

- Preliminary criteria:
To be considered “undervalued,” a stock must meet all of these:

   - P/FCF > 0 and < industry average 
   - P/B > 0 and < industry average 
   - A/E > 1 and < industry average
   - ROE > 10%
   - ROA > 5%
   - P/E > 0

- Additional criteria (bonus signals): 
Stocks that meet the preliminary criteria are then ranked based on these bonus signals. For each criterion met, a stock gets 1 point. The highest score a stock can get is 5 points.

   - P/B < 70% of industry average 
   - ROE > industry average 
   - ROA > industry average 
   - P/E < industry average 
   - P/E between 1 and 25

### Statistical Methods

- Quartile Calculations: Quartiles (Q1, Q3) are calculated for each fundamental indicator, and outliers are identified based on the upper and lower bounds.
- Mean Calculations: The mean of each fundamental metric is calculated for stocks within each industry and market cap category (Large Cap, Mid Cap, Small Cap). The means are calculated without outliers to ensure that the results reflect the central tendency of the data.  
- Standard Deviation and Z-score Calculations: Z-scores for individual fundamentals are used to compare a stock’s performance against the industry average or specific peers.
  - P/FCF, P/B, A/E, P/E → negative z-score that is further from 0 is preferred
  - ROE, ROA → positive z-score that is further from 0 is preferred

### Exit Signals Framework

Exit signals are review triggers, not automatic sell signals.
Refer to `Exit Signals.pdf` for detailed explanation and instructions.

- Overvaluation Signals
  - P/FCF > Industry average 
  - P/B > Industry average 
  - P/E > Industry average
- Quality Deterioration Signals
  - ROE < 10% or < Industry average 
  - ROA < 5% or < Industry average
- Severe Deterioration
  - P/FCF ≤ 0
  - P/E ≤ 0 
  - ROE < 0
  - ROA < 0

## Summary of Data Pipelines

### Pipeline for Undervalued Stock Scanning
1. Raw stock data is downloaded from the Thinkorswim scanner.
11 CSV files (one per sector) are saved in `\Downloaded CSV Files`.
2. `etl.py` processes the raw CSV files. Outputs:
   - 11 filtered Excel workbooks in `\Results`. Each of these workbooks contains data of stocks that passed the preliminary conditions. 
   - 11 industry mean workbooks in `\Industry Means`
3. Interactive Power BI dashboard presents data from the Excel workbooks in `\Results` and in `\Industry Means`.

### Pipeline for Exit Signals
1. The position statement is downloaded from Thinkorswim and saved in `\Position Statement`.
2. `exit_signals.py` processes the position statement and raw data from `\Downloaded CSV Files`, then applies exit signal logic and filters for stocks with at least 1 exit signal.
The final output is a formatted Excel file saved in `\Exit Signals\Scannable`.
3. Exit Signals.pbix presents categorized red flags.

### Pipeline for Stock Snapshot
1. stock_snapshot.py retrieves fundamental metrics across sectors and market caps.
2. User inputs a list of selected stocks.
3. Filtered Excel output is saved in `\Selected Stock Snapshots`

## Project Folders and Files

``Undervalued Stock Scanner`` contains the following folders and files:

```bash
Undervalued Stock Scanner\
│              
├── Downloaded CSV Files\              # Folder containing 11 raw CSV files downloaded from Thinkorswim
├── Results\                           # Folder containing all result workbooks (.xlsx files) exported from etl.py
├── Industry Means\                    # Folder containing all industry mean calculation outputs (.xlsx files) from etl.py
├── Position Statement\                # Folder containing the current position statement (.csv file) downloaded from Thinkorswim
├── Exit Signals\                      # Folder containing exit signal output files exported from exit_signals.py
├── Selected Stock Snapshot\           # Folder containing a sample snapshot of selected stocks and their metrics
├── SCRIPTS\                           # Package folder containing all Python scripts
│   ├── etl.py                              # Python script for scanning undervalued stocks
│   ├── exit_signals.py                     # Python script for exit signals detection
│   └── stock_snapshot.py                   # Python script that take snapshots of selected stocks and their metrics
├── POWER BI\                          # Folder containing dashboards
│   ├── Undervalued Stocks Scanner.pbix     # Undervalued stock valuation dashboard
│   └── Exit Signals.pbix                   # Exit monitoring dashboard
├── Instructions.pdf                             # User instructions
├── Conceptual Framework.pdf                     # Detailed explanation of the project's logic and methodology
├── Exit Signal Framework.pdf                    # Exit logic documentation
├── Draft_Undervalued Stock Scanner ETL.html     # HTML export of the Jupyter Notebook used to develop etl.py
├── Draft_Exit Signals.html                      # HTML export of the Jupyter Notebook used to develop exit_signals.py
├── Table Schema.xlsx                            # An outline of the structure of tables
└── requirements.txt                             # Required Python libraries
```
Note: To ensure personal and financial information security, folder Position Statement\ is not uploaded in this repo. This means the exit_signals.py script can't be run.

## Usage

1. Download the repository
   - Fork the repository or download as ZIP. 
   - Extract locally to create the Undervalued Stock Scanner folder.
2. Update raw data
   - Download fresh CSV files from Thinkorswim. 
   - Replace files inside \Downloaded CSV Files.
3. Run processing scripts in `SCRIPTS\`
    From project terminal:
    ```
    py -m SCRIPTS.etl
    py -m SCRIPTS.exit_signal
    py -m SCRIPTS.stock_snapshot
    ```
4. Open Power BI dashboard 
   - Open `Undervalued Stock Scanner.pbix` or `Exit Signals.pbix`
   - Update folder path parameter if needed.  
   - Click **Refresh** in the **Home** tab 

**For detailed operational instructions, refer to `Instructions.pdf`.**