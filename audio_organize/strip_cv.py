#!/usr/bin/env python3

import os
import re
import shutil
# custom lib
from . import subprog


@subprog.SubprogReg.new_subprog("strip_cv",
	help = "strip character CV info from file names",
	desc = "strip character CV info from file names")
class SubprogStripCv(subprog.SubprogWithLogBase):
	@subprog.SubprogBase.append_opt_verbose
	@subprog.SubprogBase.append_opt_dryrun
	@subprog.SubprogBase.append_opt_force
	def create_argparser(self, subparsers, *ka, **kw):
		ap = super().create_argparser(subparsers, *ka, **kw)
		ap.add_argument("files", type = str, nargs = "+",
			metavar = "file [file ...]",
			help = "input files to rename")
		def_pattern = r" \(CV： [^)]+\)"
		ap.add_argument("-p", "--pattern", type = str, default = def_pattern,
			metavar = "regex",
			help = "regular expression of the pattern to strip (default: '%s')"\
				% def_pattern)
		return ap

	def _strip_cv(self, fname, pattern, *, force = None, dry_run = None,
			verbose = None):
		new_fname = re.sub(pattern, "", fname)
		if fname == new_fname:
			if verbose:
				self.log_err("skipping: %s\n" % new_fname)
		else:
			if verbose:
				self.log_err("renaming: %s -> %s\n" % (fname, new_fname))
			if not dry_run:
				if (not os.path.exists(new_fname)) or force:
					shutil.move(fname, new_fname)
				else:
					self.log_err("existing: %s\n" % new_fname)
		return

	@subprog.SubprogWithLogBase.with_log()
	def subprog_main(self, args):
		for fname in args.files:
			self._strip_cv(fname, args.pattern, force = args.force,
				dry_run = args.dry_run, verbose = args.verbose)
		return
