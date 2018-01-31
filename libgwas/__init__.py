
__author__ = 'Eric Torstenson'
__version__ = '1.0.2'

import subprocess
import sys
import exceptions

__copyright__ = "Eric Torstenson"
__license__ = "GPL3.0"
#     This file is part of libGWAS.
#
#     libGWAS is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     libGWAS is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with MVtest.  If not, see <http://www.gnu.org/licenses/>.

"""GWAS Library (libGWAS) - Genome Wide Association Library for Python

This library contains all of the classes required to parse standard and
transposed pedigree data using most of PLINK style enhancements (such as
tolerating bases and missing/additional columns). In addition to standard
text pedigrees, there is also support for bed files.

Copyright (C) 2015 Edwards, Li & Torstenson

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""


class GenotypeData(object):
    """Simple data structure to help build vectors of genotypes and then determine
       which allele is minor/major, effect, etc. """
    conversion = {
        "0/0": 0,
        "0/1": 1,
        "1/0": 1,
        "1/1": 2
    }
    def __init__(self):
        self.genotypes = []
        self.ref_counts = 0
        self.alt_counts = 0
        self.het_counts = 0
        self.missing = 0

    def append(self, gt):
        gt = GenotypeData.conversion[gt]
        if gt >= 0:
            self.ref_counts = 2-gt
            self.alt_counts = gt
            if gt == 1:
                self.het_counts += 1
        else:
            self.missing += 2
        self.genotypes.append(gt)

    def maf(self):
        if self.alt_counts > self.ref_counts:
            return self.ref_counts / (self.alt_counts + self.ref_counts)
        return self.alt_counts / (self.alt_counts + self.ref_counts)

    def freq1(self):
        return self.ref_counts / (self.ref_counts + self.alt_counts)

    def freq2(self):
        return self.alt_counts / (self.ref_counts + self.alt_counts)



def sys_call(cmd):
    """Execute cmd and capture stdout and stderr

    :param cmd: command to be executed
    :return: (stdout, stderr)
    """
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    return p.stdout.readlines(), p.stderr.readlines()


def Exit(msg, code=1):
    """Exit execution with return code and message
    :param msg: Message displayed prior to exit
    :param code: code returned upon exiting
    """
    print >> sys.stderr, msg
    sys.exit(code)

def ExitIf(msg, do_exit, code=1):
    """Exit if do_exit is true

    :param msg: Message displayed prior to exit
    :param do_exit: exit when true
    :param code: application's return code upon exit
    """
    if do_exit:
        Exit(msg, code)

def BuildReportLine(key, value, offset=None):
    """Prepare key/value for reporting in configuration report

    :param key: configuration 'keyword'
    :param value: value reported to be associated with keyword

    :return: formatted line starting with a comment
    """
    reportline = "# " + key.ljust(20) + " : "

    if offset is None:
        return reportline + str(value)

    try:
        try:
            v=int(value)
            return reportline + "%*s" % (offset, str(value))
        except:
            pass
        v = float(value)
        return reportline + "%*s" % (offset - 1 + len(str(value)), str(value))
    except:
        return reportline + "%*s" % (offset - 1 + len(value), value)