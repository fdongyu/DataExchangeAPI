from typing import Optional
from fastapi import FastAPI, HTTPException, Header, Request, Response
from sys import argv

from ModelDataExchange.data_classes import SessionData, JoinSessionData, SessionID, SessionStatus

import uvicorn
import struct
import threading
import asyncio
import warnings
import uuid

warnings.filterwarnings("ignore", category=DeprecationWarning)
app = FastAPI()

# Shared resource: sessions dictionary and a lock to manage concurrent access
sessions = {}
session_lock = threading.Lock()

@app.on_event("startup")
async def startup_event():
    """ Start background tasks at server startup """
    app.state.print_sessions_task = asyncio.create_task(print_sessions_every_n_seconds(n=1))


@app.on_event("shutdown")
async def shutdown_event():
    """ Cancel the periodic print task on server shutdown """
    app.state.print_sessions_task.cancel()
    try:
        await app.state.print_sessions_task
    except asyncio.CancelledError:
        print("Background task was cancelled")


async def print_sessions_every_n_seconds(n=1):
    """ Periodically print the current sessions and their flags every `n` seconds """
    while True:
        with session_lock:
            print("Current Sessions and Flags:")
            for session_id, session_info in sessions.items():
                flags = session_info['flags']
                print(f"Session ID: {session_id}, Flags: {flags}")
        await asyncio.sleep(n)


@app.post("/create_session")
async def create_session(session_data: SessionData):
    """ 
    Creates a new session with given parameters and store it in a global dictionary

    Parameters:
        session_data (SessionData): The data required to create a new session.

    Returns:
        A dictionary containing the status of the session and the session ID.
        {status: int, session_id: str} 
    
    """
    with session_lock:
        # base_session_id = f"{session_data.source_model_id},{session_data.destination_model_id},{session_data.initiator_id},{session_data.invitee_id}"
        # session_id = base_session_id + ",1"
        # i = 1
        # while session_id in sessions:
        #     i += 1
        #     session_id = f"{base_session_id},{i}"
        
        # Generate a unique session ID
        session_id = SessionID(
            source_model_id=session_data.source_model_id,
            destination_model_id=session_data.destination_model_id,
            initiator_id=session_data.initiator_id,
            invitee_id=session_data.invitee_id,
            client_id=str(uuid.uuid4())
        )

        print(f"Creating session with ID: {session_id}")
        # Map variable IDs to their respective sizes
        var_sizes = {**dict(zip(session_data.input_variables_id, session_data.input_variables_size)),
                     **dict(zip(session_data.output_variables_id, session_data.output_variables_size))}
        
        # Initialize session data
        sessions[session_id] = {
            'status': SessionStatus.CREATED,
            'data': {var: None for var in set(session_data.input_variables_id) | set(session_data.output_variables_id)},
            'flags': {var: 0 for var in set(session_data.input_variables_id) | set(session_data.output_variables_id)},
            'client_vars': {session_data.initiator_id: list(session_data.input_variables_id)},
            'client_id': session_id.client_id,
            'invitee_id': session_data.invitee_id,
            'initiator_id': session_data.initiator_id,
            'end_requests': set(),
            'var_sizes': var_sizes
        }
        
        return {"status": SessionStatus.CREATED, "session_id": session_id}
    

@app.get("/get_session_status")
async def get_session_status(session_id: str) -> int:
    """
    Retrieves the status of a specific session.

    Parameters:
        session_id (str): The ID of the session.

    Returns:
        The status of the session as an int.

        SessionStatus.UNKNOWN = 0
        SessionStatus.CREATED = 1
        SessionStatus.ACTIVE = 2
        SessionStatus.PARTIAL_END = 3
        SessionStatus.END = 4
    """

    session_id = string_to_session_id(session_id) # type: ignore
    with session_lock:  # Assuming session_lock is a threading lock for thread-safe operations
        # Check if the session exists
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")

        # See data_classes.py for SessionStatus enum
        return sessions[session_id]['status']


@app.post("/join_session")
async def join_session(data: JoinSessionData) -> dict:
    """ 
    Allow a new client to join an existing session 
    """

    with session_lock:
        session_id = data.session_id
        joining_invitee_id = data.invitee_id
        

        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        elif sessions[session_id].get('status') == SessionStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="Session is already active")
        elif joining_invitee_id != sessions[session_id]['invitee_id']:
            print(f"Invitee ID does not match. Expected: {sessions[session_id]['invitee_id']}, Got: {joining_invitee_id}")
            raise HTTPException(status_code=403, detail="Invitee ID does not match")

        # Assign variables not used by the initiator to the joining client
        session = sessions[session_id]
        initiator_input_vars = session['client_vars'].get(list(session['client_vars'].keys())[0], [])
        all_vars = set(session['data'].keys())
        joining_client_input_vars = list(all_vars - set(initiator_input_vars))

        session['status'] = SessionStatus.ACTIVE
        session['client_vars'][joining_invitee_id] = joining_client_input_vars

        return {"status": SessionStatus.ACTIVE, "session_id": session_id}


