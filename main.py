import pandas as pd
import sqlite3
import streamlit as st
import plotly.graph_objects as go
import matplotlib.colors as mc
import db_calc as db


conn = sqlite3.connect("Scouting_Data.db")
cursor = conn.cursor()

st.set_page_config(layout="wide")

def retrieve_data(data_type, team_number, match_number=None):
    if match_number is None:
        query = f'SELECT "{data_type}" FROM Scouting_Data WHERE "Team Number" = ?'
        params = (team_number,)
    else:
        query = f'SELECT "{data_type}" FROM Scouting_Data WHERE "Team Number" = ? AND "Match Number" = ?'
        params = (team_number, match_number)
    cursor.execute(query, params)
    return cursor.fetchall()

def color_alliance(row):
    if row["Position"].startswith("RED"):
        return ["background-color: rgba(255, 0, 0, 0.15)"] * len(row)
    elif row["Position"].startswith("BLUE"):
        return ["background-color: rgba(0, 100, 255, 0.15)"] * len(row)
    return [""] * len(row)


def plot_team_scores(team_number, show_table=False):
    team_data = pd.read_sql(
        f"SELECT * FROM Scouting_Data WHERE `Team Number` = {team_number} ORDER BY `Team Match Number` ASC",
        conn
    )
    if team_data.empty:
        st.error("Please enter a valid team number.")
        st.stop()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=team_data['Team Match Number'], y=team_data['Total Score'], mode='lines+markers', name='Total Score'))
    fig.add_trace(
        go.Scatter(x=team_data['Team Match Number'], y=team_data['Auto Score'], mode='lines+markers', name='Auto Score'))
    fig.add_trace(
        go.Scatter(x=team_data['Team Match Number'], y=team_data['Teleop Score'], mode='lines+markers', name='Teleop Score'))
    fig.add_trace(
        go.Scatter(x=team_data['Team Match Number'], y=team_data['Endgame Score'], mode='lines+markers', name='Endgame Score'))

    fig.update_layout(
        title=f"Team {team_number} Score Trend",
        xaxis_title="Match Number",
        yaxis_title="Score",
        yaxis=dict(range=[0, 125]),
    )

    st.plotly_chart(fig, width="stretch")


    if show_table:
        pit_data = pd.read_sql(
            f'SELECT * FROM "Pit Scouting" WHERE "Team #" = {team_number}',
            conn
        )

        ucolumns = ['Timestamp', 'Name(s)', 'Team #', 'Climb', 'Processor Auto', 'Barge Auto', 'Center auto',
                    'Auto Leave', 'Pictures']
        pit_data.drop(columns=ucolumns, inplace=True)
        team_data.drop(columns='Scouter Initials', inplace=True)
        team_data.drop(columns='Team Number', inplace=True)

        pit_data = pit_data.transpose()

        auto = ['Auto PROCESSOR', 'Auto NET', 'Auto L1', 'Auto L2', 'Auto L3', 'Auto L4', 'Auto Score',
                'Team Match Number']
        teleop = ['PROCESSOR', 'NET', 'L1', 'L2', 'L3', 'L4', 'Teleop Score', 'Team Match Number']
        endgame = ['Endgame Score', 'Team Match Number']

        auto_data = team_data[auto]
        auto_data.set_index("Team Match Number", inplace=True)
        auto_data = auto_data.transpose()
        auto_data['Averages'] = auto_data.mean(axis=1, numeric_only=True)

        teleop_data = team_data[teleop]
        teleop_data.set_index("Team Match Number", inplace=True)
        teleop_data = teleop_data.transpose()
        teleop_data['Averages'] = teleop_data.mean(axis=1, numeric_only=True)

        endgame_data = team_data[endgame]
        endgame_data.set_index("Team Match Number", inplace=True)
        endgame_data = endgame_data.transpose()
        endgame_data['Averages'] = endgame_data.mean(axis=1, numeric_only=True)

        st.markdown("**Auto**")
        st.dataframe(auto_data)
        st.markdown("**Teleop**")
        st.dataframe(teleop_data)
        st.markdown("**Endgame**")
        st.dataframe(endgame_data)
        st.markdown("**Pit Data**")
        st.dataframe(pit_data)



if st.sidebar.button("Refresh Values"):
    db.perform_calculations()

dataType = st.sidebar.selectbox("View", ["Single Team", "Compare", "Averages", "Match Reference", "Bubble Chart", "Radar Chart"])


if dataType.lower() == "single team":
    try:
        teamNumber = int(st.sidebar.text_input("Team Number", "1100"))
    except ValueError:
        st.error("Please enter a valid integer team number.")
        st.stop()

    df = pd.read_sql(f'SELECT * FROM Calcs WHERE "Team Number" = {teamNumber}', conn)

    fig = go.Figure(data=go.Scatterpolar(
        r=[df['Total Score AVG'].loc[0], df['Teleop Score AVG'].loc[0], df['Auto Score AVG'].loc[0], df['Climb Score AVG'].loc[0]],
        theta=['Total Score', 'Auto Score', 'Teleop Score', 'Climb Score'],
        fill='toself'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True
            ),
        ),
        showlegend=True
    )

    st.plotly_chart(fig)

    plot_team_scores(teamNumber, True)


