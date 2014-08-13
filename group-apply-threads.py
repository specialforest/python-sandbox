#!/usr/bin/env python

import sys
import os
import threading
import Queue
import subprocess
import logging


def is_begin(line):
	return line.startswith("= BEGIN =")


def is_end(line):
	return line.startswith("= END =")


def read_input(source, worker_cmd, workers):
	logging.debug("read_input start")
	f = open(source, "r")
	input_queue = None
	for line in f:
		if is_begin(line):
			logging.debug("group start")
			if input_queue:
				sys.stderr.write("Missing end of a group.\n")
				input_queue.put(None)
				input_queue = None

			worker = {}
			worker['iqueue'] = Queue.Queue()
			worker['oqueue'] = Queue.Queue()
			worker['process'] = subprocess.Popen(worker_cmd, bufsize=0, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
			worker['stdin_thread'] = threading.Thread(target = write_input, args = [worker['iqueue'], worker['process'].stdin])
			worker['stdin_thread'].start()
			worker['stdout_thread'] = threading.Thread(target = read_output, args = [worker['process'].stdout, worker['oqueue']])
			worker['stdout_thread'].start()
			workers.put(worker)
			input_queue = worker['iqueue']
		elif is_end(line):
			logging.debug("group end")
			if input_queue:
				input_queue.put(None)
				input_queue = None
			else:
				sys.stderr.write("Unexpected end of a group.\n")
		else:
			if input_queue:
				input_queue.put(line)

	if input_queue:
		pass

	workers.put(None)
	logging.debug("read_input end")


def write_input(queue, target):
	logging.debug("write_input start")
	while True:
		line = queue.get()
		if not line:
			break

		target.write(line)

	target.close()
	logging.debug("write_input end")


def read_output(source, queue):
	logging.debug("read_output start")
	for line in source:
		queue.put(line)

	queue.put(None)
	logging.debug("read_output end")


def write_output(workers):
	logging.debug("write_output start")
	while True:
		worker = workers.get()
		if not worker:
			break

		output_queue = worker['oqueue']
		while True:
			line = output_queue.get()
			if not line:
				break

			print(line)

		worker['stdin_thread'].join()
		worker['stdout_thread'].join()
		worker['process'].wait()

	logging.debug("write_output end")


def main():
	source = sys.argv[1]
	args = sys.argv[2:]

	logging.debug("start")
	workers = Queue.Queue()
	input_reader = threading.Thread(target = read_input, args = [source, args, workers])
	input_reader.start()

	output_writer = threading.Thread(target = write_output, args = [workers])
	output_writer.start()

	input_reader.join()
	output_writer.join()
	logging.debug("end")


if __name__ == "__main__":
	logging.basicConfig()
	logging.getLogger().setLevel(logging.DEBUG)
	main()
