from fastapi import FastAPI, HTTPException, Request, Response, Header
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import struct
import threading
import asyncio
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
app = FastAPI()

class SessionData(BaseModel):
    """Model for session creation data, validates incoming data."""
    source_model_ID: int
    destination_model_ID: int
    initiator_id: int
    invitee_id: int
    input_variables_ID: List[int] = []
    input_variables_size: List[int] = []
    output_variables_ID: List[int] = []
    output_variables_size: List[int] = []

class JoinSessionData(BaseModel):
    """Model for joining a session, includes session and invitee IDs."""
    session_id: str
    invitee_id: int

# Global dictionary for session data and a lock for thread-safe operations
sessions = {}
session_lock = threading.Lock()

@app.on_event("startup")
async def startup_event():
    """Initializes background tasks at server startup, like periodic session logging."""
    app.state.print_sessions_task = asyncio.create_task(print_sessions_every_n_seconds(n=10))

@app.on_event("shutdown")
async def shutdown_event():
    """Cancels background tasks at server shutdown."""
    app.state.print_sessions_task.cancel()
    try:
        await app.state.print_sessions_task
    except asyncio.CancelledError:
        print("Background task was cancelled")

async def print_sessions_every_n_seconds(n=10):
    """Periodically logs the current sessions and their flags."""
    while True:
        with session_lock:
            print("Current Sessions and Flags:")
            for session_id, session_info in sessions.items():
                print(f"Session ID: {session_id}, Flags: {session_info['flags']}")
        await asyncio.sleep(n)

@app.post("/create_session")
async def create_session(session_data: SessionData):
    """Creates a new session based on the provided data, storing it in a global dictionary."""
    with session_lock:
        base_session_id = f"{session_data.source_model_ID},{session_data.destination_model_ID},{session_data.initiator_id},{session_data.invitee_id}"
        session_id = f"{base_session_id},1"
        i = 1
        while session_id in sessions:
            i += 1
            session_id = f"{base_session_id},{i}"

        var_sizes = {**dict(zip(session_data.input_variables_ID, session_data.input_variables_size)),
                     **dict(zip(session_data.output_variables_ID, session_data.output_variables_size))}

        sessions[session_id] = {
            'status': 'created',
            'data': {var: None for var in set(session_data.input_variables_ID) | set(session_data.output_variables_ID)},
            'flags': {var: 0 for var in set(session_data.input_variables_ID) | set(session_data.output_variables_ID)},
            'client_vars': {session_data.initiator_id: list(session_data.input_variables_ID)},
            'end_requests': set(),
            'var_sizes': var_sizes
        }
        
        return {"status": "created", "session_id": session_id}
    
@app.get("/get_session_status")
async def get_session_status(session_id: str):
    """
    Retrieves the status of a specific session.

    Parameters:
        session_id (str): The ID of the session.

    Returns:
        The status of the session as an integer.
    """
    with session_lock:  # Assuming session_lock is a threading lock for thread-safe operations
        # Check if the session exists
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")

        # Map statuses to integers
        status_mapping = {
            "created": 1, # Session is created, when one client has created the session
            "active": 2, # Session is active, when both the clients has joined coupling
            "partial end": 3 # Session is partial end, when one client has ended the session
        }

        # Return the status of the session
        session_status = sessions[session_id]['status']
        return status_mapping.get(session_status, 0)  # Return 0 if status is unknown

@app.post("/join_session")
async def join_session(data: JoinSessionData):
    """
    Allows a new client to join an existing session using session and invitee IDs.
    """
    with session_lock:
        session_id = data.session_id
        joining_invitee_id = data.invitee_id

        # Check session availability
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        if sessions[session_id].get('status') == 'active':
            raise HTTPException(status_code=400, detail="Session is already active")

        # Assign unused variables to the new joiner
        session = sessions[session_id]
        initiator_vars = session['client_vars'].get(list(session['client_vars'].keys())[0], [])
        unused_vars = set(session['data'].keys()) - set(initiator_vars)
        session['client_vars'][joining_invitee_id] = list(unused_vars)
        session['status'] = 'active'

        return {"status": "joined and activated", "session_id": session_id}

@app.post("/send_data")
async def send_data(request: Request, session_id: Optional[str] = Header(None), var_id: Optional[int] = Header(None)):
    """
    Receives and stores binary data for a specified variable within an active session.
    """
    if not session_id or not var_id:
        raise HTTPException(status_code=400, detail="Session-ID or Var-ID header missing")

    binary_data = await request.body()
    # Unpack binary data to a list of doubles
    array_data = list(struct.unpack('<' + 'd' * (len(binary_data) // 8), binary_data))

    with session_lock:
        if session_id in sessions and var_id in sessions[session_id]['data']:
            sessions[session_id]['data'][var_id] = array_data
            sessions[session_id]['flags'][var_id] = 1
            return {"status": f"Binary data received for variable ID {var_id}"}
        else:
            raise HTTPException(status_code=404, detail="Session or variable not found")

@app.get("/get_variable_flag")
async def get_variable_flag(session_id: str, var_id: int):
    """
    Retrieves the flag status indicating the presence of data for a specific variable in a session.
    """
    with session_lock:
        if session_id in sessions and var_id in sessions[session_id]['flags']:
            return {"var_id": var_id, "flag_status": sessions[session_id]['flags'][var_id]}
        else:
            raise HTTPException(status_code=404, detail="Session or variable not found")

@app.get("/get_variable_size")
async def get_variable_size(session_id: str, var_id: int):
    """
    Retrieves the size of a specific variable from its session.
    """
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
    Retrieves and sends binary data for a specific variable in a session as an octet-stream.
    """
    with session_lock:
        if session_id in sessions and var_id in sessions[session_id]['data']:
            data = sessions[session_id]['data'][var_id]
            if data is not None:
                binary_data = struct.pack('<' + 'd' * len(data), *data)
                sessions[session_id]['flags'][var_id] = 0  # Reset the flag to indicate data has been sent
                return Response(content=binary_data, media_type='application/octet-stream')
            else:
                raise HTTPException(status_code=404, detail="Data not available for variable ID " + str(var_id))
        else:
            raise HTTPException(status_code=404, detail="Session or variable not found")

class EndSessionData(BaseModel):
    """Data model for ending a session, includes session and user IDs."""
    session_id: str
    user_id: int

@app.post("/end_session")
async def end_session(data: EndSessionData):
    """
    Ends a session for a given user, marking it as fully ended if all users have requested to end it.
    """
    with session_lock:
        session_id = data.session_id
        user_id = data.user_id

        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        if user_id not in session['client_vars']:
            raise HTTPException(status_code=404, detail="User not part of the session")

        session = sessions[session_id]
        session['end_requests'].add(user_id)

        # Check if all users have requested to end the session
        if len(session['end_requests']) < len(session['client_vars']):
            session['status'] = 'partial end'
            # Clear data for the user ending the session
            vars_to_clear = session['client_vars'][user_id]
            for var in vars_to_clear:
                if var in session['data']:
                    session['data'][var] = None
                    session['flags'][var] = 0
            return {"status": f"Partial session end for user {user_id}", "session_id": session_id}
        else:
            session['status'] = 'end'
            del sessions[session_id]
            return {"status": "Session ended successfully", "session_id": session_id}

if __name__ == '__main__':
    def main():
        """
        Main function to initiate the FastAPI server with asynchronous task management.
        """
        loop = asyncio.get_event_loop()
        loop.create_task(print_sessions_every_n_seconds())
        uvicorn.run(app, host='0.0.0.0', port=8000)

    main()
