#!/usr/bin/env python3

import os
import shutil
# custom lib
from . import subprog
from audio_organizer import Metadata


@subprog.SubprogReg.new_subprog("remap_metadata",
	help = "re-map metadata to audio files on a list",
	desc = "re-map metadata to audio files on a list; mapping metadata must "
		"contain at least artist and title fields; 'ffmpeg' must be available "
		"unless -m/--move-only is used; if -R/--re-encode is used, required "
		"external codecs/tools must also be available")
class SubprogRemapMetadata(subprog.SubprogWithLogBase,
		subprog.ListBasedSubprogBase):
	@subprog.SubprogBase.append_opt_verbose
	@subprog.SubprogBase.append_opt_dryrun
	@subprog.SubprogBase.append_opt_force
	@subprog.SubprogBase.append_opt_program("ffmpeg")
	def create_argparser(self, subparsers, *ka, **kw):
		ap = super().create_argparser(subparsers, *ka, **kw)
		ap.add_argument("-p", "--rename-pattern", type = str, default = None,
			metavar = "pattern",
			help = ("output file renaming pattern, not including extension; "
				"available fields: %s (default: no renaming)"\
				% Metadata.get_fields_help_str()).replace("%", "%%"))
		gp = ap.add_mutually_exclusive_group()
		gp.add_argument("-m", "--move-only", action = "store_true",
			help = "when set, listed files will be only moved/renamed without "
				"metadata re-mapping; this is useful when no metadata content "
				"need to be changed, therefore can accelerate the process by "
				"bypassing making changes in file content; exclusive with "
				"-R/--re-encode (default: no)")
		gp.add_argument("-R", "--transcode", type = str, default = None,
			metavar = "format",
			help = "transcode audio stream to given format/extension; if not "
				"set, the extension of input audio file will be used; exclusive"
				" with -m/--move-only (default: no)")
		return ap

	def _remap_by_move(self, fname, new_fname, args, metadata):
		if args.verbose:
			self.log_err("copying: %s -> %s\n" % (fname, new_fname))
		if not args.dry_run:
			shutil.copy(fname, new_fname)
		return

	def _remap_call_ffmpeg(self, fname, new_fname, args, metadata):
		# finalize file names
		# these file name modifications must be done just before cmd calling
		fname = self.util.fname_prevent_monkey_patch(fname)
		new_fname = self.util.fname_prevent_monkey_patch(new_fname)
		ffmetadata = self.util.fname_prevent_monkey_patch(metadata.ffmetadata)
		# make cmd
		cmd = [args.ffmpeg]
		if args.force:
			cmd.append("-y")
		cmd.extend(["-i", fname, "-i", ffmetadata, "-map_metadata", "1"])
		# differentiate if need re-encode
		# if re-encode is set, it should not be None
		if args.transcode:
			cmd.append(new_fname)
		else:
			cmd.extend(["-codec", "copy", new_fname])
		# call
		self.logged_external_call(cmd, dry_run = args.dry_run,
			verbose = args.verbose)
		return

	@subprog.SubprogWithLogBase.with_log()
	def subprog_main(self, args):
		for fname in self.read_list(args):
			# parse metadata
			ffmetadata = Metadata.standard_ffmetadata(fname)
			metadata = Metadata.read_ffmetadata(ffmetadata)
			# figure out new file name
			# first 1 selects the extension, second 1: discard extsep
			extension = args.transcode or os.path.splitext(fname)[1][1:]
			if args.rename_pattern:
				new_fname = self.util.append_filename_extension(
					metadata.format(args.rename_pattern), extension
				)
			else:
				# if not renaming, the file name is kept
				# this will always trigger adding conflict prefix however
				new_fname = fname
			# finally, protect windows users
			new_fname = self.util.fname_replace_win_special_chars(new_fname)
			# make sure no conflicts
			if self.util.samefile(fname, new_fname):
				new_fname = self.util.get_conflict_prefix() + new_fname
			# remap metadata
			if args.move_only:
				self._remap_by_move(fname, new_fname, args, metadata)
			else:
				self._remap_call_ffmpeg(fname, new_fname, args, metadata)
		return
