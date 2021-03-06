from .data_parser import DataParser
from .pheno_covar import PhenoCovar
from .boundary import BoundaryCheck
from .parsed_locus import ParsedLocus
from .exceptions import TooManyAlleles
from .exceptions import TooFewAlleles
import gzip
import numpy
import os
import tabix
from . import sys_call
from . import ExitIf

from . import Exit
from . import BuildReportLine
from . import GenotypeData as GenotypeData
import sys
import logging

import faulthandler

from contextlib import contextmanager
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

# We'll assume count of minor alleles

class BasicFile(object):
    def __enter__(self, filename, compressed):
        self.filename = filename
        self.compressed = compressed

        if self.compressed:
            self._file = gzip.open(self.filename, 'rt')
        else:
            self._file = open(self.filename)

    def __iter__(self):
        for line in self._file:
            yield line.strip().split()
            
    def __del__(self):
        self._file.close()

def OpenFile(filename, compressed):
    if compressed:
        file = gzip.open(filename, 'rt')
    else:
        file = open(filename)

    return file


class GenotypeExtraction(object):
    """Basic class for Parser functor. This assumes a single value as the 
        data found at the key. For more complex values, such as probabilities,
        a different functor should be used."""
    def __init__(self, genokey='GT', missing=None):
        global genotype_values
        self.genokey = genokey
        if missing is None:
            missing = DataParser.missing_storage

        self.missing = int(missing)

        # Let the missing representation map to the missing notation
        GenotypeData.conversion['./.'] = self.missing
        GenotypeData.conversion[self.missing] = self.missing

    def __call__(self, locus, format):
        """We assume locus has been split and is an array with no return character at end"""
        global genotype_values
        try:
            if self.genokey not in format:
                faulthandler.dump_traceback(all_threads=True)
            data_index = format.index(self.genokey)
        except:
            Exit(f"Unable to find data key, {self.genokey}, in  format list: {format}")
        genotypes = GenotypeData()
        for genotype in locus[9:]:
            genotype = genotype.split(":")
            if len(genotype) > data_index:
                genotypes.append(genotype[data_index])
            else:
                genotypes.append(self.missing)
        return genotypes


