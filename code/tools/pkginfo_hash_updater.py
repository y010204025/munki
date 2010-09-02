#!/usr/bin/python
#
# Copyright 2010 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Updates all pkginfo plists '(un)installer_item_hash' key.

This script will recursively update the '(un)installer_item_hash' key in all
pkginfo plists in the pkgsinfo directory of a Munki repo with a SHA-256 hash of
the corresponding package.

This script will run from Mac OSX or Linux alike, and it is safe to run more
than once on any pkginfo plist(s).

Created on 2010-09-02.
"""

import optparse
import os
import hashlib
import plistlib


MUNKI_ROOT_PATH = '/var/www/munki/repo'
MUNKI_PKGS_DIR_NAME = 'pkgs'
MUNKI_PKGSINFO_DIR_NAME = 'pkgsinfo'


def GetHash(filename, hash_function):
  """Calculates the hashvalue of the given file with the given hash_function.

  Args:
    filename: The file name to calculate the hash value of.
    hash_function: The hash function object to use, which was instanciated
        before calling this function, e.g. hashlib.md5().

  Returns:
    The hashvalue of the given file as hex string.
  """
  if not os.path.isfile(filename):
    return None

  f = open(filename, 'rb')
  while 1:
    chunk = f.read(2**16)
    if not chunk:
      break
    hash_function.update(chunk)
  f.close()
  return hash_function.hexdigest()


def GetSHA256Hash(filename):
  """Returns the SHA-256 hash value of a file as a hex string."""
  hash_function = hashlib.sha256()
  return GetHash(filename, hash_function)


def AddHashesToPkginfoPlists(pkgsinfo_path, pkgs_path):
  """Recursively updates plists' '(un)installer_item_hash' kay with pkg hash.

  Args:
    pkgsinfo_path: root dir to start updating from.
    pkgs_path: root dir where Munki pkgs live.
  """
  for f_path in os.listdir(pkgsinfo_path):
    f_path = os.path.join(pkgsinfo_path, f_path)
    # if a directory is found, recursively call this function on that dir.
    if os.path.isdir(f_path):
      AddHashesToPkginfoPlists(f_path, pkgs_path)
    elif os.path.islink(f_path):
      print 'WARNING: symlinks not supported; skipping: %s' % f_path
      continue
    elif os.path.isfile(f_path):
      # read plist
      try:
        plist = plistlib.readPlist(f_path)
      except IOError, e:
        print 'WARNING: pkginfo plist failed to open: %s\n%s' % (f_path, str(e))
        continue
      # generate the package path from the pkginfo plist intaller_item_location.
      pkg_path = os.path.join(pkgs_path, plist['installer_item_location'])
      # display warning for packages that cannot be found.
      if not os.path.isfile(pkg_path):
        print 'WARNING: Package (%s) not found as specified in %s' % (
            pkg_path, f_path)
        continue
      # generate the package hash, update plist dict, and write the plist file.
      pkg_hash = GetSHA256Hash(pkg_path)
      # Update plist dict based on if it's a install or uninstall pkginfo.
      if 'installer_item_size' in plist:
        plist['installer_item_hash'] = pkg_hash
      elif 'uninstaller_item_size' in plist:
        plist['uninstaller_item_hash'] = pkg_hash
      else:
        print 'WARNING: pkginfo plist type is not known: %s' % f_path
        continue
      plistlib.writePlist(plist, f_path)
      print '- Wrote hash to plist: %s' % f_path


def main():
  usage = 'usage: %prog [options]'
  p = optparse.OptionParser(usage=usage)
  p.add_option('-r', '--munki_root', default=MUNKI_ROOT_PATH,
               help='Munki repo root path where pkginfo and pkgs dirs live; '
               'default "/var/www/munki/repo"')
  p.add_option('-p', '--pkgsinfo_dir_name', default=MUNKI_PKGSINFO_DIR_NAME,
               help='Munki pkgsinfo dir name; default "pkgsinfo".')
  p.add_option('-f', '--pkgs_dir_name', default=MUNKI_PKGS_DIR_NAME,
               help='Munki packages dir name; default "pkgs".')
  options, unused_arguments = p.parse_args()

  pkgsinfo_path = os.path.join(options.munki_root, options.pkgsinfo_dir_name)
  pkgs_path = os.path.join(options.munki_root, options.pkgs_dir_name)
  if not os.path.isdir(pkgsinfo_path) or not os.listdir(pkgsinfo_path):
    print 'Pkgsinfo directory not found or is empty: %s' % pkgsinfo_path
  elif not os.path.isdir(pkgs_path) or not os.listdir(pkgs_path):
    print 'Pkgs directory not found or is empty: %s' % pkgs_path
  else:
    AddHashesToPkginfoPlists(pkgsinfo_path, pkgs_path)
    print '\nYou must run makecatalogs to update catalogs with pkginfo changes.'


if __name__ == '__main__':
  main()