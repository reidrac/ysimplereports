#!/usr/bin/env python
# coding: utf-8
# vim:fileencoding=utf-8
#
# Copyright (C) 2010 Juan J. Martinez <jjm@usebox.net>
# Please check README file for licensing details :)
#

import csv
import simplejson as json
from xml.dom.minidom import Document

import logging
import argparse
import re

class ysimplereports:
	def __init__(self, yaml):
		self._yaml = yaml
		self._format = None
		self._output = None
		self._db = None

		self.STATUS = { 'init': 0, 'parsed': 1, 'connected': 2 }
		self._status = 0

	def parse(self):
		# basic checks
		if not 'report' in self._yaml:
			self.log.error('At least one report is expected')

		r = self._yaml['report']
		checkFields = ('name', 'query', 'output', 'connect')
		for check in checkFields:
			if not check in r:
				raise Exception('Missing %s in report' % check)

		self._format = r['output'].split('.')
		if len(self._format) < 2 or self._format[-1] not in ('csv', 'json', 'xml'):
			raise Exception('Unable to detect the output format (csv, json, xml) in report "%s"'
				% r['name'])
		self._format = self._format[-1]
		self._output = r['output']

		if not 'type' in r['connect'] or r['connect']['type'] not in ('sqlite', 'mysql'):
			raise Exception('Invalid connect type (sqlite, mysql) in report "%s"' % r['name'])

		if r['connect']['type'] == 'mysql':
			if not 'username' in r['connect'] or not 'password' in r['connect']:
				raise Exception('username and/or password missing in report "%s"' % r['name'])
			if not 'hostname' in r['connect'] and 'port' in r['connect']:
				raise Exception('port without hostname in report "%s"' % r['name'])
			if 'hostname' in r['connect'] and not 'port' in r['connect']:
				# use default port if not specified
				r['connect']['port'] = 3306

		self._status |= self.STATUS['parsed']

	@property
	def format(self):
		if self._status < self.STATUS['parsed']:
			raise Exception('Parse the report first')
		return self._format

	@property
	def output(self):
		if self._status < self.STATUS['parsed']:
			raise Exception('Parse the report first')
		return self._output

	def connect(self, connect = None):
		if self._status < self.STATUS['parsed']:
			raise Exception('Parse the report first')

		if connect is None:
			connect = self._yaml['report']['connect']

		if connect['type'] == 'sqlite':
			try:
				import sqlite3
			except:
				raise Exception('Unable to load sqlite3 support')

			try:
				self._db = sqlite3.connect(connect['database'])
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

				self._db = MySQLdb.connect(**args)
			except:
				raise Exception('Failed to open %s' % connect['database'])
		else:
			# unlikely
			raise Exception('Unsupported connection type %s' % connect['type'])

		self._status |= self.STATUS['connected']

	def execute(self, query = None):
		if self._status < self.STATUS['connected']:
			raise Exception('Connect first')

		if query is None:
			query = self._yaml['report']['query']

		cur = self._db.cursor()
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

		self.write(cols, data)
		self._status = self.STATUS['init']

	def write(self, header, rows):
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
	VERSION = '0.1'

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
