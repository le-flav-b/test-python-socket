from communication import CommunicationPlayer


test = CommunicationPlayer()
if test.init_worked:
	test.my_socket.close()
	exit(0)
else:
	exit(1)
