from cyberwater_library import *
import time

# source_model_ID = 2001
# destination_model_ID = 2005
# initiator_id = 35
# inviter_id = 36
# input_variables_ID = [1,2,3]  # Example
# input_variables_size = [20,20,20]  # Example
# output_variables_ID = [4,5,6]  # Example
# output_variables_size = [20,20,20]  # Example

# # Start session
# session_response = create_session(source_model_ID, destination_model_ID, 
#                                     initiator_id, inviter_id, 
#                                     len(input_variables_ID), input_variables_ID, input_variables_size, 
#                                     len(output_variables_ID), output_variables_ID, output_variables_size)
# session_id = session_response.get('session_id')

# Join session
session_id = [2001, 2005, 35, 36, 1]
session_id = array_to_string(session_id)
join_session(session_id)

get_flags(session_id)

print ("------ Sleeping for 10 seconds ------")
# Pause for setup
time.sleep(10)

# Example data to send
var_send_id = 4  # Placeholder variable ID
data_array = list(range(300, 320))
check_and_send_data(session_id, var_send_id, data_array)
print ("------ Sleeping for 10 seconds ------")
time.sleep(10)


# Receive data
var_receive_id = 1
print ("------ Sleeping for 10 seconds ------")
check_and_receive_data(session_id, var_receive_id)

# Pause before ending session
time.sleep(10)

# End session
end_session(session_id)
