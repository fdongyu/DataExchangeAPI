program test_start_session
    use high_level_api
    use iso_c_binding, only: c_int, c_double, c_null_char
    implicit none
    type(session_data) :: sd

    ! Initialize session data
    sd%source_model_id = 2001
    sd%destination_model_id = 2005
    sd%initiator_id = 35
    sd%invitee_id = 38
    sd%input_variables_id = [1]
    sd%input_variables_size = [50]
    sd%output_variables_id = [4]
    sd%output_variables_size = [50]

    ! Set the server URL
    call set_server_url("http://127.0.0.1:8000")

    ! Test 1: Start Session Normally
    call start_session(sd)

    ! Test 2: Start Session without URL
    call set_server_url(" ")
    call start_session(sd)  ! Expected to fail or handle the error

    ! Test 3: Invalid Data (negative IDs)
    sd%source_model_id = -1
    call start_session(sd)  ! Expected to fail or handle the error

end program test_start_session
