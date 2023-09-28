# Switch Data Monitoring Plot

## Description

Switch Data Monitoring Plot is a Python script designed to visualize and analyze network switch data. The script provides graphical representations of incoming and outgoing data volumes for each switch port on a given network, in real-time. Users have the flexibility to visualize data from a single port or from all active ports simultaneously.

## Features

- **Port Prompt Translation**: Translates user prompts into numerical port values.
- **Switch Info Retrieval**: Extracts switch data from a PostgreSQL database.
- **Human-Readable Size**: Converts byte values into a human-readable format.
- **Data Visualization**: Plots switch information including inbound and outbound bytes with time stamps.
- **Multi-port Support**: Enables data visualization for all active ports.

## Dependencies

The script relies on several Python libraries, including `psycopg2` for interacting with the PostgreSQL database and `matplotlib` for data visualization. Ensure to install these dependencies using `pip`:

```bash
pip install psycopg2-binary matplotlib numpy
```

## Usage

### Database Configuration

Ensure your database settings are correctly configured in the `db_params` dictionary:

```python
db_params = {
    'dbname': 'YourDatabaseName',
    'user': 'YourUsername',
    'password': 'YourPassword',
    'host': 'YourHost',
    'port': 'YourPort'
}
```

### Running the Script

Execute the script using Python 3. Be prepared to respond to the prompt asking whether you want to plot data for a single port or all ports:

```bash
python SwitchDataMonitoringPlot.py
```

### Execution Options

The script will prompt you whether you want to view data for a single port or all ports. Input `single` for a single port and `all` for all ports.

### Visualization

Upon execution, a window will pop up displaying the generated plot. Inbound and outbound data are plotted on separate subplots for clear and concise analysis.

