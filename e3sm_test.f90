program e3sm_test
    use data_exchange
    implicit none
    type(session_data) :: sd
    integer(c_int), dimension(5) :: id

    ! Set the server URL at runtime
    call set_server_url("http://10.249.0.64:8080")


    ! User sets values directly
    sd%source_model_ID = 2001
    sd%destination_model_ID = 2005
    sd%initiator_id = 35
    sd%inviter_id = 36
    sd%input_variables_ID = [1, 2, 3]
    sd%input_variables_size = [20, 20, 20]
    sd%output_variables_ID = [4, 5, 6]
    sd%output_variables_size = [20, 20, 20]

    ! write the session_ID for whole program
    id = [2001, 2005, 35, 36, 1]
    call set_session_id(id)

    call set_var_send(1)  ! Setting variable ID for sending data
    call set_var_receive(4)  ! Setting variable ID for receiving data

    ! Start the session
    call start_session(sd)
    print *, "------ Sleeping for 10 seconds ------"
    call sleep(10)

    ! Join the session (if needed)
    ! call join_session()
    ! print *, "------ Sleeping for 10 seconds ------"
    ! call sleep(10)

    ! Send data to the server
    call send_data_with_retries()
    print *, "------ Sleeping for 10 seconds ------"
    call sleep(10)

    ! Receive data from the server
    call recv_data_with_retries()
    print *, "------ Sleeping for 10 seconds ------"
    call sleep(10)

    ! End the session
    call end_session()

end program e3sm_test
