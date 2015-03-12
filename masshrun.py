import sys
import time
import os
from os.path import join, exists, basename
from masshrun.sshclient import SSHClient


def main():
    if len(sys.argv) < 2:
        print "Usage: %s script_file" % sys.argv[0]
        sys.exit(2)

    script_fname = sys.argv[1]
    with open(script_fname, 'rb') as f:
        script_data = f.read()
    if '\r' in script_data:
        print 'Supplied script contains "\\r", please save with Unix EOLs'
        sys.exit(3)

    output_dir = join("output", 'lastrun')
    if exists(output_dir):
        last_run_filename = join(output_dir, 'script')
        if exists(last_run_filename):
            with open(last_run_filename, 'r') as script_file:
                last_run_script = script_file.read()
        else:
            last_run_script = ''
        last_output_dir = join("output", last_run_script+time.strftime('_%Y%m%d_%H%M%S'))
        os.rename(output_dir, last_output_dir)
    os.makedirs(output_dir)

    # Record script name to identify the output history
    with open(join(output_dir, 'script'), 'w') as script_file:
        script_file.write(basename(script_fname))

    input_lines = []
    while True:
        line = raw_input()
        if not line:
            break
        input_lines.append(line)

    for line in input_lines:
        fields = line.split()
        if len(fields) < 4:
            print "Invalid line, must contain: system_name username hostname password"
            sys.exit(2)
        name, username, hostname, password = fields[:4]
        su_username = fields[4] if len(fields) > 4 else ''
        client = SSHClient(name, username, hostname, password)
        client.connect()
        client.run_su_script(script_fname + ':' + output_dir, su_username)


if __name__ == '__main__':
    main()
