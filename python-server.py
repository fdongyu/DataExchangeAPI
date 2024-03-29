from flask import Flask, request, jsonify
from flask import Response
import threading
import struct

app = Flask(__name__)

# Session storage
sessions = {}
session_lock = threading.Lock()

import time

def print_sessions_every_10_seconds():
    while True:
        with session_lock:
            print("Current Sessions:", sessions)
        time.sleep(10)

@app.route('/create_session/<client_id>', methods=['POST'])
def create_session(client_id):
    with session_lock:
        data = request.json
        client_id = data.get('client_id', client_id)  # Use URL client_id as a fallback
        source_model_ID = data['source_model_ID']
        destination_model_ID = data['destination_model_ID']
        initiator_id = data.get('initiator_id')
        inviter_id = data.get('inviter_id')

        # Ensure initiator_id and inviter_id are part of the session id
        base_session_id = f"{source_model_ID}_{destination_model_ID}_{initiator_id}_{inviter_id}"

        # Simplified structure for input and output variables
        input_variables_ID = data.get('input_variables_ID', [])
        input_variables_size = data.get('input_variables_size', [])
        output_variables_ID = data.get('output_variables_ID', [])
        output_variables_size = data.get('output_variables_size', [])

        # Generate a unique session ID
        session_id = base_session_id + "_1"
        i = 1
        while session_id in sessions:
            i += 1
            session_id = f"{base_session_id}_{i}"

        sessions[session_id] = {
            'status': 'created',  # Use 'status' to explicitly track the session state
            'data': {var: None for var in set(input_variables_ID) | set(output_variables_ID)},
            'flags': {var: 0 for var in set(input_variables_ID) | set(output_variables_ID)},
            'client_vars': {client_id: list(input_variables_ID)},
            'end_requests': set()
        }

        return jsonify({"status": "created", "session_id": session_id}), 200

@app.route('/join_session', methods=['POST'])
def join_session():
    with session_lock:
        data = request.json
        session_id = data['session_id']
        joining_client_id = data.get('client_id')

        # Check if the session exists
        if session_id not in sessions:
            return jsonify({"error": "Session not found"}), 404

        # Check if the session is already active
        if sessions[session_id].get('status') == 'active':
            return jsonify({"error": "Session is already active"}), 400

        # Retrieve the session
        session = sessions[session_id]

        initiator_input_vars = session['client_vars'].get(list(session['client_vars'].keys())[0], [])

        all_vars = set(session['data'].keys())
        joining_client_input_vars = list(all_vars - set(initiator_input_vars))

        # Update the session status to active
        sessions[session_id]['status'] = 'active'

        # Update client_vars to include the joining client with their input variables
        sessions[session_id]['client_vars'][joining_client_id] = joining_client_input_vars

        return jsonify({"status": "joined and activated", "session_id": session_id}), 200


    
@app.route('/list_sessions', methods=['GET'])
def list_all_session_statuses():
    with session_lock:
        session_statuses = {
            session_id: session.get('status') for session_id, session in sessions.items()
        }
        return jsonify(session_statuses), 200


@app.route('/session_status', methods=['GET'])
def session_status():
    session_id = request.args.get('session_id')

    with session_lock:
        if session_id in sessions:
            status = 'active' if sessions[session_id]['active'] else 'created'
            return jsonify({"status": status, "session_id": session_id}), 200
        else:
            return jsonify({"error": "Session not found"}), 404

@app.route('/get_flags', methods=['GET'])
def get_flags():
    session_id = request.args.get('session_id')

    with session_lock:
        if session_id in sessions:
            # Convert all keys in the 'flags' dictionary to strings
            flags = {str(key): value for key, value in sessions[session_id]['flags'].items()}
            # Return the flags for the session with consistent key types
            return jsonify(flags), 200
        else:
            return jsonify({"error": "Session not found"}), 404
        
@app.route('/send_data', methods=['POST'])
def send_data():
    # Assuming the session_id and var_id are sent as headers
    session_id = request.headers.get('Session-ID')
    var_id = int(request.headers.get('Var-ID'))
    binary_data = request.data  # This is the binary payload, e.g., an array of doubles

    # Convert the binary data to a Python list of doubles
    # '<' means little-endian, 'd' means double; adjust according to your data format
    array_data = list(struct.unpack('<' + 'd' * (len(binary_data) // 8), binary_data))

    with session_lock:
        if session_id in sessions and var_id in sessions[session_id]['data']:
            sessions[session_id]['data'][var_id] = array_data
            sessions[session_id]['flags'][var_id] = 1  # Data is present
            return jsonify({"status": "Binary data received for " + str(var_id)}), 200
        else:
            return jsonify({"error": "Session or variable not found"}), 404

@app.route('/receive_data', methods=['GET'])
def receive_data():
    with session_lock:
        session_id = request.args.get('session_id')
        var_id = int(request.args.get('var_id'))


        if session_id in sessions and var_id in sessions[session_id]['data']:
            data = sessions[session_id]['data'][var_id]
            if data is not None:
                binary_data = struct.pack(f'<{len(data)}d', *data)
                sessions[session_id]['flags'][var_id] = 0  # Ensure this line correctly updates the flag
                return Response(binary_data, mimetype='application/octet-stream')
            else:
                return jsonify({"error": "Data not available for " + var_id}), 404
        else:
            return jsonify({"error": "Session or variable not found"}), 404
        
@app.route('/end_session', methods=['POST'])
def end_session():
    with session_lock:
        data = request.json
        session_id = data['session_id']
        client_id = data['client_id']  # The client attempting to end the session

        # Check if the session exists
        if session_id not in sessions:
            return jsonify({"error": "Session not found"}), 404

        session = sessions[session_id]

        # Check if client is part of the session
        if client_id not in session['client_vars']:
            return jsonify({"error": "Client not part of the session"}), 404

        # Add client to the end_requests to indicate they want to end the session
        session['end_requests'].add(client_id)

        # Check if this is a partial or full end
        if len(session['end_requests']) < len(session['client_vars']):
            # Partial end scenario
            session['status'] = 'partial end'

            # Determine variables associated with the client and clear them
            vars_to_clear = session['client_vars'][client_id]
            for var in vars_to_clear:
                if var in session['data']:
                    session['data'][var] = None  # Clear the data
                    session['flags'][var] = 0  # Reset the flag

            return jsonify({"status": "Partial session end for client " + client_id, "session_id": session_id}), 200
        else:
            # Full end scenario
            session['status'] = 'end'  # Mark the session as fully ended

            # Optionally perform any final processing or logging here before deleting the session

            # Delete the session
            del sessions[session_id]

            return jsonify({"status": "Session ended successfully", "session_id": session_id}), 200

if __name__ == '__main__':
    threading.Thread(target=print_sessions_every_10_seconds, daemon=True).start()
    #app.run(port = 5001, debug=True, threaded=True)
    app.run(host='0.0.0.0', port=8080)
