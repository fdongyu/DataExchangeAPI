program e3sm_test
    use high_level_api
    use low_level_fortran_interface
    use iso_c_binding, only: c_int, c_double, c_null_char
    implicit none
    type(session_data) :: sd
    type(SessionID) :: id
    real(c_double), dimension(50) :: arr_send
    integer :: var_to_send, send_status, loop_index
    real(c_double), dimension(:), allocatable :: arr_receive
    integer :: status_receive     ! Corrected type for status_receive
    integer :: receive_var_id, receive_var_size
    integer :: i  ! Declaration for the loop index
    integer :: join_status
    integer(c_int) :: session_status
    character(len=1024) :: URL

    URL = "https://dataexchange.cis240199.projects.jetstream-cloud.org"
    ! Set the server URL at runtime
    ! call set_server_url("http://127.0.0.1:8000")
    call set_server_url(URL)

    ! User sets values directly
    sd%source_model_ID = 2001
    sd%destination_model_ID = 2005
    sd%initiator_id = 35
    sd%invitee_id = 38
    sd%input_variables_ID = [1]
    sd%input_variables_size = [50]
    sd%output_variables_ID = [4]
    sd%output_variables_size = [50]

    ! Write the session_ID for the whole program
    id = start_session(sd)

    print *, "Source Model ID: ", id%source_model_id
    print *, "Destination Model ID: ", id%destination_model_id
    print *, "Initiator ID: ", id%initiator_id
    print *, "Invitee ID: ", id%invitee_id
    print *, "Session ID: ", id%instance_id

    call set_session_id(id)

    ! Join the session
    ! Check the session status first
    session_status = retrieve_session_status(id)
    if (session_status == 1) then
        print *, "Session status is 'created'"
        join_status = join_session_with_retries(id, sd%invitee_id, 5, 5)
        if (join_status == 1) then
            print *, "Joined the session successfully."
        else
            print *, "Not able to join properly."
        endif
    else
        print *, "Current status of session: ", session_status
    endif
    ! Exit


    ! Send data to the server
    var_to_send = 4
    ! Initialize data array
    do loop_index = 1, 50
        arr_send(loop_index) = real(loop_index, kind=c_double)
    end do
    ! Call the function and capture the return status
    send_status = send_data_with_retries(var_to_send, arr_send, 5, 5)

    print *, "Status of send operation:", send_status
    print *, "------ Sleeping for 1 second ------"
    call sleep(1)

    receive_var_id = 4
    if (check_data_availability_with_retries(receive_var_id, 5, 5) == 1) then
        ! Proceed with data retrieval
        receive_var_size = retrieve_variable_size(id, receive_var_id)
        
        if (receive_var_size > 0) then
            print *, "Variable size for ID", receive_var_id, "is", receive_var_size
            ! Allocate the receive array
            allocate(arr_receive(receive_var_size))
            
            status_receive = receive_data_with_retries(receive_var_id, arr_receive, 5, 5)
            if (status_receive == 1) then
                ! Print received data
                print *, "Received data:"
                do i = 1, receive_var_size
                    print *, "arr_receive(", i, ") = ", arr_receive(i)
                end do
            else
                print *, "Failed to receive data for variable ID:", receive_var_id
            endif
        else
            print *, "Failed to retrieve variable size for ID", receive_var_id
        endif
    else
        ! Handle the case where data is not available
        print *, "Data is not available after retries."
    endif

    ! Clean up allocated resources if allocated
    if (allocated(arr_receive)) then
        deallocate(arr_receive)
    endif
    print *, "------ Sleeping for 1 second ------"
    call sleep(1)

    ! End the session
    call end_session_now(sd%invitee_id)

end program e3sm_test
