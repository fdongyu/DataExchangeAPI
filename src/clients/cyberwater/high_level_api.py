import asyncio
import numpy as np

from ModelDataExchange.clients.cyberwater.low_level_api import create_session, get_session_status, join_session, send_data, get_variable_flag, receive_data, end_session, call_delay
from ModelDataExchange.data_classes import SessionData, SessionStatus, SessionID, JoinSessionData
from ModelDataExchange.cw_cpl_indices import Vars
from typing import Union, List




# Global configuration
SERVER_URL = ""
SESSION_ID = None
SERVER_URL_SET = False

def set_server_url(url: str):

    """
    Sets the server URL for the current session.

    Used for `high_level_api` commands that require a server URL.

    Parameters:
        url (str): The server URL to set.
    """

    global SERVER_URL, SERVER_URL_SET
    if url.strip():
        SERVER_URL = url.strip()
        SERVER_URL_SET = True
    else:
        SERVER_URL_SET = False
        raise Exception("Error: Invalid server URL provided.")


def set_session_id(session_id: SessionID):
    """
    Sets the session ID for the current session.

    Used for `high_level_api` commands that require a session ID.

    Parameters:
        session_id (SessionID): The session ID to set.
    """

    global SESSION_ID
    SESSION_ID = session_id


def start_session(sd: SessionData) -> SessionID:
    """
    Starts a session with the provided session data. 

    Note:
        The server URL must be set using `set_server_url` before starting a session.

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
    """
    Retrieves the status of the session with the provided session ID.

    The status of the session can be:
    - `SessionStatus.ERROR`
    - `SessionStatus.UNKNOWN`
    - `SessionStatus.CREATED`
    - `SessionStatus.ACTIVE`
    - `SessionStatus.PARTIAL_END`
    - `SessionStatus.END`

    Parameters:
        session_id (SessionID): The session ID to retrieve the status for.
    """

    if not SERVER_URL_SET:
        raise Exception("Error: Server URL not set. Please set a valid server URL before joining a session.")
    
    return get_session_status(SERVER_URL, session_id)


def join_session_with_retries(session_id: SessionID, invitee_id: int, max_retries: int, retry_delay: float):
    """
    Continuously attempts to join a session until successful or until the maximum number of retries is reached.
    
    Session must be created and have a SessionStatus == SessionStatus.CREATED. i.e. no other 
    invitee has joined the session.

    Parameters:
        session_id (SessionID): The session ID to join.
        invitee_id     (int): The ID of the invitee.
        max_retries    (int): Maximum number of attempts to join the session.
        retry_delay  (float): Seconds to wait between retries.

    Returns:
        SessionStatus: The status of the session after joining.
    
    
    """
    retries = 0

    while retries < max_retries:
        response = join_session(SERVER_URL, session_id, invitee_id)
        if response['success']:
            print("Successfully joined the session.")
            return SessionStatus.CREATED
        else:
            print(f"Failed to join the session. Error: {response['error']}. Retrying... ({retries}/{max_retries})")
            if "Session is already active" in response['error']:
                return SessionStatus.ERROR
            asyncio.run(call_delay(retry_delay))
            retries += 1
    return SessionStatus.UNKNOWN

def send_data_with_retries(var_send: int, arr_send: np.ndarray, max_retries: int, retry_delay: float, delay: float = 0) -> int:

    """
    Continuously attempts to send data until successful or until the maximum number of retries is reached.

    Parameters:
        var_send        (int): The variable ID to which data will be sent.
        arr_send (np.ndarray): The data array to be sent.
        max_retries     (int): Maximum number of attempts to send the data.
        retry_delay   (float): Seconds to wait between retries.
        delay         (float): Seconds to wait before sending data to server. Default is 0.

    Returns:
        int: 1 for successful send, 0 for failure after all retries.
    """

    retries = 0
    while retries < max_retries:
        flag = get_variable_flag(SERVER_URL, SESSION_ID, var_send) # type: ignore
        print(f"Flag status: {flag}")

        if flag == 0:  # Check if the flag indicates readiness to send
            response = send_data(SERVER_URL, SESSION_ID, var_send, arr_send, delay) # type: ignore
            if response.ok:  # Check if the data was sent successfully
                print("Data successfully sent.")
                return 1  # Return 1 to indicate successful send
            else:
                print("Failed to send data, error:", response.text)
                # Decide whether to break or continue depending on your application's requirements
                break
        else:
            print(f"Flag is not set for sending, retrying... ({retries}/{max_retries})")
        
        asyncio.run(call_delay(retry_delay))  # Wait before retrying
        retries += 1  # Increment the retry count

        if retries >= max_retries:
            print(f"Failed to send data for var_id {var_send} after {max_retries} attempts due to flag status.")
            return 0  # Return 0 to indicate failure after all retries

    return 0  # Ensure a return value if the loop exits normally

def check_data_availability_with_retries(var_id: int, max_retries: int, retry_delay: float) -> int:
    """
    Continuously attempts to check data availability until successful or until the maximum number of retries is reached.

    Parameters:
        var_id        (int): The variable ID for which data availability is checked.
        max_retries   (int): Maximum number of attempts to check data availability.
        retry_delay (float): Seconds to wait between retries.

    Returns:
        int: 1 for successful availability, 0 for failure after all retries.
    """
    retries = 0
    while retries < max_retries:
        flag_status = get_variable_flag(SERVER_URL, SESSION_ID, var_id) # type: ignore
        if flag_status == 1:
            print(f"Data is available for session {SESSION_ID}, variable {var_id}.")
            return 1
        else:
            print(f"Data not available for session {SESSION_ID}, variable {var_id}, retrying... ({retries}/{max_retries})")
            asyncio.run(call_delay(retry_delay))
            retries += 1
    
    print(f"Failed to find available data for session {SESSION_ID}, variable {var_id} after {max_retries} retries.")
    return 0


def receive_data_with_retries(var_receive: int, max_retries: int, retry_delay: float, delay: float = 0) -> tuple[int, Union[List[float], None]]:
    """
    Continuously attempts to receive data until successful or until the maximum number of retries is reached.

    Parameters:
        var_receive  (int): The variable ID for which data is expected.
        max_retries  (int): Maximum number of attempts to fetch the data.
        retry_delay (float): Seconds to wait between retries.
        delay       (float): Seconds to wait before server sends data. Default is 0.
    
    Returns:
        tuple:
            int: Status code (1 for success, 0 for failure)
            list of float or None: The received data array if successful, otherwise None.
    """
    retries = 0
    status_receive = 0  # Initialize status as 0 (failure)
    while retries < max_retries: 
        flag = get_variable_flag(SERVER_URL, SESSION_ID, var_receive) # type: ignore
        if flag:
            data_array = receive_data(SERVER_URL, SESSION_ID, var_receive, delay) # type: ignore
            if data_array is tuple[float]:  # Check if data was received successfully
                status_receive = 1  # Set status to 1 (success)
                print(f"Data for var_id [{var_receive}] received successfully.")
                return (status_receive, data_array) # type: ignore
            else:
                raise Exception("Error: Flag shows data is available, but failed to fetch data.")
        else:
            print(f"Failed to fetch data for var_id [{var_receive}], retrying... ({retries}/{max_retries})")
            asyncio.run(call_delay(retry_delay))
            retries += 1

    print(f"Failed to receive data for var_id [{var_receive}] after [{max_retries}] attempts.")
    return (status_receive, None)  # Return the final status (still 0) and None for the data

def end_session_now():
    """
    Ends the current session immediately.

    Note:
        The server URL must be set using `set_server_url` before ending a session.
    """

    global SESSION_ID
    if not SERVER_URL_SET or SESSION_ID is None:
        print("Error: Server URL not set. Please set a valid server URL before ending a session.")
        return
    
    end_session(SERVER_URL, SESSION_ID)


if __name__ == "__main__":

    server_url = "https://dataexchange.cis240199.projects.jetstream-cloud.org"
    # server_url = "http://127.0.0.1:8000"

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
    print("Server URL:", server_url)

    set_server_url(server_url)
    session_id: SessionID = start_session(data)
    set_session_id(session_id)
    print("Session ID:", session_id)
    print("Session ID JSON:", session_id.model_dump())
    print("Session status:", retrieve_session_status(session_id))
    # "{'source_model_id': 2001, 'destination_model_id': 2005, 'initiator_id': 35, 'invitee_id': 38, 'client_id': '931204ec-664d-4b4d-a343-b453ba573323'}"
     # {'source_model_id': 2002, 'destination_model_id': 2005, 'initiator_id': 35, 'invitee_id': 38, 'client_id': '51dc5fe7-dc9d-4f50-9462-1fc2e1c4c2cd'}
    print(JoinSessionData(session_id=session_id, invitee_id=38).model_dump())
    join_session(server_url, session_id, 38)

    # send_data(server_url, session_id, 1, np.array([1.0, 2.0]), delay=5)
    send_data_with_retries(1, np.array([1.0, 2.0]), 5, retry_delay=0)
    # send_data_with_retries(1, np.array([1.0, 2.0]), 5, retry_delay=2)

    receive_data(server_url, session_id, 1)
    # receive_data_with_retries(2, 5, 5, delay=3)
    # end_session(server_url, session_id)
    end_session_now()


