import gspread
import pandas as pd
import sqlite3
import plotly.graph_objects as go
from google.oauth2.service_account import Credentials

endgame_scores = {
    "Deep Climb": 12,
    "Shallow Climb": 6,
    "Parked": 2,
    "Nothing": 0
}

leave_scores = {
    "TRUE": 3,
    "FALSE": 0
}

auto_scores = {
    "Auto L4": 7,
    "Auto L3": 6,
    "Auto L2": 4,
    "Auto L1": 3,
    "Auto NET": 4,
}

teleop_scores = {
    "L4": 5,
    "L3": 4,
    "L2": 3,
    "L1": 2,
    "NET": 4,
    "PROCESSOR": 2,
}

def write_to_db(dataframe, table_name):
    conn = sqlite3.connect("Scouting_Data.db")
    cursor = conn.cursor()
    dataframe.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()

def perform_calculations():
    apis = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(
        "data_reader_account.json",
        scopes=apis
    )

    gc = gspread.authorize(creds)
    spreadsheet = gc.open("Copy of NEW AMAZONG 2025 SCOUTING DASHBOARD!!!! (dcmp data)")
    worksheet = spreadsheet.worksheet("Data Entry")
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)

    df['Auto Score'] = pd.DataFrame(
        {col: df[col].fillna(0) * weight for col, weight in auto_scores.items()}
    ).sum(axis=1)
    df['Auto Score'] += df['Leave (Did the robot move)?'].map(leave_scores).fillna(0)

    df['Teleop Score'] = pd.DataFrame(
        {col: df[col].fillna(0) * weight for col, weight in teleop_scores.items()}
    ).sum(axis=1)

    df['Endgame Score'] = df['Endgame'].map(endgame_scores).fillna(0)
    df['Total Score'] = df['Auto Score'] + df['Teleop Score'] + df['Endgame Score']

    df = df.sort_values(['Team Number', 'Match Number'])

    df['Team Match Number'] = df.groupby('Team Number').cumcount() + 1

    calc_df = pd.DataFrame()
    calc_df['Team Number'] = df['Team Number'].unique()

    team_counts = (
        df.groupby('Team Number')
        .size()
        .reset_index(name='Matches Played')
    )


    auto_cols = ['Auto L1', 'Auto L2', 'Auto L3', 'Auto L4']
    auto_avg = (
        df.groupby('Team Number')[auto_cols]
        .mean()
        .sum(axis=1)
        .reset_index(name='Auto Coral AVG')
    )

    teleop_cols = ['L1', 'L2', 'L3', 'L4']
    teleop_avg = (
        df.groupby('Team Number')[teleop_cols]
        .mean()
        .sum(axis=1)
        .reset_index(name='Teleop Coral AVG')
    )



    calc_df = df.groupby('Team Number', as_index=False).agg(
        **{
            'Auto Score AVG': ('Auto Score', 'mean'),
            'Teleop Net Algae AVG': ('NET', 'mean'),
            'Teleop Processor Algae AVG': ('PROCESSOR', 'mean'),
            'Teleop Score AVG': ('Teleop Score', 'mean'),
            'Climb Score AVG': ('Endgame Score', 'mean'),
            'Total Score AVG': ('Total Score', 'mean')
        }
    )

    calc_df = (
        calc_df
        .merge(auto_avg, on='Team Number')
        .merge(team_counts, on='Team Number')
        .merge(teleop_avg, on='Team Number')
    )


    calc_df = calc_df[
        ['Team Number', 'Auto Coral AVG', 'Auto Score AVG', 'Teleop Net Algae AVG', 'Teleop Processor Algae AVG', 'Teleop Coral AVG', 'Teleop Score AVG', 'Climb Score AVG', 'Total Score AVG']
    ]

    calc_df = calc_df.round(2)


    write_to_db(calc_df, "Calcs")

    write_to_db(df, "Scouting_Data")

perform_calculations()