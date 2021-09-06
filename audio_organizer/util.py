#!/usr/bin/env python3

import io
import os


SPEC_CHAR_TRANSTABLE = {int.from_bytes(k.encode("utf-8"), "little") : v\
	for k, v in zip("\\/*?:<>|", "＼／＊？：＜＞｜")
}


class PosInt(int):
	def __new__(cls, *ka, **kw):
		new = super().__new__(cls, *ka, **kw)
		if new <= 0:
			raise ValueError("PosInt must be positive")
		return new


class NonNegInt(int):
	def __new__(cls, *ka, **kw):
		new = super().__new__(cls, *ka, **kw)
		if new < 0:
			raise ValueError("NonNegInt must be non-negative")
		return new


class CommaSepNonNegInts(list):
	def __init__(self, s, *ka, **kw):
		if isinstance(s, str):
			s = s.split(",")
		super().__init__([NonNegInt(i) for i in s], *ka, **kw)
		return


class StaticUtilityMethods(object):
	def decorate(cls):
		"""
		use as decorator on class
		the decorated class can use
		cls.util.<methods> or self.util.<methods>
		"""
		cls.util = StaticUtilityMethods
		return cls

	@staticmethod
	def get_fp(file, *ka, factory = open, **kw):
		if isinstance(file, io.IOBase):
			ret = file
		elif isinstance(file, str):
			ret = factory(file, *ka, **kw)
		else:
			raise TypeError("file must be file handle or str, not '%s'"\
				% type(file).__name__)
		return ret

	@staticmethod
	def samefile(f1, f2):
		ret = False if ((not os.path.exists(f1)) or (not os.path.exists(f2)))\
			else os.path.samefile(f1, f2)
		return ret

	#@staticmethod
	#def safe_fname(fname, *, check_suffix = "-"):
	#	# replace special characters (mostly, to protect windows users)
	#	ret = StaticUtilityMethods.replace_win_special_chars(fname)
	#	# replace leading "-" to prevent monkey-patch
	#	ret = os.path.join(".", ret) if ret.startswith(check_suffix) else ret
	#	return ret

	@staticmethod
	def fname_prevent_monkey_patch(fname, *, check_chars = "-"):
		# prevent monkey-patching filenames starting with specific characters,
		# usually a dash (-)
		if any([fname.startswith(c) for c in check_chars]):
			ret = os.path.join(os.path.curdir, fname)
		else:
			ret = fname
		return ret

	@staticmethod
	def fname_replace_win_special_chars(fname):
		return fname.translate(SPEC_CHAR_TRANSTABLE).replace("\"", "''")

	@staticmethod
	def get_cmd_str(cmd):
		return str(cmd)

	@staticmethod
	def append_filename_extension(fname: str, extension: str) -> str:
		"""
		append extension to a file name
		"""
		return fname + os.path.extsep + extension

	@staticmethod
	def change_filename_extension(fname: str, extension: str) -> str:
		"""
		change the extension of a file name
		if the file name has no extension, append the extension instead
		"""
		bname, ext = os.path.splitext(fname)
		return bname + os.path.extsep + extension

	@staticmethod
	def get_default_conflict_prefix():
		return "CONFLICT" + os.path.extsep
