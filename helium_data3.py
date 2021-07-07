import requests
import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import streamlit as st 

headers = {}
nen = st.secrets['nen_account']

assets = {}

for i in range(1,51):
    digits = len(str(i))
    s = 'M' + '0'*(7-digits) + str(i)
    assets[st.secrets[s]] = s

url = 'https://api.helium.io/v1/accounts/' + nen +'/hotspots'
r = requests.get(url=url, headers=headers)
data = r.json()
new_hotspots = pd.DataFrame(data['data'])
new_hotspots['asset id'] = new_hotspots['name'].map(assets)

options = []
new_hotspots['clntcity'] = [d.get('short_city').upper() for d in new_hotspots['geocode']]
new_hotspots['clntaddr1'] = [d.get('short_street') for d in new_hotspots['geocode']]

options = ['ALL'] + list(set(new_hotspots['clntcity']))

def get_mined(address, time = '2021-06-01T00:00:00'):
    if time != '2021-06-01T00:00:00':  
        t = repr(time).replace('\'','')
    else:
        t = time
    url = 'https://api.helium.io/v1/hotspots/' + address + '/rewards/sum' + '?min_time=' + t
    r = requests.get(url=url, headers=headers)
    data = r.json()
    total_mined = data['data']['total']
    return total_mined
def get_cities(city):
    cities = {}
    time_24_hrs_ago = (dt.datetime.now() - dt.timedelta(hours=24)).isoformat()
    time_30_d_ago = (dt.datetime.now() - dt.timedelta(days=30)).isoformat()
    if city != 'ALL':
        df = new_hotspots[new_hotspots['clntcity']==city]
    else:
        df = new_hotspots
    for idx, row in df.iterrows():
        if row['clntcity'] not in cities.keys():
            cities[row['clntcity']] = []
        status = row['status']['online']
        day_earnings = get_mined(row['address'], time_24_hrs_ago)
        month_earnings = get_mined(row['address'], time_30_d_ago)
        total_earnings = get_mined(row['address'])
        d = {'name': row['name'].replace("-", " "),'location':row['clntaddr1'], 'status': status, 'day earnings': day_earnings, 'month earnings': month_earnings, 'total earnings': total_earnings}
        cities[row['clntcity']].append(d)
    if city == 'ALL':
        return cities
    else:
        df = pd.DataFrame(cities[city]).sort_values(by= 'total earnings', ascending = False)
        d = dict(df.mean(axis =0, numeric_only = True))
        d_total = dict(df.sum(axis =0, numeric_only = True))

        d['name'] = 'AVERAGE'
        d['location'] = " "
        d['status'] = ""
        d['total earnings'] = " "
        df = df.append(d, ignore_index = True)

        d_total['name'] = 'TOTAL'
        d_total['location'] = " "
        d_total['status'] = " "
        df = df.append(d_total, ignore_index = True)
        return df.set_index('name')

def compiled():
    data = get_cities('ALL')
    total = []
    for key in data.keys():
        offline = 0
        day_earnings = 0
        month_earnings = 0
        total_earnings = 0 
        num_hotspots = len(data[key])
        for hotspot in data[key]:
            if hotspot['status'] == 'offline':
                offline +=1
            day_earnings += hotspot['day earnings']
            month_earnings += hotspot['month earnings']
            total_earnings += hotspot['total earnings']
        d = {'city': key, '# hotspots': num_hotspots, '# offline': offline, '24hr earnings': day_earnings, '30d earnings': month_earnings, 'total earnings': total_earnings }
        total.append(d)
    df = pd.DataFrame(total).sort_values(by= 'total earnings', ascending = False)
    d = dict(df.sum(axis =0, numeric_only = True))
    d['city'] = 'TOTAL'
    df = df.append(d, ignore_index = True)
    data_types_dict = {'city':str, '# hotspots': int, '# offline': int}
    df = df.astype(data_types_dict)
    return df  

def activity_count(address):
    url = 'https://api.helium.io/v1/hotspots/' + address + '/activity/count'
    r = requests.get(url=url, headers=headers)
    data = r.json()
    return data['data']

