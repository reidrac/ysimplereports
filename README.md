YAML Simple SQL Reports
=======================

This is a script to make queries to different databases (sqlite3 and MySQL
supported, others can be added), and output the result in CVS, JSON or XML
format.

The report it's specified in a YAML file:

	report:
		name: example report		# req
		connect:					# req
			type: mysql				# req: sqlite, mysql
			database: dbname		# req (sqlite: filename, mysql: dbname)
			hostname: localhost 	# opt with mysql, by default UNIX socket
			port: 3306				# opt with mysql, requited if hostname
			username: user			# req with mysql
			password: passwd		# req with mysql, use '' for empty
		query: select * from table	# req
		output: file.csv			# req (format by ext: .csv, .json, .xml)

Required
--------

 - PyYAML

At least one of the following:

 - sqlite3
 - MySQLdb

License
-------

 Copyright (c) 2010 Juan J. Martinez <jjm@usebox.net>

 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included in
 all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 THE SOFTWARE.

