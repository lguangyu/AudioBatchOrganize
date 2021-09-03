#!/usr/bin/env python3

import abc
import argparse
import functools
import io
import os
import sys
import subprocess
import time
# custom lib
from . import util


@util.StaticUtilityMethods.decorate
class SubprogBase(abc.ABC):
	@abc.abstractmethod
	def subprog_main(self, args, *ka, **kw) -> None:
		pass

	def create_argparser(self, subparsers, *ka, **kw)\
			-> argparse.ArgumentParser:
		return subparsers.add_parser(self.subprog_name, *ka,
			help = self.subprog_help, description = self.subprog_desc, **kw)

	def refine_args(self, args) -> argparse.Namespace:
		if getattr(args, "dry_run", None):
			args.verbose = True
		return args

	def append_opt(*arg_ka, **arg_kw):
		def decorator(func):
			@functools.wraps(func)
			def wrapper(self, *ka, **kw):
				ap = func(self, *ka, **kw)
				ap.add_argument(*arg_ka, **arg_kw)
				return ap
			return wrapper
		return decorator

	def append_opt_program(prog_name, *, default: str = None,
			dest: str = None, help_extra = None):
		default = prog_name if default is None else default
		dest = prog_name if dest is None else dest
		help_str = "path to call '%s' program (default: %s)"\
			% (prog_name, default)
		if help_extra:
			help_str += help_extra
		def decorator(func):
			deco = SubprogBase.append_opt("--%s-path" % prog_name, type = str,
				dest = dest, default = default, metavar = "path",
				help = help_str)
			return deco(func)
		return decorator

	def append_opt_force(func):
		deco = SubprogBase.append_opt("-f", "--force", action = "store_true",
			help = "force overwrite output files (default: no)")
		return deco(func)

	def append_opt_dryrun(func):
		deco = SubprogBase.append_opt("-n", "--dry-run", action = "store_true",
			help = "run without making any output; will check inputs and show "
				"system call cmds (if any, but not executed); assumes "
				"-v/--verbose (default: no)")
		return deco(func)

	def append_opt_verbose(func):
		deco = SubprogBase.append_opt("-v", "--verbose", action = "store_true",
			help = "increase output verbosity (default: no)")
		return deco(func)

	def external_call(self, cmd, *ka, **kw):
		return subprocess.call(cmd, *ka, **kw)


class ListBasedSubprogBase(SubprogBase):
	@functools.wraps(SubprogBase.create_argparser)
	def create_argparser(self, subparsers, *ka, **kw):
		ap = super().create_argparser(subparsers, *ka, **kw)
		# add local args
		ap.add_argument("list", type = str, nargs = "?", default = "list",
			help = "list of audio file names to be processed (default: list)")
		ap.add_argument("--list-encoding", type = str, default = "utf-8",
			metavar = "encoding",
			help = "encoding in the input list file (default: utf-8)")
		return ap

	def refine_args(self, args):
		args = super().refine_args(args)
		if args.list == "-":
			args.list = sys.stdin
		return args

	def read_list(self, args) -> list:
		with self.util.get_fp(args.list, "r", encoding = args.list_encoding)\
				as fp:
			ret = fp.read().splitlines()
		return ret


class SubprogWithLogBase(SubprogBase):
	@util.StaticUtilityMethods.decorate
	class LogFiles(object):
		def __init__(self, *ka, out_file = sys.stdout, err_file = sys.stderr,
				**kw):
			super().__init__(*ka, **kw)
			self.out_file = self.util.get_fp(out_file, "w")
			self.err_file = self.util.get_fp(err_file, "w")
			return

		def out(self, s):
			return self.out_file.write(s)

		def err(self, s):
			return self.err_file.write(s)

		def close_all(self):
			self.out_file.close()
			self.err_file.close()
			return

	def create_argparser(self, subparsers, *ka, **kw):
		ap = super().create_argparser(subparsers, *ka, **kw)
		# add log options
		ap.add_argument("--log-file", type = str, default = None,
			metavar = "file",
			help = "stream stdout into this file, '-' for stdout "
				"(default: <auto>)")
		ap.add_argument("--err-file", type = str, default = "-",
			metavar = "file",
			help = "stream stderr into this file, '-' for stderr "
				"(default: -)")
		return ap

	def refine_args(self, args):
		args = super().refine_args(args)
		if args.log_file == "-":
			args.log_file = sys.stdout
		if args.err_file == "-":
			args.err_file = sys.stderr
		return args

	def with_log(check_dry_run = True):
		def decorator(func):
			@functools.wraps(func)
			def wrapper(self, args, *ka, **kw):
				# open log files
				self.log = type(self).LogFiles(
					out_file = args.log_file or ("%s.%s.log"\
						% (args.subprog, time.strftime("%Y%m%d%H%M%S"))),
					err_file = args.err_file)
				# check dry run with text report
				if check_dry_run and ("dry_run" in args) and args.dry_run:
					self.log_err("[DryRunMode]: no outputs will be generated\n")
				# run original func
				ret = func(self, args, *kw, **kw)
				# close log file handles
				self.log.close_all()
				return ret
			return wrapper
		return decorator

	def log_out(self, s):
		return self.log.out(s)

	def log_err(self, s):
		return self.log.err(s)

	def logged_external_call(self, cmd, *ka, dry_run = None, verbose = None,
			**kw):
		cmd_str = self.util.get_cmd_str(cmd)
		if verbose:
			self.log_err("calling: %s\n" % cmd_str)
		# make system call
		ret = self.external_call(cmd, *ka, stdout = self.log.out_file,
			stderr = self.log.err_file, **kw)\
			if not dry_run else 0
		if ret:
			self.log_err("[NonZeroReturn]: %s\n" % cmd_str)
		return ret


class SubprogReg(object):
	"""
	registry for subprograms
	"""
	_SUBPROGS_ = dict()

	@classmethod
	def new_subprog(cls, name: str, *, help: str = None, desc: str = None):
		def new_subprog_deco(subprog_cls):
			if " " in name:
				raise ValueError("space not allowed in subprog name, offender: "
					"'%s'" % name)
			cls._SUBPROGS_[name] = subprog_cls
			subprog_cls.subprog_name = name
			subprog_cls.subprog_help = help
			subprog_cls.subprog_desc = desc
			return subprog_cls
		return new_subprog_deco

	def __init__(self, *ka, **kw):
		super().__init__(*ka, **kw)
		self.subprog_dict = {k: v() for k, v in type(self)._SUBPROGS_.items()}
		return

	def iter_subprog_names(self, sort = None):
		keys = self.subprog_dict.keys()
		return sorted(keys) if sort else keys
	
	def iter_subprog_items(self, sort = None):
		for key in self.iter_subprog_names(sort):
			yield key, self.subprog_dict[key]
		return

	def get_subprog(self, subprog_name: str):
		return self.subprog_dict[subprog_name]
