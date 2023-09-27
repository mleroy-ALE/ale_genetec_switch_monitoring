# Importing required libraries and modules
from pathlib import Path
from matplotlib.ticker import MaxNLocator
import psycopg2
from psycopg2 import sql
import matplotlib.pyplot as plt
import matplotlib.dates as md

# Translate user input into numerical port value
def translate_prompt_to_port(portprompt):
    try:
        module, submodule, port_number = map(int, portprompt.split('/'))
        return (module * 1000) + port_number
    except ValueError:
        print("Invalid port format. Please enter in format X/X/X.")
        return None

# Fetch switch information from database
def fetch_switch_info(db_params, port):
    result = []
    try:
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        query = """
            SELECT ifhcinoctets, ifhcoutoctets, timestamps FROM public.switchinfos
            WHERE switchport = %s ORDER BY rowid ASC;
        """
        cur.execute(query, (port,))
        rows = cur.fetchall()
        for row in rows:
            result.append({
                'ifhcinoctets': row[0],
                'ifhcoutoctets': row[1],
                'timestamps': row[2]
            })
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()
    return result

# Convert byte values to human-readable format
def human_readable_size(size):
    units = ["B", "KB", "MB", "GB", "TB"]
    for unit in units:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

# Translate numerical port value to user-friendly format
def translate_port(port):
    module_number = port // 1000
    port_number = port % 1000
    return f"{module_number}/1/{port_number}"

# Plot inbound and outbound data volume for specified port
def plot_switch_info(data, port):
    switchport = translate_port(port)
    ifhcinoctets = [d['ifhcinoctets'] for d in data]
    ifhcoutoctets = [d['ifhcoutoctets'] for d in data]
    timestamps = [d['timestamps'] for d in data]
    delta_in = [j - i for i, j in zip(ifhcinoctets[:-1], ifhcinoctets[1:])]
    delta_out = [j - i for i, j in zip(ifhcoutoctets[:-1], ifhcoutoctets[1:])]
    delta_timestamps = timestamps[1:]
    plt.figure(figsize=(14, 6))
    draw_plot("Timestamps", "Recieved", f'Switch Info for Port {switchport} (Inbound)', delta_timestamps, delta_in, 1, 'b')
    draw_plot("Timestamps", "Transmitted", f'Switch Info for Port {switchport} (Outbound)', delta_timestamps, delta_out, 2, 'r')
    plt.tight_layout()
    plt.show()

# Utility function to draw plot for data
def draw_plot(label_x, label_y, plot_name, points_x, points_y, plot_number, plot_color):
    x_axis = plt.subplot(2, 1, plot_number)
    xfmt = md.DateFormatter('%m-%d %H:%M:%S')
    x_axis.xaxis.set_major_formatter(xfmt)
    plt.plot(points_x, points_y, marker='o', linestyle='-', color=plot_color)
    plt.title(plot_name)
    plt.xlabel(label_x)
    y_values = plt.yticks()[0]
    y_values = [y for y in y_values if y >= 0]  # Exclude negative values for a meaningful plot
    plt.yticks(y_values, [human_readable_size(y) for y in y_values])
    plt.ylabel(label_y)

# Retrieve all active ports from database
def fetch_all_ports(db_params):
    try:
        with psycopg2.connect(**db_params) as conn:
            with conn.cursor() as cur:
                query = "SELECT DISTINCT switchport FROM public.switchinfos WHERE ifhcinoctets > 0 OR ifhcoutoctets > 0 ORDER BY switchport ASC;"
                cur.execute(query)
                return [row[0] for row in cur.fetchall()]
    except Exception as e:
        print(f"Error: {e}")
        return []

# Visualize data for all ports
def plot_all_ports_info(db_params):
    ports = fetch_all_ports(db_params)
    if not ports:
        print("No active ports found.")
        return
    plt.figure(figsize=(14, 14))
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    color_index = 0
    for port in ports:
        data = fetch_switch_info(db_params, port)
        if not data: 
            continue  # Skip the port if no data is available

        switchport = translate_port(port)
        
        # Extracting the values of 'ifhcinoctets' and 'ifhcoutoctets' from data dictionaries
        ifhcinoctets = [d['ifhcinoctets'] for d in data]
        ifhcoutoctets = [d['ifhcoutoctets'] for d in data]
        timestamps = [d['timestamps'] for d in data]

        # Calculating the deltas for 'in' and 'out' data
        delta_in = [j - i for i, j in zip(ifhcinoctets[:-1], ifhcinoctets[1:])]
        delta_out = [j - i for i, j in zip(ifhcoutoctets[:-1], ifhcoutoctets[1:])]

        color = colors[color_index % len(colors)]  # Assign unique color for each port's data
        color_index += 1

        # Plotting the 'in' data
        plt.subplot(2, 1, 1)
        plt.plot(timestamps[1:], delta_in, 'o-', color=color, label=f'Port {switchport} In')

        # Plotting the 'out' data
        plt.subplot(2, 1, 2)
        plt.plot(timestamps[1:], delta_out, 'o-', color=color, label=f'Port {switchport} Out')

    # Formatting the x-axis for better readability
    ax = plt.gca()
    ax.xaxis.set_major_formatter(md.DateFormatter('%m-%d %H:%M:%S'))
    plt.xticks(rotation=25)

    plt.tight_layout()
    plt.legend()
    plt.show()

# Main execution point of the script
if __name__ == "__main__":
   # Switch and database configuration
    switch_address = "10.255.226.163"
    db_params = {
        'dbname': 'SwitchData',
        'user': 'postgres',
        'password': 'admin',
        'host': '127.0.0.1',
        'port': '5432'
    }

    
    choice = input("Do you want to plot data for a single port or all ports? Enter 'single' or 'all': ").lower()

    if choice == 'single':
        port_prompt = input("Enter the port in format X/X/X: ")  # Get the specific port from the user
        port = translate_prompt_to_port(port_prompt)
        if port is not None:
            plot_switch_info(fetch_switch_info(db_params, port), port)
        else:
            print("Invalid port format.")
    elif choice == 'all':
        plot_all_ports_info(db_params)
    else:
        print("Invalid choice. Please enter 'single' or 'all'.")
