import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from nba_api.stats.endpoints import leaguedashplayerstats

st.set_page_config(page_title='NBA Heat Ratings 2025-26', layout='wide')

# Apply a global dark style for matplotlib to match Streamlit
plt.style.use('dark_background')

@st.cache_data(ttl=3600)
def fetch_nba_data():
    season_stats_all = leaguedashplayerstats.LeagueDashPlayerStats(season='2025-26', per_mode_detailed='PerGame').get_data_frames()[0]
    recent_stats_all = leaguedashplayerstats.LeagueDashPlayerStats(season='2025-26', per_mode_detailed='PerGame', last_n_games=5).get_data_frames()[0]
    return season_stats_all, recent_stats_all

def process_data(season_stats_all, recent_stats_all):
    season_subset = season_stats_all[['PLAYER_ID', 'PLAYER_NAME', 'PTS', 'REB', 'AST']].rename(columns={'PTS': 'SEASON_PTS', 'REB': 'SEASON_REB', 'AST': 'SEASON_AST'})
    recent_subset = recent_stats_all[['PLAYER_ID', 'PTS', 'REB', 'AST']].rename(columns={'PTS': 'RECENT_PTS', 'REB': 'RECENT_REB', 'AST': 'RECENT_AST'})
    combined_df = pd.merge(season_subset, recent_subset, on='PLAYER_ID')
    filtered_df = combined_df[(combined_df['RECENT_PTS'] > 0) & (combined_df['SEASON_PTS'] >= 10)].copy()
    for cat in ['PTS', 'REB', 'AST']:
        filtered_df[f'DIFF_{cat}'] = filtered_df[f'RECENT_{cat}'] - filtered_df[f'SEASON_{cat}']
        filtered_df[f'HEAT_RATING_{cat}'] = (filtered_df[f'RECENT_{cat}'] / filtered_df[f'SEASON_{cat}'] * 5).clip(0, 10)
    return filtered_df

st.title('🔥 NBA Player Heat Ratings (2025-26)')
st.sidebar.header('Dashboard Settings')
metric_display = st.sidebar.selectbox('Select Category', ['Points', 'Rebounds', 'Assists'])

mapping = {'Points': ('PTS', 'PPG'), 'Rebounds': ('REB', 'RPG'), 'Assists': ('AST', 'APG')}
key, unit = mapping[metric_display]

s_all, r_all = fetch_nba_data()
df = process_data(s_all, r_all)

col1, col2 = st.columns(2)

def create_styled_plot(data, title, y_label, metric_season, metric_recent):
    fig, ax = plt.subplots(figsize=(5, 4), facecolor='none')
    ax.set_facecolor('none')
    x = np.arange(len(data))
    width = 0.35
    
    # Use cleaner colors
    ax.bar(x - width/2, data[metric_season], width, label='Season', color='#4A90E2', alpha=0.8)
    ax.bar(x + width/2, data[metric_recent], width, label='Last 5', color='#FF4B4B', alpha=0.9)
    
    ax.set_xticks(x)
    ax.set_xticklabels(data['PLAYER_NAME'], rotation=45, ha='right', fontsize=9, color='white')
    ax.set_ylabel(y_label, color='white')
    ax.legend(fontsize=8, frameon=False)
    
    # Remove chart borders for a modern look
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    ax.spines['bottom'].set_color('#444444')
    ax.spines['left'].set_color('#444444')
    
    plt.tight_layout()
    return fig

with col1:
    st.subheader('📈 Top 10 Overperformers')
    hot = df.sort_values(by=f'DIFF_{key}', ascending=False).head(10)
    st.dataframe(hot[['PLAYER_NAME', f'SEASON_{key}', f'RECENT_{key}', f'DIFF_{key}', f'HEAT_RATING_{key}']], use_container_width=True)
    st.pyplot(create_styled_plot(hot, '', unit, f'SEASON_{key}', f'RECENT_{key}'), use_container_width=True)

with col2:
    st.subheader('❄️ Top 10 Underperformers')
    cold = df.sort_values(by=f'DIFF_{key}', ascending=True).head(10)
    st.dataframe(cold[['PLAYER_NAME', f'SEASON_{key}', f'RECENT_{key}', f'DIFF_{key}', f'HEAT_RATING_{key}']], use_container_width=True)
    st.pyplot(create_styled_plot(cold, '', unit, f'SEASON_{key}', f'RECENT_{key}'), use_container_width=True)
