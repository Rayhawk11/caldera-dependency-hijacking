#!/usr/bin/env python3
import argparse
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('caldera_dir')
    parser.add_argument('exfil_dir')
    args = parser.parse_args()
    exfil_dir = args.exfil_dir
    caldera_dir = args.caldera_dir
    config_file = f'{caldera_dir}/conf/local.yml'
    decryptor_file = f'{caldera_dir}/app/utility/file_decryptor.py'
    file_list = subprocess.check_output(['find', exfil_dir, '-name', 'requirements_files.txt']).decode(
        'utf-8').splitlines()
    output_file = f'{exfil_dir}/aggregated_requirements.txt'
    with open(output_file, 'w') as f:
        for file in file_list:
            print(f'Starting decryption of exfiltrated file {file}')
            subprocess.check_output(['python3', decryptor_file, '--config', config_file, file])
            decrypted_file = file + '_decrypted'
            with open(decrypted_file) as f2:
                f.write(f2.read())


if __name__ == '__main__':
    main()
