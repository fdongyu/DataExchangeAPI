import uuid
import pytest
import uvicorn
import threading
import time
import contextlib

from ..src.data_classes import SessionStatus
from ..src.clients.cyberwater.high_level_api import *
from ..src.clients.cyberwater.low_level_api import *
from ..src.server.exchange_server import app 


# Server class allows the uvicorn server to be run while testing
#
# See link below for source of the Server class
# https://github.com/encode/uvicorn/issues/742#issuecomment-674411676
class Server(uvicorn.Server):

    def signal_handler(self):
        pass
    
    @contextlib.contextmanager
    def run_in_thread(self):
        thread = threading.Thread(target=self.run)
        thread.start()

        try:
            while not self.started:
                # Startup is not instantaneous. Client will fail to connect
                # if we don't wait for the server to start.
                time.sleep(1e-3)
            yield
        finally: # This is called when start_server is finished yielding
            self.should_exit = True
            thread.join()
    

class Test:

    @pytest.fixture(autouse=True)
    def setUp(self):
        # Set the server URL before each test
        self.server_url = "http://0.0.0.0:8000"      
        self.session_data = SessionData(
            source_model_id=2001,
            destination_model_id=2005,
            initiator_id=35,
            invitee_id=38,
            input_variables_id=[1],
            input_variables_size=[50],
            output_variables_id=[4],
            output_variables_size=[50]
        )

        set_server_url(self.server_url)

    @pytest.fixture(autouse=True, scope="function")
    def start_server(self):
        """
        Server fixture for each test. Every test will start on a fresh server instance
        """

        config = uvicorn.Config(app=app, host="0.0.0.0", port=8000)
        server = Server(config)

        # Tests are run in this context
        with server.run_in_thread():
            yield

    def test_start_session_success(self):
        """ Test successful start of a session """
        # Assuming `start_session` returns some status or None if successful
        
        # SessionID is only returned if the session is successfully started
        session_id: SessionID = start_session(self.session_data)
        assert type(session_id) is SessionID, "Session should start successfully without any errors."
        assert session_id.source_model_id == 2001, "Source model ID should be 2001."
        assert session_id.destination_model_id == 2005, "Destination model ID should be 2005."
        assert session_id.initiator_id == 35, "Initiator ID should be 35."
        assert session_id.invitee_id == 38, "Invitee ID should be 38."
        assert type(uuid.UUID(session_id.client_id)) is uuid.UUID, "Client ID should be a UUID."

        assert retrieve_session_status(session_id) == SessionStatus.CREATED, "Session should be created."   


    def test_start_session_without_url(self):
        """ Test starting a session without setting server URL """
        
        with pytest.raises(Exception) as context:
            set_server_url("")  # Clearing the server URL
            assert str(context) in "Error: Server URL not set" 
        
        # Server should not start without resetting URL
        with pytest.raises(Exception) as context:
            start_session(self.session_data)
            assert str(context) in "Error: Server URL not set." 

        
    def test_start_session_invalid_data(self):
        """ Test starting a session with invalid session data """
        
        # Invalid source model ID
        self.session_data.source_model_id = None # type: ignore  
        
        with pytest.raises(Exception) as context:
            start_session(self.session_data)
            assert "Error: Server URL not set." in str(context).lower()

    def test_status_join(self):

        session_id = start_session(self.session_data)
        set_session_id(session_id)

        # # Check the session status first
        session_status = retrieve_session_status(session_id)
        assert session_status is not None, "Session should be created."

        join_status = join_session_with_retries(session_id, invitee_id=38, max_retries=5, retry_delay=5)
        assert join_status == 1, "Joined the session successfully."
            
    def test_status_active(self):

        session_id = start_session(self.session_data)

        # # Check the session status first
        session_status = retrieve_session_status(session_id)
        assert session_status is not None, "Session should be created."

        join_status = join_session_with_retries(session_id, invitee_id=38, max_retries=5, retry_delay=5)
        assert join_status == 1, "Joined the session successfully."
    
    def test_status_partial_end(self):

        session_id = start_session(self.session_data)
        set_session_id(session_id)

        # # Check the session status first
        session_status = retrieve_session_status(session_id)
        assert session_status is not None, "Session should be created."

        join_status = join_session_with_retries(session_id, invitee_id=38, max_retries=5, retry_delay=5)
        assert join_status == SessionStatus.CREATED, "Joined the session successfully."

        end_status = end_session(self.server_url, session_id)
        assert end_status == True, "Session should end successfully."

    # def test_end_session_of_another_user(self):
            
    #         # User 1
    #         session_id_1 = start_session(self.session_data)
    #         # session_id_1 = [2001,2005,35,38,1]
    #         # set_session_id(session_id)

    #         # User 2           
    #         session_id_2 = join_session(self.server_url, session_id_1, session_id_1.invitee_id)
    #         # session_id = [2001,2005,1,1,2]
    #         # set_session_id(session_id)
            
    #         # # Check the session status first
    #         session_status = retrieve_session_status(session_id)
    #         assert session_status is not None, "Session should be created."
    
    #         join_status = join_session_with_retries(session_id, invitee_id=38, max_retries=5, retry_delay=5)
    #         assert join_status == 1, "Joined the session successfully."
    
    #         assert end_session(self.server_url, session_id, 38) == SessionStatus.PARTIAL_END.name, "Session should not end successfully."