import numpy as np
import time

from ModelDataExchange.clients.cyberwater.low_level_api import create_session, get_session_status, join_session, send_data, get_variable_flag, receive_data, end_session
from ModelDataExchange.data_classes import SessionData, SessionStatus, SessionID
from ModelDataExchange.cw_cpl_indices import Vars
from typing import Union, List


# Global configuration
SERVER_URL = ""
SESSION_ID = None
SERVER_URL_SET = False

def set_server_url(url: str):
    global SERVER_URL, SERVER_URL_SET
    if url.strip():
        SERVER_URL = url.strip()
        SERVER_URL_SET = True
    else:
        SERVER_URL_SET = False
        raise Exception("Error: Invalid server URL provided.")

def set_session_id(session_id: SessionID):
    global SESSION_ID
    SESSION_ID = session_id

def start_session(sd: SessionData) -> SessionID:
    """
    Starts a session with the provided session data.

    Parameters:
        sd (SessionData): The session data object containing the required information.
    
    Returns:
        SessionID: The session ID object if the session is successfully started

    Raises:
        Exception: If the server URL is not set
    """

    if not SERVER_URL_SET:
        raise Exception("Error: Server URL not set. Please set a valid server URL before starting a session.")

    return create_session(SERVER_URL, sd.source_model_id, sd.destination_model_id,
                sd.initiator_id, sd.invitee_id, sd.input_variables_id, sd.input_variables_size,
                sd.output_variables_id, sd.output_variables_size)


def retrieve_session_status(session_id: SessionID):
    if not SERVER_URL_SET:
        raise Exception("Error: Server URL not set. Please set a valid server URL before joining a session.")
    
    return get_session_status(SERVER_URL, session_id)

def join_session_with_retries(session_id: SessionID, invitee_id: int, max_retries: int, retry_delay: int):
    retries = 0

    while retries < max_retries:
        response = join_session(SERVER_URL, session_id, invitee_id)
        if response['success']:
            print("Successfully joined the session.")
            return SessionStatus.CREATED
        else:
            print(f"Failed to join the session. Error: {response['error']}")
            if "Session is already active" in response['error']:
                return SessionStatus.ERROR
            time.sleep(retry_delay)
            retries += 1
    return SessionStatus.UNKNOWN

def send_data_with_retries(var_send: int, arr_send: np.ndarray, max_retries: int, retry_delay: int) -> int:

    """
    Continuously attempts to send data until successful or until the maximum number of retries is reached.

    Parameters:
        var_send (int): The variable ID to which data will be sent.
        arr_send (np.ndarray): The data array to be sent.
        max_retries (int): Maximum number of attempts to send the data.
        retry_delay (int): Seconds to wait between retries.

    Returns:
        int: 1 for successful send, 0 for failure after all retries.
    """

    retries = 0
    while retries < max_retries:
        flag = get_variable_flag(SERVER_URL, SESSION_ID, var_send)
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
        
        time.sleep(retry_delay)  # Wait before retrying
        retries += 1  # Increment the retry count

        if retries >= max_retries:
            print(f"Failed to send data for var_id {var_send} after {max_retries} attempts due to flag status.")
            return 0  # Return 0 to indicate failure after all retries

    return 0  # Ensure a return value if the loop exits normally

def check_data_availability_with_retries(var_id, max_retries, retry_delay) -> int:
    """
    Continuously attempts to check data availability until successful or until the maximum number of retries is reached.

    Parameters:
        var_id (int): The variable ID for which data availability is checked.
        max_retries (int): Maximum number of attempts to check data availability.
        retry_delay (int): Seconds to wait between retries.

    Returns:
        int: 1 for successful availability, 0 for failure after all retries.
    """
    retries = 0
    while retries < max_retries:
        flag_status = get_variable_flag(SERVER_URL, SESSION_ID, var_id)
        if flag_status == 1:
            print(f"Data is available for session {SESSION_ID}, variable {var_id}.")
            return 1
        else:
            print(f"Data not available for session {SESSION_ID}, variable {var_id}, retrying...")
            time.sleep(retry_delay)
            retries += 1
    
    print(f"Failed to find available data for session {SESSION_ID}, variable {var_id} after {max_retries} retries.")
    return 0

def receive_data_with_retries(var_receive, max_retries, retry_delay) -> tuple[int, Union[List[float], None]]:
    """
    Continuously attempts to receive data until successful or until the maximum number of retries is reached.

    Parameters:
        var_receive (int): The variable ID for which data is expected.
        max_retries (int): Maximum number of attempts to fetch the data.
        retry_delay (int): Seconds to wait between retries.
    
    Returns:
        tuple:
            int: Status code (1 for success, 0 for failure)
            list of float or None: The received data array if successful, otherwise None.
    """
    retries = 0
    status_receive = 0  # Initialize status as 0 (failure)
    while retries < max_retries: 
        data_array = receive_data(SERVER_URL, SESSION_ID, var_receive)
        if data_array is not None:
            status_receive = 1  # Set status to 1 (success)
            print("Data received successfully.")
            return (status_receive, data_array) # type: ignore
        else:
            print("Failed to fetch data, retrying...")
            time.sleep(retry_delay)
            retries += 1

    print(f"Failed to receive data for var_id {var_receive} after {max_retries} attempts.")
    return (status_receive, None)  # Return the final status (still 0) and None for the data

def end_session_now():
    global SESSION_ID
    if not SERVER_URL_SET or SESSION_ID is None:
        print("Error: Server URL not set. Please set a valid server URL before ending a session.")
        return
    
    end_session(SERVER_URL, SESSION_ID)

if __name__ == "__main__":
   
    # server_url = "https://dataexchange.cis240199.projects.jetstream-cloud.org"
    server_url = "http://127.0.0.1:8000"

    data = SessionData(
        source_model_id=Vars.index_ELM.value,
        destination_model_id=Vars.index_VIC5.value,
        initiator_id=35,
        invitee_id=38,
        input_variables_id=[Vars.index_a2l_latitude.value, 
                            Vars.index_a2l_longitude.value, 
                            Vars.index_Sa_z.value],
        input_variables_size=[2, 3, 4],
        output_variables_id=[Vars.index_l2a_latitude.value, 
                             Vars.index_l2a_longitud.value, 
                             Vars.index_Sl_t.value],
        output_variables_size=[2, 3, 4]
    )
  
    set_server_url(server_url)

    session_id: SessionID = start_session(data)

    set_session_id(session_id)

    end_session(server_url, session_id)