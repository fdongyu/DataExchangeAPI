from src.clients.cyberwater.high_level_api import * 

import urllib3
from urllib3.exceptions import InsecureRequestWarning
import time

# Disable the warning
urllib3.disable_warnings(InsecureRequestWarning)

# Setting up the server and session parameters
set_server_url("http://0.0.0.0:8000")
session_id = [2001, 2005, 35, 38, 1]
set_session_id(session_id)
session_data = SessionData(
    source_model_id=2001,
    destination_model_id=2005,
    initiator_id=35,
    invitee_id=38,
    input_variables_id=[1],
    input_variables_size=[50],
    output_variables_id=[4],
    output_variables_size=[50]
)

# Start the session
start_session(session_data)

# Define the number of iterations
num_iterations = 2

for iteration in range(1, num_iterations + 1):
    print(f"Iteration: {iteration}")
    
    # Send data
    arr_send = [1] * 50  # Example data to send
    status_send = send_data_with_retries(1, arr_send, 5, 5)
    print(f"Status of send operation: {status_send}")
    time.sleep(10)

    # Check data availability and receive data
    flag_status = check_data_availability_with_retries(var_id=4, max_retries=5, retry_delay=5)
    if flag_status == 1:
        status_receive, received_data = receive_data_with_retries(var_receive=4, max_retries=5, retry_delay=5)
        if status_receive == 1:
            print("Data received successfully:", received_data)
        else:
            print("Data reception failed after all retries.")
    else:
        print("Data not available after retries.")

    print("------ Sleeping for 10 seconds ------")
    time.sleep(10)

# End the session
end_session_now(35)

# Optionally, check session status or handle other session-specific logic here as needed
