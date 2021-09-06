#!/usr/bin/env python3

import glob
import shutil
# custom lib
from . import subprog


@subprog.SubprogReg.new_subprog("rename_conflict",
	help = "rename files with conflict prefix",
	desc = "rename files with conflict prefix, will only scans for file namse "
		"starting with the given prefix")
class SubprogRenameConflict(subprog.SubprogWithLogBase):
	@subprog.SubprogBase.append_opt_verbose
	@subprog.SubprogBase.append_opt_dryrun
	@subprog.SubprogBase.append_opt_force
	def create_argparser(self, subparsers, *ka, **kw):
		ap = super().create_argparser(subparsers, *ka, **kw)
		ap.add_argument("-C", "--conflict-prefix", type = str,
			default = self.util.get_default_conflict_prefix(), metavar = "str",
			help = "file name conflict prefix to remove (default: '%s')"\
				% self.util.get_default_conflict_prefix())
		return ap

	def _rename_conflict(self, fname, prefix, *, force = None, dry_run = None,
			verbose = None):
		if not fname.startswith(prefix):
			raise ValueError("fname must be string starting with '%s', "
				"got '%s'" % (prefix, fname))
		new_fname = fname[len(prefix):]
		if verbose:
			self.log_err("renaming: %s -> %s\n" % (fname, new_fname))
		if not dry_run:
			if (not os.path.exists(new_fname)) or force:
				shutil.move(fname, new_fname)
			else:
				self.log_err("existing: %s\n" % (new_fname))
		return

	@subprog.SubprogWithLogBase.with_log()
	def subprog_main(self, args):
		for fname in glob.glob(args.conflict_prefix + "*"):
			self._rename_conflict(fname, args.conflict_prefix,
				force = args.force, dry_run = args.dry_run,
				verbose = args.verbose)
		return
