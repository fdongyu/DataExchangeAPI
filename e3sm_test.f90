program e3sm_test
    use data_exchange
    implicit none
    type(session_data) :: sd
    integer(c_int), dimension(5) :: id
    real(c_double), dimension(50) :: arr_send
    integer :: i
    real(c_double), dimension(:), allocatable :: arr_receive
    integer :: arr_receive_length
    integer :: var_receive_size, var_receive_status

    ! Set the server URL at runtime
    call set_server_url("http://10.252.1.95:8080")

    ! User sets values directly
    sd%source_model_ID = 2001
    sd%destination_model_ID = 2005
    sd%initiator_id = 35
    sd%invitee_id = 36
    sd%input_variables_ID = [1]
    sd%input_variables_size = [50]
    sd%output_variables_ID = [4]
    sd%output_variables_size = [50]

    ! write the session_ID for whole program
    id = [2001, 2005, 35, 36, 1]
    call set_session_id(id)

    ! Start the session
    call start_session(sd)
    print *, "------ Sleeping for 10 seconds ------"
    call sleep(10)

    ! Join the session (if needed)
    ! call join_current_session()
    ! print *, "------ Sleeping for 10 seconds ------"
    ! call sleep(10)

    ! Check session availability
    call check_session_availability()

    ! If needed, also check specific session flags
    call check_specific_session_flags(session_id)
    
    ! Send data to the server
    var_send = 4
    ! Initialize data array
    do i = 1, 50
        arr_send(i) = real(i, kind=c_double)
    end do
    call send_data_with_retries(var_send, arr_send, 5, 5)
    print *, "------ Sleeping for 10 seconds ------"
    call sleep(10)

    ! Receive data from the server
    var_receive = 1
    call get_specific_variable_size(session_id, var_receive, var_receive_size, var_receive_status)
    if (var_receive_status == 0) then
        print *, "Variable size for ID", var_receive, "is", var_receive_size
    else
        print *, "Failed to retrieve variable size for ID", var_receive
    endif

    ! Allocate the receive array
    allocate(arr_receive(var_receive_size))
    call recv_data_with_retries(var_receive,arr_receive, 5 ,5)
    ! Clean up allocated resources
    deallocate(arr_receive)
    print *, "------ Sleeping for 10 seconds ------"
    call sleep(10)

    ! End the session
    call end_session_now(sd%initiator_id)

end program e3sm_test
