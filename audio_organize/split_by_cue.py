#!/usr/bin/env python3

import os
# custom lib
from . import subprog
from .metadata import Metadata


@subprog.SubprogReg.new_subprog("split_by_cue",
	help = "split single-piece audio files by cue, 'shnsplit' must be present",
	desc = "split single-piece audio files by cue, 'shnsplit' must be present")
class SubprogSplitByCue(subprog.SubprogWithLogBase):
	@subprog.SubprogBase.append_opt_verbose
	@subprog.SubprogBase.append_opt_dryrun
	@subprog.SubprogBase.append_opt_force
	@subprog.SubprogBase.append_opt_program("ffmpeg",
		help_extra = ", required for transcoding")
	@subprog.SubprogBase.append_opt_program("shnsplit")
	def create_argparser(self, subparsers, *ka, **kw):
		ap = super().create_argparser(subparsers, *ka, **kw)
		ap.add_argument("-i", "--input", type = str, required = True,
			metavar = "file",
			help = "input audio file in single-piece (required)")
		ap.add_argument("-c", "--cue", type = str, required = True,
			metavar = "file",
			help = "input cue file (required)")
		ap.add_argument("-R", "--transcode", type = str, metavar = "format",
			help = "output audio file format; note using some format may cause "
				"problems (default: do not transcode)")
		return ap

	def _transcode(self, input, output_ext, *, ffmpeg = "ffmpeg", force = None,
			dry_run = None, verbose = None) -> str:
		bn, ext = os.path.splitext(input)
		if (not output_ext) or (ext == os.path.extsep + output_ext):
			# no need to transcode
			if verbose:
				self.log_err("skipping transcoding: '%s'\n" % input)
			ret = input
		else:
			# do transcoding
			ret = output = bn + os.path.extsep + output_ext
			cmd = [ffmpeg]
			if force:
				cmd.append("-y")
			cmd.extend(["-i", self.util.fname_prevent_monkey_patch(input),
				self.util.fname_prevent_monkey_patch(output)])
			self.logged_external_call(cmd, dry_run = dry_run, verbose = verbose)
		return ret

	def _split_by_cue(self, input, cue, *, shnsplit = "shnsplit", force = None,
			dry_run = None, verbose = None):
		cmd = [shnsplit]
		if force:
			cmd.extend(["-O", "always"])
		cmd.extend(["-t", "%n. %t - %p", "-f",
			self.util.fname_prevent_monkey_patch(cue), "-o",
			(os.path.splitext(input)[1]).lstrip(os.path.extsep),
			self.util.fname_prevent_monkey_patch(input)])
		self.logged_external_call(cmd, dry_run = dry_run, verbose = verbose)
		return

	@subprog.SubprogWithLogBase.with_log()
	def subprog_main(self, args):
		split_input = self._transcode(args.input, args.transcode,
			ffmpeg = args.ffmpeg, force = args.force, dry_run = args.dry_run,
			verbose = args.verbose)
		self._split_by_cue(split_input, args.cue, shnsplit = args.shnsplit,
			force = args.force, dry_run = args.dry_run, verbose = args.verbose)
		# clean temp transcode file
		if (not args.dry_run)\
			and (not self.util.samefile(args.input, split_input)):
			os.remove(split_input)
		return
