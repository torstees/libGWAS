from .data_parser import DataParser
from .parsed_locus import ParsedLocus
from .exceptions import TooManyAlleles
from .exceptions import TooFewAlleles
import gzip
import numpy
from .pheno_covar import PhenoCovar
import logging

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

class Parser(DataParser):
    """Parse transposed pedigree dataset

    Class Members:
    tfam_file       filename associated with the pedigree information
    tped_file       Filename associated with the genotype data
    families        Pedigree information for reporting
    genotype_file   Actual pedigree file begin parsed (file object)


    """
    def __init__(self, tfam, tped):
        self.tfam_file = tfam
        self.tped_file = tped
        self.families = []
        self.genotype_file = None
        self.alleles = []
        self.ind_count = -1

        #: Name used for reporting information about this dataset
        self.name = tped.split("/")[-1].split(".")[0]

        self.parser_name = self.name

        #: Subjects dropped by user or don't match phenotype/covariate id list
        self.ind_mask = None

        #: Subjects dropped due to missing individual threshold
        self.alt_not_missing = None

        #: Count of valid loci without filtering on missingness other than explicit drops
        self.locus_count = -1

    def initialize(self, map3=None, pheno_covar=None):
        # Required for some parser types

        self.load_tfam(pheno_covar)
        self.load_genotypes()

    def getnew(self):
        return Parser(self.tfam_file, self.tped_file)


    def ReportConfiguration(self):
        log = logging.getLogger('tped_parser::ReportConfiguration')
        log.info(BuildReportLine("TPED_FILE", self.tped_file))
        log.info(BuildReportLine("TFAM FILE", self.tfam_file))

    def load_tfam(self, pheno_covar):
        """Load the pedigree portion of the data and sort out exclusions"""

        pheno_col = 5
        if not DataParser.has_sex:
            pheno_col -= 1
        if not DataParser.has_parents:
            pheno_col -= 2
        if not DataParser.has_fid:
            pheno_col -= 1

        sex_col = pheno_col - 1
        mask_components = []
        with open(self.tfam_file) as f:
            for line in f:
                words = line.strip().split()
                if len(words) > 1:
                    indid = PhenoCovar.build_id(words)
                    if DataParser.valid_indid(indid):
                        mask_components.append(0)

                        sex = None
                        pheno = None
                        if DataParser.has_sex:
                            sex = int(words[sex_col])
                        if DataParser.has_pheno:
                            pheno = float(words[pheno_col])
                        if pheno_covar is not None:
                            pheno_covar.add_subject(indid, sex, pheno)
                        if len(words) > 0:
                            self.families.append(words)
                    else:
                        mask_components.append(1)
        mask_components = numpy.array(mask_components)
        self.ind_mask = numpy.zeros(len(mask_components) * 2, dtype=numpy.int8).reshape(-1, 2)
        self.ind_mask[0:, 0] = mask_components
        self.ind_mask[0:, 1] = mask_components
        self.ind_count = self.ind_mask.shape[0]

        if pheno_covar is not None:
            pheno_covar.freeze_subjects()
        self.load_genotypes()


    def __del__(self):
        if self.genotype_file is not None:
            self.genotype_file.close()

    def load_genotypes(self):
        """This really just intializes the file by opening it up. """

        if self.genotype_file is not None:
            self.genotype_file.close()
        if DataParser.compressed_pedigree:
            self.genotype_file = gzip.open("%s.gz" % self.tped_file, 'rt')
        else:
            self.genotype_file = open(self.tped_file)

        self.filter_missing()

    def process_genotypes(self, data):
        """Parse pedigree line and remove excluded individuals from geno

        Translates alleles into numerical genotypes (0, 1, 2) counting
        number of minor alleles.

        Throws exceptions if an there are not 2 distinct alleles


        """
        # Get a list of uniq entries in the data, except for missing
        alleles = list(set(data[4:]) - set([DataParser.missing_representation]))
        if len(alleles) > 2:
            print(alleles)
            print(data[4:])
            print(DataParser.missing_representation)
            print((set(data[4:]) - set(['0'])))
            raise TooManyAlleles(chr=self.chr, rsid=self.rsid, alleles=alleles)

        # We don't have a way to know this in advance, so we want to just iterate onward
        # if we encounter one of these
        if len(alleles) == 1:
            raise TooFewAlleles(chr=self.chr, rsid=self.rsid, alleles=alleles)

        # Strip out any excluded individuals
        allelic_data = numpy.ma.MaskedArray(numpy.array(data[4:], dtype=str), self.ind_mask).compressed().reshape(-1, 2)

        maj_allele_count = numpy.sum(allelic_data == alleles[0])

        min_allele_count = numpy.sum(allelic_data == alleles[1])

        effect_allele_count = min_allele_count
        if min_allele_count > maj_allele_count:
            alleles = [alleles[1], alleles[0]]
            allele_count = maj_allele_count
            maj_allele_count = min_allele_count
            min_allele_count = allele_count

        #genotypes = []
        major_allele = alleles[0]
        minor_allele = alleles[1]

        # Genotypes represent the sum of minor alleles at each sample
        genotype_data = numpy.sum(allelic_data == minor_allele, axis=1)
        missing_alleles = allelic_data[:, 0] == DataParser.missing_representation
        genotype_data[missing_alleles] = DataParser.missing_storage
        hetero_count = numpy.sum(genotype_data == 1)

        return (genotype_data,
                major_allele,
                minor_allele,
                hetero_count,
                maj_allele_count,
                min_allele_count,
                missing_alleles,
                effect_allele_count)

    def filter_missing(self):
        """Filter out individuals and SNPs that have too many missing to be considered"""

        missing = None
        locus_count = 0

        # Filter out individuals according to missingness
        self.genotype_file.seek(0)
        for genotypes in self.genotype_file:
            genotypes = genotypes.split()
            chr, rsid, junk, pos = genotypes[0:4]
            chr = int(chr)
            pos = int(pos)
            if DataParser.boundary.TestBoundary(chr, pos, rsid):
                locus_count += 1
                allelic_data = numpy.array(genotypes[4:], dtype=str).reshape(-1, 2)
                if missing is None:
                    missing = numpy.zeros(allelic_data.shape[0], dtype='int8')
                missing += (numpy.sum(0+(allelic_data==DataParser.missing_representation), axis=1) * 0.5).astype(int)


        if missing is not None:
            max_missing = DataParser.ind_miss_tol * locus_count
            dropped_individuals = 0+(max_missing<missing)

            if sum(dropped_individuals) > 0:
                # This will be ORd, so it needs to be one for not
                self.alt_not_missing = dropped_individuals != 1
                self.alt_not_missing = self.alt_not_missing[self.ind_mask[0:, 0] != 1]
        self.locus_count = locus_count


    def populate_iteration(self, iteration):
        """Pour the current data into the iteration object"""

        cur_idx = iteration.cur_idx
        
        # Let's go ahead and set those alleles as bytes, but
        # we'll need to fix the rest
        genotypes = next(self.genotype_file).split()
        iteration.chr, iteration.rsid, junk, iteration.pos = genotypes[0:4]
        iteration.chr = int(iteration.chr)
        iteration.pos = int(iteration.pos)

        if DataParser.boundary.TestBoundary(iteration.chr, iteration.pos, iteration.rsid):
            try:
                [iteration.genotype_data,
                    iteration.major_allele,
                    iteration.minor_allele,
                    iteration.hetero_count,
                    iteration.maj_allele_count,
                    iteration.min_allele_count,
                    iteration.missing_genotypes,
                    iteration.allele_count2] = self.process_genotypes(genotypes)
                iteration.missing_allele_count = numpy.sum(iteration.missing_genotypes)
                return True
                #return iteration.maf >= DataParser.min_maf and iteration.maf <= DataParser.max_maf
            except TooFewAlleles:
                print("\n\n\nSkipping %s:%s %s %s" % (iteration.chr, iteration.pos, iteration.rsid, cur_idx))

        return False



    def __iter__(self):
        """Reset the file and begin iteration"""

        self.genotype_file.seek(0)
        # Make sure this didn't get tripped and remain wrongfully telling us we are finished
        DataParser.boundary.beyond_upper_bound = False
        return ParsedLocus(self)
