from .locus import Locus
from . import allele_counts
from .exceptions import InvalidFrequency
from .exceptions import TooMuchMissing
from . import data_parser

__copyright__ = "Todd Edwards, Chun Li & Eric Torstenson"
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


# Extract genotypes from raw genotypes (considering missing @ phenotype)
# Convert genotypes to analyzable form if there is any need
def default_geno_extraction(alleles, rawgeno, non_missing):
    genotypes = rawgeno[non_missing]

    het = sum(genotypes == 1)
    a1c = (2 * sum(genotypes==0)) + het
    a2c = (2 * sum(genotypes==2)) + het

    alc = allele_counts.AlleleCounts(genotypes, alleles, non_missing)
    alc.set_allele_counts(a1c, a2c, het)
    return alc



class ParsedLocus(Locus):
    """Locus data representing current iteration from a dataset

    Provide an iterator interface for all dataset types.

    """

    def __init__(self, datasource, index=-1):
        """Basic initialization (nothing is currently valid)"""

        super(ParsedLocus, self).__init__()
        #: Reference back to the parser that generated this object
        self.__datasource       = datasource
        #: Index within the list of loci being analyzed
        self.cur_idx            = index
        #: Actual genotype data for this locus
        self.genotype_data      = None
        #: Genotypes missing at locus as well as individuals marked to be ignored
        self.missing_genotypes = None       # True for 1 locus only

        #: Used to filter the filtered individuals out at extraction
        self.ind_mask =None

        self._extract_genotypes = default_geno_extraction

    def get_genotype_data(self, non_missing):
        """Return genotypes filtered by the missing phenotypes encapsulated in an AlleleCounts object"""
        not_missing = ~self.missing_genotypes & non_missing
        if self.__datasource.alt_not_missing is not None:
            not_missing = not_missing & self.__datasource.alt_not_missing

        alc = self._extract_genotypes(self.alleles, self.genotype_data, not_missing)
        if alc.freq_missing > data_parser.DataParser.snp_miss_tol:
            raise TooMuchMissing(chr=self.chr,
                                 pos=self.pos,
                                 rsid=self.rsid,
                                 maf=alc.maf,
                                 miss=alc.freq_missing)
        if alc.maf < data_parser.DataParser.min_maf or alc.maf > data_parser.DataParser.max_maf:
            raise InvalidFrequency(chr=self.chr,
                                   pos=self.pos,
                                   rsid=self.rsid,
                                   maf=alc.maf,
                                   almin=alc.minor_allele,
                                   almaj=alc.major_allele,
                                   a2c=alc.a2_count)

        return alc

    def __next__(self):
        """Move to the next valid locus.

        Will only return valid loci or exit via StopIteration exception

        """
        while True and not data_parser.DataParser.boundary.beyond_upper_bound:
            self.cur_idx += 1
            if self.__datasource.populate_iteration(self):
                return self

        raise StopIteration

    def filter_on_y(self, y_missing):
        locus = FilteredLocus()
        locus.filter(y_missing)

        return locus

    def __iter__(self):
        """Basic iterator functionality. """

        return self
