import logging
import os
import pandas as pd
import json
import requests
import time
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Loading environment variables and setting up logging
env_path = 'C:/Users/mleroy/Documents/0Projets/ALE Genetec/PythonBDD/.env'
logging.basicConfig(level=logging.INFO)
load_dotenv(dotenv_path=env_path)

# Function to authenticate to the switch and get the cookie
def authenticate_to_switch(switch_address, username, password):
    logging.info("Sending authentication request...")
    headers = {'Accept': 'application/vnd.alcatellucentaos+json'}
    auth_url = f"https://{switch_address}/auth/?&username={username}&password={password}"
    auth_response = requests.get(auth_url, headers=headers, verify=False)
    # Returning the authentication cookie if the request is successful
    return auth_response.cookies if auth_response.status_code == 200 else None

# Function to fetch data from the switch using the cookie
def fetch_switch_data(switch_address, cookies):
    logging.info("Fetching switch data...")
    headers = {'Accept': 'application/vnd.alcatellucentaos+json'}
    data_url = f"https://{switch_address}/mib/ifXTable?mibObject0=ifHCInOctets&mibObject1=ifHCOutOctets"
    data_response = requests.get(data_url, headers=headers, cookies=cookies, verify=False)
    # Returning the fetched data if the request is successful
    return json.loads(data_response.text)["result"]["data"]["rows"] if data_response.status_code == 200 else None

# Function to save fetched data to the database
def save_to_db(df, db_params):
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        # Iterating through dataframe rows and inserting them into the database
        for index, row in df.iterrows():
            insert_sql = sql.SQL(
                "INSERT INTO SwitchInfos (switchPort, ifHCInOctets, ifHCOutOctets) VALUES (%s, %s, %s)"
            )
            cur.execute(insert_sql, (index, int(row['ifHCInOctets']), int(row['ifHCOutOctets'])))
        conn.commit()
        logging.info("Changes have been saved in the database.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

# Main job function that coordinates the authentication, data fetching and saving processes
def job():
    cookies = authenticate_to_switch(switch_address, username, password)
    if not cookies:
        logging.error("Authentication failed.")
        return

    raw_data = fetch_switch_data(switch_address, cookies)
    if not raw_data:
        logging.error("Data fetch failed.")
        return

    df = pd.DataFrame(raw_data).transpose().astype('int64')
    save_to_db(df, db_params)

# Main execution point
if __name__ == "__main__":
    # Setting up the switch and database parameters
    switch_address = "10.255.226.163"
    username = os.getenv('SWITCH_USERNAME')
    password = os.getenv('SWITCH_PASSWORD')
    db_params = {
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT')
    }

    # Continuous loop for executing the job function at regular intervals
    while True:
        logging.info("Starting a new iteration...")
        try:
            job()
            logging.info("Pause till next data update.")
            time.sleep(300)  # Pausing for 5 minutes before the next iteration
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            time.sleep(60)  # If an error occurs, pause for 1 minute before retrying
