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

Author
------

Juan J. Martinez <jjm@usebox.net>

This tool is free software under the MIT license.

