import socket
import pickle

import const


class Communication:
	"""Object that maintains ways to communicate between programs
	"""

	def __init__(self, my_host: str = socket.gethostname(),
					   my_port: int = const.CLIENT_PORT) -> None:
		"""Initialize network informations

		Args:
			my_host (str, optional): localhost, the IP address of the machine
									 on which this code is executed
			my_port (int, optional): the local port to communicate with,
									 defaults to const.CLIENT_PORT.
		"""
		self.init_worked: bool = False
		self.my_host: str = my_host
		self.my_port: int = my_port
		self.my_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	def close(self) -> None:
		"""Close the socket
		"""
		self.my_socket.close()

	def	send_message(self, obj: any, client_socket: socket.socket = None) -> int:
		"""Send an object of any type preceded by its length

		Args:
			client_socket (socket.socket): the socket with which the message will be send
			object (any): the object to send

		Returns:
			int: 0 if the object has been sent, 1 if it's too large to be sent
		"""
		if client_socket is None:
			client_socket = self.my_socket
		msg = pickle.dumps(obj)
		if len(msg) > const.MAX_MSG_SIZE:
			print('\033[31m' + "Error : message too big" + '\033[0m')
			return 1
		client_socket.send(bytes(f'{len(msg):<{const.HEADER_SIZE}}', 'utf8') + msg)
		return 0

	def receive_message(self, client_socket: socket.socket = None, waiting_time: float = 1) -> any:
		"""Wait for a message and return it if it arrive

		Args:
			client_socket (socket.socket): the socket from which we are waiting for a message
			waiting_time (float, optional): the time in seconds before aborting, defaults to 1sec.

		Returns:
			any: an object of any type received from the socket,
				 None if 'waiting_time' is up and no message has been catch
		"""
		if client_socket is None:
			client_socket = self.my_socket
		client_socket.settimeout(waiting_time)
		try:
			header = client_socket.recv(const.HEADER_SIZE).decode('utf8')
		except socket.timeout:
			return None
		return pickle.loads(client_socket.recv(int(header)))


class CommunicationServer(Communication):

	def __init__(self, my_host: str = socket.gethostname(),
					   my_port: int = const.SERVER_PORT) -> None:
		"""Initialize network informations of the server and wait for 2 players to connect

		Args:
			my_host (str, optional): localhost, the IP address of the machine
									 on which this code is executed
			my_port (int, optional): the local port to communicate with
		"""     
		super().__init__(my_host, my_port)
		self.my_socket.bind((my_host, my_port))
		self.my_socket.listen(2)
		print(f"\033[92mServer running on {self.my_host}\033[0m")
		self.players_sockets: list[socket.socket, socket.socket] = [None, None]
		self.my_socket.settimeout(const.LOBBY_TIMEOUT)
		try:
			for player in range(2):
				print(f"\033[1;36m... waiting for {2 - player} player{"s" if not player else ""} ...\033[0m", end='\r')
				self.players_sockets[player], player_ip = self.my_socket.accept()
				print(f"\033[1mPlayer {player + 1}\033[0m connected from \033[1m{player_ip}\033[0m")
				if not player:
					self.send_message("Please wait for the second player to connect", self.players_sockets[0])
			self.send_message("Ready to play !", self.players_sockets[0])
			self.send_message("Ready to play !", self.players_sockets[1])
		except socket.timeout:
			if self.players_sockets[0]:
				self.send_message("\033[31mNo match found\033[0m", self.players_sockets[0])
				print(self.receive_message(self.players_sockets[0]), 13 * ' ')
			else:
				print("\033[31mNo player found\033[0m", 13 * ' ')
			self.close()
			return
		msg = self.receive_message(self.players_sockets[0])
		if msg == self.receive_message(self.players_sockets[1]):
			print(msg)
		else:
			print("\033[31mError : shouldn't arrive here\033[0m")
			self.close()
			return
		self.init_worked = True


class CommunicationPlayer(Communication):

	def __init__(self, server_host: str = socket.gethostname(),
						server_port : int = const.SERVER_PORT,
					   my_host: str = socket.gethostname(),
					   my_port: int = const.CLIENT_PORT) -> None:
		"""Initialize network informations of the local player and the server

		Args:
			server_host (str, optional): the IP address of the machine that
										 run the server, defaults to localhost.
			server_port (int, optional): the port on which communicate with the server
			my_host (str, optional): localhost, the IP address of the machine
									 on which this code is executed
			my_port (int, optional): the local port to communicate with
		"""
		super().__init__(my_host, my_port)
		try:
			self.my_socket.connect((server_host, server_port))
		except ConnectionRefusedError:
			print("\033[31mServer not found\033[0m")
			self.close()
			return
		msg = self.receive_message()
		print(msg)
		if msg != "Ready to play !":
			msg = self.receive_message(waiting_time=const.LOBBY_TIMEOUT + 1)
			print(msg)
		self.send_message(msg)
		if msg != "Ready to play !":
			self.close()
			return
		self.init_worked = True
