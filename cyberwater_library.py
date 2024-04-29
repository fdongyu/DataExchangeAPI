import requests
import struct


SERVER_URL = "http://10.249.0.171:8000"

client_id  = "ClientB"

def create_session(source_model_ID, destination_model_ID, 
                   initiator_id, 
                   inviter_id,
                   no_of_input_variables=0, input_variables_ID=[], input_variables_size=[], no_of_output_variables=0, output_variables_ID=[], output_variables_size=[]):
    data = {
        "client_id": client_id,
        "source_model_ID": source_model_ID,
        "destination_model_ID": destination_model_ID,
        "initiator_id": initiator_id,  # New field
        "inviter_id": inviter_id,      # New field
        "no_of_input_variables": no_of_input_variables,
        "input_variables_ID": input_variables_ID,
        "input_variables_size": input_variables_size,
        "no_of_output_variables": no_of_output_variables,
        "output_variables_ID": output_variables_ID,
        "output_variables_size": output_variables_size
    }

    response = requests.post(f"{SERVER_URL}/create_session/{client_id}", json=data)
    if response.ok:
        session_info = response.json()
        print(f"Session status: {session_info['status']}. Session ID: {session_info['session_id']}")
    else:
        print("Error occurred:", response.text)
    return response.json()

def join_session(session_id):
    data = {
        "client_id": client_id,
        "session_id": session_id,
    }
    response = requests.post(f"{SERVER_URL}/join_session", json=data)
    if response.ok:
        print(f"Successfully joined session {session_id}")
    else:
        print("Error occurred while joining session:", response.text)

def get_all_session_statuses():
    response = requests.get(f"{SERVER_URL}/list_sessions")
    if response.ok:
        sessions = response.json()
        print("Session statuses:")
        for session_id, status in sessions.items():
            print(f"Session ID: {session_id}, Status: {status}")
    else:
        print(f"Error occurred while retrieving session statuses: {response.text}")

def get_flags(session_id):
    response = requests.get(f"{SERVER_URL}/get_flags", params={"session_id": session_id})
    if response.ok:
        flags = response.json()
        print(f"Flags for session {session_id}: {flags}")
    else:
        print("Error occurred while retrieving flags:", response.text)

def get_variable_flag(session_id, var_id):
    # Build the URL for the GET request
    url = f"{SERVER_URL}/get_variable_flag"
    # Set the parameters with session_id and var_id
    params = {'session_id': session_id, 'var_id': var_id}
    # Make the GET request
    response = requests.get(url, params=params)
    # Check if the response is successful
    if response.ok:
        # Extract the flag status from the JSON response
        flag_status = response.json().get('flag_status')
        print(f"Flag for session {session_id} variable {var_id}: {flag_status}")
        return flag_status
    else:
        # Print the error message if something went wrong
        print("Error occurred while retrieving flag status:", response.text)
        return None

def send_data(session_id, var_id, data):
    # Convert data (list of doubles) to binary
    binary_data = struct.pack('<' + 'd'*len(data), *data)

    headers = {
        'Session-ID': session_id,
        'Var-ID': str(var_id)
    }

    response = requests.post(f"{SERVER_URL}/send_data", data=binary_data, headers=headers)
    if response.ok:
        print(f"Data sent for {var_id}.")
    else:
        print("Error sending data:", response.text)

def receive_data(session_id, var_id):
    params = {"session_id": session_id, "var_id": var_id}
    response = requests.get(f"{SERVER_URL}/receive_data", params=params)

    # Check if the response is JSON
    if response.headers['Content-Type'] == 'application/json':
        try:
            data = response.json()
            if 'error' in data:
                print(f"Error: {data['error']}")
            else:
                print(f"Received JSON data: {data}")
        except ValueError as e:
            print(f"Error parsing JSON: {e}")
    elif response.headers['Content-Type'] == 'application/octet-stream':
        # Handle binary data
        binary_data = response.content
        # Assuming the binary data consists of a series of doubles
        num_doubles = len(binary_data) // 8  # Each double is 8 bytes
        unpacked_data = struct.unpack(f'<{num_doubles}d', binary_data)
        print(f"Received binary data of length {len(binary_data)}")
        print("Data array:", unpacked_data)
    else:
        print("Received unexpected content type:", response.headers['Content-Type'])
    
def end_session(session_id):
    data = {
        "session_id": session_id,
        "client_id": client_id
    }
    response = requests.post(f"{SERVER_URL}/end_session", json=data)
    if response.ok:
        print(response.json().get("status"))
    else:
        print("Error ending session:", response.text)

# Function to check and send data with retry logic and feedback using specific flag
def check_and_send_data(session_id, var_id, data_array, max_retries=5):
    retry_count = 0
    while retry_count < max_retries:
        flag = get_variable_flag(session_id, var_id)
        print ("------------------------------", flag, "------------------------------")
        if flag == 0:
            send_data(session_id, var_id, data_array)
            return
        else:
            time.sleep(3)
            print(f"---- Trying to send for the variable: {var_id} | retries: {retry_count}")
            retry_count += 1
    print(f"Failed to send data for var_id {var_id} after {max_retries} attempts: Flag is not in the expected state.")

# Function to check and receive data with retry logic and feedback using specific flag
def check_and_receive_data(session_id, var_id, max_retries=5):
    retry_count = 0
    while retry_count < max_retries:
        flag = get_variable_flag(session_id, var_id)
        print ("------------------------------", flag, "------------------------------")
        if flag == 1:
            receive_data(session_id, var_id)
            return
        else:
            time.sleep(3)
            print(f"---- Trying to receive for the variable: {var_id} | retries: {retry_count}")
            retry_count += 1
    print(f"Failed to receive data for var_id {var_id} after {max_retries} attempts: Flag is not in the expected state.")

def array_to_string(int_array):
    """Converts a list of integers to a comma-separated string."""
    return ','.join(str(num) for num in int_array)