def color_status(val):
    if val == 'online':
        color = 'lightgreen'
    elif val == 'offline':
        color = 'tomato'
    elif val == ' ':
        color = 'lightsteelblue'
    else:
        color = 'white'
    return f'background-color:{color}'

def stats(city_name):
    if city_name == 'ALL':
        cit = new_hotspots
    else:
        cit = new_hotspots[new_hotspots['clntcity'] == city_name]

    witness = []
    for idx, row in cit.iterrows():
        url = 'https://api.helium.io/v1/hotspots/' + row['address'] + '/witnesses'
        r = requests.get(url=url, headers=headers)
        data = r.json()
        count_interactions = 0 
        for wit in data['data']:
            if wit['owner'] == nen:
                count_interactions +=1
        recent_witnesses = len(data['data'])
        
        d = activity_count(row['address'])
        d['name'] = row['name'].replace("-", " ")
        d['location'] = row['clntaddr1']
        d['asset id'] = row['asset id']
        d['city'] = row['clntcity']
        d['status'] = row['status']['online']
        d['reward scale'] = row['reward_scale']

        d['total mined'] = get_mined(row['address'], '2021-06-01T00:00:00')
        
        d['witnessing self'] = count_interactions
        d['recent witnesses'] = recent_witnesses
        if d['recent witnesses'] == 0: 
                d['percent witnessing self'] = "0%" 
        else:
            p = int(d['witnessing self']/d['recent witnesses'] *100)                
            d['percent witnessing self'] = str(p) + "%"
        witness.append(d)
        
    df = pd.DataFrame(witness).sort_values(by= 'total mined', ascending = False)
    cols = ['name','location','asset id','city', 'status','total mined', 'reward scale','recent witnesses', 'percent witnessing self','vars_v1', 'transfer_hotspot_v1', 'token_burn_v1', 'token_burn_exchange_rate_v1', 'state_channel_open_v1', 'security_exchange_v1', 'security_coinbase_v1', 'routing_v1', 'rewards_v2', 'rewards_v1', 'redeem_htlc_v1', 'price_oracle_v1', 'poc_request_v1', 'poc_receipts_v1','state_channel_close_v1', 'payment_v2', 'payment_v1', 'oui_v1', 'gen_gateway_v1', 'dc_coinbase_v1', 'create_htlc_v1', 'consensus_group_v1', 'coinbase_v1']
    
    d_total = dict(df.sum(axis =0, numeric_only = True))
    d_total['name'] = 'TOTAL'
    d_total['location'] = " "
    d_total['status'] = " "
    d_total['asset id'] = " "
    d_total['city'] = " "
    d_total['percent witnessing self'] = " "
    d_total['reward scale'] = " "

    df = df.append(d_total, ignore_index = True)
    return df[cols].loc[:, (df != 0).any(axis=0)]

# sidebar 
st.sidebar.write("## Helium Hotspots")
page = st.sidebar.selectbox("App Navigation", ["Hotspot Data", "Earnings Data"])
city_name = st.sidebar.selectbox('Choose a city' ,options)
filt = st.sidebar.selectbox('Filter Online/Offline', ['All', 'Online','Offline'])

if page == 'Hotspot Data':
    hot_data = stats(city_name).set_index('name')
    if filt == 'Online':
        hot_data = hot_data[hot_data['status']== 'online']
    elif filt == 'Offline':
        hot_data = hot_data[hot_data['status']== 'offline']
    hot_data = hot_data.style.apply(lambda x: ['background: lightsteelblue' if x.name == 'TOTAL' else '' for i in x], axis=1)
    st.table(hot_data.applymap(color_status, subset=['status']).set_precision(2))
    
if page == 'Earnings Data':
    if city_name == 'ALL':
        cities = compiled().set_index('city')
        st.table(cities.style.apply(lambda x: ['background: lightsteelblue' if x.name == 'TOTAL' else '' for i in x], axis=1).set_precision(2))

    else:
        df = get_cities(city_name)

        if filt == 'Online':
            df = df[df['status']== 'online']
        elif filt == 'Offline':
            df = df[df['status']== 'offline']
        
        df = df.style.apply(lambda x: ['background: lightsteelblue' if x.name == 'TOTAL' else '' for i in x], axis=1)
        st.table(df.applymap(color_status, subset=['status']).set_precision(2))
