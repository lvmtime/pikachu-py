#!/usr/bin/env python

###
#   Copytight Lev Meirovitch 2018 <lvmtime@gmail.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
###

import sys
import os.path

APP_VERSION = "1.0.0"


class PikatimeError(Exception):
	"""Class representing interpreter or runtime errors encountered in pikachu
	   code
	"""

	def __init__(self, kind, error, line):
		"""
		   kind -- type of error (string)
		   error -- error message (string)
		   line -- number of program line where error occured
		"""

		self.kind = kind
		self.error = error
		self.line = line

	def message(self):
		return "%s: %s on line %d" % (self.kind, self.error, self.line)


class LoadError(Exception):
	"""Class representing errors encountered while loading input
	"""

	def __init__(self, kind, error):
		"""
		   kind -- type of error (string)
		   error -- error message (string)
		"""

		self.kind = kind
		self.error = error

	def message(self):
		return "%s: %s" % (self.kind, self.error)


class Pikatime:
	"""Pikachu language runtime implements all language commands and executes
	   interpreted programs.
	"""

	PI_PIKACHU = []
	PIKA_PIKACHU = []
	IP = 0
	PROG_LENGTH = 0

	def run(self, program):
		"""Run a porogram stored in list

		   program -- list of Command objects comprizing a program

		   returns True if program completed succesfully, False on runtime error
		"""

		self.PROG_LENGTH = len(program)
		self.IP = 1

		try:
			while self.IP < self.PROG_LENGTH:
				program[self.IP].execute(self)
		except PikatimeError as e:
			sys.stderr.write("\n" + e.message() + "\n")
			return False
		except:
			sys.stderr.write("\nInternal error: " +  sys.exc_info()[0] + "\n")
			return False

		return True


	def set_input(self, data):
		for index, item in enumerate(data):
			if not isinstance(item, (int, long)):
				raise LoadError("Input error", "non integer data at index: " + str(index))
			else:
				self.PI_PIKACHU.append(item)

	def clear_stacks(self):
		del self.PI_PIKACHU[:]
		del self.PIKA_PIKACHU[:]


	### opcodes ###
	def nop(self, ignored1, ignored2):
		self.IP += 1

	def push(self, pikachu, value):
		if not isinstance(value, (int, long)):
			raise PikatimeError("Internal VM error", "pushing non integer",	self.IP)

		pikachu.append(value)
		self.IP += 1

	def pop(self, pikachu, ignored):
		self._check_underflow(pikachu, 1)
		pikachu.pop()
		self.IP += 1

	def add(self, pikachu, ignored):
		self._check_underflow(pikachu, 2)
		pikachu.append(pikachu[-2] + pikachu[-1])
		self.IP += 1

	def sub(self, pikachu, ignored):
		self._check_underflow(pikachu, 2)
		pikachu.append(pikachu[-2] - pikachu[-1])
		self.IP += 1

	def mul(self, pikachu, ignored):
		self._check_underflow(pikachu, 2)
		pikachu.append(pikachu[-2] * pikachu[-1])
		self.IP += 1

	def div(self, pikachu, ignored):
		self._check_underflow(pikachu, 2)
		if pikachu[-1] == 0:
			raise PikatimeError("Runtime error", "division by zero", self.IP)
		pikachu.append(pikachu[-2] / pikachu[-1])
		self.IP += 1

	def iprn(self, pikachu, ignored):
		self._check_underflow(pikachu, 1)
		sys.stdout.write(str(pikachu.pop()))
		self.IP += 1

	def aprn(self, pikachu, ignored):
		self._check_underflow(pikachu, 1)
		sys.stdout.write(chr(pikachu.pop() % 256))
		self.IP += 1

	def cpy(self, source, target):
		self._check_underflow(source, 1)
		target.append(source[-1])
		self.IP += 1

	def je(self, destination, ignored):
		self._check_underflow(self.PI_PIKACHU, 1)
		self._check_underflow(self.PIKA_PIKACHU, 1)
		self._check_jump_target(destination)
		if self.PI_PIKACHU[-1] == self.PIKA_PIKACHU[-1]:
			self.IP = destination
		else:
			self.IP += 2

	def jne(self, destination, ignored):
		self._check_underflow(self.PI_PIKACHU, 1)
		self._check_underflow(self.PIKA_PIKACHU, 1)
		self._check_jump_target(destination)
		if self.PI_PIKACHU[-1] != self.PIKA_PIKACHU[-1]:
			self.IP = destination
		else:
			self.IP += 2


	## utility functions ##

	def	_stack_name(self, pikachu):
		if pikachu is Pikatime.PI_PIKACHU:
			return 'pi pikachu'
		elif pikachu is Pikatime.PIKA_PIKACHU:
			return 'pika pikachu'

		return 'ellegal stack reference'

	def _check_underflow(self, pikachu, needed):
		if len(pikachu) < needed:
			raise PikatimeError("Runtime error", "stack underflow on " + self._stack_name(pikachu), self.IP)

	def _check_jump_target(self, destination):
		if not isinstance(destination, (int, long)):
			raise PikatimeError("Internal VM error", "jump address not integer", self.IP)

		if destination < 1 or destination >= self.PROG_LENGTH:
			raise PikatimeError("Runtime error", "jump to illegal line " + str(destination), self.IP)


