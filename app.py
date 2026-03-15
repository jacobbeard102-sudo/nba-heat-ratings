import streamlit as st
import pandas as pd
import plotly.express as px
from nba_api.stats.endpoints import leaguedashplayerstats

st.set_page_config(page_title='NBA Heat Ratings 2025-26', layout='wide')

@st.cache_data(ttl=3600)
def fetch_nba_data():
    season_stats_all = leaguedashplayerstats.LeagueDashPlayerStats(season='2025-26', per_mode_detailed='PerGame').get_data_frames()[0]
    recent_stats_all = leaguedashplayerstats.LeagueDashPlayerStats(season='2025-26', per_mode_detailed='PerGame', last_n_games=5).get_data_frames()[0]
    return season_stats_all, recent_stats_all

def process_data(season_stats_all, recent_stats_all):
    season_subset = season_stats_all[['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'PTS', 'REB', 'AST']].rename(columns={'PTS': 'SEASON_PTS', 'REB': 'SEASON_REB', 'AST': 'SEASON_AST'})
    recent_subset = recent_stats_all[['PLAYER_ID', 'PTS', 'REB', 'AST']].rename(columns={'PTS': 'RECENT_PTS', 'REB': 'RECENT_REB', 'AST': 'RECENT_AST'})
    combined_df = pd.merge(season_subset, recent_subset, on='PLAYER_ID')
    filtered_df = combined_df[(combined_df['RECENT_PTS'] > 0) & (combined_df['SEASON_PTS'] >= 10)].copy()
    for cat in ['PTS', 'REB', 'AST']:
        filtered_df[f'DIFF_{cat}'] = (filtered_df[f'RECENT_{cat}'] - filtered_df[f'SEASON_{cat}']).round(2)
        filtered_df[f'HEAT_RATING_{cat}'] = (filtered_df[f'RECENT_{cat}'] / filtered_df[f'SEASON_{cat}'] * 5).clip(0, 10).round(2)
    return filtered_df

def create_plotly_chart(data, key, unit):
    # Melt the dataframe for grouped bar chart
    plot_df = data.melt(id_vars=['PLAYER_NAME', f'DIFF_{key}', f'HEAT_RATING_{key}'], 
                        value_vars=[f'SEASON_{key}', f'RECENT_{key}'],
                        var_name='Stat Type', value_name='Value')
    
    fig = px.bar(
        plot_df, x='PLAYER_NAME', y='Value', color='Stat Type',
        barmode='group',
        template='plotly_dark',
        color_discrete_map={f'SEASON_{key}': '#4A90E2', f'RECENT_{key}': '#FF4B4B'},
        hover_data={'PLAYER_NAME': True, 'Value': ':.1f', f'DIFF_{key}': True, f'HEAT_RATING_{key}': True}
    )
    fig.update_layout(xaxis_title=None, yaxis_title=unit, legend_title=None, margin=dict(l=20, r=20, t=20, b=20))
    return fig

st.title('🔥 NBA Player Heat Ratings (2025-26)')
st.sidebar.header('Dashboard Filters')

s_all, r_all = fetch_nba_data()
df = process_data(s_all, r_all)

teams = ['All Teams'] + sorted(df['TEAM_ABBREVIATION'].unique().tolist())
selected_team = st.sidebar.selectbox('Filter by Team', teams)
player_search = st.sidebar.text_input('Search Player Name', '')
metric_display = st.sidebar.selectbox('Select Category', ['Points', 'Rebounds', 'Assists'])

if selected_team != 'All Teams':
    df = df[df['TEAM_ABBREVIATION'] == selected_team]
if player_search:
    df = df[df['PLAYER_NAME'].str.contains(player_search, case=False)]

mapping = {'Points': ('PTS', 'PPG'), 'Rebounds': ('REB', 'RPG'), 'Assists': ('AST', 'APG')}
key, unit = mapping[metric_display]

col1, col2 = st.columns(2)

with col1:
    st.subheader('📈 Top Overperformers')
    hot = df.sort_values(by=f'DIFF_{key}', ascending=False).head(10)
    if not hot.empty:
        st.plotly_chart(create_plotly_chart(hot, key, unit), use_container_width=True)
        st.dataframe(hot[['PLAYER_NAME', 'TEAM_ABBREVIATION', f'SEASON_{key}', f'RECENT_{key}', f'DIFF_{key}', f'HEAT_RATING_{key}']], use_container_width=True)
    else:
        st.write('No players found.')

with col2:
    st.subheader('❄️ Top Underperformers')
    cold = df.sort_values(by=f'DIFF_{key}', ascending=True).head(10)
    if not cold.empty:
        st.plotly_chart(create_plotly_chart(cold, key, unit), use_container_width=True)
        st.dataframe(cold[['PLAYER_NAME', 'TEAM_ABBREVIATION', f'SEASON_{key}', f'RECENT_{key}', f'DIFF_{key}', f'HEAT_RATING_{key}']], use_container_width=True)
    else:
        st.write('No players found.')

# Update requirements.txt
with open('requirements.txt', 'w') as f:
    f.write('pandas\nnba_api\nplotly\nstreamlit\n')
