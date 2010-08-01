#!/usr/bin/env python
# coding: utf-8
# vim:fileencoding=utf-8
#
# ysimplereports.py
# Copyright (c) 2010 Juan J. Martinez <jjm@usebox.net>
# 
# Permission is hereby granted, free of charge, to any
# person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the
# Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice
# shall be included in all copies or substantial portions of
# the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

"""YAML SQL Simple Reports.

This is a small tool to run simple reports as specified in a
YAML input format.

Here is an example YAML file:

	report:
		name: example report
		connect:
			type: sqlite
			database: database.db
		query: select a as Col_a, b as Col_b from table
		output: example.csv

The output format it's determined by the extension of the
output file.

Subreports are supported, adding a report item inside the
main report:

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

The subquery will be executed for each row in the main query, and
any {KEY} will be replaced by VALUE.

In subreports, 'connect' is optional (and then, main report connection
will be used).

More information: http://github.com/reidrac/ysimplereports
"""

import csv
try:
	import json
except:
	import simplejson as json
from xml.dom.minidom import Document

import logging
import argparse
import re

class ysimplereports:
	def __init__(self, yaml):
		"""Create a ysimplereports instance given a YAML parsed Python object."""
		self._yaml = yaml
		self._format = None
		self._output = None

		# main report database handler
		self._db = None

	def parse(self):
		"""Parse the YAML file. This method must be called once before
		   running the report."""

		if not 'report' in self._yaml:
			self.log.error('One report is expected')

		r = self._yaml['report']
		checkFields = ('name', 'output', 'connect')
		for check in checkFields:
			if not check in r:
				raise Exception('Missing %s in report' % check)

		self._format = r['output'].split('.')
		if len(self._format) < 2 or self._format[-1] not in ('csv', 'json', 'xml'):
			raise Exception('Unable to detect the output format (csv, json, xml) in report "%s"'
				% r['name'])
		self._format = self._format[-1]
		self._output = r['output']

		# parse fields common to both reports and subreports
		self._parse(self._yaml['report'])

	def _parse(self, r):
		# this parse checks fields that may be available in both reports
		# and subreports

		# just in case (name in subreports is optional)
		if not 'name' in r:
			r['name'] = '<unamed subreport>'

		if not 'query' in r:
				raise Exception('Missing query in report "%s"' % r['name'])

		if 'connect' in r:
			if not 'type' in r['connect'] or r['connect']['type'] not in ('sqlite', 'mysql', 'postgresql'):
				raise Exception('Invalid connect type %s (expected sqlite, mysql, postgresql) in report "%s"' % 
					(r['connect']['type'], r['name']))

			if r['connect']['type'] == 'mysql' or r['connect']['type'] == 'postgresql':
				if not 'username' in r['connect'] or not 'password' in r['connect']:
					raise Exception('username and/or password missing in report "%s"' % r['name'])
				if not 'hostname' in r['connect'] and 'port' in r['connect']:
					raise Exception('port without hostname in report "%s"' % r['name'])
				if 'hostname' in r['connect'] and not 'port' in r['connect']:
					# use default port if not specified
					if r['connect']['type'] == 'mysql':
						r['connect']['port'] = 3306
					else:
						r['connect']['port'] = 5432

	@property
	def format(self):
		"""Get output format (csv, xml or json)."""
		if self._format is None:
			raise Exception('Parse the report first')
		return self._format

	@property
	def output(self):
		"""Get output filename."""
		if self._output is None:
			raise Exception('Parse the report first')
		return self._output

	def connect(self):
		"""Connect to the database before executing the report."""

		try:
			self._db = self._connect(self._yaml['report']['connect'])
		except Exception as e:
			raise Exception('In report "%s": %s' % (self._yaml['report']['name'], e))

	def _connect(self, connect = None):
		if self._output is None:
			raise Exception('Parse the report first')

		if connect['type'] == 'sqlite':
			try:
				import sqlite3
			except:
				raise Exception('Unable to load sqlite3 support')

			try:
				db = sqlite3.connect(connect['database'])
			except:
				raise Exception('Failed to open %s' % connect['database'])
		elif connect['type'] == 'mysql':
			try:
				import MySQLdb
			except:
				raise Exception('Unable to load mysql support')

			try:
				args = { 
					'db': connect['database'],
					'user': connect['username'],
					'passwd': connect['password'],
					}

				if 'hostname' in connect:
					# hostname implies port (although it can be default)
						args['host'] = connect['hostname']
						args['port'] = connect['port']

				db = MySQLdb.connect(**args)
			except:
				raise Exception('Failed to open %s' % connect['database'])
		elif connect['type'] == 'postgresql':
			try:
				import psycopg2
			except:
				raise Exception('Unable to load postgresql support')

			try:
				args = { 
					'database': connect['database'],
					'user': connect['username'],
					'password': connect['password'],
					}

				if 'hostname' in connect:
					# hostname implies port (although it can be default)
						args['host'] = connect['hostname']
						args['port'] = connect['port']

				db = psycopg2.connect(**args)
			except:
				raise Exception('Failed to open %s' % connect['database'])
		else:
			# unlikely
			raise Exception('Unsupported connection type %s' % connect['type'])

		return db

	def _replace(self, yaml, fields):
		# replace {KEY} with VALUE in a Pyhton object
		if type(yaml).__name__ == 'str':
			for fkey in fields.keys():
				yaml = yaml.replace('{' + str(fkey) + '}', str(fields[fkey]))
		else:
			for key in yaml.keys():
				yaml[key] = self._replace(yaml[key], fields)

		return yaml

	def execute(self):
		"""Execute the report once connection it's called. The results will be
		   stored in the output file identified by parse()."""

		try:
			header, rows = self._execute(self._yaml['report']['query'], self._db)
		except Exception as e:
			raise Exception('In report "%s": %s' % (self._yaml['report']['name'], e))

		# subreport support: execute the subquery for each row of the parent
		# query, remplacing the row values in the subquery
		if 'report' in self._yaml['report']:
			subheader = None
			subrows = None
			for r in rows:
				subyaml = self._yaml['report']['report'].copy()
				fields = {}
				for i in range(len(header)):
					fields[header[i]] = r[i]
				subyaml = self._replace(subyaml, fields)

				self._parse(subyaml)

				# allow connection to other databases based in the
				# parent query results, or use main connection
				# TODO: detect if connection string changed in the loop
				# and just open one extra connection in that case
				if 'connect' in subyaml:
					try:
						db = self._connect(subyaml['connect'])
					except Exception as e:
						raise Exception('In report "%s": %s' % (subyaml['name'], e))
				else:
					db = self._db

				try:
					dummy, newrows = self._execute(subyaml['query'], db)
				except Exception as e:
					raise Exception('In report "%s": %s' % (subyaml['name'], e))

				if subheader is None:
					subheader = dummy
					subrows = newrows
				else:
					subrows.extend(newrows)

				# actually we open one connection per iteration, so close it
				if 'connect' in subyaml:
					db.close()

			header = subheader
			rows = subrows

		# main report connection
		self._db.close()
		self._write(header, rows)

	def _execute(self, query = None, db = None):
		if db is None:
			raise Exception('Connect first')

		cur = db.cursor()
		try:
			result = cur.execute(query)
		except:
			cur.close()
			raise

		cols = []
		for col in cur.description:
			cols.append(col[0])

		data = cur.fetchall()

		cur.close()

		return (cols, data)

	def _write(self, header, rows):
		if self._output is None:
			raise Exception('Parse the report first')

		fd = open(self._output, 'w')

		if self._format == 'csv':
			writer = csv.writer(fd)
			writer.writerow(header)
			writer.writerows(rows)

		if self._format == 'json':
			obj = []
			for row in rows:
				map = {}
				for idx in range(len(header)):
					map[header[idx]] = row[idx]
				obj.append(map)

			json.dump(obj, fd, indent=2)

		if self._format == 'xml':
			doc = Document()
			root = doc.createElement('result')
			doc.appendChild(root)

			for row in rows:
				rowNode = doc.createElement('row')
				for idx in range(len(header)):
					element = doc.createElement(header[idx])
					element.appendChild(doc.createTextNode(str(row[idx])))
					rowNode.appendChild(element)
				root.appendChild(rowNode)

			doc.writexml(fd, indent='  ', newl='\n')

		fd.close()