class Command:
	"""Holds a single command of the program ready for execution"""


	def __init__(self, opcode = Pikatime.nop, target=None, value=0):
		"""Fills in command parameters"

		   opcode -- command to execute (ref. to function in Pikatime)
		   target -- ref. to stack to operate on (None for copy commands)
		   value  -- integer value for commands that need it (push, jmp, math)
		"""

		self.opcode = opcode
		self.target = target
		self.value = value


	def execute(self, pikatime):
		"""Executes command on the supplied runtime

		   pikatime -- Pikachu language runtime to execute on
		"""

		self.opcode(pikatime, self.target, self.value)


	def is_jump(self):
		return self.opcode == Pikatime.je or self.opcode == Pikatime.jne


	def set_address(self, address):
		"""Set the address of a jump command
		   This function will do nothing if this object does not contain a jump
		   command

		   address -- line number to jump to
		"""

		if self.is_jump():
			self.target = address


	def get_address(self):
		"""Return jump address

		   returns address if this is a jump command, otherwise None
		"""

		if self.is_jump():
			return self.target

		return None


class PikaInterpreter:
	"""Pikachu language interpreter. Loads program from file and converts it
	   to commands that can be executed by pikatime
	"""

	valid_syntax_set = set([ "pi", "pika", "pikachu"])


	def load(self, pika_file):
		"""Load a program from file

		   pika_file -- full path to file contaning program to interpret

		   returns program as list of command object or None if error occured.
		"""

		try:
			with open(pika_file) as  in_file:
				source_code = in_file.readlines()
				return self.interpret(source_code)
		except IOError as e:
			sys.stderr.write("\nError %s loading program %s\n" % (e.strerror, pika_file))
		except PikatimeError as e:
			sys.stderr.write("\n" + e.message() + "\n")

		return None


	def interpret(self, source_lines):
		"""Interprets lines of source code in to commands

		   source_lines -- list of program lines to interpret

		   returns program as list of command object
		   throws PikatimeError if something goes wrong
		"""

		self.current_line = 0
		commands = [ Command() ]
		next_line_is_address = False

		for line in source_lines:
			self.current_line += 1
			tokenized_line = self._validate_line(self._normalize_line(line))

			if next_line_is_address:
				commands[-1].set_address(len(tokenized_line))
				commands.append(Command())
				next_line_is_address = False
			else:
				command = self._parse_line_as_command(tokenized_line)
				commands.append(command)
				if command.is_jump():
					next_line_is_address = True

		return self._sanitize_addresses(commands)

	def _parse_line_as_command(self, line):
		"""Parses a line of code to command object that can be executed by the
		   interpreter

		   line -- list of command tokens

		   returns Command object if successful
		   raises PikatimeError on error
		"""

		try:
			if line[-1] == 'pikachu':
				if line[-2] == 'pi':
					target_stack = Pikatime.PI_PIKACHU
				elif line[-2] == 'pika':
					target_stack = Pikatime.PIKA_PIKACHU
				elif len(line) == 2: # this is one exception to the rule of single stack commands
					return self._parse_dual_stack_command(line)
				else:
					raise PikatimeError("Syntax error", "invalid stack", self.current_line)

				num_tokens = len(line)
				if  num_tokens == 2:
					return Command(Pikatime.pop, target_stack)
				elif num_tokens == 3:
					if line[0] == 'pikachu':
						return Command(Pikatime.div, target_stack)
					else:
						return Command(Pikatime.push, target_stack, 1)
				elif num_tokens == 4:
					if line[0] == 'pi' and line[1] == 'pika':
						return Command(Pikatime.add, target_stack)
					elif line[0] == 'pika' and line[1] == 'pi':
						return Command(Pikatime.sub, target_stack)
					elif line[0] == 'pi' and line[1] == 'pikachu':
						return Command(Pikatime.mul, target_stack)
					elif line[0] == 'pika' and line[1] == 'pikachu':
						return Command(Pikatime.iprn, target_stack)
					elif line[0] == 'pikachu' and line[1] == 'pikachu':
						return Command(Pikatime.aprn, target_stack)
					else:
						return Command(Pikatime.push, target_stack, 2)
				else:
					return Command(Pikatime.push, target_stack, num_tokens - 2)
			else:
				return self._parse_dual_stack_command(line)
		except IndexError: # not enough tokens for valid command
			raise PikatimeError("Syntax error", "bad command: " + ' '.join(line), self.current_line)


	def _parse_dual_stack_command(self, line):
		"""Parses commands that operate on both stacks at the same time

		   line -- code line as list of tokens

		   returns Command object if successful
		   raises PikatimeError on error
		"""

		if line[0] == 'pi' and line[1] == 'pika':
			return Command(Pikatime.cpy, Pikatime.PI_PIKACHU, Pikatime.PIKA_PIKACHU)
		elif line[0] == 'pika' and line[1] == 'pi':
			return Command(Pikatime.cpy, Pikatime.PIKA_PIKACHU, Pikatime.PI_PIKACHU)
		elif line[0] == line[1] == 'pikachu':
			return Command(Pikatime.je)
		elif line[0] == line[1] == 'pika':
			return Command(Pikatime.jne)

		raise PikatimeError("Syntax error", "bad command: " + ' '.join(line), self.current_line)


	def _normalize_line(self, line):
		"""Prepaires line for validation and parsing
		"""

		if line is not None:
			line = line.lower().strip()

		return line


	def _validate_line(self, line):
		"""Check if line has only pikachu language words and in valid order

			line -- line string to validate

			returns all valid tokens in line as list
		"""

		if not line:
			raise PikatimeError("Syntax error", "empty line", self.current_line)

		line_list = line.split()
		line_set = set(line_list)
		if not line_set <= self.valid_syntax_set:
			raise PikatimeError("Syntax error", "Non Pikachu word", self.current_line)

		if len(line_list) >= 3:
			for i in range(len(line_list) - 3):
				if line_list[i] == line_list[i + 1] == line_list[i + 2]:
					raise PikatimeError("Syntax error",
						"Three of same word in a row", self.current_line)

		return line_list


	def _sanitize_addresses(self, program):
		"""Checks that all jump addresses are valid and there are no infinite
		   loops created by jumping to same line as the jump command

		   program -- list of commands

		   returns the list of commands unchanged (pass through)
		   raises PikatimeError if invalid address found
		"""

		for line, command in enumerate(program):
			if command.is_jump():
				target = command.get_address()
				if target is None:
					raise PikatimeError("Address error", "jump command missing address", line)
				elif not isinstance(target, (int, long)):
					raise PikatimeError("Address error", "jump address not an integer", line)
				elif target >= len(program):
					raise PikatimeError("Address error", "jump past end of program", line)
				elif target < 1:
					raise PikatimeError("Address error", "invalid jump address: " + target, line)
				elif target == line:
					raise PikatimeError("Address error", "infinite loop -- jump to self", line)
				elif program[target].opcode is Pikatime.nop:
					sys.stderr.write("WARNING: jump to address (NOP) line #" + target +" on line " + line)

		return program


