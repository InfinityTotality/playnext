#!/usr/bin/python

import os
import re
import sys
import glob
import argparse
import subprocess


def debug_print(message_level, message, file=sys.stderr):
    global debug_level
    if debug_level >= message_level:
        print(message,file=file)


def parse_local_config(config_file):
    try:
       with open(config_file) as f:
            config_line = f.readline()
    except:
        return None
    if re.match('[^\t]*\t[0-9]+', config_line) is None:
        print('Invalid line in config file: "{}"'.format(config_line),
                file=sys.stderr)
        return None
    else:
        return config_line.strip().split('\t')


def update_local_config(config_file, file_pattern, next_num):
    debug_print(1, 'Updating config with pattern = "{}" and file number = {}'\
                .format(file_pattern,next_num))
    with open(config_file, 'w') as f:
        f.write('{}\t{}\n'.format(file_pattern,next_num))


def parse_global_config(config_file, media_dir):
    try:
        with open(config_file) as f:
            config_lines = f.read().splitlines()
    except:
        return None
    for line in config_lines:
        line_parts = line.split('\t')
        if len(line_parts) < 3:
            print('Invalid line in config file: "{}"'.format(line),
                  file=sys.stderr)
            return None
        elif line_parts[2] == os.path.basename(media_dir):
            return (line_parts[0], line_parts[1])
    return None


def update_global_config(config_file, file_pattern, next_num, media_dir):
    new_lines = []
    media_basedir = os.path.basename(media_dir)
    try:
        with open(config_file) as f:
            existing_lines = f.readlines()
        for line in existing_lines:
            line_parts = line.split('\t')
            if len(line_parts) != 3:
                print('Warning: invalid line in config file: "{}"'.format(line),
                      file=sys.stderr)
                new_lines.append(line)
            elif line_parts[2].rstrip('\n') != media_basedir:
                new_lines.append(line)
    except:
        pass
    new_lines.append('{}\t{}\t{}\n'.format(file_pattern, next_num, media_basedir))
    with open(config_file, 'w') as f:
        f.writelines(new_lines)


def update_config(file_pattern, output, config_file,
        starting_num, num_requested, config_mode, media_dir):
    output_lines = split_output_lines(output)
    if output_lines is None:
        final_num = starting_num + num_requested
    else:
        num_watched = process_output(output_lines, file_pattern, starting_num)
        final_num = starting_num + num_watched
    if config_mode == 'local':
        debug_print(1, 'Mode is local')
        update_local_config(config_file, file_pattern, final_num)
    elif config_mode == 'global':
        debug_print(1, 'Mode is global')
        update_global_config(config_file, file_pattern, final_num, media_dir)


def insert_file_number(file_pattern, file_number):
    match = re.findall('\|#+\|', file_pattern)
    if len(match) > 1:
        print('Multiple replacement patterns found in file pattern "{}"'\
                .format(file_pattern))
        return None
    else:
        replacement_pattern = match[0]
        sigfigs = replacement_pattern.count('#')
        number_string = str(file_number)
        if len(number_string) < sigfigs:
            difference = sigfigs - len(number_string)
            number_string = '0'*difference + number_string
        return file_pattern.replace(replacement_pattern, number_string)


def find_file(file_dir, file_name):
    glob_pattern = '*{}*'.format(glob.escape(file_name))
    glob_dir = glob.escape(file_dir)
    glob_path = os.path.join(glob_dir, glob_pattern)
    debug_print(1, 'Glob pattern: {}'.format(glob_path))
    file_list = glob.glob(glob_path)
    if len(file_list) > 1:
        print('Found more than one file matching pattern {}'\
                .format(glob_path))
        return None
    elif len(file_list) < 1:
        print('Could not find any files matching pattern {}'\
                .format(glob_path))
        return None
    else:
        return file_list[0]


def get_all_files(file_dir, file_pattern, starting_num, num_files):
    files = []
    for num in range(num_files):
        file_name = insert_file_number(file_pattern, starting_num + num)
        file_path = find_file(file_dir, file_name)
        if file_path is None:
            debug_print(1, 'Only found {} of {} files requested'\
                        .format(num, num_files))
            break
        else:
            files.append(file_path)
    if len(files) > 0:
        return files
    else:
        return None


def play_files(files):
    lua_path = os.path.expanduser('~/.mpv/file_completion.lua')
    if not os.path.exists(lua_path):
        print('Warning: mpv file completion script not found' +
               '({})'.format(lua_path))
        print('config will be updated with number of files' +
              'requested regardless of how many were played')
        mpv_command = ['mpv']
        mpv_command.extend(files)
        subprocess.call(mpv_command)
        return None
    else:
        mpv_command = ['mpv','--lua',lua_path,
                       '--msg-level=all=no:file_completion=info']
        mpv_command.extend(files)
        return subprocess.check_output(mpv_command)


