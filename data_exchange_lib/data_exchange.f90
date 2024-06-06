module data_exchange
  use iso_c_binding, only: c_char, c_double, C_NULL_CHAR
  use http_interface
  implicit none

  character(len=256) :: server_url = ""  ! Dynamic server URL
  integer(c_int), dimension(5) :: session_id
  integer(c_int) :: invitee_id
  ! [source_model_ID, destination_model_ID, initiator_id, invitee_id, unique_counter]
  integer :: var_send  ! Global variable ID for sending data
  integer :: var_receive  ! Global variable ID for receiving data
  logical :: server_url_set = .false.    ! Flag to check if server URL has been set

  type session_data
    integer :: source_model_ID
    integer :: destination_model_ID
    integer :: initiator_id
    integer :: invitee_id
    integer, dimension(:), allocatable :: input_variables_ID
    integer, dimension(:), allocatable :: input_variables_size
    integer, dimension(:), allocatable :: output_variables_ID
    integer, dimension(:), allocatable :: output_variables_size
  end type session_data

contains

  !===============================================================================
  subroutine set_server_url(url)
    character(len=*), intent(in) :: url
    if (len(trim(url)) > 0) then
      server_url = trim(url)
      server_url_set = .true.
    else
      print *, "Error: Invalid server URL provided."
      server_url_set = .false.
    endif
  end subroutine set_server_url

  !===============================================================================

  subroutine set_session_id(id)
    integer(c_int), dimension(5), intent(in) :: id
    session_id = id
  end subroutine set_session_id
  
  !===============================================================================

  subroutine start_session(sd)
    type(session_data), intent(inout) :: sd

    ! Create a session with the server using the data from 'sd'
    call create_session(trim(server_url)// C_NULL_CHAR, sd%source_model_ID, sd%destination_model_ID, &
                          sd%initiator_id, sd%invitee_id, sd%input_variables_ID, &
                          sd%input_variables_size, size(sd%input_variables_ID), &
                          sd%output_variables_ID, sd%output_variables_size, &
                          size(sd%output_variables_ID))
    ! No cleanup needed here as 'sd' is managed by the calling program
  end subroutine start_session

  !===============================================================================

  subroutine join_session()
      use http_interface               
      use iso_c_binding, only: c_int
      implicit none

      ! Call the C function to join a session
      call join_session_c(trim(server_url)// C_NULL_CHAR, session_id, invitee_id)

  end subroutine join_session

  !===============================================================================

  subroutine check_session_availability()
    ! Checks the availability of sessions and prints their statuses
    if (.not. server_url_set) then
        print *, "Error: Server URL not set. Please set a valid server URL before checking session statuses."
        return
    endif

    ! Call the C binding to print all session statuses
    call print_all_session_statuses(trim(server_url) // C_NULL_CHAR)
  end subroutine check_session_availability

  !===============================================================================

  subroutine check_specific_session_flags(session_ids)
    integer, dimension(:), intent(in) :: session_ids
    ! Checks and prints the flag status for the variables of a specific session
    if (.not. server_url_set) then
        print *, "Error: Server URL not set. Please set a valid server URL before checking variable flags."
        return
    endif

    ! Ensure session IDs are passed correctly
    if (size(session_ids) /= 5) then
        print *, "Error: Invalid session ID array size."
        return
    endif

    ! Call the C binding to print all variable flags for the session
    call print_all_variable_flags(trim(server_url) // C_NULL_CHAR, session_ids)
  end subroutine check_specific_session_flags

  !===============================================================================

  subroutine get_specific_variable_size(session_ids, var_id, var_size, status)
    integer, dimension(:), intent(in) :: session_ids
    integer, intent(in) :: var_id
    integer, intent(out) :: var_size
    integer, intent(out) :: status

    ! Call the low-level API function to get the size
    var_size = get_variable_size(trim(server_url)//C_NULL_CHAR, session_ids, var_id)

    ! Status checking after API call
    if (var_size < 0) then
      print *, "Error: Unable to get variable size for ID", var_id
      status = -1  ! Indicating an error
    else
      status = 0   ! Indicating success
    end if
  end subroutine get_specific_variable_size


  !===============================================================================

  subroutine send_data_with_retries(var_send, arr_send, max_retries, sleep_time)
      use http_interface           
      use iso_c_binding, only: c_double 
      implicit none

      integer, intent(in) :: var_send, max_retries, sleep_time
      real(c_double), dimension(:), intent(in) :: arr_send

      ! Variable declarations
      integer :: arr_length                                ! Length of the array to send
      integer :: i                                         ! Loop variable
      integer :: flag                                      ! Flag to check status
      integer :: retries                                   ! Retry count allowed
      integer :: status_send                               ! Status of the send operation

      retries = 0                                          ! Initialize retry counter

      ! Prepare data array
      arr_length = get_variable_size(trim(server_url)// C_NULL_CHAR, session_id, var_send)

      ! Attempt to send data with retries
      do while (retries < max_retries)
          flag = get_variable_flag(trim(server_url)// C_NULL_CHAR, session_id, var_send)
          print *, "Flag status:", flag

          if (flag == 0) then
              status_send = send_data(trim(server_url)// C_NULL_CHAR, session_id, var_send, arr_send, arr_length)
              if (status_send == 1) then
                  print *, "Data successfully sent."
                  exit
              else
                  print *, "Failed to send data, retrying..."
              end if
          else
              print *, "Flag is not set for sending, retrying..."
              retries = retries + 1
          call sleep(sleep_time)
          end if
      end do

      ! Check if maximum retries have been exceeded
      if (retries >= max_retries) then
          print *, "Failed to send data for var_id", var_send, "after", max_retries, "attempts due to flag status."
      endif

      ! Clean up
    !   deallocate(arr_send)

  end subroutine send_data_with_retries
  !===============================================================================

  subroutine recv_data_with_retries(var_receive, arr_receive, max_retries, sleep_off_time)
      use http_interface              
      use iso_c_binding, only: c_double  
      implicit none

      integer, intent(in) :: var_receive, max_retries, sleep_off_time
      real(c_double), dimension(:), intent(inout) :: arr_receive

      ! Variable declarations
      integer :: arr_length                                     ! Length of the array to receive
      integer :: i                                              ! Loop variable
      integer :: flag                                           ! Flag to check status
      integer :: retries                                        ! Retry count allowed
      integer :: status_receive                                 ! Status of the receive operation
      
      retries = 0                                               ! Initialize retry counter

      ! Determine the size of the data to be received and allocate memory
      arr_length = get_variable_size(trim(server_url)// C_NULL_CHAR, session_id, var_receive)

      ! Attempt to receive data with retries
      do while (retries < max_retries)
          flag = get_variable_flag(trim(server_url)// C_NULL_CHAR, session_id, var_receive)
          print *, "Flag status:", flag

          if (flag == 1) then
              print *, "Flag set, attempting to receive data..."
              status_receive = receive_data(trim(server_url)// C_NULL_CHAR, session_id, var_receive, arr_receive, arr_length)
              if (status_receive == 1) then
                  print *, "Data received successfully:"
                  do i = 1, arr_length
                      print *, "arr_receive(", i, ") = ", arr_receive(i)
                  end do
                  exit
              else
                  print *, "Failed to fetch data, retrying..."
              end if
          else
              print *, "Flag not set for receiving, retrying..."
              retries = retries + 1
              call sleep(sleep_off_time)
          end if
      end do

      ! Check if maximum retries have been exceeded
      if (retries >= max_retries) then
          print *, "Failed to receive data for var_id:", var_receive, "after", max_retries, "attempts due to flag status."
      endif

  end subroutine recv_data_with_retries

  !===============================================================================

  subroutine end_session_now(user_id)
      use http_interface                  ! Include module for HTTP interface methods
      use iso_c_binding, only: c_int      ! Use ISO C binding to ensure compatibility with C types
      implicit none

      integer(c_int), intent(in) :: user_id


      ! End the session with the server
      call end_session(trim(server_url)// C_NULL_CHAR, session_id, user_id)

  end subroutine end_session_now

  !===============================================================================

end module data_exchange