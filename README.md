playnext
========
A utility for keeping track of the last file played within a directory containing similarly named files. The utility will play the next *n* files within the specified directory, starting from the file following last file played, where *n* is the number specified as the final argument, or 1 by default. Each file should include in its name a number which corresponds to its position in the list of files to be played. For example, if the files are episodes in a TV series, each file name should include the episode number.

Currently, only the mpv player is supported as this utility uses its lua API to determine how many files were actually played to completion. A file is considered complete if the final playback position within the file was at least 85% of the duration or if another file was played after it. It will function without this feature, but it will assume all files requested to be played were played to completion. 

The utility supports both a global configuration mode and a local configuration mode. In local mode, pattern for matching files and the number of the next file to play are stored in a file named .playnext within the directory containing the media files. In global mode, this information will be stored in a single file called .playnextrc in the user's home directory.

Installation
------------
Save file\_completion.lua in the directory ~/.mpv. The main script, playnext.py, can be saved anywhere and executed directly if the python 3 binary is located in /usr/bin/python. Otherwise, run it via the python interpreter: "python playnext.py"

Pattern Specification
---------------------
The first time this utility is run for any given directory, it must be given a pattern for the files it will play in that directory. The pattern should be such that, using file globbing, \*pattern\* will match every file that should be played. The file number, such as the episode number for files in a TV series, in the file name should be included in the pattern and replaced with the special pattern |#|, where the number of #s in the pattern represents the number of digits in the first file's number. For example, many file names will include "EP01" in the name. In this case, the 01 would be replaced by |##|. Example:

For the following list of files:  
The Best Show - EP01 (BD 1080p).mkv  
The Best Show - EP02 (BD 1080p).mkv  
The Best Show - EP03 (BD 1080p).mkv  
The Best Show - EP04 (BD 1080p).mkv  

Specify the pattern like so:  
**playnext -p "The Best Show - EP|##|"**

Usage
-----
**playnext [options] [number of files to play]**

Options
-------
-p pattern  
Specify the pattern for files in the specified directory as described above. Each time this option is specified, the saved pattern for the directory will be overwritten with the new pattern.

-s starting number  
Specify the file number from which to start playing, overriding the saved number of the next file to play. The the next file to play will be saved normally starting from this number.

-d directory  
Specify the directory in which the files to be played are located. The current directory will be used if none is specified. The file pattern and number of the next file to play are read from and stored in this directory as well.

-v  
Enable additional debugging messages. Can be specified multiple times for greater verbosity.
