#!/usr/bin/env python3

import os
# custom lib
from . import subprog


@subprog.SubprogReg.new_subprog("draw_spectrogram",
	help = "draw spectrogram for audio files on a list",
	desc = "draw spectrogram for audio files on a list, 'sox' must be "
		"available")
class SubprogDrawSpectrogram(subprog.SubprogWithLogBase,
		subprog.ListBasedSubprogBase):
	@subprog.SubprogBase.append_opt_verbose
	@subprog.SubprogBase.append_opt_dryrun
	@subprog.SubprogBase.append_opt_program("sox")
	def create_argparser(self, subparsers, *ka, **kw):
		ap = super().create_argparser(subparsers, *ka, **kw)
		ap.add_argument("-g", "--image-format", type = str, default = "png",
			choices = ["png", "jpg", "bmp", "tiff"],
			help = "output spectrogram image format/extension (default: png)")
		return ap

	@subprog.SubprogWithLogBase.with_log()
	def subprog_main(self, args):
		for fname in self.read_list(args):
			spec = self.util.append_filename_extension(fname, args.image_format)
			cmd = [args.sox, self.util.fname_prevent_monkey_patch(fname), "-n",
				"spectrogram", "-o", self.util.fname_prevent_monkey_patch(spec)]
			self.logged_external_call(cmd, dry_run = args.dry_run,
				verbose = args.verbose)
		return
