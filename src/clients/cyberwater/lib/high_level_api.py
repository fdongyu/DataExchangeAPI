import ctypes
from dataclasses import dataclass
import numpy as np
import time
from typing import List

# Assuming there is an external module named http_interface that provides required HTTP functionalities
from .low_level_api import *

# Global configuration
SERVER_URL = ""
SESSION_ID = [0]*5
SERVER_URL_SET = False


@dataclass
class SessionData:
    source_model_id: int
    destination_model_id: int
    initiator_id: int
    invitee_id: int
    input_variables_id: List[int]
    input_variables_size: List[int]
    output_variables_id: List[int]
    output_variables_size: List[int]

class EndSessionData:
    session_id: str
    user_id: int

def set_server_url(url: str):
    global SERVER_URL, SERVER_URL_SET
    if url.strip():
        SERVER_URL = url.strip()
        SERVER_URL_SET = True
    else:
        print("Error: Invalid server URL provided.")
        SERVER_URL_SET = False

def set_session_id(ids: List[int]):
    global SESSION_ID
    if len(ids) == 5:
        # Convert list of integers to a comma-separated string
        SESSION_ID = ','.join(map(str, ids))
        print(SESSION_ID)
    else:
        print("Error: Invalid session ID array size.")


def start_session(sd: SessionData):
    if not SERVER_URL_SET:
        print("Error: Server URL not set. Please set a valid server URL before starting a session.")
        return

    create_session(SERVER_URL, sd.source_model_id, sd.destination_model_id,
                sd.initiator_id, sd.invitee_id, sd.input_variables_id, sd.input_variables_size,
                sd.output_variables_id, sd.output_variables_size)

def retrieve_specific_session_status(session_id):
    if not SERVER_URL_SET:
        print("Error: Server URL not set. Please set a valid server URL before joining a session.")
        return
    
    session_id = ','.join(map(str, session_id))
    return(get_specific_session_status(SERVER_URL, session_id))

def join_session_with_retries(session_id, invitee_id, max_retries, sleep_time):
    retries = 0
    session_id = ','.join(map(str, session_id))
    while retries < max_retries:
        response = join_session(SERVER_URL, session_id, invitee_id)
        if response['success']:
            print("Successfully joined the session.")
            return 1
        else:
            print(f"Failed to join the session. Error: {response['error']}")
            if "Session is already active" in response['error']:
                return 0
            time.sleep(sleep_time)
            retries += 1
    return 0

def send_data_with_retries(var_send: int, arr_send: np.ndarray, max_retries: int, sleep_time: int):
    retries = 0
    while retries < max_retries:
        flag = get_specific_variable_flag(SERVER_URL, SESSION_ID, var_send)
        print(f"Flag status: {flag}")

        if flag == 0:  # Check if the flag indicates readiness to send
            response = send_data(SERVER_URL, SESSION_ID, var_send, arr_send)
            if response.ok:  # Check if the data was sent successfully
                print("Data successfully sent.")
                return 1  # Return 1 to indicate successful send
            else:
                print("Failed to send data, error:", response.text)
                # Decide whether to break or continue depending on your application's requirements
                break
        else:
            print("Flag is not set for sending, retrying...")
        
        time.sleep(sleep_time)  # Wait before retrying
        retries += 1  # Increment the retry count

        if retries >= max_retries:
            print(f"Failed to send data for var_id {var_send} after {max_retries} attempts due to flag status.")
            return 0  # Return 0 to indicate failure after all retries

    return 0  # Ensure a return value if the loop exits normally

def check_data_availability_with_retries(var_id, max_retries, sleep_time):
    retries = 0
    while retries < max_retries:
        flag_status = get_specific_variable_flag(SERVER_URL, SESSION_ID, var_id)
        if flag_status == 1:
            print(f"Data is available for session {SESSION_ID}, variable {var_id}.")
            return 1
        else:
            print(f"Data not available for session {SESSION_ID}, variable {var_id}, retrying...")
            time.sleep(sleep_time)
            retries += 1
    
    print(f"Failed to find available data for session {SESSION_ID}, variable {var_id} after {max_retries} retries.")
    return 0

def receive_data_with_retries(var_receive, max_retries, sleep_time):
    """
    Continuously attempts to receive data until successful or until the maximum number of retries is reached.

    Parameters:
        server_url (str): The server URL.
        session_id (str): The session ID.
        var_receive (int): The variable ID for which data is expected.
        max_retries (int): Maximum number of attempts to fetch the data.
        sleep_time (int): Seconds to wait between retries.
    
    Returns:
        list of float: The received data array, or None if failed to receive after all retries.
    """
    retries = 0
    while retries < max_retries:
        data_array = receive_data(SERVER_URL, SESSION_ID, var_receive)
        if data_array is not None:
            print("Data received successfully.")
            return data_array
        else:
            print("Failed to fetch data, retrying...")
            time.sleep(sleep_time)
            retries += 1

    print(f"Failed to receive data for var_id {var_receive} after {max_retries} attempts.")
    return None


def end_session_now(user_id: int):
    if not SERVER_URL_SET:
        print("Error: Server URL not set. Please set a valid server URL before ending a session.")
        return
        
    end_session(SERVER_URL, SESSION_ID, user_id)



# Unused/ Extra High level endpoints provided for interacting with the server

# def join_session(invitee_id):
#     if not SERVER_URL_SET:
#         print("Error: Server URL not set. Please set a valid server URL before joining a session.")
#         return

#     join_session(SERVER_URL, SESSION_ID, invitee_id)


# def check_all_session_availability():
#     if not SERVER_URL_SET:
#         print("Error: Server URL not set. Please set a valid server URL before checking session statuses.")
#         return

#     print_all_session_statuses(SERVER_URL)


# def check_specific_session_variable_flags(session_id: List[int]):
#     if not SERVER_URL_SET:
#         print("Error: Server URL not set. Please set a valid server URL before checking variable flags.")
#         return

#     if len(session_id) != 5:
#         print("Error: Invalid session ID array size.")
#         return

#     print_all_variable_flags(SERVER_URL, session_id)


# def get_specific_variable_size(session_ids: List[int], var_id: int):
#     if not SERVER_URL_SET:
#         print("Error: Server URL not set. Please set a valid server URL before retrieving variable sizes.")
#         return

#     var_size = get_variable_size(SERVER_URL, session_ids, var_id)
#     if var_size < 0:
#         print(f"Error: Unable to get variable size for ID {var_id}")
#         return -1  # Indicating an error
#     return var_size  # Indicating success


