#!/usr/bin/env python3

import argparse
import os
import platform
import subprocess
import sys
import shutil

def testFile(name, klee_path, lli_path):
    print(f'CWD: \"{os.getcwd()}\"')
    baseName,ext = os.path.splitext(name)
    exeFile = f'Output/linked_{baseName}.bc'

    make_prog = 'gmake' if platform.system() == 'FreeBSD' else 'make'
    print('-- building test bitcode --')
    if os.path.exists("Makefile.cmake.test"):
        # Prefer CMake generated make file
        make_cmd = f'{make_prog} -f Makefile.cmake.test {exeFile} 2>&1'
    else:
        make_cmd = f'{make_prog} {exeFile} 2>&1'
    print(f"EXECUTING: {make_cmd}")
    sys.stdout.flush()
    if os.system(make_cmd):
        raise SystemExit('make failed')

    print('\n-- running lli --')
    lli_cmd = [lli_path, '-force-interpreter=true', exeFile]
    print(f"EXECUTING: {lli_cmd}")

    lliOut = subprocess.check_output(lli_cmd).decode()
    print('-- lli output --\n%s--\n' % (lliOut,))

    print('-- running klee --')
    klee_out_path = f"Output/{baseName}.klee-out"
    if os.path.exists(klee_out_path):
        shutil.rmtree(klee_out_path)
    klee_cmd = klee_path.split() + [
        f'--output-dir={klee_out_path}',
        '--write-no-tests',
        exeFile,
    ]

    print(f"EXECUTING: {klee_cmd}")
    sys.stdout.flush()

    kleeOut = subprocess.check_output(klee_cmd).decode()
    print('-- klee output --\n%s--\n' % (kleeOut,))

    if lliOut != kleeOut:
        raise SystemExit('outputs differ')
        
def testOneFile(f, printOutput=False):
    try:
        testFile(f, printOutput)
        code = ['pass','xpass'][f.startswith('broken')]
        extra = ''
    except TestError as e:
        code = ['fail','xfail'][f.startswith('broken')]
        extra = str(e)

    print(f'{code}: {f} -- {extra}')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('test_path', help='test path')

    parser.add_argument('--klee', dest='klee_path',
                        help="path to the klee binary",
                        required=True)
    parser.add_argument('--lli', dest='lli_path',
                        help="path to the lli binary",
                        required=True)

    opts = parser.parse_args()

    test_name = os.path.basename(opts.test_path)
    testFile(test_name, opts.klee_path, opts.lli_path)

if __name__=='__main__':
    main()
