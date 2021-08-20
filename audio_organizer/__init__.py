#!/usr/bin/env python3

import argparse
import sys
import traceback
# custom lib
from . import subprog
from .metadata import Metadata
# subprog implementations
# these modules only need import when they will be added to subprogram registry
# automatically
from . import clean_temps
from . import draw_spectrogram
from . import dump_metadata
from . import parse_metadata
from . import remap_metadata
from . import sort_by_metadata
from . import sort_disc_track
from . import split_by_cue


# main program class
class AudioOrganizer(object):
	def __init__(self, *ka, **kw):
		super().__init__(*ka, **kw)
		self.subprogs = subprog.SubprogReg()
		self.setup_argparser()
		return

	def setup_argparser(self) -> "self":
		# this is main argparser
		self.argparser = ap = argparse.ArgumentParser()
		# add subprog argparser
		sp = ap.add_subparsers(dest = "subprog", required = True,
			metavar = "subprog",
			help = "subprogram to call, choices: "\
				+ (", ").join(self.subprogs.iter_subprog_names(True)))
		for _, subprog in self.subprogs.iter_subprog_items(sort = True):
			subprog.create_argparser(sp)
		return self

	def parse_args(self):
		self.args = self.argparser.parse_args()
		# refine args with subprog refine function
		self.subprogs.get_subprog(self.args.subprog).refine_args(self.args)
		return self.args

	def call_arg_subprog_main(self):
		subprog = self.subprogs.get_subprog(self.args.subprog)
		return subprog.subprog_main(args = self.args)

	def main(self):
		self.parse_args()
		self.call_arg_subprog_main()
		return
