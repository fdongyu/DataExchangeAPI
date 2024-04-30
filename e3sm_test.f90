module data_exchange_test
  use iso_c_binding, only: c_char, C_NULL_CHAR
  use http_interface

  implicit none

    character(len=256), parameter :: url = "http://10.249.0.171:8000" // C_NULL_CHAR
    character(len=100), parameter :: client_id = "ClientA" // C_NULL_CHAR

contains

 ! This function needs to be in data_exchange.f90
  subroutine start_session()

    implicit none

    ! Declare variables related to session management and data transmission.
    integer, dimension(:), allocatable :: input_variables_ID, input_variables_size
    integer, dimension(:), allocatable :: output_variables_ID, output_variables_size
    real(c_double), dimension(:), allocatable :: arr_send, arr_receive

    ! Session and model information variables.
    integer :: source_model_ID, destination_model_ID
    integer :: initiator_id, inviter_id
    integer :: no_of_input_variables, no_of_output_variables
    integer :: arr_length, i
    integer :: status_send, status_receive

    ! Variable identifiers for sending and receiving.
    integer :: var_send, var_receive

    ! Intialize variables for the session
    source_model_ID = 2001
    destination_model_ID = 2005
    initiator_id = 35
    inviter_id = 36

    ! Initialize session information and input/output variable arrays.
    no_of_input_variables = 3
    no_of_output_variables = 3
    allocate(input_variables_ID(no_of_input_variables))
    allocate(input_variables_size(no_of_input_variables))
    allocate(output_variables_ID(no_of_output_variables))
    allocate(output_variables_size(no_of_output_variables))

    input_variables_ID = [1, 2, 3]
    input_variables_size = [20, 20, 20]
    output_variables_ID = [4, 5, 6]
    output_variables_size = [20, 20, 20]

    ! Create a session with the server.
    call create_session_c(trim(url), source_model_ID, destination_model_ID, trim(client_id), &
                          initiator_id, inviter_id, input_variables_ID, input_variables_size, &
                          no_of_input_variables, output_variables_ID, output_variables_size, &
                          no_of_output_variables)
    ! Clean up the ID and size arrays to free memory.
    deallocate(input_variables_ID, input_variables_size, output_variables_ID, output_variables_size)

  end subroutine start_session

  !===============================================================================

  ! This function needs to be in data_exchange.f90
  subroutine join_session()
      use http_interface               
      use iso_c_binding, only: c_int    
      implicit none

      ! Variable declarations
      integer(c_int), dimension(5) :: session_id ! Array to hold session identifiers and flags

      ! Initialize session identifiers
      session_id = [2001,2005,35,36,1]   ! [source_model_ID, destination_model_ID, initiator_id, inviter_id, unique_counter]

      ! Call the C function to join a session
      call join_session_c(trim(url), session_id, client_id)

  end subroutine join_session

  !===============================================================================

  ! This function needs to be in data_exchange.f90 (similar one but not for testing).
  subroutine send_data_test()
      use http_interface           
      use iso_c_binding, only: c_double 
      implicit none

      ! Variable declarations
      real(c_double), dimension(:), allocatable :: arr_send ! Array for data to send
      integer :: arr_length                                ! Length of the array to send
      integer :: i                                         ! Loop variable
      integer :: flag                                      ! Flag to check status
      integer :: retries, max_retries                      ! Retry count and maximum retries allowed
      integer :: status_send                               ! Status of the send operation
      integer(c_int), dimension(5) :: session_id           ! Session identifiers
      integer :: var_send                                  ! Variable ID for sending data
      integer :: sleep_off_time                            ! Sleep time between retries in seconds

      ! Initialization of session parameters
      session_id = [2001, 2005, 35, 36, 1]                 ! Define session ID
      var_send = 1                                         ! Set variable ID for sending data
      sleep_off_time = 3                                   ! Set sleep offset time between retries
      max_retries = 5                                      ! Set maximum number of retries
      retries = 0                                          ! Initialize retry counter

      ! Retrieve session and flag status
      call get_all_session_statuses(trim(url))
      call get_flags(trim(url), session_id)

      ! Prepare data array
      arr_length = get_variable_size_c(trim(url), session_id, var_send)
      print *, 'Array length to send:', arr_length
      allocate(arr_send(arr_length))
      arr_send = [(real(i, kind=c_double), i = 1, arr_length)]

      ! Attempt to send data with retries
      do while (retries < max_retries)
          flag = get_variable_flag_c(trim(url), session_id, var_send)
          print *, "Flag status:", flag

          if (flag == 0) then
              status_send = send_data_to_server(trim(url), session_id, var_send, arr_send, arr_length)
              if (status_send == 1) then
                  print *, "Data successfully sent."
                  exit
              else
                  print *, "Failed to send data, retrying..."
              end if
          else
              print *, "Flag is not set for sending, retrying..."
              retries = retries + 1
              call sleep(sleep_off_time)
          end if
      end do

      ! Check if maximum retries have been exceeded
      if (retries >= max_retries) then
          print *, "Failed to send data for var_id", var_send, "after", max_retries, "attempts due to flag status."
      endif

      ! Clean up
      deallocate(arr_send)

  end subroutine send_data_test
  !===============================================================================

  ! This function needs to be in data_exchange.f90 (similar one but not for testing purpose).
  subroutine recv_data_test()
      use http_interface              
      use iso_c_binding, only: c_double  
      implicit none

      ! Variable declarations
      real(c_double), dimension(:), allocatable :: arr_receive  ! Array to receive data
      integer :: arr_length                                     ! Length of the array to receive
      integer :: i                                              ! Loop variable
      integer :: flag                                           ! Flag to check status
      integer :: retries, max_retries                           ! Retry count and maximum retries allowed
      integer :: status_receive                                 ! Status of the receive operation
      integer(c_int), dimension(5) :: session_id                ! Session identifiers
      integer :: var_receive                                    ! Variable ID for receiving data
      integer :: sleep_time, base_sleep_time                    ! Sleep times between retries

      ! Initialization of session parameters and retry logic
      session_id = [2001, 2005, 35, 36, 1]                      ! Define session ID
      var_receive = 4                                           ! Set variable ID for receiving data
      sleep_time = 5                                            ! Set sleep time
      max_retries = 10                                          ! Set maximum number of retries
      retries = 0                                               ! Initialize retry counter

      ! Retrieve session flags
      call get_flags(trim(url), session_id)

      ! Determine the size of the data to be received and allocate memory
      arr_length = get_variable_size_c(trim(url), session_id, var_receive)
      allocate(arr_receive(arr_length))

      ! Attempt to receive data with retries
      do while (retries < max_retries)
          flag = get_variable_flag_c(trim(url), session_id, var_receive)
          print *, "Flag status:", flag

          if (flag == 1) then
              print *, "Flag set, attempting to receive data..."
              status_receive = receive_data_from_server(trim(url), session_id, var_receive, arr_receive, arr_length)
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
              call sleep(sleep_time)
          end if
      end do

      ! Check if maximum retries have been exceeded
      if (retries >= max_retries) then
          print *, "Failed to receive data for var_id:", var_receive, "after", max_retries, "attempts due to flag status."
      endif

      ! Clean up allocated resources
      deallocate(arr_receive)

  end subroutine recv_data_test

  !===============================================================================
  ! This function needs to be in data_exchange.f90

  subroutine end_session()
      use http_interface                  ! Include module for HTTP interface methods
      use iso_c_binding, only: c_int      ! Use ISO C binding to ensure compatibility with C types
      implicit none

      ! Variable declaration
      integer(c_int), dimension(5) :: session_id  ! Array to hold session identifiers

      ! Initialize session identifiers
      session_id = [2001, 2005, 35, 36, 1]        ! Define session IDs [source_model_ID, destination_model_ID, initiator_id, inviter_id, unique_identifier]

      ! End the session with the server
      call end_session_c(trim(url), session_id, trim(client_id))

  end subroutine end_session

end module data_exchange_test

program e3sm_test
    use data_exchange_test           ! Include module for data exchange routines
    implicit none

    ! Start the session
    call start_session()
    print *, "------ Sleeping for 10 seconds ------"
    call sleep(10)

    ! Join the session (if needed)
    ! call join_session()
    ! print *, "------ Sleeping for 10 seconds ------"
    ! call sleep(10)

    ! Send data to the server
    call send_data_test()
    print *, "------ Sleeping for 10 seconds ------"
    call sleep(10)

    ! Receive data from the server
    call recv_data_test()
    print *, "------ Sleeping for 10 seconds ------"
    call sleep(10)

    ! End the session
    call end_session()

end program e3sm_test
