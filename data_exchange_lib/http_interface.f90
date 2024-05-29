module http_interface
    use, intrinsic :: iso_c_binding, only: c_int, c_char, c_double
    implicit none

    ! Define interfaces to C functions for HTTP interactions
    interface
        ! Creates a new session on the server
        subroutine create_session(url, source_model_ID, destination_model_ID, &
                                    initiator_id, invitee_id, input_variables_ID, input_variables_size, &
                                    no_of_input_variables, output_variables_ID, output_variables_size, &
                                    no_of_output_variables) bind(C)
            import
            character(kind=c_char), intent(in) :: url(*)
            integer(c_int), value :: source_model_ID, destination_model_ID
            integer(c_int), value :: initiator_id, invitee_id
            integer(c_int), intent(in) :: input_variables_ID(*), input_variables_size(*)
            integer(c_int), value :: no_of_input_variables
            integer(c_int), intent(in) :: output_variables_ID(*), output_variables_size(*)
            integer(c_int), value :: no_of_output_variables
        end subroutine create_session

        ! Joins an existing session on the server
        subroutine join_session_c(url, session_id, invitee_id) bind(C)
            import
            character(kind=c_char), intent(in) :: url(*)
            integer(c_int), intent(in) :: session_id(*)
            integer(c_int), value :: invitee_id
        end subroutine join_session_c


        ! Retrieves and print the status of all sessions from the server
        subroutine print_all_session_statuses(url) bind(C)
            import :: c_char
            character(kind=c_char), intent(in) :: url(*)
        end subroutine print_all_session_statuses

        ! Retrieves and print flag status for a given session
        subroutine print_all_variable_flags(base_url, session_id) bind(C)
            import :: c_char, c_int
            character(kind=c_char), intent(in) :: base_url(*)
            integer(c_int), intent(in) :: session_id(*)
        end subroutine print_all_variable_flags

        ! Gets the flag status for a specific variable
        function get_variable_flag(base_url, session_id, var_id) bind(C)
            import :: c_char, c_int
            character(kind=c_char), intent(in) :: base_url(*)
            integer(c_int), intent(in) :: session_id(*)
            integer(c_int), value :: var_id
            integer(c_int) :: get_variable_flag
        end function get_variable_flag

        ! Gets the size of a variable from the server
        function get_variable_size(base_url, session_id, var_id) bind(C)
            import :: c_char, c_int
            character(kind=c_char), intent(in) :: base_url(*)
            integer(c_int), intent(in) :: session_id(*)
            integer(c_int), value :: var_id
            integer(c_int) :: get_variable_size
        end function get_variable_size


        ! Sends data to the server
        function send_data(url, session_id, var_id, arr, n) bind(C)
            import :: c_char, c_int, c_double
            character(kind=c_char), intent(in) :: url(*)
            integer(c_int), intent(in) :: session_id(*)
            integer(c_int), value :: var_id
            real(c_double), intent(in) :: arr(*)
            integer(c_int), value :: n
            integer(c_int) :: send_data
        end function send_data
        
        ! Receives data from the server
        function receive_data(url, session_id, var_id, arr, n) bind(C)
            import :: c_char, c_int, c_double
            character(kind=c_char), intent(in) :: url(*)
            integer(c_int), intent(in) :: session_id(*)
            integer(c_int), value :: var_id
            real(kind=c_double), intent(out) :: arr(*)
            integer(c_int), value :: n
            integer(c_int) :: receive_data
        end function receive_data

        ! Ends a session on the server
        subroutine end_session(server_url, session_id, user_id) bind(C)
            import :: c_char, c_int
            character(kind=c_char), intent(in) :: server_url(*)
            integer(c_int), intent(in) :: session_id(*)
            integer(c_int), value :: user_id 
        end subroutine end_session

    end interface

end module http_interface