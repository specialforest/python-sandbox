#!/usr/bin/env python

import sys
import os
import gevent
import gevent.fileobject
import gevent.queue
import gevent.subprocess


def is_begin(line):
	return line.startswith("= BEGIN =")


def is_end(line):
	return line.startswith("= END =")


class Processor:
	def __init__(self, source, args):
		self.source = source
		self.args = args
		self.active_buffer = None
		self.children = []
		self.input_writers = []
		self.output_readers = []
		self.output_queue = gevent.queue.Queue()


	def process(self):
		input_file = open(self.source, 'r')		
		input_thread = gevent.fileobject.FileObjectThread(input_file)
		input_reader = gevent.spawn(Processor.read_input, self, input_thread)

		output_thread = gevent.fileobject.FileObjectThread(sys.stdout)
		output_writer = gevent.spawn(Processor.write_output, self, output_thread)

		input_reader.join()
		input_file.close()

		for writer in self.input_writers:
			writer.join()

		self.output_queue.put(None)
		output_writer.join()


	def begin_group(self):
		if self.active_buffer:
			sys.stderr.write("Missing end of a group.\n")
			self.end_group()

		self.active_buffer = gevent.queue.Queue()
		self.children.append(gevent.subprocess.Popen(self.args, bufsize=0, stdin=gevent.subprocess.PIPE, stdout=gevent.subprocess.PIPE))
		
		self.input_writers.append(gevent.spawn(Processor.write_input, self, self.active_buffer, self.children[-1].stdin))

		output_buffer = gevent.queue.Queue()
		self.output_readers.append(gevent.spawn(Processor.read_output, self, self.children[-1].stdout, output_buffer))
		self.output_queue.put(output_buffer)		


	def end_group(self):
		if not self.active_buffer:
			sys.stderr.write("Unexpected end of a group.\n")
			return

		self.active_buffer.put(None)
		self.active_buffer = None
		self.cleanup_pending_input_writers()


	def cleanup_pending_input_writers(self):
		pass


	def read_input(self, file):
		for line in file:
			if is_begin(line):
				self.begin_group()
			elif is_end(line):
				self.end_group()
			else:
				if self.active_buffer:
					self.active_buffer.put(line)
				else:
					print(line)

		if self.active_buffer:
			sys.stderr.write("Missing end of a group.\n")
			self.end_group()


	def write_input(self, buffer, file):
		while True:
			line = buffer.get()
			if line is None:
				break

			file.write(line)

		file.close()


	def read_output(self, file, buffer):
		for line in file:
			buffer.put(line)

		buffer.put(None)


	def write_output(self, file):
		while True:
			buffer = self.output_queue.get()
			if buffer is None:
				break

			while True:
				line = buffer.get()
				if line is None:
					break

				file.write(line)


def main():
	source = sys.argv[1]
	args = sys.argv[2:]
	Processor(source, args).process()


if __name__ == "__main__":
	main()
