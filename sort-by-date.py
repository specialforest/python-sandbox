'''
The MIT License (MIT)

Copyright (c) 2014 specialforest

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

import argparse
import os
import os.path
import shutil
import sys
import time
import fnmatch


class GlobFilter:

  def __init__(self, includes, excludes):
    if includes and len(includes) > 0:
      self._includes = includes
    else:
      self._includes = None

    if excludes and len(excludes) > 0:
      self._excludes = excludes
    else:
      self._excludes = None

  def match(self, fileName):
    if self._excludes:
      for pattern in self._excludes:
        if fnmatch.fnmatch(fileName, pattern):
          return False

    if self._includes:
      for pattern in self._includes:
        if fnmatch.fnmatch(fileName, pattern):
          return True
      return False

    return True



def sort_by_date(sources, dest, filter, dryRun):

  dest = os.path.abspath(dest)

  dirs = set()
  for path in sources:
    if not os.path.isdir(path):
      print('"{0}" does not exist or is not a directory'.format(path))
      continue

    for dirPath, dirNames, fileNames in os.walk(path):
      for fileName in fileNames:
        if not filter.match(fileName): continue
        sourceFile = os.path.abspath(os.path.join(dirPath, fileName))
        stats = os.stat(sourceFile)
        dirName = time.strftime("%Y-%m-%d", time.localtime(stats.st_mtime))
        targetDir = os.path.join(dest, dirName)
        if dirName not in dirs:
          dirs.add(dirName)
          if not os.path.exists(targetDir):
            os.mkdir(targetDir)

        targetFile = os.path.join(targetDir, fileName)
        if sourceFile != targetFile:
          print('Moving "{0}" to "{1}"'.format(sourceFile, targetFile))
          if not dryRun:
            shutil.move(sourceFile, targetFile)
          


def main():
  parser = argparse.ArgumentParser(description='Sorts files into folders by modification date.')
  parser.add_argument('-i', '--include', action='append')
  parser.add_argument('-e', '--exclude', action='append')
  parser.add_argument('-d', '--destination', default='')
  parser.add_argument('--dry-run', action='store_true')
  parser.add_argument('source', nargs='*')
  if len(sys.argv) <= 1:
    parser.print_help()
    return

  args = parser.parse_args()
  sort_by_date(args.source, args.destination, GlobFilter(args.include, args.exclude), args.dry_run)


if __name__ == '__main__':
  main()
