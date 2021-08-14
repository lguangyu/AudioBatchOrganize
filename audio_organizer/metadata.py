#!/usr/bin/env python3

import io
import os
import re
# custom lib
from . import util


@util.StaticUtilityMethods.decorate
class Metadata(dict):
	class MetadataError(RuntimeError):
		pass

	COMMENTS	= ";"
	HEAD_LINE	= ";FFMETADATA1"
	TAG_SEP		= "="

	_FORMATTER_BY_FMT = dict()
	_FORMATTER_BY_TAG = dict()

	class Value(object):
		def __init__(self, value, *ka, **kw):
			super().__init__(*ka, **kw)
			self._value = value
			return
		@property
		def value(self):
			return self._value

		@classmethod
		def from_ffmetadata(cls, value):
			return cls(value = value)
		def to_ffmetadata(self):
			return str(self.value)
		# by default, these are aliases to above methods
		# can be overridden for different behavious between ffmetadata and
		# formatted display values
		@classmethod
		def from_formatted(cls, value):
			return cls.from_ffmetadata(value)
		def to_formatted(self):
			return self.to_ffmetadata()

		@classmethod
		def _setup(cls, tag, fmtstr, regex):
			cls.tag, cls.fmtstr, cls.regex = tag, fmtstr, regex
			return cls
		@property
		def tag(self):
			return self._tag
		@property
		def fmtstr(self):
			return self._fmtstr
		@property
		def regex(self):
			return self._regex

		def __str__(self):
			return self.to_ffmetadata()
		def __repr__(self):
			return str(self)

	# below two class methods are used to add new value type (subclass of Value)
	# to registered Metadata value type list
	@classmethod
	def add_value(host_cls, *, tag, fmtstr, regex):
		def decorator(cls):
			cls._setup(tag, fmtstr, regex)
			host_cls._FORMATTER_BY_FMT[fmtstr] = cls
			host_cls._FORMATTER_BY_TAG[tag] = cls
			return cls
		return decorator
	# this formatter is called for everything not specifically defined
	@classmethod
	def default_value(host_cls):
		return host_cls.add_value(tag = "*", fmtstr = "*", regex = ".+")

	@classmethod
	def get_formatter_by_fmtstr(cls, fmtstr, allow_default = False):
		if fmtstr in cls._FORMATTER_BY_FMT:
			return cls._FORMATTER_BY_FMT[fmtstr]
		elif allow_default:
			return cls._FORMATTER_BY_FMT["*"]
		else:
			raise cls.MetadataError("invalid formatter fmtstr '%s'" % fmtstr)
		return

	@classmethod
	def get_formatter_by_tag(cls, tag, allow_default = False):
		if tag in cls._FORMATTER_BY_TAG:
			return cls._FORMATTER_BY_TAG[tag]
		elif allow_default:
			return cls._FORMATTER_BY_TAG["*"]
		else:
			raise cls.MetadataError("invalid formatter tag '%s'" % tag)
		return

	@classmethod
	def iter_formatter_tags(cls, sort = True):
		meth = sorted if sort else lambda k: k
		yield from meth(cls._FORMATTER_BY_TAG.keys())

	@classmethod
	def iter_formatters(cls, sort = True):
		for k in cls.iter_formatter_tags(sort = sort):
			yield cls.get_formatter_by_tag(k)

	@classmethod
	def get_fields_help_str(cls):
		splits = ["%s=%s" % (f.fmtstr, f.tag) for f in cls.iter_formatters()\
			if (f.tag != "*")]
		return (", ").join(splits)

	def __init__(self, *ka, ffmetadata = None, **kw):
		super().__init__(*ka, **kw)
		# self.ffmetadata stores the ffmetadata file from which is is parsed
		# for metadata instances that are not parsed from an ffmetadata file,
		self.ffmetadata = ffmetadata
		return

	@classmethod
	def standard_ffmetadata(cls, fname, *, extension = "metadata"):
		return cls.util.append_filename_extension(fname, extension)

	@classmethod
	def read_ffmetadata(cls, fname):
		with cls.util.get_fp(fname, "r") as fp:
			lines = fp.read().splitlines()
		if (not lines) or (lines[0] != cls.HEAD_LINE):
			raise RuntimeError("metadata header line missing in %s" % fname)
		# parse metadata content
		new = cls(ffmetadata = fname)
		for line in lines:
			if (not line) or line.startswith(cls.COMMENTS):
				continue
			tag, value = line.split(cls.TAG_SEP, maxsplit = 1)
			# get value formatter and parse values
			tag = tag.lower()
			formatter = cls.get_formatter_by_tag(tag, allow_default = True)
			new[tag] = formatter.from_formatted(value)
		return new

	def save_ffmetadata(self, fname, *, force = None):
		if os.path.exists(fname) and (not force):
			raise IOError("file '%s' already exists" % fname)
		with self.util.get_fp(fname, "w") as fp:
			fp.write(self.HEAD_LINE + "\n")
			for k in sorted(self.keys()):
				v = self[k]
				fp.write(self.TAG_SEP.join([k, self[k].to_ffmetadata()]) + "\n")
		return

	def format(self, fmtstr):
		pos, ret = 0, ""
		for i in re.split("(%.?)", fmtstr):
			# parse each format string started with %
			if i.startswith("%"):
				if i == "%%":
					ret += "%"
					continue
				# parse by formatter
				# here need to allow default formatter
				tag = type(self).get_formatter_by_fmtstr(i).tag
				if tag in self:
					ret += self[tag].to_formatted()
				else:
					raise self.MetadataError("tag '%s' required by '%s' is not "
						"defined in file '%s'" % (tag, i, str(self.ffmetadata)))
					# str(self.ffmetadata) to avoid potential problems caused by
					# self.ffmetadata = None (default value)
			else:
				ret += i
			pos += len(i)
		return ret

	@classmethod
	def fmtstr_to_regex(cls, fmtstr):
		"""
		primarily used internally to turn format string into regular expressions
		"""
		regex, formatters = "", list()
		for i in re.split("(%.?)", fmtstr):
			# parse each format string started with %
			if i.startswith("%"):
				if i == "%%":
					regex += "%"
					continue
				formatter = cls.get_formatter_by_fmtstr(i)
				formatters.append(formatter)
				regex += "(" + formatter.regex + ")"
			else:
				regex += re.escape(i)
		return regex, formatters

	@classmethod
	def from_formatted(cls, fmtstr, s: str):
		regex, formatters = cls.fmtstr_to_regex(fmtstr)
		m = re.match(regex, s)
		if not m:
			raise cls.MetadataError("'%s' unmatch pattern '%s'" % (s, fmtstr))
		new = cls()
		for f, v in zip(formatters, m.groups()):
			new[f.tag] = f.from_formatted(v)
		return new

	def append_merge(self, other):
		for k, v in other.items():
			if k not in self:
				self[k] = v
		return self

	def overwrite_merge(self, other):
		for k, v in other.items():
			self[k] = v
		return self


