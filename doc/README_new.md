# Testing Procedure for Data Exchange Service

This document describes the procedure to test the integration of the E3SM and Cyberwater clients with the Exchange Server. Follow these steps to ensure each component functions correctly in your environment.

## Prerequisites
Ensure that Python and Fortran are correctly installed on your system and that all necessary libraries are available.

## Step 1: Start the Exchange Server

Navigate to the directory containing the server code and start the exchange server. This will facilitate the data exchange between the E3SM and Cyberwater clients.

```bash
cd ~/Final_Data_Exchange_Service_Code1/src/server
python exchange_server.py
```

Make sure the server is running and listening on the default port `8000` or adjust accordingly in the client configurations if it's running on a different port.

## Step 2: Compile and Test the E3SM Client

Before running the E3SM client, ensure that it is compiled:

```bash
cd ~/Final_Data_Exchange_Service_Code1/tests/ex1/e3sm
make clean
make
```

If the compilation is successful, run the E3SM test executable:

```bash
./e3sm_test
```

## Step 3: Test the Cyberwater Client

If not already set in your environment, configure the `PYTHONPATH` to recognize custom modules:

```bash
export PYTHONPATH=~/Final_Data_Exchange_Service_Code1/src:$PYTHONPATH
```

Navigate to the Cyberwater test directory and execute the Python script:

```bash
cd ~/Final_Data_Exchange_Service_Code1/tests/ex1/cyberwater
python cyberwater_test.py
```
