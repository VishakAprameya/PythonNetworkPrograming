#! usr/bin/python 

import socket

target_host = "0.0.0.0"
target_port = 9999 # http port 

#creating the socket
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#connect the socket
client.connect((target_host, target_port))
#send some data
client.send("I am vishak aprameya")
#receive data	
response = client.recv(4096)
#print data
print response