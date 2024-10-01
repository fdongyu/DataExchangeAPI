from base64 import b64encode
import base64
import requests
import struct

from typing import Union

from ModelDataExchange.data_classes import JoinSessionData, SessionData, SessionID, SessionStatus, SendSessionData


def create_session(server_url, source_model_id, destination_model_id, initiator_id, invitee_id,
                   input_variables_id=None, input_variables_size=None,
                   output_variables_id=None, output_variables_size=None) -> SessionID:
    """
    Creates a session with specified parameters on the server.

    Parameters:
        server_url (str): The server URL.
        source_model_id (int): ID of the source model.
        destination_model_id (int): ID of the destination model.
        initiator_id (int): ID of the session initiator.
        inviter_id (int): ID of the inviter.
        input_variables_id (list): Optional list of input variable IDs.
        input_variables_size (list): Optional list of sizes for input variables.
        output_variables_id (list): Optional list of output variable IDs.
        output_variables_size (list): Optional list of sizes for output variables.

    Returns:
        SessionID: BaseModel of JSON response from the server
    """

    # Prepare data for the POST request
    data: SessionData = SessionData(
        source_model_id=source_model_id,
        destination_model_id=destination_model_id,
        initiator_id=initiator_id,
        invitee_id=invitee_id,
        input_variables_id=input_variables_id or [],
        input_variables_size=input_variables_size or [],
        output_variables_id=output_variables_id or [],
        output_variables_size=output_variables_size or []
    )

    # Send POST request to the server
    response = requests.post(f"{server_url}/create_session", json=data.model_dump())
    print(response)
    # Check response status
    if response.json().get('status') == SessionStatus.CREATED.value:
        session_info = response.json()
        session_id = session_info.get('session_id')

        print(f"Session status: {session_info.get('status', SessionStatus.UNKNOWN)}. Session ID: {session_id}")

        return SessionID(
            source_model_id=source_model_id,
            destination_model_id=destination_model_id,
            initiator_id=initiator_id,
            invitee_id=invitee_id,
            client_id= str(f'{session_id["client_id"]}') # type: ignore
        )
    
    else:
        print("Error occurred. Invalid input:", response.text)
        raise Exception(f"Error occurred. Invalid input: {response.text}") 

def get_session_status(server_url, session_id):
    """
    Client-side function to retrieve the status of a session from the server.

    Parameters:
        server_url (str): The base URL of the server.
        session_id (str): The ID of the session to check.

    Returns:
        The status of the session as an integer if successful, or None if an error occurs.
    """
    # Construct the URL for the GET request
    url = f"{server_url}/get_session_status"
    
    # Send the GET request to the server
    response = requests.get(url, verify=False, json=session_id.model_dump())
    
    # Check the response status
    if response.ok:
        # Extract the session status from the JSON response
        session_status = response.json()
        # print(f"Session status: {SessionStatus[session_status]}")
        return SessionStatus(session_status)
    else:
        # Optionally handle different error codes distinctly if needed
        raise Exception(f"Failed to retrieve session status. Server responded with: {response.status_code} - {response.text}")
        

def join_session(server_url, session_id: SessionID, invitee_id) -> dict:
    """
    Attempts to join a session with a given session ID and invitee ID.
    
    Parameters:
        server_url (str): The server URL.
        session_id (str): The ID of the session to join.
        invitee_id (int): The invitee ID to authenticate the joining.
        
    Returns:
        dict: A dictionary with 'success' status and 'error' message if applicable.
    """
    data = JoinSessionData(
        session_id=session_id,
        invitee_id=invitee_id
    )

    try:
        response = requests.post(f"{server_url}/join_session", json=data.model_dump(), verify=False)
        if response.ok:
            return {'success': True}
        else:
            return {'success': False, 'error': response.json().get('detail', 'Unknown error')}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_variable_size(server_url, session_id, var_id) -> int:
    """
    Retrieves the size of a specific variable within a session from the server.

    Parameters:
        server_url (str): The server URL.
        session_id (str): The ID of the session.
        var_id (int): The ID of the variable.

    Returns:
        int: The size of the variable if the request is successful, -1 otherwise.
    """
    # Construct the URL and set parameters for the GET request
    url = f"{server_url}/get_variable_size"
    params = {'session_id': str(session_id), 'var_id': var_id}

    # Perform the GET request
    response = requests.get(url, params=params)
    if response.ok:
        # Parse and return the size from the JSON response
        size_info = response.json()
        print(f"Size of variable {var_id} in session {session_id}: {size_info.get('size', 'Unknown')}")
        return size_info.get('size', -1)
    else:
        # Log and return -1 if there was an error during the request
        print("Error occurred while retrieving variable size:", response.text)
        return -1
    
