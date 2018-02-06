"""
Very simple HTTP server for decoding logs strings received via http POST requests.

Usage::
    python decoder.py [<port>]

    Then on the client side send a post message with encoded data in field encodedString
    
	--------------------------------
"""

import SimpleHTTPServer, SocketServer
import subprocess, json, time
import xml.dom.minidom as XML
import urlparse


class DecoderReceiver(SocketServer.TCPServer):

	def __init__(self, port=8080):
		self.port = port

		# keep trying to start the server until the port is available
		# mainly for debugging
		bound = False
		while not bound:
			try:
				server = SocketServer.TCPServer.__init__(self, ("", self.port), HTTPPostHandler)
				bound = True
			except:
				print "waiting for port %s to become available" % self.port
				time.sleep(3)
		
		return server


	def start(self):
		print "Decoding Server listening at port", self.port
		try:
			self.serve_forever()
		except KeyboardInterrupt:
			print "\nShutting down"


class HTTPPostHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
			
	def do_POST(self):
		content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
		post_data = self.rfile.read(content_length) # <--- Gets the data itself
		
		self.send_response(200)
		self.send_header('Content-type', 'text/html')
		self.end_headers()

		# load syntax highlighting library
		self.wfile.write('''
			<link rel="stylesheet" href="//cdnjs.cloudflare.com/ajax/libs/highlight.js/9.12.0/styles/default.min.css"/>
			<script src="//cdnjs.cloudflare.com/ajax/libs/highlight.js/9.12.0/highlight.min.js"></script>''')

		# get encoded string from post_data
		if "encodedString" in urlparse.parse_qs(post_data).keys():
			encoded = urlparse.parse_qs(post_data)["encodedString"][0]
		else:
			self.wfile.write("No encoded string received, please go back and try again")
			return

		# send response to browser
		self.wfile.write("<body style='word-wrap: break-word; white-space: pre-wrap;'>")
		self.wfile.write("You asked me to decode this:<br><div style='font-family: monospace'>%s</div><br>Working...<br><br>" % encoded)

		# decode string
		# automatically detects whether it's from live or test
		decoded = subprocess.check_output(['decodeLogLiveRaw', encoded])
		if len(decoded) == 0:
			decoded = subprocess.check_output(['decodeLogNonLiveRaw', encoded])
			if len(decoded) == 0:
				print("Invalid string to decode, please try again")
				return
		
		# activate syntax highlighting
		self.wfile.write("<script>hljs.initHighlightingOnLoad();</script>")

		# detect output format
		if decoded[0] == "{":
			decoded_formatted = json.dumps(json.loads(decoded), indent=4)
		elif decoded[0] == "<":
			decoded_formatted = XML.parseString(decoded).toprettyxml().replace("<", "&lt")
		else:
			decoded_formatted = decoded.replace("&", "\n")
		decoded_formatted = "<pre><code>" + decoded_formatted + "</code></pre>"

		self.wfile.write("Decoded version:<br>%s" % decoded_formatted)
		self.wfile.write("</body>")
	
	
if __name__ == "__main__":
	server = DecoderReceiver()
	server.start()


