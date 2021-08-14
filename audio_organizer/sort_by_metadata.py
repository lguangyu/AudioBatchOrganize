#!/usr/bin/env python3

import os
import shutil
# custom lib
from . import subprog
from . import util
from audio_organizer import Metadata


@subprog.SubprogReg.new_subprog("sort_by_metadata",
	help = "create and sort files into metadata-based sub-directories",
	desc = "create and sort files into metadata-based sub-directories")
class SubprogSortByMetadata(subprog.SubprogWithLogBase,
		subprog.ListBasedSubprogBase):
	@subprog.SubprogBase.append_opt_verbose
	@subprog.SubprogBase.append_opt_dryrun
	@subprog.SubprogBase.append_opt_force
	def create_argparser(self, subparsers, *ka, **kw):
		ap = super().create_argparser(subparsers, *ka, **kw)
		ap.add_argument("pattern", type = str,
			help = "pattern to create sub-directories, available fields: %s"\
				% Metadata.get_fields_help_str().replace("%", "%%"))
		ap.add_argument("-c", "--copy", "--keep-source", action = "store_true",
			help = "copy and sort into sub-directory, keep source file(s) "
				"(default: no)")
		return ap

	@subprog.SubprogWithLogBase.with_log()
	def subprog_main(self, args):
		for fname in self.read_list(args):
			ffmetadata = Metadata.standard_ffmetadata(fname)
			metadata = Metadata.read_ffmetadata(ffmetadata)
			subdir = self.util.fname_replace_win_special_chars(
				metadata.format(args.pattern))
			# make sub-directory
			if not args.dry_run:
				os.makedirs(subdir, exist_ok = True)
			# sort into the sub-directory
			for src in [fname, ffmetadata]:
				dst = os.path.join(subdir, os.path.basename(src))
				method = shutil.copy if args.copy else shutil.move
				if os.path.exists(dst) and (not args.force):
					self.log_err("skipping: %s (already exists)\n" % dst)
				else:
					if args.verbose:
						self.log_err("%s: %s -> %s\n" % (
							("copying" if args.copy else "moving"), src, dst))
					if not args.dry_run:
						method(src, dst)
		return