@app.post("/send_data")
async def send_data(request: Request, session_id: Optional[str] = Header(None), var_id: Optional[int] = Header(None)):
    """
    Receive binary data for a specific variable in a session.
    """
    session_id = string_to_session_id(session_id) # type: ignore

    if session_id is None or var_id is None:
        raise HTTPException(status_code=400, detail="Session-ID or Var-ID header missing")
    elif sessions[session_id]['flags'][var_id] == 1:
        raise HTTPException(status_code=400, detail="Data already present for variable ID " + str(var_id))  

    binary_data = await request.body()
    # `binary_data` is a bytes object that contains packed binary data, 
    # and `data` is a list or tuple of floating-point numbers to be packed into binary format.

    # Unpacking binary data into a list of doubles (double-precision floating points):
    # 1. '<' indicates little-endian byte order.
    # 2. 'd' represents a double in C (8 bytes).
    # 3. 'len(binary_data) // 8' calculates how many doubles are packed in `binary_data`.
    array_data = list(struct.unpack('<' + 'd' * (len(binary_data) // 8), binary_data))

    with session_lock:
        if session_id in sessions and var_id in sessions[session_id]['data']:
            sessions[session_id]['data'][var_id] = array_data
            sessions[session_id]['flags'][var_id] = 1  # Data is present
            return {"status": "Binary data received for " + str(var_id)}
        else:
            raise HTTPException(status_code=404, detail="Session or variable not found")


@app.get("/get_variable_flag")
async def get_variable_flag(session_id: str, var_id: int):
    """
    Get the flag status for a specific variable in the session.
    """
 
    session_id = string_to_session_id(session_id) # type: ignore

    with session_lock:
        if session_id in sessions and var_id in sessions[session_id]['flags']:
            flag_status = sessions[session_id]['flags'][var_id]
            return {"var_id": var_id, "flag_status": flag_status}
        else:
            raise HTTPException(status_code=404, detail="Session or variable not found")
        

@app.get("/get_variable_size")
async def get_variable_size(session_id: str, var_id: int):
    """
    Retrieve the size of a specific variable in the session.
    """

    session_id = string_to_session_id(session_id) # type: ignore

    with session_lock:
        if session_id in sessions and 'var_sizes' in sessions[session_id]:
            var_sizes = sessions[session_id]['var_sizes']
            if var_id in var_sizes:
                return {"var_id": var_id, "size": var_sizes[var_id]}
            else:
                raise HTTPException(status_code=404, detail="Variable ID not found in session")
        else:
            raise HTTPException(status_code=404, detail="Session not found")


@app.get("/receive_data")
async def receive_data(session_id: str, var_id: int):
    """
    Send binary data for a specific variable in a session.

    Parameters:
        session_id (str): The session ID.
        var_id (int): The variable ID.
        delay (int): The delay in seconds before sending the data. Default is 0.

    Returns:
        Response: The binary data as a response object.

    Raises:
        HTTPException: If the session or variable is not found.
    """

    session_id = string_to_session_id(session_id) # type: ignore

    with session_lock:
        if session_id in sessions and var_id in sessions[session_id]['data']:
            data = sessions[session_id]['data'][var_id]
            if data is not None:
                
                binary_data = struct.pack('<' + 'd' * len(data), *data)
                sessions[session_id]['flags'][var_id] = 0  # Reset the flag after data is sent

                return Response(content=binary_data, media_type='application/octet-stream')
            else:
                raise HTTPException(status_code=404, detail="Data not available for variable ID " + str(var_id))
        else:
            raise HTTPException(status_code=404, detail="Session or variable not found")


@app.post("/end_session")
async def end_session(data: SessionID):
    with session_lock:

        if data not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")

        session = sessions[data]
        if data.client_id not in session['client_id']:
            raise HTTPException(status_code=400, detail="User not part of the session")

        session['end_requests'].add(data.client_id)

        # if len(session['end_requests']) < len(session['client_vars']):
        if session['status'] is not SessionStatus.PARTIAL_END:
            session['status'] = SessionStatus.PARTIAL_END
            # if client_id belongs to initiator, end initiator, otherwise end invitee
            if session["client_id"] == data.client_id:
                vars_to_clear = session['client_vars'][data.initiator_id]
            else:
                vars_to_clear = session['client_vars'][data.invitee_id]
            
            for var in vars_to_clear:
                # print ("Variable Clearing:", var)
                if var in session['data']:
                    session['data'][var] = None
                    session['flags'][var] = 0
            return {"status": SessionStatus.PARTIAL_END, "session_id": data}
        else:
            # session['status'] = SessionStatus.END
            print("Ending session for user", data)
            del sessions[data]
            return {"status": SessionStatus.END, "session_id": data}


def string_to_session_id(data: str | SessionID) -> SessionID:

    """
    Convert a string to a SessionID object.

    Parameters:
        data (str): The string to convert.

    Returns:
        SessionID: The SessionID object.
    """
    
    if isinstance(data, SessionID):
        return data
    
    session_id_str = data.split(',')

    session_id = SessionID( # type: ignore
        source_model_id=int(session_id_str[0]),
        destination_model_id=int(session_id_str[1]),
        initiator_id=int(session_id_str[2]),
        invitee_id=int(session_id_str[3]),
        client_id=session_id_str[4]
    )

    return session_id


if __name__ == '__main__':
    # Task to print sessions periodically
    loop = asyncio.get_event_loop()
    loop.create_task(print_sessions_every_n_seconds())

    host_ip = "0.0.0.0"
    host_port = 8000
    # If this is run as main, check for command line arguments
    match len(argv):
        case 1:
            pass
        case 2:
            host_ip = argv[1]
        case 3:
            host_ip = argv[1]
            host_port = int(argv[2])
        case _:
            print("Usage: python exchange_server.py [host_ip - optional. Default = localhost] [host_port - optional. Default = 8000]")
    print(f"Starting server at {host_ip}:{host_port}")
    # Start the server with Uvicorn
    uvicorn.run(app, host=host_ip, port=host_port)

