from cyberwater_high_level import *
# Usage of the module functions
set_server_url("http://10.252.1.58:8000")
session_id = [2001,2005,35,38,1]
set_session_id(session_id)
# session_data = SessionData(1, 2, 3, 4, [1, 2, 3], [10, 20, 30], [4, 5, 6], [40, 50, 60])
# start_session(session_data)
join_session(38)
print(check_specific_session_status(session_id))
print("------ Sleeping for 10 seconds ------")
time.sleep(10)
arr_send = [1]*50
status_send = send_data_with_retries(1, arr_send, 5, 5)
print(f"Status of send operation: {status_send}")
print("------ Sleeping for 10 seconds ------")
time.sleep(10)
arr_receive = recv_data_with_retries(4, 5, 5)
print("------ Sleeping for 10 seconds ------")
time.sleep(10)
end_session_now(38)


# Updates
# Flag of sucessfully sent on E3SM side
# Check_session_availability(session_id) --> Flag whether it is available or not.