def split_output_lines(output):
    if output is None:
        return None
    else:
        output_lines = output.decode(sys.stdout.encoding).splitlines()
        output_lines = [line for line in output_lines if line != '']
        if len(output_lines) < 1:
            return None
        else:
            return output_lines


def process_output(output_lines, file_pattern, starting_num):
    num_watched = 0
    final_percent = 0
    line_gen = (line for line in output_lines)
    for line in line_gen:
        file_name = insert_file_number(file_pattern,
                                       starting_num + num_watched)
        if re.match('\[file_completion\] started .*' +
                    re.escape(file_name), line) is not None:
            num_watched += 1
            final_percent = 0
            for line in line_gen:
                match = re.match('\[file_completion\] percent ' +
                        '([0-9]+)\.[0-9]*', line)
                if match is not None:
                    final_percent = int(match.group(1))
                elif line[0:23] == '[file_completion] ended':
                    break
                else:
                    print('Unexpected line during episode:')
                    print(line)
                    break
        elif re.match('\[file_completion\] percent ' +
                '([0-9]+)\.[0-9]*', line) is not None:
            pass
        else:
            print('Unexpected line when looking for start of episode {}: '\
                  .format(starting_num + num_watched))
            print(line)
            return None
    if final_percent < 85 and num_watched > 0:
        num_watched -= 1

    return num_watched


parser = argparse.ArgumentParser(description='A utility for keeping track of '+
        'the last file played within a directory containing similarly named '+
        'files. The utility will play the next n files within the specified ' +
        'directory, starting from the file following the next file to play, '+
        'where n is the number specified as the last argument, or 1 by '+
        'default. Each file should include in its name a number which '+
        'corresponds to its position in the list of files to be played. '+
        'For example, if the files are episodes in a TV series, each file '+
        'name should include the episode number.')

parser.add_argument('-p', dest='pattern', help='Specify the pattern which '+
        'matches files within the specified directory such that, using file '+
        'globbing, *pattern* will match all the files to be played. The file '+
        'number should be replaced with the special pattern |#|. The number '+
        'of #s in this pattern corresponds to the number of digits in the '+
        'first file\'s number.')
parser.add_argument('-d', dest='directory', help='Specify the directory in '+
        'which the files to be played are located. The current directory '+
        'will be used if none is specified. If using local config mode, '+
        'the config file will be saved in and read from this directory '+
        'as well.')
parser.add_argument('-s', dest='start', help='Specify the file number from '+
        'which to start playing, overriding the saved number of the next '+
        'file to play. The the next file to play will be saved normally '+
        'starting from this number.')
parser.add_argument('-c', dest='config_mode', help='Specify which config '+
        'mode should be used; either "global" or "local". Global uses a '+
        'single config file in the home directory to store data. Local '+
        'mode creates a file in each directory files are opened from '+
        'to keep track of progress within that directory.', default='global')
parser.add_argument('-v', dest='verbosity', action='count', default=0,
        help='Enable additional debugging messages. Can be specified '+
        'multiple times for greater verbosity.')
parser.add_argument('number', nargs='?', default=1)

args = parser.parse_args()

debug_level = args.verbosity
num_files = int(args.number)

if args.directory is None:
    file_dir = os.getcwd()
else:
    if os.path.isdir(args.directory):
        file_dir = args.directory
    else:
        print('Invalid directory: {}'.format(args.directory))
        exit()

if args.config_mode == 'local':
    config_file = os.path.join(file_dir, '.playnext')
else:
    config_file = os.path.expanduser('~/.playnextrc')
config = None

if args.start is None or args.pattern is None:
    if args.config_mode == 'local':
        config = parse_local_config(config_file)
    else:
        config = parse_global_config(config_file, file_dir)
    debug_print(1, 'Config:')
    debug_print(1, config)
    if config is None:
        if args.pattern is None:
            print('No config found for directory {}'.format(file_dir))
            print('Please specify a pattern with -p')
            exit()

pattern = args.pattern if args.pattern is not None else config[0]\
        if config is not None else exit() # this should never be reached
starting_num = int(args.start) if args.start is not None else int(config[1])\
        if config is not None else 1

files = get_all_files(file_dir, pattern, starting_num, num_files)
debug_print(1, 'Files:')
debug_print(1, files)
if files is not None:
    print("Playing:")
    for file in files:
        print(os.path.basename(file))
    output = play_files(files)
    debug_print(2, 'Output:')
    debug_print(2, output)
    update_config(pattern, output, config_file, starting_num,
                  num_files, args.config_mode, file_dir)
else:
    print('Error: could not get file list')
    update_config(pattern, None, config_file, starting_num,
                  0, args.config_mode, file_dir)
