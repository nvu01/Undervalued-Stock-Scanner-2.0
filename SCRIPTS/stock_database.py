import glob
import os
from io import StringIO
import pandas as pd
from datetime import date
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from SCRIPTS.etl import get_files
from SCRIPTS.exit_signals import get_all_stock_data

# Create a SQLite database named "my_database" and set up a session using sessionmaker to allow interacting with the database.
engine = create_engine('sqlite+pysqlite:///../my_database.db', echo=True) # Replace ../my_database.db with the actual path to the database
Session = sessionmaker(engine)
class Base (DeclarativeBase):
    pass

# Create a class that represents a table named "Weather_Data"
class StockData(Base):
    __tablename__ = 'stock_data'
    date = Column(DateTime, primary_key=True, nullable=False)
    symbol = Column(String(10), primary_key=True, nullable=False)
    market_cap_group = Column(String(10))
    industry = Column(String(10))
    company_name = Column(String(100))
    market_cap = Column(Integer)
    current_price = Column(Float)
    PFCF = Column(Float)
    PB = Column(Float)
    ROE = Column(Float)
    ROA = Column(Float)
    AE = Column(Float)
    PE = Column(Float)
    PFCF_mean = Column(Float)
    PB_mean = Column(Float)
    ROE_mean = Column(Float)
    ROA_mean = Column(Float)
    AE_mean = Column(Float)
    PE_mean = Column(Float)

Base.metadata.create_all(engine)

def get_pos_stmt(year, month):
    '''
    Retrieve position statement file based on the year and month of download timestamp in the file's name.
    Return a dataframe containing a list of undervalued stocks in the portfolio within the input month-year.
    '''

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    folder_path = os.path.join(project_root, 'Position Statement')
    matches = glob.glob(os.path.join(folder_path, f'{year}-{month:02d}*'))

    if not matches:
        raise FileNotFoundError(f'No file found for {year}-{month:02d}. No data to add.')
    else:
        filepath = matches[0]
        filename = os.path.splitext(os.path.basename(filepath))[0]
        print(f'Found {filename} in "Position Statement" folder')

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

def add_pos_stmt_stocks(df, full_df, month_year, col_names):
    '''
    Add new stock data for each holding ticker within the selected month-year.
    '''

    pos_data = pd.merge(df, full_df, how='left', on='Symbol')     # Get data for stocks in the position statement

    pos_data['date'] = month_year

    pos_data = pos_data.rename(columns=col_names)

    # Delete duplicate records that have the same stock symbols and the same month as the new records
    with Session() as session:
        session.query(StockData).filter(StockData.date == month_year, StockData.symbol.in_(pos_data['symbol'].tolist())).delete()
        session.commit()

    pos_data.to_sql('stock_data', con=engine, if_exists='append', index=False)

    print(f'\nNew data for positions in {month_year.strftime("%m/%Y")} has been added to the database.')

def add_new_selected_stocks(full_df, month_year, col_names):
    '''
    Add stock data for selected stocks that are not yet in the position statement.
    '''

    # Get a list of selected stocks from user input
    print("\nTo add any stock that is not in the current position list, enter the stock symbol(s) below.")
    print("When done, press Enter again.")

    symbol = []
    while True:
        line = input()
        if not line:
            break
        symbol.append(line)

    # Filter stock data for just selected stocks
    new_df = full_df.loc[full_df['Symbol'].isin(symbol), :]

    new_df['date'] = month_year

    new_df = new_df.rename(columns=col_names)

    if new_df.empty:
        print('No data to add.')
        return

    with Session() as session:
        # Delete and replace records in the same month as the new records
        session.query(StockData).filter(StockData.date == month_year, StockData.symbol.in_(new_df['symbol'].tolist())).delete()
        session.commit()

    new_df.to_sql('stock_data', con=engine, if_exists='append', index=False)

    print('\nNew selected stocks have been added to the database.')

def delete_data():
    '''
    For developer only: Delete specific records based on input month-year and symbols
    '''
    year = int(input('Enter year: '))
    month = int(input('Enter month: '))
    month_year = date(year, month, 1)

    print('Enter the stock symbol(s) to delete: ')
    print('When done, press Enter again.')
    symbol = []
    while True:
        line = input()
        if not line:
            break
        symbol.append(line)

    with Session() as session:
        session.query(StockData).filter(StockData.date == month_year, StockData.symbol.in_(symbol)).delete()
        session.commit()

def update_symbols():
    '''
    For developer only: Update stock symbols
    '''
    old_symbol = input('Enter stock symbol to replace: ')
    new_symbol = input('Enter new stock symbol: ')

    with Session() as session:
        session.query(StockData).filter(StockData.symbol == old_symbol).update({'symbol': new_symbol})
        session.commit()

def main():
    '''
    Create a pipeline to process and store data in my_database.db
    '''
    year = int(input('Enter year: '))
    month = int(input('Enter month (1-12): '))
    month_year = date(year, month, 1)

    col_names = {'Market Cap Group': 'market_cap_group',
                 'Industry': 'industry',
                 'Symbol': 'symbol',
                 'Company Name': 'company_name',
                 'Market Cap (M)': 'market_cap',
                 'Current Price': 'current_price',
                 'P/FCF': 'PFCF',
                 'P/B': 'PB',
                 'A/E': 'AE',
                 'P/E': 'PE',
                 'P/FCF_mean': 'PFCF_mean',
                 'P/B_mean': 'PB_mean',
                 'ROE_mean': 'ROE_mean',
                 'ROA_mean': 'ROA_mean',
                 'A/E_mean': 'AE_mean',
                 'P/E_mean': 'PE_mean'}

    all_files, _, project_root = get_files()
    full_df = get_all_stock_data(all_files)

    try:
        pos_stmt = get_pos_stmt(year, month)
        add_pos_stmt_stocks(pos_stmt, full_df, month_year, col_names)
    except FileNotFoundError as e:
        print(e)

    add_new_selected_stocks(full_df, month_year, col_names)

    # Query data
    df = pd.read_sql('SELECT * FROM stock_data', con=engine)
    df.to_csv("../stock_data.csv", index=False)  # Replace ../stock_data.csv with the actual filepath
    print('\nstock_data.csv in the project folder has been updated.')


if __name__ == '__main__':
    main()
    print('\nTo see the database, go to sqliteviewer.app and upload my_database.db from the project folder')

    # The following functions are for developer only:
    #delete_data()
    #update_symbols()