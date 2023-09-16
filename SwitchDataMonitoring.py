import pandas as pd
import json
import requests
from pathlib import Path
import psycopg2
from psycopg2 import sql
import matplotlib.pyplot as plt
import schedule
import time

def authenticate_to_switch(switch_address, username, password):
    headers = {'Accept': 'application/vnd.alcatellucentaos+json'}
    auth_url = f"https://{switch_address}/auth/?&username={username}&password={password}"
    auth_response = requests.get(auth_url, headers=headers, verify=False)
    return auth_response.cookies if auth_response.status_code == 200 else None

def fetch_switch_data(switch_address, cookies):
    headers = {'Accept': 'application/vnd.alcatellucentaos+json'}
    data_url = f"https://{switch_address}/mib/ifXTable?mibObject0=ifHCInOctets&mibObject1=ifHCOutOctets"
    data_response = requests.get(data_url, headers=headers, cookies=cookies, verify=False)
    return json.loads(data_response.text)["result"]["data"]["rows"] if data_response.status_code == 200 else None

def save_to_db(df, db_params):
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        
        for index, row in df.iterrows():
            insert_sql = sql.SQL(
                "INSERT INTO SwitchInfos (switchPort, ifHCInOctets, ifHCOutOctets) VALUES (%s, %s, %s)"
            )
            cur.execute(insert_sql, (index, int(row['ifHCInOctets']), int(row['ifHCOutOctets'])))
        
        conn.commit()
        print("Changes has been saved in the database")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

def fetch_switch_info(db_params, port):
    result = []
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT ifhcinoctets, ifhcoutoctets, timestamps FROM public.switchinfos
            WHERE switchport = %s
            ORDER BY rowid ASC;
        """, (port,))
        
        rows = cur.fetchall()
        for row in rows:
            result.append({
                'ifhcinoctets': row[0],
                'ifhcoutoctets': row[1],
                'timestamps': row[2]
            })
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()
    
    return result

def plot_switch_info(data, port):
    ifhcinoctets = [d['ifhcinoctets'] for d in data]
    ifhcoutoctets = [d['ifhcoutoctets'] for d in data]
    timestamps = [d['timestamps'] for d in data]
    
    plt.figure(figsize=(14, 6))
    
    plt.subplot(2, 1, 1)
    plt.plot(timestamps, ifhcinoctets, marker='o', linestyle='-', color='b')
    plt.title(f'Switch Info for Port {port}')
    plt.xlabel('Timestamps')
    plt.ylabel('Received Octets,')
    
    plt.subplot(2, 1, 2)
    plt.plot(timestamps, ifhcoutoctets, marker='o', linestyle='-', color='r')
    plt.xlabel('Timestamps')
    plt.ylabel('Transmitted Octets')
    
    plt.tight_layout()
    plt.show()

def fetch_all_ports(db_params):
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT switchport FROM public.switchinfos WHERE ifhcinoctets > 0 OR ifhcoutoctets > 0 ORDER BY switchport ASC;")
        rows = cur.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        print(f"An error occurred: {e}")
        return []
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

def plot_all_ports_info(db_params):
    ports = fetch_all_ports(db_params)
    
    plt.figure(figsize=(14, 14))
    
    for port in ports:
        data = fetch_switch_info(db_params, port)
        ifhcinoctets = [d['ifhcinoctets'] for d in data]
        ifhcoutoctets = [d['ifhcoutoctets'] for d in data]
        timestamps = [d['timestamps'] for d in data]

        # Ignore ports with all zero data
        if all(v == 0 for v in ifhcinoctets) and all(v == 0 for v in ifhcoutoctets):
            continue

        plt.subplot(2, 1, 1)
        plt.plot(timestamps, ifhcinoctets, marker='o', linestyle='-', label=f'Port {port} In')
        
        plt.subplot(2, 1, 2)
        plt.plot(timestamps, ifhcoutoctets, marker='o', linestyle='-', label=f'Port {port} Out')

    plt.subplot(2, 1, 1)
    plt.title('Switch Info for All Ports (In)')
    plt.xlabel('Timestamps')
    plt.ylabel('Received Octets,')
    plt.legend()
    
    plt.subplot(2, 1, 2)
    plt.title('Switch Info for All Ports (Out)')
    plt.xlabel('Timestamps')
    plt.ylabel('Transmitted Octets')
    plt.legend()
    
    plt.tight_layout()
    plt.show()

def job():
        cookies = authenticate_to_switch(switch_address, username, password)
        if not cookies:
            print("Authentication failed.")
            return
    
        raw_data = fetch_switch_data(switch_address, cookies)
        if not raw_data:
            print("Data fetch failed.")
            return

        df = pd.DataFrame(raw_data).transpose().astype('int64')
        df.to_json(Path(__file__).parent / 'BDDJson' / 'transformed_data.json')
    
        save_to_db(df, db_params)

if __name__ == "__main__":
    switch_address = "10.255.226.163"
    username = "admin"
    password = "switch"
    port = 1001
    
    db_params = {
        'dbname': 'SwitchData',
        'user': 'postgres',
        'password': 'admin',
        'host': '127.0.0.1',
        'port': '5432'
    }

    job()
    
    while True:
        print("Pause till next data update")
        time.sleep(300)
        job()

    #plot_switch_info(fetch_switch_info(db_params, port), port)
    #plot_all_ports_info(db_params)
