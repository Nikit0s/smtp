import base64
import os
import mySMTP
import argparse
import getpass
import sys

def sendMail(smtp, msg):
	smtp.sock.send('DATA'.encode('utf-8'))
	smtp.sock.send(smtp.bCRLF)
	smtp.getreply()
	smtp.sock.send('{}\r\n.\r\n'.format(msg).encode('utf-8'))
	smtp.getreply()
	print('Email sended')


def sendImages(smtp, reciever, directory, sender="pictureDelieverer@mail.com"):
	try:
		files = os.listdir(directory)
	except FileNotFoundException:
		print("There is no such directory")
		sys.exit(0)
	pictures = []
	JPGFiles = list(filter(lambda x: x.endswith('.jpg'), files))
	PNGFiles = list(filter(lambda x: x.endswith('.png'), files))
	pictures = JPGFiles + PNGFiles
	if len(pictures) == 0:
		print("There is no pictures in this directory")
		sys.exit(0)
	msg = 'From: %s\r\nTo: %s\r\nSubject: Some Pictures\r\nMIME-Version: 1\r\nContent-Type: multipart/mixed; boundary="mybound"\r\n' % (sender, reciever)
	for filename in pictures:
		if filename != "":
			fo = open(filename, 'rb')
			filecontent = fo.read()
			encodedcontent = base64.b64encode(filecontent)
			att = '--mybound\r\nContent-Type: application/octet-stream\r\nContent-Transfer-Encoding:base64\r\nContent-Disposition: attachment; filename="{}"\r\n\r\n"{}"\r\n'.format(filename, encodedcontent.decode('utf-8'))
			msg += att
	msg += '--mybound--'

	sendMail(smtp, msg)


def main(args):
	host = str(args.SMTPServer)
	port = int(args.SMTPPort)
	reciever = str(args.reciever)
	directory = str(args.directory)
	code = 220
	seq = [
		"EHLO 1",
		"STARTTLS",
		"EHLO 1",
		"MAIL FROM: <pictureDelieverer@mail.com>",
		"RCPT TO: <grizzlyarchi@gmail.com>",
		"DATA",
		]
	s = mySMTP.SMTP(host, port)
	needAuth = False
	for command in seq:
		s.sock.send(command.encode('utf-8'))
		s.sock.send(s.bCRLF)
		reply = s.getreply()
		if command == "STARTTLS":
			s.starttls()
		code = reply[0]
		if str(code) in ("503", "530"):
			needAuth = True
			break
	if not needAuth:
		sendImages(s,reciever, directory)
	else:
		s.close()
		s = mySMTP.SMTP(host, port)
		print("Sorry, we need your login on this server. Please input...")
		login = str(input())
		print("Also we need your password")
		password = str(getpass.getpass())
		encoded_login = base64.b64encode(login.encode('utf-8'))
		encoded_pass = base64.b64encode(password.encode('utf-8'))
		code = 220
		seq = [
				"EHLO 1".encode('utf-8'),
				"STARTTLS".encode('utf-8'),
				"EHLO 1".encode('utf-8'),
				"AUTH LOGIN".encode('utf-8'),
				encoded_login,
				encoded_pass,
				"MAIL FROM: <{}>".format(login).encode('utf-8'),
				"RCPT TO: <{}>".format(reciever).encode('utf-8')
			]
		for command in seq:
			s.sock.send(command)
			s.sock.send(s.bCRLF)
			reply = s.getreply()
			code = reply[0]
			if str(code)[0] == "5":
				print("Some server error, sorry")
				sys.exit(0)
			if command == "STARTTLS".encode('utf-8'):
				s.starttls()
		sendImages(s, reciever, directory, sender=login)
		s.close()

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Arguments for smtp_mime")
	parser.add_argument("SMTPServer", help="Input smtp server name")
	parser.add_argument("SMTPPort", help="Port for smtp on that server")
	parser.add_argument("reciever", help="e-mail of the reciever for pictures")
	parser.add_argument("directory", help="directory with images", nargs="?", default=".")
	args = parser.parse_args()
	main(args)