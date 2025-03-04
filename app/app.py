import streamlit as st
import pandas as pd
import geopandas as gpd
import h3
import numpy as np
import plotly.express as px
px.set_mapbox_access_token(st.secrets['MAPBOX_TOKEN'])
my_style = st.secrets['MAPBOX_STYLE']
from pathlib import Path
from shapely import wkt

st.set_page_config(page_title="Research App", layout="wide", initial_sidebar_state='expanded')
st.markdown("""
<style>
button[title="View fullscreen"]{
        visibility: hidden;}
</style>
""", unsafe_allow_html=True)

#title
st.header("Zoning density",divider='grey')
st.subheader("Zoning plans' density")

# get the data
@st.cache_data()
def load_data():
    path = Path(__file__).parent / 'data/hki_ak_data_202210.csv'
    with path.open() as f:
        data = pd.read_csv(f, index_col='kaavayksikkotunnus', header=0)#.astype(str)
    return data
try:
    df_data = load_data()
except:
    st.warning('Dataan ei yhteyttä.')
    st.stop()

df_data['geometry'] = df_data['geometry'].apply(wkt.loads)
hki_ak_data = gpd.GeoDataFrame(df_data, crs=4326, geometry='geometry')
# drop zero GFAs
hki_ak_data = hki_ak_data.loc[hki_ak_data['rakennusoikeus'] != 0]

# select designations
all_list = hki_ak_data['kayttotarkoitusluokka_koodi'].unique().tolist()
c1,c2 = st.columns(2)
use_list = c1.multiselect('Select landuse types to include',all_list,default=['AK','AP'])
years = [1940,2020] #c2.slider('Set decades to include',1940,2020,(1940,2020),step=10)
trendline = c2.radio('Trendline model',['lowess','ols'], horizontal=True)
# create plot gdf
plot = hki_ak_data.loc[(hki_ak_data['vuosikymmen'] >= years[0]) & (hki_ak_data['vuosikymmen'] <= years[1])]
plot = plot[plot['kayttotarkoitusluokka_koodi'].isin(use_list)]
plot['vuosikymmen'] = plot['vuosikymmen'].astype(str)

# exclude outliers for scatt plot
q =0.99
plot = plot.loc[plot['rekisteriala'] != 0]
plot = plot.loc[plot['rakennusoikeus'] != 0]
plot = plot.loc[plot['rekisteriala'] < plot['rekisteriala'].quantile(q)]
scatt = plot.loc[plot['rakennusoikeus'] < plot['rakennusoikeus'].quantile(q)]
range_y = scatt['rakennusoikeus'].quantile(0.99) + 2000
range_x = scatt['rekisteriala'].quantile(0.99) + 3000
fig = px.scatter(scatt , color="vuosikymmen", x="rekisteriala", y="rakennusoikeus", opacity=0.6, trendline=trendline,
                 labels={'rakennusoikeus':'GFA','rekisteriala':'Plan area','vuosikymmen':'Decade'},
                 title=f'GFA and plan sizes in detail plans in Helsinki by decade (trendline={trendline})',
                 range_y=[0,range_y],range_x=[0,range_x],
                 color_discrete_sequence=px.colors.qualitative.Dark24)
fig.update_traces(patch={"line": {"width": 5}}, selector={"legendgroup": "2020"})
st.plotly_chart(fig, use_container_width=True)
st.caption('Highest percentile(99%) of values are excluded.')

# summaries
scatt['tehokkuus'] = scatt['rakennusoikeus']/scatt['rekisteriala']
gfa_1970 = round(scatt.loc[scatt['vuosikymmen'] == '1970']['rakennusoikeus'].mean(),-1)
e_1970 = scatt.loc[scatt['vuosikymmen'] == '1970']['tehokkuus'].mean()
gfa_1980 = round(scatt.loc[scatt['vuosikymmen'] == '1980']['rakennusoikeus'].mean(),-1)
e_1980 = scatt.loc[scatt['vuosikymmen'] == '1980']['tehokkuus'].mean()
gfa_1990 = round(scatt.loc[scatt['vuosikymmen'] == '1990']['rakennusoikeus'].mean(),-1)
e_1990 = scatt.loc[scatt['vuosikymmen'] == '1990']['tehokkuus'].mean()
gfa_2000 = round(scatt.loc[scatt['vuosikymmen'] == '2000']['rakennusoikeus'].mean(),-1)
e_2000 = scatt.loc[scatt['vuosikymmen'] == '2000']['tehokkuus'].mean()
gfa_2010 = round(scatt.loc[scatt['vuosikymmen'] == '2010']['rakennusoikeus'].mean(),-1)
e_2010 = scatt.loc[scatt['vuosikymmen'] == '2010']['tehokkuus'].mean()
gfa_2020 = round(scatt.loc[scatt['vuosikymmen'] == '2020']['rakennusoikeus'].mean(),-1)
e_2020 = scatt.loc[scatt['vuosikymmen'] == '2020']['tehokkuus'].mean()

