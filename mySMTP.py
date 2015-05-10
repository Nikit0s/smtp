import socket
from sys import stderr
import ssl
import base64

SMTP_PORT = 25
SMTP_SSL_PORT = 465
CRLF = "\r\n"
bCRLF = b"\r\n"
_MAXLINE = 8192 # more than 8 times larger than RFC 821, 4.5.3




# Exception classes used by this module.
class SMTPException(Exception):
	pass

class SMTPServerDisconnected(SMTPException):
	pass

class SMTPResponseException(SMTPException):
	def __init__(self, code, msg):
		self.smtp_code = code
		self.smtp_error = msg
		self.args = (code, msg)

class SMTPConnectError(SMTPResponseException):
	pass


class SMTP:
	def _get_socket(self, host, port):
		return socket.create_connection((host, port))

	def __init__(self, host='', port=0):
		self.bCRLF = b"\r\n"
		self.debuglevel = 1
		self.does_esmtp = 0
		(code, msg) = self.connect(host, port)
		if code != 220:
			raise SMTPConnectError(code, msg)


	def connect(self, host='localhost', port=0):
		self.sock = self._get_socket(host, port)
		self.file = None
		(code, msg) = self.getreply()
		return (code, msg)

	def getreply(self):
		resp = []
		if self.file is None:
			self.file = self.sock.makefile('rb')
		while 1:
			try:
				line = self.file.readline(_MAXLINE + 1)
			except socket.error as e:
				self.close()
				raise SMTPServerDisconnected("Connection unexpectedly closed: " + str(e))
			if not line:
				self.close()
				raise SMTPServerDisconnected("Connection unexpectedly closed")
			if self.debuglevel > 0:
				pass
				# print('reply:', repr(line), file=stderr)
			if len(line) > _MAXLINE:
				raise SMTPResponseException(500, "Line too long.")
			resp.append(line[4:].strip(b' \t\r\n'))
			code = line[:3]
			try:
				errcode = int(code)
			except ValueError:
				errcode = -1
				break
			if line[3:4] != b"-":
				break

		errmsg = b"\n".join(resp)
		return errcode, errmsg

	def close(self):
		if self.file:
			self.file.close()
		self.file = None
		if self.sock:
			self.sock.close()
		self.sock = None
	def starttls(self, keyfile=None, certfile=None):
		self.sock = ssl.wrap_socket(self.sock, keyfile, certfile)
		self.file = None