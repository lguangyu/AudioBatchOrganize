Audio Batch Organizer
=====================

This program is used to edit audio file metadata (like title, track number,
disc number, artists) in batch, and organize audio files based on metadata.

Typical use cases include:

* dump metadata from audio files as text files for editing
* remap updated metadata back to audio files
* reformat file names based on metadata, for example, to `<title> - <artist>`
* sort files into sub-directories based on metadata, for example, per album
* split CD extract into tracks based on CUE file


External dependencies
---------------------

* `ffmpeg`: required to transcode between audio formats, read and remap metadata
* `shntool`: required to split with CUE file
* `sox`: required to draw audio spectrogram


Installation
------------

Download this repository then run in terminal/command line:

```
python3 setup.py install
```

Note: dependencies are external programs not in python native.
They must be installed separately.


Examples
--------

### 1. Split EAC-extracted single-track file by CUE

Assuming there are two files: `cd.wav` and `cd.cue` ripped from a CD.
The first command is a wrapper to call `shntool` to split it into tracks:

```
audio-organize split_by_cue -i cd.wav -c cd.cue
```

The result may look like:

```
01. track_title_01 - Artist_1.wav
02. track_title_02 - Artist_1.wav
03. track_title_03 - Artist_1.wav
```

The second command parses the track#, title and artists from those files:

```
# first need to make a 'list' file for all audio files we want to process.
ls *.wav > list

# the list filename is defaulted to be 'list', which can be omitted;
# if a different name is used for the above ls output, then it must be specified
# here
audio-organize parse_metadata list "%t. %T - %a.wav"
```

`"%t. %T - %a.wav"` is used to pattern-matching the file names to parse specific
fields.
More field specifiers and their definitions are explained by
`audio-organize parse_metadata --help`.

If we want to set more metadata, or override parsed values, other manual field
overriding options can be used.
For example:

```
audio-organize parse_metadata list "%t. %T - %a.wav" \
	--album "some album" \
	--artist "Artist_1,Artist_2"
```

will set `album=some album` in all output metadata files, and override their
`artist` field to the manual value instead of the parsed value.

The output should look like:

```
01. track_title_01 - Artist_1.wav
01. track_title_01 - Artist_1.wav.metadata
02. track_title_02 - Artist_1.wav
02. track_title_02 - Artist_1.wav.metadata
03. track_title_03 - Artist_1.wav
03. track_title_03 - Artist_1.wav.metadata
```

At this stage, more text editing can be done on the metadata files.


The third command remaps the new metadata back to audio files with preferred
renaming pattern:

```
audio-organize remap_metadata -p "%T - %a" -R flac list
```

`remap_metadata` will update `*.metadata` files back into the audio files.
In addition, `-p "%T - %a"` requires the output file names to be in
`<title> - <artist>` format (file extensions will be added automatically).
Finally `-R flac` instructs the output to be transcoded into `flac`.

The output will be (here assuming we didn't override artist field):

```
01. track_title_01 - Artist_1.wav
01. track_title_01 - Artist_1.wav.metadata
02. track_title_02 - Artist_1.wav
02. track_title_02 - Artist_1.wav.metadata
03. track_title_03 - Artist_1.wav
03. track_title_03 - Artist_1.wav.metadata
track_title_01 - Artist_1.flac
track_title_02 - Artist_1.flac
track_title_03 - Artist_1.flac
```

The last command cleans up all temporary files in this process, including
input files in the `list` file and all `*.metadata` files.

```
audio-organize clean_temps list
```

In some cases the output files with file names labelled as `CONFLICT` will be
generated by `remap_metadata` due to file names being exactly the same between
input and output.
In those cases the next command can be added *after* the `clean_temps` call to
remove `CONFLICT` tags:

```
audio-organize rename_conflict
```

Known issues
------------

* In some cases, conflict file names cannot be recognized
* Need file name mangling to trim down those longer than system file name limit
* Certain versions of `shntool` can experience error dealing with >16bit formats
