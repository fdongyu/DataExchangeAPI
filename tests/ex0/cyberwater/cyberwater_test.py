import unittest
from clients.cyberwater.lib.high_level_api import set_server_url, start_session, SessionData

class TestSessionAPI(unittest.TestCase):

    def setUp(self):
        # Set the server URL before each test
        set_server_url("http://128.55.64.33:8000")
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

    def test_start_session_success(self):
        """ Test successful start of a session """
        # Assuming `start_session` returns some status or None if successful
        result = start_session(self.session_data)
        self.assertIsNone(result, "Session should start successfully without any errors.")

    def test_start_session_without_url(self):
        """ Test starting a session without setting server URL """
        set_server_url("")  # Clearing the server URL
        with self.assertRaises(Exception) as context:
            start_session(self.session_data)
        self.assertIn("Server URL not set", str(context.exception))

    def test_start_session_invalid_data(self):
        """ Test starting a session with invalid session data """
        self.session_data.source_model_id = None  # Invalid source model ID
        with self.assertRaises(Exception) as context:
            start_session(self.session_data)
        self.assertIn("invalid input", str(context.exception.lower()))

if __name__ == "__main__":
    unittest.main()
