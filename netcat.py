#! usr/bin/python	
import sys
import socket 
import getopt
import threading 
import subprocess

# define some global variables
listen			= False
command 		= False
upload 			= False
execute			= ""
target			= ""
upload_destination = ""
port 			= 0

def usage():
	print "netcat.py net tool"
	print 
	print "Usage: netcat.py -t target_host -p port"
	print "-l 		--listen		- listen on [host]:[port] for incomming connection"
	print "-e 		--execute-file-to-run	-	execute the given file upon receiving"
	print "-c 		--command				- initialize a command shell"
	print "-u 		--upload_destination	- upon receiving the connection upload the file and write to destination"
	
	print 
	print 
	print "Examples: "
	print "netcat.py -t 192.168.1.1 -p 2222 -l -c"
	print "netcat.py -t 192.168.1.2 -p 3232 -l -u=c:\\target.exe"
	print "netcat.py -t 192.168.1.2 -p 3232 -l -e=\"cat /etc/passwd\""
	print "echo 'abcdefghi'| ./netcat.py -t 192.168.1.3 -p 135"	
	sys.exit(0)

def client_sender(buffer):
	
	client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	
	try :
		#connect to our target host
		client.connect((target, port))
		
		if len(buffer):
			client.send(buffer)
		while True:
			 
			# wait for the data
			# setting varibales 
			recv_len = 1 # recv_len setting length to 1 
			response = "" # setting response ""
			
			while recv_len:
				data = client.recv(4096)
				recv_len = len(data)
				response += data
				
				if recv_len < 4096:
					break
			print response,
			
			#wait for more input 
			buffer = raw_input ("")
			buffer += "\n"
			
			# send the data off 
			client.send(buffer)
	except:
		print "[*] Exceptional ! Exiting."
		
		# tear down the connection 
		client.close()	
		
## Server loop to listen for all connections  	
def server_loop():
	global target 
	
	# if no target is defined, we listen on all interfaces 
	if not len(target):
		target = "0.0.0.0"
		
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.bind((target, port))
	server.listen(5)
	
	while True:
		
		client_socket, addr = server.accept()
		
		#spin off a thread to handle our new client 
		client_thread = threading.Thread(target = client_handler, args= (client_socket,))
		client_thread.start()
		
def run_command(command):
	
	# trim the newline 
	command = command.rstrip()
	
	# run the command and get the output back 
	try:
		output = subprocess.check_output(command, stderr = subprocess.STDOUT, shell=True)
		
	except:
		output = "Failed to execute command. \r\n"
		
	#send the output back to the client 
	return output
		
def client_handler(client_socket):
	global upload
	global command 
	global execute 
	
	#check for upload
	if len(upload_destination):
		
		#read in all the bytes and write to our destination
		file_buffer = ""
		
		#keep reading data untill none is available 
		while True:
			data = client_socket.recv(1024)
			
			if not data:
				break
			else:
				file_buffer += data 
				
		#now we try to write them out 
		try:
			file_descriptor = open (upload_destination, "wb")
			file_descriptor.write(file_buffer)
			file_descriptor.close()
			
			#acknowledge the file write out.
			client_socket.send("Successfully saved the file to %s\r\n" % upload_destination)
			
		except:
			client_socket.send("Falied to save the file to %s \r\n" % upload_destination)
			
			
			
	#check for the command "execution" 
	if len(execute):
		
		#run the command 
		output = run_command(execute)
		client_socket.send(output)
			
	# loop if the command shell was requested 
	if command:
		while True:
			# show a simple command prompt 
			client_socket.send("<NC:#>")
			cmd_buffer = ""
			while "\n" not in cmd_buffer:
				cmd_buffer += client_socket.recv(1024)
				
			#send back the command output
			response = run_command(cmd_buffer)
			
			#send back the response 
			client_socket.send(response)
# Main function to call other functions 

def main():
	global listen 
	global port 
	global execute 
	global command
	global upload_destination 
	global target 
	
	
	if not len(sys.argv[1:]):
		usage()
		
	# Read the commandline options 
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu", 
		["help", "listen", "execute", "target", "port", "command", "upload"])
	except getopt.GetoptError as err:
		print str(err)
		usage()
		
	for o, a in opts:
		if o in ("-h","--help"):
			usage()
		elif o in ("-l", "--listen"):
			listen = True
		elif o in ("-e", "--execute"):
			execute = a
		elif o in ("-c", "--command"):
			command = True 
		elif o in ("-u", "--upload"):
			upload_destination = a
		elif o in ("-t", "--target"):
			target = a 
		elif o in ("-p", "--port"):
			port = int(a)
		#if not sending input to stdin
		else :
			
			assert False, "Unhandled Options"
			
	# Sending or listening ?
	if not listen and len(target) and port > 0:
		# reading the buffer form the command line this will block, so send CLTR+D 
		
		buffer = sys.stdin.read()
		
		#send data off
		client_sender(buffer)
		
	# Will listen and possibly send upload things, execute commands 
	# and drop a shell back 
	if listen:
		server_loop()
		
main()
