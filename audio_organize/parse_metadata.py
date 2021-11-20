#!/usr/bin/env python3

import os
# custom lib
from . import subprog
from . import util
from .metadata import Metadata


@subprog.SubprogReg.new_subprog("parse_metadata",
	help = "parse metadata from file names on a list",
	desc = "parse metadata from file names on a list")
class SubprogParseMetadata(subprog.SubprogWithLogBase,
		subprog.ListBasedSubprogBase):
	@subprog.SubprogBase.append_opt_verbose
	@subprog.SubprogBase.append_opt_dryrun
	@subprog.SubprogBase.append_opt_force
	def create_argparser(self, subparsers, *ka, **kw):
		ap = super().create_argparser(subparsers, *ka, **kw)
		ap.add_argument("pattern", type = str,
			help = ("file name pattern, must full-match including extension; "
				"available fields: %s"\
				% Metadata.get_fields_help_str()).replace("%", "%%"))
		xp = ap.add_mutually_exclusive_group()
		xp.add_argument("--append-merge", action = "store_true",
			help = "merge parsed metadata into metadata file (if exists); "
				"only add parsed tags that are not seen in the existing "
				"metadata file; "
				"exclusive with --overwrite-merge and assumes -f/--force "
				"(default: no)")
		xp.add_argument("--overwrite-merge", action = "store_true",
			help = "merge parsed metadata into metadata file (if exists); "
				"parsed tags will always overwrite those in the existing "
				"metadata file; "
				"exclusive with --append-merge and assumes -f/--force "
				"(default: no)")
		# add options to allow manually override values
		gp = ap.add_argument_group("manually override metadata values")
		for valtype in Metadata.iter_valtypes():
			params = valtype.argparse_params
			if (not valtype.is_default()) and params:
				gp.add_argument("--" + (valtype.tag.replace("_", "-")),
					type = params["type"], metavar = params["metavar"],
					help = ("override tag '%s'" % valtype.tag)\
						+ params.get("help_extra", ""))
		return ap

	def refine_args(self, args):
		args = super().refine_args(args)
		if args.overwrite_merge or args.append_merge:
			args.force = True
		return args

	def override_by_manual(self, args, metadata):
		for valtype in Metadata.iter_valtypes():
			if not valtype.is_default():
				val = getattr(args, valtype.tag)
				if val:
					metadata[valtype.tag] = valtype.from_formatted(val)
		return

	@subprog.SubprogWithLogBase.with_log()
	def subprog_main(self, args):
		for fname in self.read_list(args):
			if args.verbose:
				self.log_err("parsing: '%s'\n" % fname)
			ffmetadata = Metadata.standard_ffmetadata(fname)
			parsed_metadata = Metadata.from_formatted(args.pattern, fname)
			exist_metadata = Metadata.read_ffmetadata(ffmetadata)\
				if os.path.exists(ffmetadata) else Metadata()
			# update metadata values
			# resolve conflicts between parsed and already-exist
			# then apply manual override (highest priority)
			if args.append_merge:
				metadata = exist_metadata.append_merge(parsed_metadata)
			elif args.overwrite_merge:
				metadata = exist_metadata.overwrite_merge(parsed_metadata)
			else:
				metadata = parsed_metadata
			self.override_by_manual(args, metadata)
			# save metadata file
			ffmetadata = Metadata.standard_ffmetadata(fname)
			if args.verbose:
				self.log_err("writing: '%s'\n" % ffmetadata)
			if not args.dry_run:
				metadata.save_ffmetadata(ffmetadata, force = args.force)
		return
