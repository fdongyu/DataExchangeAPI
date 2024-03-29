program e3sm

  use session_send_recv

  implicit none

  call start_session() 
  
  call sleep(50)

  !call send_data_test()

  call recv_data_test()

  !call sleep(10)

  !call end_session()

end program e3sm
