from pathlib import Path
from matplotlib.ticker import MaxNLocator
import psycopg2
from psycopg2 import sql
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.dates as md


def translate_prompt_to_port(portprompt): # Translates the user prompt into a numerical port value
    try:
        module, submodule, port_number = map(int, portprompt.split('/'))
        return (module * 1000) + port_number
    except ValueError: # Handles the case where the port format is incorrect
        print("Invalid port format. Please enter in the format X/X/X.")
        return None

def fetch_switch_info(db_params, port):# Fetches the switch information from the database
    result = []
    try:
        conn = psycopg2.connect(**db_params) # Establishing a connection to the database using provided parameters
        cur = conn.cursor()

        cur.execute("""
            SELECT ifhcinoctets, ifhcoutoctets, timestamps FROM public.switchinfos
            WHERE switchport = %s
            ORDER BY rowid ASC;
        """, (port,)) # Executing the SQL query to fetch switch information for the specific port

        rows = cur.fetchall()
        for row in rows:
            result.append({
                'ifhcinoctets': row[0],
                'ifhcoutoctets': row[1],
                'timestamps': row[2]
            }) # Appending fetched rows to the result list in dictionary format for easy access
    except Exception as e:# Print exception message if an error occurs during the process
        print(f"An error occurred: {e}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()# Ensuring that the cursor and connection are closed after fetching data, regardless of the outcome

    return result# Returning the result list containing the switch information

def human_readable_size(size): # Converts byte values into a human-readable format (B, KB, MB, GB, TB)
    units = ["B", "KB", "MB", "GB", "TB"]
    for unit in units:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

def translate_port(port):
    module_number = port // 1000
    port_number = port % 1000
    return f"{module_number}/1/{port_number}"

def draw_plot(label_x, label_y, plot_name, points_x, points_y, plot_number, plot_color):
    x_axis = plt.subplot(2, 1, plot_number)
    xfmt = md.DateFormatter('%m-%d %H:%M:%S') # Formatting the x-axis labels to display date and time for better readability
    x_axis.xaxis.set_major_formatter(xfmt)# Applying the date format to the x-axis
    x_axis.xaxis.set_major_locator(MaxNLocator(integer=True, prune='both', nbins=8))# Configuring the x-axis to have a limited number of ticks for readability
    plt.plot(points_x, points_y, marker='o', linestyle='-', color=plot_color)
    plt.title(plot_name)
    plt.xlabel(label_x)
    y_values = plt.yticks()[0]
    y_values = [y for y in y_values if y >= 0] # Filtering out negative y-values to ensure the plot remains meaningful and accurate
    plt.yticks(y_values, [human_readable_size(y) for y in y_values])

    plt.ylabel(label_y)

def plot_switch_info(data, port): # Plots the inbound and outbound data volume for a specific port
    switchport = translate_port(port)

    # Extracting individual data lists for inbound and outbound octets and timestamps
    ifhcinoctets = [d['ifhcinoctets'] for d in data]
    ifhcoutoctets = [d['ifhcoutoctets'] for d in data]
    timestamps = [d['timestamps'] for d in data]

    # Calculate the deltas
    delta_in = [j - i for i, j in zip(ifhcinoctets[:-1], ifhcinoctets[1:])]
    delta_out = [j - i for i, j in zip(ifhcoutoctets[:-1], ifhcoutoctets[1:])]

    # Adjust the timestamps to match the number of delta points
    delta_timestamps = timestamps[1:]

    plt.figure(figsize=(14, 6))

    draw_plot("Timestamps", "Recieved", f'Switch Info for Port {switchport} (Inbound Data Volume)', delta_timestamps, delta_in, 1, 'b')

    draw_plot("Timestamps", "Transmitted", f'Switch Info for Port {switchport} (Outbound Data Volume)', delta_timestamps, delta_out, 2, 'r')

    plt.tight_layout()
    plt.show()



def fetch_all_ports(db_params):
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT switchport FROM public.switchinfos WHERE ifhcinoctets > 0 OR ifhcoutoctets > 0 ORDER BY switchport ASC;")
        rows = cur.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        print(f"An error occurred: {e}")
        return []
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


def plot_all_ports_info(db_params):
    ports = fetch_all_ports(db_params)
    plt.figure(figsize=(14, 14))

    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    color_index = 0

    for port in ports:
        data = fetch_switch_info(db_params, port)
        ifhcinoctets = [d['ifhcinoctets'] for d in data]
        ifhcoutoctets = [d['ifhcoutoctets'] for d in data]
        timestamps = [d['timestamps'] for d in data]

        # Ensure the port has valid data before attempting to plot
        if all(v == 0 for v in ifhcinoctets) and all(v == 0 for v in ifhcoutoctets):
            continue

        switchport = translate_port(port)

        # Calculate the deltas
        delta_in = [j - i for i, j in zip(ifhcinoctets[:-1], ifhcinoctets[1:])]
        delta_out = [j - i for i, j in zip(ifhcoutoctets[:-1], ifhcoutoctets[1:])]

        # Adjust the timestamps to match the number of delta points
        delta_timestamps = timestamps[1:]

        # Incrementing color index to switch color for the next port's data visualization
        color = colors[color_index % len(colors)]
        color_index += 1

        # Plot received data
        plt.subplot(2, 1, 1)
        plt.plot(delta_timestamps, delta_in, marker='o', linestyle='-', color=color, label=f'Port {switchport} In')
        plt.title('Switch Info for All Ports (Inbound Data Volume)')
        plt.xlabel('Timestamps')
        plt.ylabel('Recieved')

        # Plot transmitted data
        plt.subplot(2, 1, 2)
        plt.plot(delta_timestamps, delta_out, marker='o', linestyle='-', color=color, label=f'Port {switchport} Out')
        plt.title('Switch Info for All Ports (Outbound Data Volume)')
        plt.xlabel('Timestamps')
        plt.ylabel('Transmitted')

    # Formatting the x-axis as date and rotating the labels for better readability
    ax = plt.gca()
    xfmt = md.DateFormatter('%m-%d %H:%M:%S')
    ax.xaxis.set_major_formatter(xfmt)
    plt.xticks(rotation=25)

    plt.tight_layout()
    plt.legend()
    plt.show()
    


if __name__ == "__main__":
    switch_address = "10.255.226.163"
    username = "admin"
    password = "switch"
    port_prompt = "1/1/1"

    db_params = {
        'dbname': 'SwitchData',
        'user': 'postgres',
        'password': 'admin',
        'host': '127.0.0.1',
        'port': '5432'
    }

    port = translate_prompt_to_port(port_prompt)

    if port is not None:
        switchport = translate_port(port)

        #Choose between of of the two options, plot all ports or plot only one port
    
        #plot_switch_info(fetch_switch_info(db_params, port), port)
        plot_all_ports_info(db_params)
