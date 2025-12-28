import pandas as pd
import sqlite3
import streamlit as st
import plotly.graph_objects as go
import matplotlib.colors as mc


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


def plot_team_scores(team_number, show_table=False):
    team_data = pd.read_sql(
        f"SELECT * FROM Scouting_Data WHERE `Team Number` = {team_number} ORDER BY `Team Match Number` ASC",
        conn
    )

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
        st.dataframe(team_data)

dataType = st.sidebar.selectbox("View", ["Single Team", "Compare", "Averages", "Match Reference", "Bubble Chart"])
AutoCols = ['Auto Coral AVG', 'Auto Score AVG']

averageMatchScore = 0
averageScore = 0

if dataType.lower() == "single team":
    try:
        teamNumber = int(st.sidebar.text_input("Team Number", "1100"))
    except ValueError:
        st.error("Please enter a valid integer team number.")
        st.stop()

    df = pd.read_sql("SELECT * FROM 'Scouting_Data'", conn)
    team_data = df[df['Team Number'] == teamNumber]

    if not team_data.empty:
        plot_team_scores(teamNumber, True)
    else:
        st.warning(f"No Data for Team {teamNumber}")


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

    df = pd.read_sql("SELECT * FROM 'Scouting_Data'", conn)

    for i in range(0, len(teamNumbers), 3):
        columns = st.columns(3)
        for j, teamNumber in enumerate(teamNumbers[i:i + 3]):
            team_data = df[df['Team Number'] == teamNumber]
            if not team_data.empty:
                with columns[j]:
                    plot_team_scores(teamNumber)
            else:
                with columns[j]:
                    st.warning(f"No Data for Team {teamNumber}")

elif dataType.lower() == "averages":
    df = pd.read_sql("SELECT * FROM Calcs", conn)

    AutoColors = ["#010014", "#252525"]
    AutoCmap = mc.LinearSegmentedColormap.from_list("BlueGray", AutoColors)
    TeleopColors = ["#301500", "#252525"]
    TeleopCmap = mc.LinearSegmentedColormap.from_list("OrangeGray", TeleopColors)
    EndgameColors = ["#302d00", "#252525"]
    EndgameCmap = mc.LinearSegmentedColormap.from_list("YellowGray", EndgameColors)
    TotalColors = ["#003003", "#252525"]
    TotalCmap = mc.LinearSegmentedColormap.from_list("GreenGray", TotalColors)

    AutoCols = ['Auto Coral AVG', 'Auto Score AVG']
    TeleopCols = ['Teleop Net Algae AVG', 'Teleop Processor Algae AVG', 'Teleop Score AVG']
    EndgameCols = ['Climb Score AVG']
    TotalCols = ['Total Score AVG']
    ScoringCols = ['Auto Coral AVG', 'Auto Score AVG', 'Teleop Net Algae AVG', 'Teleop Processor Algae AVG' ,'Teleop Score AVG', 'Climb Score AVG', 'Total Score AVG']

    df = df.style.format("{:.2f}", subset=ScoringCols).background_gradient(cmap=AutoCmap, subset=AutoCols, axis=0).background_gradient(cmap=TeleopCmap, subset=TeleopCols, axis=0).background_gradient(cmap=EndgameCmap, subset=EndgameCols, axis=0).background_gradient(cmap=TotalCmap, subset=TotalCols, axis=0)
    st.dataframe(df)

elif dataType.lower() == "match reference":
    try:
        matchNumber = int(st.sidebar.text_input("Match Number", "1"))
    except ValueError:
        st.error("Please enter a valid integer team number.")
        st.stop()

    teams_df = pd.read_sql(
        'SELECT DISTINCT "Team Number" FROM "Scouting_Data" WHERE "Match Number" = ?',
        conn,
        params=(matchNumber,)
    )

    avg_scores_df = pd.read_sql(
        'SELECT "Team Number", "Auto Score AVG", "Teleop Score AVG", "Climb Score AVG", "Total Score AVG" FROM "Calcs"',
        conn
    )

    result_df = teams_df.merge(avg_scores_df, on="Team Number", how="left")

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


