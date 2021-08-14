#!/usr/bin/env python3

import os
# custom lib
from . import subprog
from . import util
from audio_organizer import Metadata


@subprog.SubprogReg.new_subprog("sort_disc_track",
	help = "split continuous metadata track# into disc&tract tags, "
		"make changes to metadata file(s) inplace",
	desc = "split continuous metadata track# into disc&tract tags, "
		"make changes to metadata file(s) inplace")
class SubprogSortDiscTrack(subprog.SubprogWithLogBase,
		subprog.ListBasedSubprogBase):
	@subprog.SubprogBase.append_opt_verbose
	@subprog.SubprogBase.append_opt_dryrun
	def create_argparser(self, subparsers, *ka, **kw):
		ap = super().create_argparser(subparsers, *ka, **kw)
		ap.add_argument("-T", "--num-track-list", metavar = "int[,int[,...]]",
			type = util.CommaSepNonNegInts, required = True,
			help = "a commpa-separated list of total num tracks per disc in "
				"disc order (required)")
		ap.add_argument("--track-offset", type = int, default = 0,
			metavar = "int",
			help = "treat input (continuous) track number as <value> + "
				"<offset> (default: 0)")
		return ap

	def _split_by_list(self, metadata, num_track_list: list, track_offset = 0)\
			-> (int, int):
		track = util.PosInt(metadata["track"]) + track_offset
		for i, v in enumerate(num_track_list):
			if track > v:
				track -= v
			else:
				disc = i + 1
				break
		return disc, track

	@subprog.SubprogWithLogBase.with_log()
	def subprog_main(self, args):
		for fname in self.read_list(args):
			ffmetadata = Metadata.standard_ffmetadata(fname)
			metadata = Metadata.read_ffmetadata(ffmetadata)
			if "disc" in metadata:
				self.log_err("skipping: %s (tag 'disc' already exists)\n"\
					% fname)
				continue
			if "track" not in metadata:
				self.log_err("skipping: %s (tag 'track' not exists)\n" % fname)
				continue
			if util.PosInt(metadata["track"]) > sum(args.num_track_list):
				self.log_err("skipping: %s (continuous track number greater "
					"than sum of -T/--num-track-list)\n")
				continue
			disc, track = self._split_by_list(metadata, args.num_track_list,
				track_offset = args.track_offset)
			if args.verbose:
				self.log_err("parsing: T%d -> D%d,T%d (%s)\n"\
					% (util.PosInt(metadata["track"]), disc, track, fname))
			metadata["disc"], metadata["track"] = str(disc), str(track)
			# save modified metadata file, force = True is a must
			if args.verbose:
				self.log_err("saving: %s\n" % ffmetadata)
			if not args.dry_run:
				metadata.save_ffmetadata(ffmetadata, force = True)
		return
