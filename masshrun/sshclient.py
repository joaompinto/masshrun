import sys
import paramiko
import re
import os
from random import randint
from os.path import isdir, join

class SSHClient():
    """
    Encapsulates an ssh client connection and integratted with the password
    manager.
    """
    def __init__(self, name, username, hostname, password):
        self.name = name
        self.hostname = hostname
        self.username = username
        self.password = password
        self.ssh = ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self):
        """ Establish the connection """
        ssh = self.ssh
        port = 22
        print self.hostname
        ssh.connect(self.hostname, port = port
                    , username=self.username, password=self.password, timeout=20)
        self.chan = chan = ssh.invoke_shell(term='vt100')
        chan.transport.set_keepalive(10)
        chan.settimeout(30)
        self._wait_for_data(["Last login", '[@#$:>]'], verbose=True)

    def _wait_for_data(self, options, verbose=False):
        chan = self.chan
        data = ""
        while True:
            x = chan.recv(1024)
            if len(x) == 0:
                self.log( "*** Connection terminated\r")
                sys.exit(3)
            data += x
            if verbose:
                sys.stdout.write(x)
                sys.stdout.flush()
            for i in range(len(options)):
                if re.search(options[i], data):
                    return i
        return -1

    def sendall(self, message):
        self.chan.sendall(message)

    def run_su_script(self, run_specification):
        if ':' in run_specification:
            local_script_fname, local_output_dir = run_specification.split(':')
            if not isdir(local_output_dir):
                sys.stderr.write("ERROR: Output directory %s for -R must exist!\n" % local_output_dir)
                sys.exit(9)
        else:
            local_script_fname = run_specification
            local_output_dir = None
        username, hostname = self.username, self.hostname
        tmp_fname = '/tmp/r_%s_%d_%d' % (username, os.getpid(), randint(1, 9999))
        sftp = paramiko.SFTPClient.from_transport(self.chan.transport)
        sftp.put(local_script_fname, tmp_fname)
        sftp.chmod(tmp_fname, 0700)
        self.sendall("sudo -K\n")
        self.sendall("sudo su -\n")
        self._wait_for_data(['[P|p]assword'])
        self.sendall(self.password+"\n")
        # Critical sync point, we must receive a prompt before resuming
        self._wait_for_data(['[@#$:>]'])
        self.sendall("%s > %s.out 2>%s.err\n" %
            (tmp_fname, tmp_fname, tmp_fname))
        self.sendall("chown %s %s.out %s.err\n" %
            (username, tmp_fname, tmp_fname))
        self.sendall('echo "Just" "Randomsassh"\n')
        self._wait_for_data(["Just Randomsassh"])
        local_fname = join(local_output_dir, self.name+'.out')
        sftp.get(tmp_fname+'.out', local_fname)
        local_fname = join(local_output_dir, self.name+'.err')
        sftp.get(tmp_fname+'.err', local_fname)
        self.sendall('rm -f %s %s.out %s.err\n' %
            (tmp_fname, tmp_fname, tmp_fname))
        if os.path.getsize(local_fname) == 0:
            os.unlink(local_fname)
        if not local_output_dir:
            sys.stdout.write(open(local_fname).read())
