module http_client_interface
    use, intrinsic :: iso_c_binding, only: c_int, c_char, c_double
    implicit none

    interface
        subroutine create_session_c(url, source_model_ID, destination_model_ID, client_id, &
            initiator_id, inviter_id, &
            input_variables_ID, input_variables_size, no_of_input_variables, &
            output_variables_ID, output_variables_size, no_of_output_variables) bind(C)
            import
            character(kind=c_char), intent(in) :: url(*)
            integer(c_int), value :: source_model_ID, destination_model_ID
            character(kind=c_char), intent(in) :: client_id(*)
            integer(c_int), value :: initiator_id, inviter_id
            integer(c_int), intent(in) :: input_variables_ID(*), input_variables_size(*)
            integer(c_int), value :: no_of_input_variables
            integer(c_int), intent(in) :: output_variables_ID(*), output_variables_size(*)
            integer(c_int), value :: no_of_output_variables
        end subroutine create_session_c

        subroutine join_session_c(url, session_id, client_id) bind(C)
            import
            character(kind=c_char), intent(in) :: url(*), client_id(*)
            integer(c_int), intent(in) :: session_id(*)
        end subroutine join_session_c

        subroutine get_all_session_statuses(url) bind(C, name="get_all_session_statuses")
            import :: c_char
            character(kind=c_char), intent(in) :: url(*)
        end subroutine get_all_session_statuses

        subroutine get_flags(base_url, session_id) bind(C, name="get_flags")
            import :: c_char, c_int
            character(kind=c_char), intent(in) :: base_url(*)
            integer(c_int), intent(in) :: session_id(*)
        end subroutine get_flags

        function get_variable_size_c(base_url, session_id, var_id) bind(C, name="get_variable_size_c")
            import :: c_int, c_char
            character(kind=c_char), intent(in) :: base_url(*)
            integer(c_int), intent(in) :: session_id(*)
            integer(c_int), value :: var_id
            integer(c_int) :: get_variable_size_c
        end function get_variable_size_c

        function get_variable_flag_c(base_url, session_id, var_id) bind(C, name="get_variable_flag_c")
            import :: c_int, c_char
            character(kind=c_char), intent(in) :: base_url(*)
            integer(c_int), intent(in) :: session_id(*)
            integer(c_int), value :: var_id
            integer(c_int) :: get_variable_flag_c
        end function get_variable_flag_c

        function send_data_to_server(url, session_id, var_id, arr, n) bind(C, name="send_data_to_server")
            import :: c_int, c_char, c_double
            character(kind=c_char), intent(in) :: url(*)
            integer(c_int), intent(in) :: session_id(*)
            integer(c_int), value :: var_id
            real(c_double), intent(in) :: arr(*)
            integer(c_int), value :: n
            integer(c_int) :: send_data_to_server
        end function send_data_to_server   
        
        function receive_data_from_server(url, session_id, var_id, arr, n) bind(C, name="receive_data_from_server")
            import :: c_int, c_char, c_double
            character(kind=c_char), intent(in) :: url(*)
            integer(c_int), intent(in) :: session_id(*)
            integer(c_int), value :: var_id
            real(kind=c_double), intent(out) :: arr(*)
            integer(c_int), value :: n
            integer(c_int) :: receive_data_from_server
        end function receive_data_from_server

        subroutine end_session_c(server_url, session_id, client_id) bind(C, name="end_session_c")
            import :: c_char, c_int
            character(kind=c_char), intent(in) :: server_url(*), client_id(*)
            integer(c_int), intent(in) :: session_id(*)
        end subroutine end_session_c
        
    end interface
end module http_client_interface
