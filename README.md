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

Subreports are supported with following data flow:

	1. Execute the main query
	2. For each row do:
		2.1. Replace {KEY} in the subreport with VALUE
		2.2. Process subreport
	3. Write result as concatenated rows from each subreport

Subreport example:

	report:
		name: example report
		connect:
			type: mysql	
			database: dbname
			username: user
			password: passwd
		query: select id, dbname, username, password from foo
		report:
			name: example subreport
			connect:			# connect is optional in subreports
				type: mysql
				database: {dbname}
				username: {username}
				password: {password}
			query: select {id} as DB_ID, * from bar
		output: file.csv

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

