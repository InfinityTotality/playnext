#!/usr/bin/python

import os
import re
import sys
import glob
import argparse
import subprocess


def debug_print(message_level, message):
    global debug_level
    if debug_level >= message_level:
        print(message)


def parse_config(config_file):
    if not os.path.isfile(config_file):
        return None
    else:
        with open(config_file) as f:
            config_line = f.readline()
        if re.match('[^\t]*\t[0-9]+', config_line) is None:
            print('Invalid line in config file {}'.format(config_file))
            return None
        else:
            return config_line.strip().split('\t')


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
    lua_path = os.path.join(os.environ['HOME'],'.mpv/file_completion.lua')
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


def update_config(file_pattern, output, config_file, starting_num, num_files):
    if output is None:
        final_num = starting_num + num_files
    else:
        final_num = starting_num
        final_percent = 0
        output_lines = output.decode(sys.stdout.encoding).split('\n')
        output_lines = [line.strip() for line in output_lines if line != '']
        if len(output_lines) < 1:
            final_num = starting_num + num_files
        else:
            line_gen = (line for line in output_lines)
            for line in line_gen:
                file_name = insert_file_number(file_pattern, final_num)
                if re.match('\[file_completion\] started .*' + 
                            re.escape(file_name), line) is not None:
                    final_num += 1
                    final_percent = 0
                    for line in line_gen:
                        match = re.match('\[file_completion\] percent ' +
                                '([0-9]+)\.[0-9]*', line)
                        if match is not None:
                            final_percent = int(match.group(1))
                        elif line == '[file_completion] ended':
                            break
                        else:
                            print('Unexpected line during episode:')
                            print(line)
                            return False
                elif re.match('\[file_completion\] percent ' +
                        '([0-9]+)\.[0-9]*', line) is not None:
                    pass
                else:
                    print('Unexpected line when looking for start of ' +
                            'episode {}:'.format(final_num))
                    print(line)
                    return False
            if final_percent < 90 and final_num > starting_num:
                final_num -= 1
    debug_print(1, 'Updating config with pattern = "{}" and file number = {}'\
                .format(file_pattern,final_num))
    with open(config_file, 'w') as f:
        f.write('{}\t{}\n'.format(file_pattern,final_num))


parser = argparse.ArgumentParser()

parser.add_argument('-p', dest='pattern')
parser.add_argument('-d', dest='directory')
parser.add_argument('-s', dest='start')
parser.add_argument('-v', dest='verbosity', action='count', default=0)
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

config_file = os.path.join(file_dir, '.playnext')
config = None

if args.start is None or args.pattern is None:
    config = parse_config(config_file)
    debug_print(1, 'Config:')
    debug_print(1, config)
    if config is None:
        if args.pattern is None:
            print('No config file found in directory {}'.format(file_dir))
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
    output = play_files(files)
    debug_print(2, 'Output:')
    debug_print(2, output)
    update_config(pattern, output, config_file, starting_num, num_files)
else:
    print('Error: could not get file list')
    update_config(pattern, None, config_file, starting_num, 0)