def main():
	VERSION = '0.2'

	LOG_LEVELS = {
		'debug': logging.DEBUG,
		'info': logging.INFO,
		'warning': logging.WARNING,
		'error': logging.ERROR,
		'critical': logging.CRITICAL
	}

	# default logging
	logging.basicConfig(level=logging.WARNING)
	log = logging.getLogger('ysimplereports')

	parser = argparse.ArgumentParser(description='YAML Simple SQL Reports')
	parser.add_argument('-v', dest='verbose', metavar='LEVEL', default='warning', 
		help='Verbosity level (debug, info, warning*, error, critical)')
	parser.add_argument('-V', action='version', version='%(prog)s ' + VERSION,
		help='Print version and exit')
	parser.add_argument('report', metavar='FILE', type=str, nargs=1,
		help='YAML file containing the reports')
	args = parser.parse_args()

	log.setLevel(LOG_LEVELS[args.verbose])
	log.debug('verbose level is %s' % args.verbose)

	try:
		import yaml
	except:
		log.critical('YAML support not found (tip: install PyYAML)')
		exit(1)

	try:
		file = open(args.report[0])
	except:
		log.error('Failed to open the report file: %s' % args.report)
		exit(1)

	try:
		report = yaml.load(file)
	except yaml.scanner.ScannerError as error:
		log.error('Failed to parse %s: %s' % (args.report[0], error))
		file.close()
		exit(1)

	file.close()

	simple = ysimplereports(report)

	try:
		simple.parse()
	except Exception as e:
		log.error(e)
		exit(1)

	try:
		log.debug('trying to connect...')
		simple.connect()
		log.debug('connect done!')
	except Exception as e:
		log.error(e)
		exit(1)

	try:
		log.debug('trying to execute into %s...' % simple.output)
		simple.execute()
		log.debug('execution done!')
	except Exception as e:
		log.error(e)
		exit(1)

	log.debug('writing done')

if __name__ == "__main__":
	main()

# EOF
