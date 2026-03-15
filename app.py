import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from nba_api.stats.endpoints import leaguedashplayerstats

st.set_page_config(page_title='NBA Heat Ratings 2025-26', layout='wide')

@st.cache_data
def fetch_nba_data():
    # Fetch live 2025-26 season averages and last 5 games
    season_stats_all = leaguedashplayerstats.LeagueDashPlayerStats(season='2025-26', per_mode_detailed='PerGame').get_data_frames()[0]
    recent_stats_all = leaguedashplayerstats.LeagueDashPlayerStats(season='2025-26', per_mode_detailed='PerGame', last_n_games=5).get_data_frames()[0]
    return season_stats_all, recent_stats_all

def process_data(season_stats_all, recent_stats_all):
    # Process and Merge
    season_subset = season_stats_all[['PLAYER_ID', 'PLAYER_NAME', 'PTS', 'REB', 'AST']].rename(columns={'PTS': 'SEASON_PTS', 'REB': 'SEASON_REB', 'AST': 'SEASON_AST'})
    recent_subset = recent_stats_all[['PLAYER_ID', 'PTS', 'REB', 'AST']].rename(columns={'PTS': 'RECENT_PTS', 'REB': 'RECENT_REB', 'AST': 'RECENT_AST'})
    combined_df = pd.merge(season_subset, recent_subset, on='PLAYER_ID')

    # Filter: Recent PPG > 0 and Season PPG >= 10
    filtered_df = combined_df[(combined_df['RECENT_PTS'] > 0) & (combined_df['SEASON_PTS'] >= 10)].copy()

    # Calculate Heat Ratings
    for cat in ['PTS', 'REB', 'AST']:
        filtered_df[f'DIFF_{cat}'] = filtered_df[f'RECENT_{cat}'] - filtered_df[f'SEASON_{cat}']
        filtered_df[f'HEAT_RATING_{cat}'] = (filtered_df[f'RECENT_{cat}'] / filtered_df[f'SEASON_{cat}'] * 5).clip(0, 10)
    return filtered_df

# Sidebar and Layout
st.title('🔥 NBA Player Heat Ratings')
st.sidebar.header('Settings')
metric_choice = st.sidebar.selectbox('Select Metric', ['Points', 'Rebounds', 'Assists'])

# Data flow
s_data, r_data = fetch_nba_data()
df = process_data(s_data, r_data)

mapping = {
    'Points': ('PTS', 'PPG'),
    'Rebounds': ('REB', 'RPG'),
    'Assists': ('AST', 'APG')
}

key, unit = mapping[metric_choice]

col1, col2 = st.columns(2)

with col1:
    st.subheader(f'Top 10 {metric_choice} Overperformers')
    hot = df.sort_values(by=f'DIFF_{key}', ascending=False).head(10)
    st.dataframe(hot[['PLAYER_NAME', f'SEASON_{key}', f'RECENT_{key}', f'DIFF_{key}', f'HEAT_RATING_{key}']])
    
    fig, ax = plt.subplots()
    x = np.arange(len(hot))
    width = 0.35
    ax.bar(x - width/2, hot[f'SEASON_{key}'], width, label='Season', color='#1f77b4')
    ax.bar(x + width/2, hot[f'RECENT_{key}'], width, label='Last 5', color='#ff7f0e')
    ax.set_xticks(x)
    ax.set_xticklabels(hot['PLAYER_NAME'], rotation=45, ha='right')
    ax.legend()
    st.pyplot(fig)

with col2:
    st.subheader(f'Top 10 {metric_choice} Underperformers')
    cold = df.sort_values(by=f'DIFF_{key}', ascending=True).head(10)
    st.dataframe(cold[['PLAYER_NAME', f'SEASON_{key}', f'RECENT_{key}', f'DIFF_{key}', f'HEAT_RATING_{key}']])
    
    fig2, ax2 = plt.subplots()
    x2 = np.arange(len(cold))
    ax2.bar(x2 - width/2, cold[f'SEASON_{key}'], width, label='Season', color='#1f77b4')
    ax2.bar(x2 + width/2, cold[f'RECENT_{key}'], width, label='Last 5', color='#ff7f0e')
    ax2.set_xticks(x2)
    ax2.set_xticklabels(cold['PLAYER_NAME'], rotation=45, ha='right')
    ax2.legend()
    st.pyplot(fig2)
