program e3sm_test
    use data_exchange
    implicit none
    type(session_data) :: sd
    integer(c_int), dimension(5) :: id
    real(c_double), dimension(50) :: arr_send
    integer :: var_to_send, send_status, loop_index
    real(c_double), dimension(:), allocatable :: arr_receive
    integer :: receive_length, receive_var_size, receive_status, receive_var_id

    ! Set the server URL at runtime
    call set_server_url("http://10.249.0.85:8000")

    ! User sets values directly
    sd%source_model_ID = 2001
    sd%destination_model_ID = 2005
    sd%initiator_id = 35
    sd%invitee_id = 38
    sd%input_variables_ID = [1]
    sd%input_variables_size = [50]
    sd%output_variables_ID = [4]
    sd%output_variables_size = [50]

    ! write the session_ID for whole program
    id = [2001, 2005, 35, 38, 1]
    call set_session_id(id)

    ! Start the session
    call start_session(sd)
    print *, "------ Sleeping for 10 seconds ------"
    call sleep(10)

    ! Check session availability
    call check_session_availability()

    ! If needed, also check specific session flags
    call check_specific_session_flags(session_id)
    
    ! Send data to the server
    var_to_send = 4
    ! Initialize data array
    do loop_index = 1, 50
        arr_send(loop_index) = real(loop_index, kind=c_double)
    end do
    ! Call the function and capture the return status
    send_status = send_data_with_retries(var_to_send, arr_send, 5, 5)
    print *, "Status of send operation:", send_status
    print *, "------ Sleeping for 10 seconds ------"
    call sleep(10)

    ! Receive data from the server
    receive_var_id = 1
    call get_specific_variable_size(session_id, receive_var_id, receive_var_size, receive_status)
    if (receive_status == 0) then
        print *, "Variable size for ID", receive_var_id, "is", receive_var_size
    else
        print *, "Failed to retrieve variable size for ID", receive_var_id
    endif

    ! Allocate the receive array
    allocate(arr_receive(receive_var_size))
    call recv_data_with_retries(receive_var_id, arr_receive, 5 ,5)
    ! Clean up allocated resources
    deallocate(arr_receive)
    print *, "------ Sleeping for 10 seconds ------"
    call sleep(10)

    ! End the session
    call end_session_now(sd%initiator_id)

end program e3sm_test