elif dataType.lower() == "compare":
    teamNumbers = []
    for i in range(1, 7):
        input_value = st.sidebar.text_input(f"Team {i}", "")
        if input_value.strip():
            try:
                teamNumber = int(input_value)
                teamNumbers.append(teamNumber)
            except ValueError:
                st.error(f"Please enter a valid number for Team {i}.")
                st.stop()

    for i in range(0, len(teamNumbers), 3):
        columns = st.columns(3)
        for j, teamNumber in enumerate(teamNumbers[i:i + 3]):
            with columns[j]:
                plot_team_scores(teamNumber)

elif dataType.lower() == "averages":
    df = pd.read_sql("SELECT * FROM Calcs", conn)

    AutoColors = ["#252525", "#010014"]
    AutoCmap = mc.LinearSegmentedColormap.from_list("BlueGray", AutoColors)
    TeleopColors = ["#252525", "#301500"]
    TeleopCmap = mc.LinearSegmentedColormap.from_list("OrangeGray", TeleopColors)
    EndgameColors = ["#252525", "#302d00"]
    EndgameCmap = mc.LinearSegmentedColormap.from_list("YellowGray", EndgameColors)
    TotalColors = ["#252525", "#003003"]
    TotalCmap = mc.LinearSegmentedColormap.from_list("GreenGray", TotalColors)

    AutoCols = ['Auto Net Algae AVG', 'Auto Processor Algae AVG', 'Auto Coral AVG', 'Auto Score AVG']
    TeleopCols = ['Teleop Net Algae AVG', 'Teleop Processor Algae AVG', 'Teleop Score AVG', 'Teleop Coral AVG']
    EndgameCols = ['Climb Score AVG']
    TotalCols = ['Total Score AVG']
    ScoringCols = ['Auto Coral AVG', 'Auto Score AVG', 'Teleop Net Algae AVG', 'Teleop Processor Algae AVG' ,'Teleop Score AVG', 'Climb Score AVG', 'Total Score AVG']

    df = df.style.format("{:.2f}", subset=ScoringCols).background_gradient(cmap=AutoCmap, subset=AutoCols, axis=0).background_gradient(cmap=TeleopCmap, subset=TeleopCols, axis=0).background_gradient(cmap=EndgameCmap, subset=EndgameCols, axis=0).background_gradient(cmap=TotalCmap, subset=TotalCols, axis=0)
    st.dataframe(df)

elif dataType.lower() == "match reference":
    try:
        matchNumber = int(st.sidebar.text_input("Match Number", "1"))
    except ValueError:
        st.error("Please enter a valid integer match number.")
        st.stop()

    test_df = pd.read_sql(
        'SELECT "red1", "blue1", "red2", "blue2", "red3", "blue3" FROM "TBA Data" WHERE "match_number" = ? AND "comp_level" = "qm"',
        conn,
        params=(matchNumber,)
    )

    try:
        row = test_df.iloc[0]
    except IndexError:
        st.error(f"Please enter a valid match number.")
        st.stop()

    position_map = {
        row["red1"]: "RED 1",
        row["red2"]: "RED 2",
        row["red3"]: "RED 3",
        row["blue1"]: "BLUE 1",
        row["blue2"]: "BLUE 2",
        row["blue3"]: "BLUE 3",
    }

    positions_df = (
        test_df
        .iloc[0]
        .reset_index()
    )

    positions_df.columns = ["Position", "Team Number"]

    teams_df = (
        test_df
        .melt(value_name="Team Number")["Team Number"]
        .dropna()
        .to_frame()
    )

    teams_df["Position"] = teams_df["Team Number"].map(position_map)

    avg_scores_df = pd.read_sql(
        'SELECT "Team Number", "Auto Score AVG", "Teleop Score AVG", "Climb Score AVG", "Total Score AVG" FROM "Calcs"',
        conn
    )

    result_df = (
        teams_df
        .merge(avg_scores_df, on="Team Number", how="left")
    )


    result_df['Team Number'].astype(str)
    result_df["Position"] = result_df["Position"].str.upper()
    result_df["Alliance"] = result_df["Position"].str[:4]
    result_df["Slot"] = result_df["Position"].str[-1]
    result_df.sort_values(by=["Alliance"], inplace=True)

    numeric_columns = ["Auto Score AVG", "Teleop Score AVG", "Climb Score AVG", "Total Score AVG"]

    result_df = result_df.style.apply(color_alliance, axis=1).format("{:.2f}", subset=numeric_columns)

    header = f"Match {matchNumber}"

    st.header(header)
    st.dataframe(result_df)

elif dataType.lower() == "bubble chart":
    df = pd.read_sql('SELECT * FROM "Calcs"', conn)

    xAxis = st.sidebar.selectbox("X-Axis", ['Select X-Axis'] + df.columns.tolist())
    yAxis = st.sidebar.selectbox("Y-Axis", ['Select Y-Axis'] + df.columns.tolist())

    fig = go.Figure()

    if xAxis == 'Select X-Axis' or yAxis == 'Select Y-Axis':
        st.info("Select Axes to Continue")

    else:
        fig.add_trace(
            go.Scatter(
                x=df[xAxis],
                y=df[yAxis],
                mode='markers+text',
                marker=dict(
                    size=12,
                ),
                text=df['Team Number'],
                textposition='bottom center',
                textfont=dict(
                    size=14,
                    color='white'
                ),
                hovertemplate=(
                        "Team: %{text}<br>"
                        f"{xAxis}: " + "%{x}<br>"
                                       f"{yAxis}: " + "%{y}<br>"
                )
            )
        )

        fig.update_layout(
            title=f"{yAxis} vs {xAxis} Scatter Plot",
            xaxis_title=xAxis,
            yaxis_title=yAxis,
        )

        st.plotly_chart(fig)