# add metadata formatters
@Metadata.default_value()
class DefaultValue(Metadata.Value):
	pass

@Metadata.add_value(tag = "album", fmtstr = "%A", regex = ".+")
class AlbumValue(Metadata.Value):
	pass

@Metadata.add_value(tag = "title", fmtstr = "%T", regex = ".+")
class TitleValue(Metadata.Value):
	pass

@Metadata.add_value(tag = "artist", fmtstr = "%a", regex = ".+")
class ArtistValue(Metadata.Value):
	@classmethod
	def from_ffmetadata(cls, value):
		return cls(value = value.split("\\; "))
	def to_ffmetadata(self):
		return ("\\; ").join(self.value)
	@classmethod
	def from_formatted(cls, value):
		return cls(value = value.split(","))
	def to_formatted(self):
		return (",").join(self.value)

@Metadata.add_value(tag = "disc", fmtstr = "%d", regex = "\\d+")
class DiscValue(Metadata.Value):
	@classmethod
	def from_ffmetadata(cls, value):
		return cls(value = util.PosInt(value))

@Metadata.add_value(tag = "track", fmtstr = "%t", regex = "\\d+")
class TrackValue(Metadata.Value):
	@classmethod
	def from_ffmetadata(cls, value):
		return cls(value = util.PosInt(value))

@Metadata.add_value(tag = "year", fmtstr = "%y", regex = "\\d+")
class YearValue(Metadata.Value):
	@classmethod
	def from_ffmetadata(cls, value):
		return cls(value = util.PosInt(value))

@Metadata.add_value(tag = "genre", fmtstr = "%g", regex = ".+")
class GenreValue(Metadata.Value):
	pass
