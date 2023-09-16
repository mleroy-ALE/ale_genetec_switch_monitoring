from pathlib import Path
import psycopg2
from psycopg2 import sql
import matplotlib.pyplot as plt


def translate_prompt_to_port(portprompt):
    try:
        module, submodule, port_number = map(int, portprompt.split('/'))
        return (module * 1000) + port_number
    except ValueError:
        print("Invalid port format. Please enter in the format X/X/X.")
        return None

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
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

    return result

def human_readable_size(size):
    units = ["B", "KB", "MB", "GB", "TB"]
    for unit in units:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

def translate_port(port):
    module_number = port // 1000
    port_number = port % 1000
    return f"{module_number}/1/{port_number}"

def plot_switch_info(data, port):
    switchport = translate_port(port)

    ifhcinoctets = [d['ifhcinoctets'] for d in data]
    ifhcoutoctets = [d['ifhcoutoctets'] for d in data]
    timestamps = [d['timestamps'] for d in data]

    plt.figure(figsize=(14, 6))

    plt.subplot(2, 1, 1)
    plt.plot(timestamps, ifhcinoctets, marker='o', linestyle='-', color='b')
    plt.title(f'Switch Info for Port {switchport}')
    plt.xlabel('Timestamps')
    plt.ylabel('Received Octets')
    plt.yticks([y for y in plt.yticks()[0]], [human_readable_size(y) for y in plt.yticks()[0]])


    plt.subplot(2, 1, 2)
    plt.plot(timestamps, ifhcoutoctets, marker='o', linestyle='-', color='r')
    plt.xlabel('Timestamps')
    plt.ylabel('Transmitted Octets')
    plt.yticks([y for y in plt.yticks()[0]], [human_readable_size(y) for y in plt.yticks()[0]])


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

    for port in ports:
        data = fetch_switch_info(db_params, port)
        ifhcinoctets = [d['ifhcinoctets'] for d in data]
        ifhcoutoctets = [d['ifhcoutoctets'] for d in data]
        timestamps = [d['timestamps'] for d in data]

        # Ignore ports with all zero data
        if all(v == 0 for v in ifhcinoctets) and all(v == 0 for v in ifhcoutoctets):
            continue

        plt.subplot(2, 1, 1)
        plt.plot(timestamps, ifhcinoctets, marker='o',
                 linestyle='-', label=f'Port {port} In')

        plt.subplot(2, 1, 2)
        plt.plot(timestamps, ifhcoutoctets, marker='o',
                 linestyle='-', label=f'Port {port} Out')

    plt.subplot(2, 1, 1)
    plt.title('Switch Info for All Ports (In)')
    plt.xlabel('Timestamps')
    plt.ylabel('Received Octets')
    plt.legend()

    plt.subplot(2, 1, 2)
    plt.title('Switch Info for All Ports (Out)')
    plt.xlabel('Timestamps')
    plt.ylabel('Transmitted Octets')
    plt.legend()

    plt.tight_layout()
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

    plot_switch_info(fetch_switch_info(db_params, port), port)
    #plot_all_ports_info(db_params)