def send_data(server_url, session_id, var_id, data) -> requests.Response:
    """
    Sends a list of double precision floats as binary data to the server for a specific session and variable.

    Parameters:
        server_url (str): The server URL.
        session_id (str): The session ID to which the data belongs.
        var_id (int): The identifier for the variable to which the data is related.
        data (list of float): The data to be sent, represented as a list of doubles.

    Note:
        The data is packed in little-endian format.
    """
    # Convert the list of doubles into binary data using little-endian format
    binary_data = struct.pack('<' + 'd' * len(data), *data)
    # binary_data = b64encode(binary_data).decode("utf-8")
    # binary_data = base64.encodebytes(struct.pack('<' + 'd' * len(data), *data)).decode("utf-8")
    # binary_data = base64.encodebytes(data).decode("utf-8")

    # Prepare HTTP headers to include session and variable identifiers
    headers = {
        'Session-ID': str(session_id),
        'Var-ID': str(var_id)
    }
    # print(','.join(map(str, arr)))
    # Send the binary data as a POST request to the server
    result = requests.post(f"{server_url}/send_data", data=binary_data, headers=headers)
    return result


def get_variable_flag(server_url, session_id, var_id) -> Union[int, None]:
    """
    Retrieves the flag status for a specific variable within a session.

    Parameters:
        server_url (str): The server URL.
        session_id (str): The ID of the session.
        var_id (int): The ID of the variable.

    Returns:
        int: The flag status if the request is successful, None otherwise.
    """
    # Construct the URL and set parameters for the GET request
    url = f"{server_url}/get_variable_flag"
    params = {'session_id': str(session_id), 'var_id': var_id}

    # Perform the GET request
    response = requests.get(url, params=params, verify=False)

    # Check if the request was successful
    if response.ok:
        # Parse and return the flag status from the JSON response
        flag_status = response.json().get('flag_status')
        print(f"Flag for session {session_id} variable {var_id}: {flag_status}")
        return flag_status
    else:
        # Log and return None if there was an error during the request
        print("Error occurred while retrieving flag status:", response.text)
        return None


def receive_data(server_url, session_id, var_id) -> Union[tuple[float], None]:
    """
    Receives binary data from the server for a given session and variable ID, assuming the data
    is a stream of double precision floats.

    Parameters:
        server_url (str): The server URL.
        session_id (str): The session ID from which data is to be retrieved.
        var_id (int): The variable ID associated with the data.
    
    Returns:
        list of float: The unpacked data array of double precision floats, or None if an error occurred.
    """
    params = {"session_id": str(session_id), "var_id": var_id}

    response = requests.get(f"{server_url}/receive_data", params=params, verify=False)

    if response.ok:
        binary_data = response.content
        num_doubles = len(binary_data) // 8  # Each double is 8 bytes
        unpacked_data = struct.unpack(f'<{num_doubles}d', binary_data)
        print(f"Received binary data of length {num_doubles}")
        print("Data array:", unpacked_data)
        return unpacked_data
    else:
        print("Error retrieving data:", response.text)
        raise Exception(f"Error retrieving data: {response.text}")
    
def end_session(server_url: str, session_id: SessionID) -> bool:
    """
    Ends a session on the server using a POST request with the session ID and user ID.
    
    Parameters:
        server_url (str): The server URL.
        session_id (str): The ID of the session to be ended.
        user_id (int): The ID of the user (initiator or invitee) ending the session.
    """

    # Send the POST request to end the session
    response = requests.post(f"{server_url}/end_session", json=session_id.model_dump(), verify=False)

    # Check if the request was successful
    if response.ok:
        # Print the status message from the response
        print(response.json().get("status", "No status message received."))
        return True
    else:
        # Print an error message if the request failed
        print("Error ending session:", response.text)
        return False