
# This file establishes the schema for communication between the Exchange Server and the clients.
from enum import Enum
from fastapi import HTTPException
from pydantic import BaseModel
from typing import List


# Data classes for the Exchange Server
# Starting a session uses this data class
class SessionData(BaseModel):

    """
    Data class for starting a session.

    Attributes:
        source_model_id (int): The ID of the source model.
        destination_model_id (int): The ID of the destination model.
        initiator_id (int): The ID of the initiator.
        invitee_id (int): The ID of the invitee.
        input_variables_id (List[int]): The IDs of the input variables.
        input_variables_size (List[int]): The sizes of the input variables.
        output_variables_id (List[int]): The IDs of the output variables.
        output_variables_size (List[int]): The sizes of the output variables.

    Example:
        SessionData(
            source_model_id=2001,
            destination_model_id=2005,
            initiator_id=35,
            invitee_id=38,
            input_variables_id=[1],
            input_variables_size=[50],
            output_variables_id=[4],
            output_variables_size=[50]
        )
    """

    source_model_id: int
    destination_model_id: int
    initiator_id: int
    invitee_id: int
    input_variables_id: List[int] = []
    input_variables_size: List[int] = []
    output_variables_id: List[int] = []
    output_variables_size: List[int] = []


# Data classes for the Cyberwater client
class SessionID(BaseModel, frozen=True):

    """
    Data class for a session ID.

    Note: 
        This class is frozen (immutable) to prevent modification of the attributes.

    Additional `__str__()` method is implemented to return a string representation of the session ID.

    Attributes:
        source_model_id (int): The ID of the source model.
        destination_model_id (int): The ID of the destination model.
        initiator_id (int): The ID of the initiator.
        invitee_id (int): The ID of the invitee.
        client_id (str): The UUID of the client.
    """
    source_model_id: int
    destination_model_id: int
    initiator_id: int
    invitee_id: int
    client_id: str

    def __str__(self) -> str:
        """
        Returns a string representation of the session ID.

        "source_model_id,destination_model_id,initiator_id,invitee_id,client_id"

        Returns:
            str: A comma seperated string representation of the session ID.
        """
        return f"{self.source_model_id},{self.destination_model_id},{self.initiator_id},{self.invitee_id},{self.client_id}"


# Data classes for joining a session
class JoinSessionData(BaseModel):

    """
    Data class for joining a session.

    Attributes:
        session_id (SessionID): The session ID to join.
        invitee_id (int): The ID of the invitee.
    """

    session_id: SessionID
    invitee_id: int


# Data classes for post requests
class PostSessionData(BaseModel):

    """
    Data class for joining a session.

    Attributes:
        session_id (SessionID): The session ID to join.
        param      (int): ID of the input (invitee_id for join_session or var_id for send/recv_data).
    """

    session_id: SessionID
    param_id:   int


class SessionStatus(Enum):

    """
    Enum for the status of a session.

    Attributes:
        ERROR       (int): Reserved. `-1`
        UNKNOWN     (int): Reserved/Default. `0`
        CREATED     (int): Created but invitee has not joined. Only initiator is present. `1`
        ACTIVE      (int): Both initiator and invitee are present. `2`
        PARTIAL_END (int): One of the users has disconnected (/end_session). `3`
        END         (int): Both users have disconnected (/end_session) The session is deleted shortly after this status is set. `4`
    """
    ERROR = -1 
    UNKNOWN = 0 
    CREATED = 1 
    ACTIVE = 2 
    PARTIAL_END = 3
    END = 4


# @DeprecationWarning
# class Session:

#     """
#     Experimental class for handling sessions. This is not in use.
#     """

#     def __init__(self, data: SessionData) -> None:
        
#         self.source_model_id = data.source_model_id
#         self.destination_model_id = data.destination_model_id
        
#         # Initiator and invitee IDs
#         self.initiator_id = data.initiator_id
#         self.invitee_id = data.invitee_id

#         # Data and flags
#         self.data = {var: None for var in set(data.input_variables_id) | set(data.output_variables_id)},
#         self.flags = {var: 0 for var in set(data.input_variables_id) | set(data.output_variables_id)},
#         self.sizes = {**dict(zip(data.input_variables_id, data.input_variables_size)),
#                       **dict(zip(data.output_variables_id, data.output_variables_size))}

#         # UUIDs for the initiator and invitee
#         # UUIDs are used to identify the session
#         self.initiator_uuid = None
#         self.invitee_uuid = None

#         self.status = SessionStatus.UNKNOWN

#     def add_invitee(self, invitee_data: JoinSessionData):
#         """
#         Adds the invitee to the session.

#         Parameters:
#             invitee_data (JoinSessionData): The data of the invitee to be added to the session.

#         Raises:
#             HTTPException: If the client invitee ID does not match this session's.
#         """
        
#         if self.invitee_id == invitee_data.invitee_id:
#             self.invitee_uuid = invitee_data.session_id.client_id
#         else:
#             return HTTPException(status_code=403, detail="Client invitee ID does not match this session's.")

#     def set_status(self, status: SessionStatus) -> None:
#         """
#         Sets the status of the session.
        
#         Parameters:
#             status (SessionStatus): The status to set the session to.
#         """
#         self.status = status

#     def get_status(self) -> SessionStatus:
#         """
#         Returns the status of the session.

#         Returns:
#             SessionStatus: an enum describing the status of the session.
#         """
#         return self.status
    
#     def disconnect_user(self, client_uuid: str):
#         """
#         Handles the disconnection of a user from the session.

#         Parameters:
#             client_uuid (str): The UUID of the client to disconnect.

#         Raises:
#             HTTPException: If the client ID does not match this session's.
#         """

#         temp_id = None

#         if self.initiator_uuid == client_uuid:
#             temp_id = self.initiator_id
#             self.initiator_uuid = None
#         elif self.invitee_uuid == client_uuid:
#             temp_id = self.invitee_id
#             self.invitee_uuid = None
#         else:
#             return HTTPException(status_code=403, detail="Client ID does not match this session's.")

#         # Clears variables of disconnecting user
#         for var in self.flags[temp_id]:
#             self.data[self.initiator_id][var] = None
#             self.flags[self.initiator_id][var] = 0

#         # Lastly, set the session status
#         if self.initiator_uuid is None and self.invitee_uuid is None:
#             self.set_status(SessionStatus.END)
#         else:
#             self.set_status(SessionStatus.PARTIAL_END)