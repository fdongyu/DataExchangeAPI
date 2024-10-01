from src.clients.cyberwater.high_level_api import * 

import urllib3
from urllib3.exceptions import InsecureRequestWarning

# Disable the warning
urllib3.disable_warnings(InsecureRequestWarning)

# Usage of the module functions
set_server_url("http://0.0.0.0:8000")
session_id = [2001,2005,35,38,1]
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
start_session(session_data)

# # Check the session status first
session_status = retrieve_session_status(session_id)

if session_status is None:
    print("Failed to get session status.")
elif session_status == 1:
    print("Session status is 'created'")
    join_status = join_session_with_retries(session_id, invitee_id=38, max_retries=5, retry_delay=5)
    if join_status == 0:
        print("Not able to join properly.")
    elif join_status == 1:
        print("Joined the session successfully.")
elif session_status == 2:
    print("Session status is 'active'")
elif session_status == 3:
    print("Session status is 'partial end'")
else:
    print(f"Current status of session: {session_status}")

print("------ Sleeping for 10 seconds ------")
time.sleep(10)
arr_send = [1]*50
status_send = send_data_with_retries(1, arr_send, 5, 5)
print(f"Status of send operation: {status_send}")
print("------ Sleeping for 10 seconds ------")
time.sleep(10)

flag_status = check_data_availability_with_retries(var_id=4, max_retries=5, retry_delay=5)
if flag_status == 1:
    status_receive, received_data = receive_data_with_retries(var_receive=4, max_retries = 5, retry_delay = 5)
    if status_receive ==1:
        print("Data Received Sucessfully")
    else:
        print("Data reception failed after all retries.")
else:
    print("Data not available after retries.")
print("------ Sleeping for 10 seconds ------")
time.sleep(10)

# End session using intiator_id, when session is started Cyberwater
end_session_now(35)

# End session using invitee_id, when session is joined by Cyberwater
# end_session_now(38)