#!/usr/bin/env python3

import os
# custom lib
from . import subprog
from audio_organizer import Metadata


@subprog.SubprogReg.new_subprog("clean_temps",
	help = "clean up temporary files created by other list-based subprograms",
	desc = "clean up temporary files created by other list-based subprograms")
class SubprogCleanTemps(subprog.SubprogWithLogBase,
		subprog.ListBasedSubprogBase):
	@subprog.SubprogBase.append_opt_verbose
	@subprog.SubprogBase.append_opt_dryrun
	def create_argparser(self, subparsers, *ka, **kw):
		ap = super().create_argparser(subparsers, *ka, **kw)
		return ap

	@subprog.SubprogWithLogBase.with_log()
	def subprog_main(self, args):
		for fname in self.read_list(args):
			ffmetadata = Metadata.standard_ffmetadata(fname)
			for f in [fname, ffmetadata]:
				if os.path.exists(f):
					if args.verbose:
						self.log_err("removing: %s\n" % f)
					os.remove(f)
				else:
					self.log_err("skipping: %s\n" % f)
		return