def parse_command_line_input(cmd_line):
	"""Parses command line arguments to list of ints to be used as program
	   input

	   cmd_line -- list of command line arguments as string (only input vals)

	   return parsing status as boolean, and list of int values, or None
	"""

	if cmd_line is None or cmd_line == []:
		return True, None

	result = []
	for val in cmd_line:
		try:
			result.append(int(val))
		except ValueError:
			sys.stderr.write("Invalid input value: " + val)
			return False, None

	return True, result


def print_version():
	print "\nPikachu programming language interpreter"
	print "Version:", APP_VERSION
	print "Copyright Lev Meirovitch 2018, 2019(C)"
	print "Published under GNU/GPL v3+\n"


def print_help(name):
	print "\nUsage:"
	print "" + name + " <program.pika> [ input }"
	print "\nprogram.pika   path to program file to run"
	print "input          space separated integer values for program input\n"


def main():
	name = os.path.basename(sys.argv[0])
	if len(sys.argv) < 2:
		print_version()
		print_help(name)
		return 1
	elif sys.argv[1] == '-h' or sys.argv[1] == '--help':
		print_help(name)
		return 1
	elif sys.argv[1] == '-v' or sys.argv[1] == '--version':
		print_version()
		return 1

	valid, input_vals = parse_command_line_input(sys.argv[2:])
	if not valid:
		print_help(name)
		return 1

	interpreter = PikaInterpreter()
	program = interpreter.load(sys.argv[1])
	if program is None:
		return 1

	runtime = Pikatime()
	if input_vals is not None:
		runtime.set_input(input_vals)

	res = runtime.run(program)

	if not res:
		return 1

	print "\n***DONE***"
	return 0


if __name__ == "__main__":
	ret = main()
	if ret != 0:
		sys.exit(ret)