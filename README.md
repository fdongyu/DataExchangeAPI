# Data Exchange Service for Computational Model Integrations between different platforms

This repository contains the codebase for a data exchange service designed to facilitate communication between the Earth System Model (E3SM) and the Cyberwater client. It also includes a Python-based middleman server to manage the data exchange.

## E3SM Client Requirements

To set up the E3SM Client, ensure the following requirements are met:

- **GCC version:** gcc (SUSE Linux) 12.3.0
- **Gfortran version:** GNU Fortran 12.3.0
- **Standard C libraries:** `stdio.h`, `stdlib.h`, `string.h`

## Installation for E3SM Client

1. Install the `libcurl` library required for the C wrapper code (`http_impl.c`):
   ```bash
   curl -O https://curl.se/download/curl-7.79.1.tar.gz
   tar -xzvf curl-7.79.1.tar.gz
   cd curl-7.79.1
   ./configure --prefix=/home/your_username/local
   make
   make install
   ```
2. Update your environment variables to include the path to `libcurl`:
 ```bash
  export PATH="/home/your_username/local/bin:$PATH"
  export LD_LIBRARY_PATH="/home/your_username/local/lib:$LD_LIBRARY_PATH"
  export PKG_CONFIG_PATH="/home/your_username/local/lib/pkgconfig:$PKG_CONFIG_PATH"
  ```
3. Confirm the installation of 'curl` by checking its version:
   ```
   curl --version
   ```
## Data Exchange Service Requirements

Ensure the following requirements are met for the Data Exchange Service:

- **Python version:** 3.9.13.1
- **FastAPI:** 0.110.1
- **Uvicorn:** 0.29.0
- **Pydantic:** 2.7.0

## Installation for Data Exchange Service

1. (Optional) Create a virtual environment to isolate the package dependencies:
   ```bash
   python3 -m venv exchange_env
   source exchange_env/bin/activate
   ```
2. Install the necessary Python libraries as specified:
  ```bash
  pip install fastapi==0.110.1 uvicorn==0.29.0 pydantic==2.7.0
  ```
## Cyberwater Client Requirements

The Cyberwater client requires the same Python version as the Data Exchange Service:

- **Python version:** 3.9.13.1

# After Installation on respective remote machines, Steps to Test the System.

To validate the functionality of the data exchange system, you need to test the server, the Cyberwater client, and the E3SM client as follows:

## Testing the Data Exchange Server

Navigate to the directory containing `exchange_server.py`. Start the server by running the following command:

```bash
  python exchange_server.py
```
This will start the server on your local machine, listening on port 8000. (default, you can change it according to the client requirements).

## Testing the Cyberwater Client
Perform the following steps on the remote machine set up as the Cyberwater client:
1. Check and ensure that cyberwater_library.py and cyberwater_test.py are in the current directory.
2. Verify that the server_url and port variables in cyberwater_test.py match the server's address and port.
3. Depending on the role you wish to take in the data exchange process:
- If initiating a new session, ensure the create_session call in cyberwater_test.py is uncommented.
- If joining an existing session, comment out the create_session call and uncomment the join_session call.

To run the Cyberwater client, execute:
```bash
python cyberwater_test.py
```

This will initiate or join a session and start the data exchange process.

## Testing the E3SM Client
Follow these steps on a different remote machine intended as the E3SM client:

1. Ensure the `data_exchange_lib` directory contains `http_impl.c`, `http_interface.f90`, and `data_exchange.f90`.
2. The parent directory should contain `e3sm_test.f90` and the Makefile.

Compile the E3SM client code with the following commands:
```bash
make clean
make
```
After compilation, run the E3SM client:
```bash
./e3sm_test
```
This will execute the compiled binary and engage in the data exchange process with the server and the Cyberwater client.

## Session Management
Both clients will interact with the data exchange server, which handles sessions, flags, and data transmission. Use the following endpoints to manage and monitor sessions:

- `/create_session/{client_id}`: Initiates a new session.
- `/join_session`: Joins an existing session.
- `/list_sessions`: Lists all current sessions and their statuses.
- `/get_flags`: Retrieves the flag status of all variables in a session.
- `/get_variable_flag`: Gets the flag status for a specific variable.
- `/get_variable_size`: Fetches the size of a specific variable.
- `/send_data`: Sends binary data for a specific variable.
- `/receive_data`: Receives binary data for a specific variable.
- `/end_session`: Ends a session.