m1,m2,m3,m4,m5,m6 = st.columns(6)
m1.metric(label=f"AvgGFA in 1970s", value=f"{gfa_1970:,.0f}", delta=f"e={e_1970:.2f}")
m2.metric(label=f"AvgGFA in 1980s", value=f"{gfa_1980:,.0f}", delta=f"e={e_1980:.2f}")
m3.metric(label=f"AvgGFA in 1990s", value=f"{gfa_1990:,.0f}", delta=f"e={e_1990:.2f}")
m4.metric(label=f"AvgGFA in 2000s", value=f"{gfa_2000:,.0f}", delta=f"e={e_2000:.2f}")
m5.metric(label=f"AvgGFA in 2010s", value=f"{gfa_2010:,.0f}", delta=f"e={e_2010:.2f}")
m6.metric(label=f"AvgGFA in 2020s", value=f"{gfa_2020:,.0f}", delta=f"e={e_2020:.2f}")

# trendline info
def trend_values(fig):
    model = px.get_trendline_results(fig)
    n = len(model)
    df = pd.DataFrame(columns=['decade','constant','slope'])
    for i in range(n):
        r = model.iloc[i]["px_fit_results"]
        alpha = r.params[0] # constant
        beta = r.params[1] # slope
        dec = years[0] + (i*10)
        df.loc[i] = [dec]+[alpha]+[beta]
    df['decade'] = df['decade'].astype(int).astype(str)
    return df

if trendline == 'ols':
    with st.expander('OLS-trendline details',expanded=False):
        trend = trend_values(fig)
        fig2 = px.scatter(trend , color="decade", x="constant", y="slope", opacity=0.9,
                        labels={'decade':'Decade','constant':'Constant','slope':'Slope'},
                        title='Details of trendlines of different decades',
                        color_discrete_sequence=px.colors.qualitative.Dark24)
        st.plotly_chart(fig2, use_container_width=True)
        st.caption('Slope value indicates the density of the plans while constant value indicates the volume in the plans. '
                    'Bigger the slope, denser the plans. Bigger the constant, more GFA in the plans.')

# map plot
st.markdown('###')
decade_list = plot['vuosikymmen'].unique().tolist()
decade_list.insert(0,'Decade..')
mydecade = st.selectbox('Plot plan units from..',decade_list)
if mydecade != 'Decade..':
    mapplot = plot.loc[plot['vuosikymmen'] == mydecade]
    lat = mapplot.unary_union.centroid.y
    lon = mapplot.unary_union.centroid.x
    mymap = px.choropleth_mapbox(mapplot,
                                geojson=mapplot.geometry,
                                locations=mapplot.index,
                                title='Plan units on map',
                                color="vuosikymmen",
                                hover_name='kayttotarkoitusluokka_koodi',
                                hover_data=['vuosi','rakennusoikeus','kaavatunnus'],
                                labels={"vuosikymmen": 'Decade'},
                                mapbox_style=my_style,
                                color_discrete_sequence=px.colors.qualitative.D3,
                                center={"lat": lat, "lon": lon},
                                zoom=10,
                                opacity=0.8,
                                width=1200,
                                height=700
                                )
    st.plotly_chart(mymap, use_container_width=True)

    plancount = len(mapplot)
    st.caption(f'Total {plancount} plans of types {use_list} in {mydecade}. Zero GFA units excluded.')
    source = '''
    <p style="font-family:sans-serif; color:dimgrey; font-size: 10px;">
    Data: <a href="https://hri.fi/data/fi/dataset/helsingin-kaavayksikot" target="_blank">HRI & Helsinki</a>
    </p>
    '''
    st.markdown(source, unsafe_allow_html=True)



#footer
st.markdown('---')
footer_title = '''
[![MIT license](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/teemuja/)
'''
st.markdown(footer_title)
disclamer = 'Data papers are constant work in progress and will be upgraded, changed & fixed while research go on.'
st.caption('Disclaimer: ' + disclamer)