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

`ffmpeg`: required to transcode between audio formats, read and remap metadata
`shntools`: required to split with CUE file
`sox`: required to draw audio spectrogram

Installation
------------

Download this repository then run in terminal/command line:

```
python3 setup.py install
```

Note: dependencies are external programs not in python native.
They must be installed separately.
