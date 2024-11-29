from communication import CommunicationServer


test = CommunicationServer()
if test.init_worked:
	test.my_socket.close()
	exit(0)
else:
	exit(1)
