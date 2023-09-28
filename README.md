# ReadMe for Switch Fetch and Switch Plot Scripts

## Introduction

The `SwitchDataMonitoringFetch` and `SwitchDataMonitoringPlot` scripts are tailored to facilitate real-time data fetching and visualization from a network switch. These scripts are designed to work in unison - `SwitchDataMonitoringFetch` handles the data retrieval and storage from the switch, while `SwitchDataMonitoringPlot` is responsible for visualizing this data, providing insights into the switch’s performance and data traffic.

### 1. `SwitchDataMonitoringFetch`

#### Objective

The primary goal of the `SwitchDataMonitoringFetch` script is to automate the process of fetching real-time data from a network switch. It retrieves data such as the volume of data transmitted and received, authenticates requests, and stores the fetched data into a PostgreSQL database for persistent storage and future analysis.

#### Key Features

- **Authentication**: The script is capable of authenticating requests to ensure secure and authorized data retrieval.
- **Real-Time Data Fetching**: It continuously retrieves real-time data from the switch at regular intervals, ensuring the data is up-to-date.
- **Database Storage**: The fetched data is stored in a PostgreSQL database, ensuring data persistence and enabling detailed analysis over time.
- **Error Handling**: The script is equipped with error handling mechanisms to deal with authentication failures and data retrieval errors, ensuring continuous and uninterrupted operation.

#### Usage

The script requires the user to have certain environment variables set up, such as the switch’s address and authentication credentials. The user can also customize the database parameters as per the specific PostgreSQL setup.

### 2. `SwitchDataMonitoringPlot`

#### Objective

The `SwitchDataMonitoringPlot` script complements `SwitchDataMonitoringFetch` by visualizing the data stored in the PostgreSQL database. It provides graphical representations of the data traffic through various ports of the switch, offering insights into patterns, volumes, and potential issues in real-time.

#### Key Features

- **Data Retrieval**: It fetches the stored data from the PostgreSQL database, ensuring real-time visualizations are based on the most recent data.
- **Custom Visualizations**: Users can visualize data for a specific port or all active ports, offering flexibility in analysis.
- **Human-Readable Format**: The data is plotted in human-readable formats, with bytes converted to appropriate units for ease of understanding.
- **Data Plotting**: Utilizing Matplotlib, the script plots the in-octets and out-octets data, offering a visual representation of the data traffic through the switch ports.

#### Usage

The script prompts the user to choose between visualizing data for a single port or all active ports. It then retrieves the relevant data from the database and plots it, displaying data volumes against timestamps for detailed temporal analysis.

## Requirements

- Python 3.x
- PostgreSQL
- Required Python libraries: `psycopg2`, `matplotlib`, `pandas`, `json`, `requests`, `os`, `time`, `dotenv`

## Setup

1. Ensure that Python and PostgreSQL are installed on your machine.
2. Clone the repository or download the `SwitchDataMonitoringFetch` and `SwitchDataMonitoringPlot` scripts.
3. Install the required Python libraries using `pip install -r requirements.txt` (you need to create a requirements.txt file with all required libraries).
4. Set up the environment variables in a `.env` file located in the root directory of the scripts. Include the database credentials and switch address.

## Execution

### switchFetch

Execute the `SwitchDataMonitoringFetch` script to start fetching data from the network switch and storing it in the PostgreSQL database. It runs in a loop, continuously updating the database with the latest data.

```bash
python SwitchDataMonitoringFetch.py
```

### switchPlot

Run the `SwitchDataMonitoringPlot` script to visualize the stored data. The script offers options to display data for a single port or all active ports.

```bash
python SwitchDataMonitoringPlot.py
```

Follow the on-screen prompts to select your preferred option for data visualization.

## Conclusion

The combination of `SwitchDataMonitoringFetch` and `SwitchDataMonitoringPlot` scripts provides a comprehensive solution for real-time data retrieval, storage, and visualization from network switches. By utilizing these scripts, network administrators and analysts can gain valuable insights into data traffic patterns, enabling informed decision-making and efficient network management.
