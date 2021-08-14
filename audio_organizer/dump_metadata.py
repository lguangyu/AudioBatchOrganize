#!/usr/bin/env python3

# custom lib
from . import subprog
from audio_organizer import Metadata


@subprog.SubprogReg.new_subprog("dump_metadata",
	help = "dump metadata from audio files on a list",
	desc = "dump metadata from audio files on a list; 'ffmpeg' must be "
		"available")
class SubprogDumpMetadata(subprog.SubprogWithLogBase,
		subprog.ListBasedSubprogBase):
	@subprog.SubprogBase.append_opt_verbose
	@subprog.SubprogBase.append_opt_dryrun
	@subprog.SubprogBase.append_opt_force
	def create_argparser(self, subparsers, *ka, **kw):
		ap = super().create_argparser(subparsers, *ka, **kw)
		return ap

	@subprog.SubprogWithLogBase.with_log()
	def subprog_main(self, args):
		for fname in self.read_list(args):
			ffmetadata = Metadata.standard_ffmetadata(fname)
			cmd = ["ffmpeg"]
			if args.force:
				cmd.append("-y")
			cmd.extend(["-i", self.util.fname_prevent_monkey_patch(fname),
				"-c:a", "discard", "-f", "ffmetadata",
				self.util.fname_prevent_monkey_patch(ffmetadata)])
			self.logged_external_call(cmd, dry_run = args.dry_run,
				verbose = args.verbose)
		return
