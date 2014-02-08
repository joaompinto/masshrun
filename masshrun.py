import sys
import time
import os
from os.path import join
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

    output_dir = join("output", time.strftime('%Y%m%d_%H%M%S'))
    os.makedirs(output_dir)

    input_lines =[]
    while True:
        line = raw_input()
        if not line:
            break
        input_lines.append(line)
    #sys.stdin.read()

    for line in input_lines:
        name, username, hostname, password = line.split()
        client = SSHClient(name, username, hostname, password)
        client.connect()
        client.run_su_script(script_fname +':' + output_dir)

if __name__ == '__main__':
    main()