class Parser(DataParser):
    """Parse VCF data 

    Class Members:
        filename
        indexed     (only true if it is gzipped with tabix index)
        sample_ids  IDs associated with the usable data
        data_field  GT/DS or whatever the data we are expected to extract
        compressed  T/F indicating gzip file (determined by filename)
        vcf_file    This is the iterable "file" that we'll be using. In some cases, 
                    it may be a tabix object, in others, it may be a plain gzip 
                    file or even a plain python file object.
    """

    #: min Quality filter
    min_qual        = 17

    #: When false, pedigree header expects no parents columns
    has_parents     = True

    # The app can overwrite this set or add values to it if there is interest
    # in permitting different filter values. We will simply check for an exact
    # match to one of the items in this set of values. So, if there are multiple
    # values, currently, this won't pass if more than one are present and all
    # occur within the pass_filters set
    pass_filters = set([".", "PASS"])

    # Default will be GT with -9 for
    ExtractGenotypes = GenotypeExtraction()

    def __init__(self, filename, data_field='GT'):
        self.vcf_filename = filename
        self.data_field = data_field
        self.ind_mask = None            # mask associated with complete set of subjects
        self.ind_count = -1

        self.indexed = False
        self.compressed = False
        if filename.split(".")[-1] == "gz":
            self.compressed = True
            if BoundaryCheck.chrom != -1 and os.path.isfile("%s.tbi" % (filename)):
                self.indexed = True

        #: Subjects dropped due to missing individual threshold
        self.alt_not_missing = None

        self.vcf_file = None
        self.reset()
    
    def __del__(self):
        if self.vcf_file is not None:
            self.vcf_file.close()

    def initialize(self, map3=None, pheno_covar=None):
        self.init_subjects(pheno_covar)
        self.load_genotypes()

    def getnew(self):
        return Parser(self.vcf_filename, self.data_field)

    def ReportConfiguration(self):
        log = logging.getLogger('bed_parser::ReportConfiguration')
        log.info(BuildReportLine("VCF FILE", self.vcf_filename))
        log.info(BuildReportLine("DATA FIELD", self.data_field))

    def init_subjects(self, pheno_covar):
        sample_ids = []
        format = []

        with OpenFile(self.vcf_filename, self.compressed) as file:
            for line in file:
                if line[0:6] == "#CHROM":
                    line = line.strip().split()
                    sample_ids = line[9:]
                    break

        mask_components = []
        for id in sample_ids:
            # Validate subjects by inclusion/exclusion criterion
            if DataParser.valid_indid(id):
                mask_components.append(0)
                pheno_covar.add_subject(id, phenotype=pheno_covar.missing_encoding)
            else:
                mask_components.append(1)

        self.ind_mask = numpy.array(mask_components) == 1
        self.ind_count = self.ind_mask.shape[0]
        pheno_covar.freeze_subjects()


        #ExitIf(len(format) < 1, "Unable to find valid FORMATs in the file, ", self.vcf_filename)

        #ExitIf(self.data_field not in format, "Unable to find %s in the FORMAT columns
            
    def reset(self, skip_all_headers=True):
        """skip_all_headers will skip all of the headers, including the sample header row. 

        This only relates to non-tabix based files"""
        if self.vcf_file is not None:
            self.vcf_file.close()
        if self.indexed and len(DataParser.boundary.bounds) > 0:
            self.tabix_file = tabix.open(self.vcf_filename)

            self.vcf_file = tabix.query(str(BoundaryCheck.chrom),
                    DataParser.boundary.bounds[0],
                    DataParser.boundary.bounds[1])
        else:
            self.vcf_file = OpenFile(self.vcf_filename, self.compressed)

            if skip_all_headers:
                for line in self.vcf_file:
                    if line[0:2] == "#C":
                        break

    def load_family_details(self, pheno_covar):
        """Load contents from the .fam file, updating the pheno_covar with \
            family ids found.

        :param pheno_covar: Phenotype/covariate object
        :return: None
        """
        self.file_index = 0
        # 1s indicate an individual is to be masked out
        mask_components = []

        if self.vcf_file is not None:
            self.vcf_file.close()
        file = OpenFile(self.vcf_filename, DataParser.compressed_pedigree)
        sample_ids = None

        while sample_ids is None:
            line = file.readline().split()
            if line[0] == "#CHROM":
                sample_ids = line[9:]

        ids_observed = set()
        for indid in sample_ids:

            # This is a side effect of transforming binary pedigree into
            # VCF using plink2. Not sure if this should be a part of the
            # program or if it could mess up legitimate IDs
            indid = indid.replace("_", ":")
            ExitIf("Duplicate ID found in dose file: %s" % (indid), indid in ids_observed)
            ids_observed.add(indid)

            if DataParser.valid_indid(indid):
                mask_components.append(0)
                pheno_covar.add_subject(indid, PhenoCovar.missing_encoding, PhenoCovar.missing_encoding)
            else:
                mask_components.append(1)

        self.ind_mask = numpy.array(mask_components) == 1
        self.ind_count = self.ind_mask.shape[0]
        pheno_covar.freeze_subjects()

    def load_genotypes(self):
        self.reset()
        missing = None
        locus_count = 0
        total_locus_count = 0

        for locus in self.vcf_file:
            locus = locus.strip().split()
            chr, pos, rsid, ref, alt, qual, filter, info, format = locus[0:9]
                
            format = format.split(":")
            chr = int(chr)
            pos = int(pos)
            if DataParser.boundary.TestBoundary(chr, pos,rsid):
                locus_count += 1
                data = Parser.ExtractGenotypes(locus, format)
                allelic_data = numpy.array(data.gt())

                if missing is None:
                    missing = numpy.zeros(allelic_data.shape[0], dtype='int8')
                missing += ((allelic_data==DataParser.missing_storage))
            total_locus_count += 1
        max_missing = DataParser.ind_miss_tol * locus_count
        
        if missing is None:
            missing = numpy.array([1] * locus_count)
        dropped_individuals = 0+(max_missing<missing)

        if sum(dropped_individuals) > 0:
            # This will be ORd, so it needs to be one for not
            self.alt_not_missing = dropped_individuals != 1
            self.alt_not_missing = self.alt_not_missing[self.ind_mask != 1]

        self.locus_count = locus_count
        self.reset()
    def populate_iteration(self, iteration):
        cur_idx = iteration.cur_idx

        locus = next(self.vcf_file).strip().split()

        iteration.chr, \
            iteration.pos, \
            iteration.rsid, \
            iteration.ref, \
            iteration.alt, \
            qual, \
            filter, \
            info, \
            format = locus[0:9]

        iteration.chr = int(iteration.chr)
        iteration.pos = int(iteration.pos)
        alleles = [iteration.ref, iteration.alt]
        if DataParser.boundary.TestBoundary(iteration.chr, iteration.pos, iteration.rsid):
            # Consider qual and filter as well
            if (qual=='.' or qual > Parser.min_qual) and filter in Parser.pass_filters:
                geno = Parser.ExtractGenotypes(locus, format.split(":"))
                iteration.genotype_data = numpy.ma.MaskedArray(geno.genotypes,
                                    self.ind_mask).compressed()
                allele_counts = [geno.ref_counts, geno.alt_counts]
                iteration.hetero_counts = geno.het_counts
                iteration.missing_allele_count = geno.missing
                iteration.allele_count2 = allele_counts[1]
                iteration.missing_genotypes = iteration.genotype_data == DataParser.missing_storage
                iteration.effa_freq = geno.maf()
                if allele_counts[0] < allele_counts[1]:
                    allele_counts = [allele_counts[1], allele_counts[0]]
                    alleles = [alleles[1], alleles[0]]
                iteration.major_allele = alleles[0]
                iteration.minor_allele = alleles[1]
                iteration.maj_allele_count = allele_counts[0]
                iteration.min_allele_count = allele_counts[1]
                iteration._maf = geno.maf()

                return iteration.maf >= DataParser.min_maf and iteration.maf <= DataParser.max_maf
            else:
                print("%s:%s %s - Filter: %s" % (iteration.chr,
                                                                      iteration.pos,
                                                                      iteration.rsid,
                                                                      filter), file=sys.stderr)
                return False
        return False


    def get_effa_freq(self, genotypes):
        return numpy.sum(numpy.array(genotypes))/float(len(genotypes))












