from cyberwater_library import *
import time

# # Define parameters for the session
# source_model_ID = 2001
# destination_model_ID = 2005
# initiator_id = 35
# inviter_id = 36
# input_variables_ID = [1, 2, 3]  # Example input variable IDs
# input_variables_size = [20, 20, 20]  # Corresponding sizes of the input variables
# output_variables_ID = [4, 5, 6]  # Example output variable IDs
# output_variables_size = [20, 20, 20]  # Corresponding sizes of the output variables

# # Create a new session with the defined parameters
# # This includes details about both input and output variables along with their sizes
# session_response = create_session(
#     source_model_ID, 
#     destination_model_ID, 
#     initiator_id, 
#     inviter_id, 
#     len(input_variables_ID), 
#     input_variables_ID, 
#     input_variables_size, 
#     len(output_variables_ID), 
#     output_variables_ID, 
#     output_variables_size
# )

# # Extract the session ID from the response
# session_id = session_response.get('session_id')

# # Output the received session ID or a default message if not found
# print(f"Session ID received: {session_id if session_id else 'No session ID returned'}")

# Join the existing session using a predefined session ID
session_id_list = [2001, 2005, 35, 36, 1]
session_id = array_to_string(session_id_list)
join_session(session_id)

# Fetch and print the flags for the all sessions
print_all_session_statuses()

# Fetch and print the flags for the session
print_all_variable_flags(session_id)

# Sleep
print("------ Sleeping for 10 seconds ------")
time.sleep(10)

# Prepare example data to send
var_send_id = 4  # Placeholder for variable ID to send data to
get_variable_size(session_id=session_id, var_id=var_send_id)
start_send_time = time.time()
arr_length = get_variable_size(session_id=session_id, var_id=var_send_id)
data_array = list(range(30, 30+arr_length))  # Example data range
check_and_send_data(session_id, var_send_id, data_array)
end_send_time = time.time()
sending_time = end_send_time - start_send_time


# Sleep
print("------ Sleeping for 10 seconds ------")
time.sleep(10)

# Attempt to receive data for a specified variable
var_receive_id = 1  # Placeholder for variable ID to receive data from
get_variable_size(session_id=session_id, var_id=var_receive_id)
print("------ Sleeping for 10 seconds ------")
start_processing_time = time.time()
check_and_receive_data(session_id, var_receive_id)
end_processing_time = time.time()
processing_time = end_processing_time - start_processing_time

print("------ Analysis for varible length: ", arr_length, " ------")
print("Array sending time:", sending_time, "seconds")
print("Array processing time:", processing_time, "seconds")

# Sleep before ending the session to ensure all processes complete
time.sleep(10)

# Terminate the session
end_session(session_id)
