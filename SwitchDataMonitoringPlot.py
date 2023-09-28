import psycopg2
import matplotlib.pyplot as plt
import matplotlib.dates as md
import os
from dotenv import load_dotenv
from psycopg2 import sql
from matplotlib.ticker import MaxNLocator
from pathlib import Path


# Load environment variables from a file
load_dotenv(dotenv_path=Path('./.env'))

# Function to convert user input into numerical port value
def translate_prompt_to_port(portprompt):
    try:
        # Convert the user's port input into numerical value
        module, submodule, port_number = map(int, portprompt.split('/'))
        return (module * 1000) + port_number
    except ValueError:
        print("Invalid port format. Please enter in format X/X/X.")
        return None

# Function to retrieve switch information from the database
def fetch_switch_info(db_params, port):
    result = []
    try:
        # Connect to the database and execute the query
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        query = """
            SELECT ifhcinoctets, ifhcoutoctets, timestamps FROM public.switchinfos
            WHERE switchport = %s ORDER BY rowid ASC;
        """
        cur.execute(query, (port,))
        rows = cur.fetchall()

        # Store the fetched data in a dictionary
        for row in rows:
            result.append({
                'ifhcinoctets': row[0],
                'ifhcoutoctets': row[1],
                'timestamps': row[2]
            })
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close database connections
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()
    return result

# Function to convert byte values to human-readable format
def human_readable_size(size):
    # Convert bytes to KB, MB, GB, etc. based on size
    units = ["B", "KB", "MB", "GB", "TB"]
    for unit in units:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

# Function to translate numerical port value to user-friendly format
def translate_port(port):
    # Convert numerical port value to X/X/X format
    module_number = port // 1000
    port_number = port % 1000
    return f"{module_number}/1/{port_number}"

# Function to plot inbound and outbound data for specified port
def plot_switch_info(data, port):
    switchport = translate_port(port)
    # Extract data for plotting
    ifhcinoctets = [d['ifhcinoctets'] for d in data]
    ifhcoutoctets = [d['ifhcoutoctets'] for d in data]
    timestamps = [d['timestamps'] for d in data]

    # Calculate the deltas for the in and out octets
    delta_in = [j - i for i, j in zip(ifhcinoctets[:-1], ifhcinoctets[1:])]
    delta_out = [j - i for i, j in zip(ifhcoutoctets[:-1], ifhcoutoctets[1:])]
    delta_timestamps = timestamps[1:]

    plt.figure(figsize=(14, 6))

    # Draw the inbound and outbound plots
    draw_plot("Timestamps", "Received", f'Switch Info for Port {switchport} (Inbound)', delta_timestamps, delta_in, 1, 'b')
    draw_plot("Timestamps", "Transmitted", f'Switch Info for Port {switchport} (Outbound)', delta_timestamps, delta_out, 2, 'r')
    plt.tight_layout()
    plt.show()

# Utility function to draw plots
def draw_plot(label_x, label_y, plot_name, points_x, points_y, plot_number, plot_color):
    x_axis = plt.subplot(2, 1, plot_number)
    xfmt = md.DateFormatter('%m-%d %H:%M:%S')
    x_axis.xaxis.set_major_formatter(xfmt)

    # Plot the data points
    plt.plot(points_x, points_y, marker='o', linestyle='-', color=plot_color)
    plt.title(plot_name)
    plt.xlabel(label_x)
    y_values = plt.yticks()[0]
    y_values = [y for y in y_values if y >= 0]  # Exclude negative values for a clear plot
    plt.yticks(y_values, [human_readable_size(y) for y in y_values])
    plt.ylabel(label_y)

# Function to retrieve all active ports from the database
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

# Function to visualize data for all ports
def plot_all_ports_info(db_params):
    # Fetch the list of all active ports
    ports = fetch_all_ports(db_params)
    if not ports:
        print("No active ports found.")
        return
    
    plt.figure(figsize=(14, 14))
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    color_index = 0
    
    ax1 = plt.subplot(2, 1, 1)  # Create a subplot for inbound data
    ax2 = plt.subplot(2, 1, 2)  # Create another subplot for outbound data

    for port in ports:
        data = fetch_switch_info(db_params, port)
        if not data:
            continue  # Skip if no data is available for the port

        # Fetch and plot data for each port
        switchport = translate_port(port)
        ifhcinoctets = [d['ifhcinoctets'] for d in data]
        ifhcoutoctets = [d['ifhcoutoctets'] for d in data]
        timestamps = [d['timestamps'] for d in data]
        delta_in = [j - i for i, j in zip(ifhcinoctets[:-1], ifhcinoctets[1:])]
        delta_out = [j - i for i, j in zip(ifhcoutoctets[:-1], ifhcoutoctets[1:])]

        color = colors[color_index % len(colors)]  # Cycle through colors for each port
        color_index += 1

        ax1.plot(timestamps[1:], delta_in, 'o-', color=color, label=f'Port {switchport} In')
        ax2.plot(timestamps[1:], delta_out, 'o-', color=color, label=f'Port {switchport} Out')

    # Set titles and labels for the plots
    ax1.set_title("Data Received for All Ports")
    ax1.set_xlabel("Timestamps")
    ax1.set_ylabel("Volume of Data Received")
    ax1.xaxis.set_major_formatter(md.DateFormatter('%m-%d %H:%M:%S'))
    ax2.set_title("Data Transmitted for All Ports")
    ax2.set_xlabel("Timestamps")
    ax2.set_ylabel("Volume of Data Transmitted")
    ax2.xaxis.set_major_formatter(md.DateFormatter('%m-%d %H:%M:%S'))

    plt.xticks(rotation=25)
    plt.tight_layout()
    ax1.legend()  # Add legend for the first plot
    ax2.legend()  # Add legend for the second plot
    plt.show()

# Main execution point for user input and plotting
if __name__ == "__main__":
    switch_address = "10.255.226.163"
    db_params = {
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT')
    }
    
    # Choose whether to plot for a single port or all ports
    choice = input("Do you want to plot data for a single port or all ports? Enter 'single' or 'all': ").lower()

    if choice == 'single':
        port_prompt = input("Enter the port in format X/X/X: ")  # Get port from user
        port = translate_prompt_to_port(port_prompt)
        if port is not None:
            plot_switch_info(fetch_switch_info(db_params, port), port)
        else:
            print("Invalid port format.")
    elif choice == 'all':
        plot_all_ports_info(db_params)
    else:
        print("Invalid choice. Please enter 'single' or 'all'.")
