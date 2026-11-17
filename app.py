"""Second Chance — Capstone I exploratory research application."""
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Second Chance | Shelter Insights", page_icon="🐾", layout="wide", initial_sidebar_state="expanded")
ROOT = Path(__file__).resolve().parent
TEAL, CORAL, NAVY, GOLD = "#0C9A9A", "#F27D69", "#17263E", "#E9AF54"
PALETTE = {"CAT":TEAL,"DOG":CORAL}
ORDER = ["Under 1", "1–2", "3–7", "8+"]
INTERMEDIARY = {"RESCUE", "TRANSFER", "TRANSPORT", "FOSTER", "FOSTER TO ADOPT", "RETURN TO RESCUE"}

st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"],.stApp {font-family:'DM Sans',sans-serif}
h1,h2,h3 {font-family:'Outfit',sans-serif!important;letter-spacing:-.03em!important;color:#17263E!important}
[data-testid="stAppViewContainer"] {background:#F7FAFA}
[data-testid="stSidebar"] {background:#EDF5F4}
[data-testid="stMetric"] {background:#FFFFFF;border:1px solid #E2EBEB;padding:16px 20px;border-radius:16px;box-shadow:0 3px 12px #152C3908}
[data-testid="stMetricLabel"] {color:#586F78}
[data-testid="stMetricValue"] {color:#17263E;font-family:'Outfit',sans-serif}
.hero {padding:30px 34px;border-radius:20px;background:linear-gradient(115deg,#17314A,#116F78);color:white;margin-bottom:22px}
.hero h1 {color:white!important;font-size:2.4rem;margin:0 0 8px}
.hero p {color:#D5F1EF;font-size:1.04rem;margin:0}
.eyebrow {font-size:.76rem;font-weight:800;letter-spacing:.16em;color:#B5F0E6;margin-bottom:10px}
.note {padding:13px 16px;background:#E9F4F2;border-left:4px solid #0C9A9A;border-radius:8px;color:#294E54}
.small {color:#667D86;font-size:.88rem}
footer {visibility:hidden}
</style>''',unsafe_allow_html=True)

@st.cache_data(show_spinner="Loading shelter records...")
def load_data():
    df=pd.read_csv(ROOT/'data'/'cats_dogs_working.csv',low_memory=False)
    for c in ['latitude','longitude','age_years']:
        df[c]=pd.to_numeric(df[c],errors='coerce')
    df['Outcome Type']=df['Outcome Type'].fillna('NOT RECORDED').astype(str).str.strip()
    df['Intake Condition']=df['Intake Condition'].fillna('NOT RECORDED').astype(str).str.strip()
    df['Animal Type']=df['Animal Type'].astype(str).str.strip()
    df['age_group']=df['age_group'].fillna('Unknown')
    df['has_outcome']=df['Outcome Type'].ne('NOT RECORDED')
    df['is_adopted']=df['Outcome Type'].eq('ADOPTION')
    df['is_euthanized']=df['Outcome Type'].eq('EUTHANASIA')
    df['Intake Date']=pd.to_datetime(df['Intake Date'],errors='coerce')
    df['year']=df['Intake Date'].dt.year
    return df

df=load_data()

def share(data,flag):
    known=data.loc[data['has_outcome']]
    return 100*known[flag].sum()/len(known) if len(known) else 0.0

def base_fig(fig,height=370):
    fig.update_layout(height=height,margin=dict(l=8,r=12,t=25,b=15),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font=dict(family='DM Sans',color=NAVY),legend_title_text='')
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor='#E5ECEC',zeroline=False)
    return fig

def outcome_chart(data):
    t=data.loc[data['has_outcome']].groupby(['Animal Type','Outcome Type']).size().reset_index(name='Records')
    order=data.loc[data['has_outcome'],'Outcome Type'].value_counts().head(8).index.tolist()
    t=t[t['Outcome Type'].isin(order)]
    fig=px.bar(t,x='Outcome Type',y='Records',color='Animal Type',barmode='group',color_discrete_map=PALETTE,category_orders={'Outcome Type':order},labels={'Animal Type':'Species'})
    fig.update_xaxes(tickangle=-28)
    return base_fig(fig,430)

def group_chart(data,group,flag,title):
    t=data.loc[data['has_outcome'] & data[group].notna()].groupby(['Animal Type',group],dropna=False).agg(n=('has_outcome','size'),positive=(flag,'sum')).reset_index()
    t['Percent']=100*t['positive']/t['n']
    if group=='age_group':
        t=t[t[group].isin(ORDER)]
        orders={group:ORDER}
    else:
        top=data[group].value_counts().head(10).index.tolist()
        t=t[t[group].isin(top)]
        orders={group:top}
    fig=px.bar(t,x=group,y='Percent',color='Animal Type',barmode='group',color_discrete_map=PALETTE,category_orders=orders,custom_data=['n','positive'],labels={group:group.replace('_',' ').title(),'Percent':f'{title} share (%)','Animal Type':'Species'})
    fig.update_traces(hovertemplate='%{x}<br>%{y:.1f}%<br>Known outcomes: %{customdata[0]:,}<br>Matching outcomes: %{customdata[1]:,}<extra></extra>')
    fig.update_yaxes(range=[0, max(12,t['Percent'].max()*1.15) if len(t) else 12])
    fig.update_xaxes(tickangle=-28 if group!='age_group' else 0)
    return base_fig(fig,420)

with st.sidebar:
    st.markdown('## 🐾 Second Chance')
    st.caption('SHELTER ANIMAL INSIGHTS · CAPSTONE I')
    st.divider()
    page=st.radio('Navigate', ['🏠 Overview','📊 Outcome Explorer','🐱 Age & Health','🗺️ Geographic Explorer','🔬 Research Findings','📚 Methods & Roadmap'],label_visibility='collapsed')
    st.divider()
    st.markdown('**Explore a subset**')
    species=st.multiselect('Species',['CAT','DOG'],default=['CAT','DOG'])
    year_options=sorted(df['year'].dropna().astype(int).unique().tolist())
    yr=st.slider('Intake year range',min_value=min(year_options),max_value=max(year_options),value=(min(year_options),max(year_options)))
    st.caption('These sidebar filters apply across the dashboard. Additional page-specific filters appear on each page.')
    st.divider()
    st.caption('Source: City of Long Beach Animal Shelter Intakes and Outcomes, downloaded November 13, 2026. Descriptive research prototype; no predictive model is trained.')

filtered=df[df['Animal Type'].isin(species) & df['year'].between(yr[0],yr[1])].copy()
known=filtered.loc[filtered['has_outcome']]

if page=='🏠 Overview':
    st.markdown('<div class="hero"><div class="eyebrow">MS DATA SCIENCE & AI · CAPSTONE I</div><h1>Every shelter animal deserves a chance.</h1><p>Explore recorded adoption, euthanasia, and intake patterns in Long Beach shelter records—and discover where earlier support may matter.</p></div>',unsafe_allow_html=True)
    a,b,c,d=st.columns(4)
    a.metric('Cat + dog records',f'{len(filtered):,}')
    b.metric('Known outcomes',f'{len(known):,}')
    c.metric('Direct adoption share',f'{share(filtered,"is_adopted"):.1f}%')
    d.metric('Euthanasia share',f'{share(filtered,"is_euthanized"):.1f}%')
    st.caption('Rates use records with a known outcome as the denominator. Records are intake episodes, not necessarily unique animals.')
    left,right=st.columns([1.3,1])
    with left:
        st.subheader('Where do records lead?')
        st.plotly_chart(outcome_chart(filtered),use_container_width=True)
    with right:
        st.subheader('Species composition')
        counts=filtered['Animal Type'].value_counts().rename_axis('Species').reset_index(name='Records')
        fig=px.pie(counts,names='Species',values='Records',hole=.63,color='Species',color_discrete_map=PALETTE)
        fig.update_traces(textinfo='label+percent')
        st.plotly_chart(base_fig(fig,430),use_container_width=True)
    st.markdown('<div class="note"><b>Research purpose:</b> Understand which animal characteristics and shelter pathways are associated with outcomes. This is exploratory analysis—not an estimate of preventable euthanasia or a prediction of individual animals.</div>',unsafe_allow_html=True)

elif page=='📊 Outcome Explorer':
    st.title('📊 Outcome Explorer')
    st.write('Explore how recorded outcome shares change across species, outcome definitions, and intake years.')
    a,b,c=st.columns(3)
    a.metric('Adoption records',f'{known["is_adopted"].sum():,}')
    b.metric('Euthanasia records',f'{known["is_euthanized"].sum():,}')
    c.metric('Rescue records',f'{known["Outcome Type"].eq("RESCUE").sum():,}')
    st.subheader('Recorded outcome pathways')
    st.plotly_chart(outcome_chart(filtered),use_container_width=True)
    st.subheader('Why outcome definitions matter')
    options=['All known outcomes','Exclude RESCUE','Exclude intermediary outcomes']
    scenario=st.selectbox('Denominator definition',options)
    valid=known.copy()
    if scenario=='Exclude RESCUE':valid=valid[valid['Outcome Type']!='RESCUE']
    if scenario=='Exclude intermediary outcomes':valid=valid[~valid['Outcome Type'].isin(INTERMEDIARY)]
    g=valid.groupby('Animal Type').agg(adoptions=('is_adopted','sum'),eligible=('is_adopted','size')).reset_index()
    g['Adoption share (%)']=100*g['adoptions']/g['eligible']
    if len(g):
        fig=px.bar(g,x='Animal Type',y='Adoption share (%)',color='Animal Type',color_discrete_map=PALETTE,text='Adoption share (%)',custom_data=['adoptions','eligible'])
        fig.update_traces(texttemplate='%{text:.1f}%',textposition='outside',hovertemplate='%{x}: %{y:.1f}%<br>Adoptions: %{customdata[0]:,}<br>Eligible records: %{customdata[1]:,}<extra></extra>')
        fig.update_yaxes(range=[0,max(15,g['Adoption share (%)'].max()*1.3)])
        st.plotly_chart(base_fig(fig,330),use_container_width=True)
        st.dataframe(g.rename(columns={'Animal Type':'Species'}),hide_index=True,use_container_width=True)
    st.info('Excluding rescue or intermediary outcomes changes the denominator. Higher percentages do not mean that more animals were adopted. These are exploratory definitions, not validated prediction targets.')
    st.subheader('Trend by intake year')
    trend=known.groupby('year').agg(known=('has_outcome','size'),adoptions=('is_adopted','sum'),euthanasia=('is_euthanized','sum')).reset_index()
    trend=trend[trend['known']>0]
    trend['Adoption (%)']=100*trend['adoptions']/trend['known']
    trend['Euthanasia (%)']=100*trend['euthanasia']/trend['known']
    metric=st.radio('Show', ['Adoption (%)','Euthanasia (%)'],horizontal=True)
    fig=px.line(trend,x='year',y=metric,markers=True,color_discrete_sequence=[TEAL if metric=='Adoption (%)' else CORAL])
    st.plotly_chart(base_fig(fig,320),use_container_width=True)
    st.caption('Year reflects intake date, not outcome date. Incomplete recent follow-up can bias comparisons; these are not survival-adjusted rates.')

elif page=='🐱 Age & Health':
    st.title('🐱 Age & Health')
    st.write('Compare the shares of known outcomes recorded as direct adoption or euthanasia within animal groups.')
    metric=st.segmented_control('Outcome of interest',['Adoption','Euthanasia'],default='Adoption')
    flag='is_adopted' if metric=='Adoption' else 'is_euthanized'
    st.subheader(f'{metric} by age group')
    st.plotly_chart(group_chart(filtered,'age_group',flag,metric),use_container_width=True)
    st.caption('Unknown ages are excluded from this age chart. Group rates use known outcomes within each age group.')
    st.subheader(f'{metric} by intake condition')
    st.plotly_chart(group_chart(filtered,'Intake Condition',flag,metric),use_container_width=True)
    st.caption('The 10 most common intake conditions in the selected subset are shown. Labels reflect the source dataset, including any original spelling inconsistencies.')
    st.markdown('<div class="note"><b>Interpretation:</b> Associations with age and health are descriptive. The data cannot establish that euthanasia was preventable or that a characteristic caused an outcome.</div>',unsafe_allow_html=True)

elif page=='🗺️ Geographic Explorer':
    st.title('🗺️ Geographic Explorer')
    st.write('Examine plausible intake/capture coordinates in the Long Beach region.')
    st.warning('These points indicate recorded intake/capture locations—not adopter addresses, adoption destinations, or proof of where adoption demand is highest.')
    loc=filtered[filtered['latitude'].between(33.55,34.05) & filtered['longitude'].between(-118.45,-117.85)].copy()
    loc=loc.dropna(subset=['latitude','longitude'])
    a,b,c=st.columns(3)
    a.metric('Plausible regional records',f'{len(loc):,}')
    b.metric('Excluded / missing coordinates',f'{len(filtered)-len(loc):,}')
    c.metric('Distinct coordinate pairs',f'{loc[["latitude","longitude"]].drop_duplicates().shape[0]:,}')
    outcome=st.selectbox('Map outcomes',['All known and unknown outcomes','ADOPTION','EUTHANASIA','RESCUE','RETURN TO OWNER'])
    if outcome!='All known and unknown outcomes':loc=loc[loc['Outcome Type']==outcome]
    if len(loc):
        # Aggregate repeated coordinates, avoid disclosing individual-level location trails and large map payloads.
        loc['lat_round']=loc['latitude'].round(3)
        loc['lon_round']=loc['longitude'].round(3)
        agg=loc.groupby(['lat_round','lon_round'],as_index=False).size().rename(columns={'lat_round':'latitude','lon_round':'longitude','size':'Records'})
        fig=px.scatter_map(agg,lat='latitude',lon='longitude',size='Records',color='Records',color_continuous_scale=['#A6D9D6',TEAL,NAVY],zoom=10,center={'lat':33.79,'lon':-118.16},hover_data={'Records':True,'latitude':':.3f','longitude':':.3f'},size_max=24)
        fig.update_layout(map_style='open-street-map',height=530,margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig,use_container_width=True)
        st.caption(f'{len(loc):,} filtered records aggregated into {len(agg):,} rounded coordinate clusters. The basemap may require an internet connection; the application itself runs locally.')
    else:st.info('No records match these geographic filters.')
    st.info('A city-boundary validation and potential ACS spatial join are planned for Capstone II. The broad screening box is not an official Long Beach boundary.')

elif page=='🔬 Research Findings':
    st.title('🔬 Research Findings')
    st.write('Findings below are recomputed from the current filtered subset. For the published Capstone I values, select both species and the full year range in the sidebar.')
    st.subheader('Age-related outcomes')
    st.plotly_chart(group_chart(filtered,'age_group','is_euthanized','Euthanasia'),use_container_width=True)
    st.subheader('Health-related outcomes')
    st.plotly_chart(group_chart(filtered,'Intake Condition','is_euthanized','Euthanasia'),use_container_width=True)
    st.subheader('Species comparison')
    vals=[]
    for s in ['CAT','DOG']:
        sub=filtered[filtered['Animal Type']==s]
        if len(sub):vals.append({'Species':s,'Known outcomes':int(sub['has_outcome'].sum()),'Direct adoption (%)':round(share(sub,'is_adopted'),1),'Euthanasia (%)':round(share(sub,'is_euthanized'),1)})
    st.dataframe(pd.DataFrame(vals),hide_index=True,use_container_width=True)
    st.markdown('''**Key full-dataset observations from the Capstone I presentation:** Senior cats (8+) had 22.4% recorded adoption and 45.1% euthanasia; senior dogs had 13.6% recorded adoption. Severe illness and severe injury were associated with high recorded euthanasia shares, particularly among cats. These observations motivate earlier assessment and targeted support, not claims of preventability.''')
    st.caption('The narrative figures above refer to the full dataset and do not change with sidebar filters; the interactive charts and table do.')
    st.info('Chi-square comparisons in the Capstone I analysis were exploratory; repeated intake episodes may violate independence assumptions. Species differences are sensitive to the outcome definition.')

else:
    st.title('📚 Methods & Capstone II Roadmap')
    st.subheader('Research framing')
    st.write('**Question:** How do species, age, intake condition, and potentially intake geography relate to recorded shelter outcomes?')
    st.write('**Goal:** Establish an auditable descriptive baseline and plan a leakage-safe predictive model to help identify animals who may need earlier support.')
    st.subheader('Data provenance')
    st.write('**Primary:** City of Long Beach, *Animal Shelter Intakes and Outcomes* (2026), public open-data extract downloaded November 13, 2026. The analysis subset contains cat and dog intake/outcome records.')
    st.write('**Future contextual sources:** Shelter Animals Count (national context); U.S. Census Bureau American Community Survey (possible geographic enrichment). Neither is row-joined in this application.')
    st.subheader('Data processing and definitions')
    st.markdown('''- Retain cats and dogs; preserve repeated intake episodes rather than pretending they are unique animals.
- Use known recorded outcomes as the denominator for direct adoption and euthanasia shares.
- Exclude missing ages from age-specific comparisons; retain them elsewhere.
- Compare multiple outcome eligibility definitions to assess sensitivity.
- Apply a broad geographic plausibility screen, not a verified city-boundary check.
- Avoid post-outcome information as predictors in future modeling.''')
    st.subheader('Limitations')
    st.markdown('''- Observational associations do not establish causation or preventability.
- Euthanasia may be medically necessary; the dataset does not determine that.
- Repeated animal IDs can make records statistically dependent.
- Age/DOB and intake-condition labels can be incomplete or inconsistent.
- Coordinates refer to intake/capture, not adopter residence.
- Recent intakes may have incomplete outcome follow-up.
- No predictive model has been trained or evaluated for Capstone I.''')
    st.subheader('Next steps: Capstone II')
    st.markdown('''1. Verify the final target and outcome eligibility rules with the mentor.
2. Audit repeated animals and design an animal-aware train/test split.
3. Validate geographic features and explore ACS joins if defensible.
4. Train a logistic-regression baseline; compare random forest if useful.
5. Evaluate class balance, calibration, discrimination, and leakage.
6. Add a validated prediction page to this application only after evaluation.''')
    st.subheader('References')
    st.markdown('''- City of Long Beach. (2026). *Animal shelter intakes and outcomes* [Data set]. Long Beach Open Data.
- Shelter Animals Count. (n.d.). *National sheltering data and statistics*. https://www.shelteranimalscount.org/
- U.S. Census Bureau. (2025). *American Community Survey, 2020–2024 5-year estimates* [Data set].''')

st.divider()
st.caption('SECOND CHANCE · FIU MS Data Science & AI · Capstone I · Sidney Bobadilla · Descriptive analysis only · Long Beach open data')
