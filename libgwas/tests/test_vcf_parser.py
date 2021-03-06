#!/usr/bin/env python
import sys

if "DEBUG" in sys.argv:
    sys.path.insert(0, "../../")
    sys.path.insert(0, "../")
    sys.path.insert(0, ".")
    sys.argv.remove("DEBUG")

import unittest
import os
from libgwas.data_parser import DataParser
from libgwas.pheno_covar import PhenoCovar
from libgwas.pheno_covar import PhenoIdFormat
from libgwas.vcf_parser import Parser
from libgwas.boundary import BoundaryCheck
from libgwas.snp_boundary_check import SnpBoundaryCheck
from pkg_resources import resource_filename
from libgwas.exceptions import InvalidFrequency
from libgwas.exceptions import TooMuchMissing
from libgwas.exceptions import TooMuchMissingpPhenoCovar
import numpy
from libgwas.tests import remove_file

class TestBase(unittest.TestCase):
    def setUp(self):
        self.nonmissing = resource_filename("libgwas", "tests/bedfiles/nomiss.vcf")
        self.nonmissinggz = resource_filename("libgwas", "tests/bedfiles/nomiss.vcf.gz")
        self.genotypes = [
            [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
            [1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1],
            [0, 2, 1, 1, 0, 0, 0, 2, 1, 1, 0, 0],
            [0, 1, 2, 1, 1, 0, 0, 1, 2, 1, 1, 0],
            [1, 2, 0, 1, 0, 0, 1, 2, 0, 1, 0, 0],
            [1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            [0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0]
        ]
        self.missing = resource_filename("libgwas", "tests/bedfiles/miss.vcf")
        self.missinggz = resource_filename("libgwas", "tests/bedfiles/miss.vcf.gz")

        self.genotypes_w_missing = [
            [0, 1],
            [1,  1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1],
            [0, 1, 1, 0, 0, 0, 2, 1, 1, 0, 0],
            [0, 2, 1, 1, 0, 0, 1, 2, 1, 1, 0],
            [1, 0, 1, 0, 0, 1, 2, 0, 1, 0, 0],
            [1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0]
        ]

        self.nonmissing_mapdata = []
        with open(self.nonmissing) as f:
            for line in f:
                if line[0] != "#":
                    words = line.strip().split()
                    # CHR   Pos ID  REF ALT
                    self.nonmissing_mapdata.append(words[0:5])
        self.missing_mapdata = []
        
        with open(self.missing) as f:
            for line in f:
                if line[0] != "#":
                    words = line.strip().split()
                    # CHR   Pos ID  REF ALT
                    self.missing_mapdata.append(words[0:5])
        self.phenotypes     = [0.1, 0.4, 1.0, 0.5, 0.9, 1.0, 0.1, 0.4, 1.0, 0.5, 0.9, 1.0]
        self.sex            = [1,1,2,2,1,1,1,1,2,2,1,1]

        self.id_encoding    = PhenoCovar.id_encoding
        self.chrom          = BoundaryCheck.chrom
        self.boundary       = DataParser.boundary
        self.min_maf        = DataParser.min_maf
        self.max_maf        = DataParser.max_maf
        self.snp_miss_tol   = DataParser.snp_miss_tol
        self.ind_miss_tol   = DataParser.ind_miss_tol
        self.sex_as_covar = PhenoCovar.sex_as_covariate
        self.has_sex        = DataParser.has_sex
        self.has_pheno      = DataParser.has_pheno
        self.has_parents    = DataParser.has_parents
        self.has_fid        = DataParser.has_fid
        self.has_liability  = DataParser.has_liability

        # This will have to be set by the application, but in most cases
        # VCF files will be either IID or FID and we have to know which
        # to ensure our IDs match between Pheno/Covar and VCF samples
        PhenoCovar.id_encoding = PhenoIdFormat.IID
        DataParser.boundary = BoundaryCheck()

    def tearDown(self):
        PhenoCovar.sex_as_covariate = self.sex_as_covar
        BoundaryCheck.chrom  = self.chrom
        DataParser.boundary  = self.boundary
        DataParser.min_maf   = self.min_maf
        DataParser.max_maf   = self.max_maf
        DataParser.snp_miss_tol  = self.snp_miss_tol
        DataParser.ind_miss_tol  = self.ind_miss_tol
        DataParser.ind_exclusions = []
        DataParser.has_sex    = self.has_sex
        DataParser.has_pheno  = self.has_pheno
        DataParser.has_fid    = self.has_fid
        DataParser.has_liability = self.has_liability
        DataParser.has_parents = self.has_parents
        PhenoCovar.id_encoding = self.id_encoding

class TestVcfFiles(TestBase):
    def testNonmissingBasics(self):
        pc = PhenoCovar()
        parser = Parser(self.nonmissing, data_field='GT')
        parser.init_subjects(pc)
        parser.load_genotypes()

        self.assertEqual(0, len(pc.covariate_labels))
        #self.assertEqual(0, len(pc.phenotype_names))
        mapdata = self.nonmissing_mapdata

        index = 0
        for snp in parser:
            snp_filter = numpy.ones(snp.missing_genotypes.shape[0]) == 1
            try:
                genodata = snp.get_genotype_data(snp_filter)
                self.assertEqual(int(mapdata[index][0]), snp.chr)
                self.assertEqual(int(mapdata[index][1]), snp.pos)
                self.assertEqual(mapdata[index][2], snp.rsid)
                self.assertEqual(self.genotypes[index], list(genodata.genotypes))
            except TooMuchMissing as e:
                pass
            except InvalidFrequency as e:
                pass
            index += 1
        self.assertEqual(7, index)

    def testGzBasics(self):
        pc = PhenoCovar()
        parser = Parser(self.nonmissinggz, data_field='GT')
        parser.init_subjects(pc)
        parser.load_genotypes()

        self.assertEqual(0, len(pc.covariate_labels))
        #self.assertEqual(0, len(pc.phenotype_names))
        mapdata = self.nonmissing_mapdata

        index = 0
        for snp in parser:
            snp_filter = numpy.ones(snp.missing_genotypes.shape[0]) == 1
            try:
                genodata = snp.get_genotype_data(snp_filter)
                self.assertEqual(int(mapdata[index][0]), snp.chr)
                self.assertEqual(int(mapdata[index][1]), snp.pos)
                self.assertEqual(mapdata[index][2], snp.rsid)
                self.assertEqual(self.genotypes[index], list(genodata.genotypes))
            except TooMuchMissing as e:
                pass
            except InvalidFrequency as e:
                pass
            index += 1
        self.assertEqual(7, index)

    def testMissingBasics(self):
        DataParser.snp_miss_tol = 0.5
        DataParser.min_maf = 0.1
        pc = PhenoCovar()
        parser = Parser(self.missing, data_field='GT')
        parser.init_subjects(pc)
        parser.load_genotypes()

        self.assertEqual(0, len(pc.covariate_labels))
        #self.assertEqual(0, len(pc.phenotype_names))
        mapdata = self.missing_mapdata

        genotypes_w_missing = [
            [0, 1],
            [1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1],
            [0, 1, 1, 0, 0, 0, 2, 1, 1, 0, 0],
            [0, 2, 1, 1, 0, 0, 1, 2, 1, 1, 0],
            [1, 0, 1, 0, 0, 1, 2, 0, 1, 0, 0],
            [1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0]
        ]
        index = 0
        for snp in parser:
            snp_filter = numpy.ones(snp.missing_genotypes.shape[0]) == 1
            try:
                genodata = snp.get_genotype_data(snp_filter)
                self.assertEqual(int(mapdata[index][0]), snp.chr)
                self.assertEqual(int(mapdata[index][1]), snp.pos)
                self.assertEqual(mapdata[index][2], snp.rsid)
                self.assertEqual(genotypes_w_missing[index], list(genodata.genotypes))
            except TooMuchMissing as e:
                pass
            except InvalidFrequency as e:
                pass
            index += 1
        self.assertEqual(7, index)

    def testMissingMxIndComplete(self):
        pc = PhenoCovar()
        DataParser.ind_miss_tol = 0.5       # We should only lose 1
        parser = Parser(self.missing, data_field='GT')
        parser.init_subjects(pc)
        parser.load_genotypes()

        mapdata = self.missing_mapdata
        genotypes_w_missing = [
            [0, 1],
            [1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1],
            [0, 1, 1, 0, 0, 0, 2, 1, 1, 0, 0],
            [0, 2, 1, 1, 0, 0, 1, 2, 1, 1, 0],
            [1, 0, 1, 0, 0, 1, 2, 0, 1, 0, 0],
            [1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0]
        ]
        index = 0
        valid = 0
        missing = 0
        freq = 0
        for snp in parser:
            snp_filter = numpy.ones(snp.missing_genotypes.shape[0]) == 1
            try:
                genodata = snp.get_genotype_data(snp_filter)
                self.assertEqual(int(mapdata[index][0]), snp.chr)
                self.assertEqual(int(mapdata[index][1]), snp.pos)
                self.assertEqual(mapdata[index][2], snp.rsid)
                self.assertEqual(genotypes_w_missing[index], list(genodata.genotypes))
                valid += 1
            except TooMuchMissing as e:
                missing += 1
            except InvalidFrequency as e:
                freq += 1
            index += 1

        self.assertEqual(0, freq)
        self.assertEqual(0, missing)
        self.assertEqual(7, valid)

    def testMissingMxSnpComplete(self):
        pc = PhenoCovar()
        DataParser.snp_miss_tol = 0.5       # We should only lose 1
        parser = Parser(self.missing, data_field='GT')
        parser.init_subjects(pc)
        parser.load_genotypes()

        mapdata = self.missing_mapdata

        index = 0
        for snp in parser:
            snp_filter = numpy.ones(snp.missing_genotypes.shape[0]) == 1
            try:
                genodata = snp.get_genotype_data(snp_filter)
                self.assertEqual(int(mapdata[index][0]), snp.chr)
                self.assertEqual(int(mapdata[index][1]), snp.pos)
                self.assertEqual(mapdata[index][2], snp.rsid)
                self.assertEqual(self.genotypes_w_missing[index], list(genodata.genotypes))
            except TooMuchMissing as e:
                pass
            except InvalidFrequency as e:
                pass
            index += 1
        self.assertEqual(7, index)

    # Test to make sure we can load everything
    def testMissingMxBothComplete(self):
        pc = PhenoCovar()
        DataParser.snp_miss_tol = 0.5       # We should only lose 1
        DataParser.ind_miss_tol = 0.5       # We should only lose 1
        parser = Parser(self.missing, data_field='GT')
        parser.init_subjects(pc)
        parser.load_genotypes()
        genotypes_w_missing = [
            [0, 1],
            [1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1],
            [0, 1, 1, 0, 0, 0, 2, 1, 1, 0, 0],
            [0, 2, 1, 1, 0, 0, 1, 2, 1, 1, 0],
            [1, 0, 1, 0, 0, 1, 2, 0, 1, 0, 0],
            [1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0]
        ]
        mapdata = self.missing_mapdata

        index = 0

        for snp in parser:
            snp_filter = numpy.ones(snp.missing_genotypes.shape[0]) == 1
            try:
                genodata = snp.get_genotype_data(snp_filter)
                self.assertEqual(int(mapdata[index][0]), snp.chr)
                self.assertEqual(int(mapdata[index][1]), snp.pos)
                self.assertEqual(mapdata[index][2], snp.rsid)
                self.assertEqual(genotypes_w_missing[index], list(genodata.genotypes))
            except TooMuchMissing as e:
                pass
            except InvalidFrequency as e:
                pass
            index += 1
        self.assertEqual(7, index)

    def testBoundary(self):
        pc = PhenoCovar()
        DataParser.boundary = BoundaryCheck()
        BoundaryCheck.chrom = 2
        parser = Parser(self.nonmissing, data_field='GT')
        parser.init_subjects(pc)
        parser.load_genotypes()

        index = 4
        for snp in parser:
            snp_filter = numpy.ones(snp.missing_genotypes.shape[0]) == 1
            try:
                genodata = snp.get_genotype_data(snp_filter)
                self.assertEqual(int(self.nonmissing_mapdata[index][0]), snp.chr)
                self.assertEqual(int(self.nonmissing_mapdata[index][1]), snp.pos)
                self.assertEqual(self.nonmissing_mapdata[index][2], snp.rsid)
                self.assertEqual(self.genotypes[index], list(genodata.genotypes))
            except TooMuchMissing as e:
                pass
            except InvalidFrequency as e:
                pass
            index += 1
        self.assertEqual(7, index)

    def testSnpBoundaryBed(self):
        pc = PhenoCovar()
        DataParser.boundary = SnpBoundaryCheck(snps=["rs0001-rs0003"])
        BoundaryCheck.chrom = 1
        parser = Parser(self.nonmissing, data_field='GT')
        parser.init_subjects(pc)
        parser.load_genotypes()

        index = 0
        self.assertEqual(3, parser.locus_count)
        for snp in parser:
            snp_filter = numpy.ones(snp.missing_genotypes.shape[0]) == 1
            try:
                genodata = snp.get_genotype_data(snp_filter)
                self.assertEqual(int(self.nonmissing_mapdata[index][0]), snp.chr)
                self.assertEqual(int(self.nonmissing_mapdata[index][1]), snp.pos)
                self.assertEqual(self.nonmissing_mapdata[index][2], snp.rsid)
                self.assertEqual(self.genotypes[index], list(genodata.genotypes))
            except TooMuchMissing as e:
                pass
            except InvalidFrequency as e:
                pass
            index += 1
        self.assertEqual(3, index)

    def testSnpBoundary2StartMidway(self):
        pc = PhenoCovar()
        DataParser.boundary = SnpBoundaryCheck(snps=["rs0005-rs0006"])
        BoundaryCheck.chrom = 2
        parser = Parser(self.nonmissing, data_field='GT')
        parser.init_subjects(pc)
        parser.load_genotypes()

        index = 4
        self.assertEqual(2, parser.locus_count)
        for snp in parser:
            snp_filter = numpy.ones(snp.missing_genotypes.shape[0]) == 1
            try:
                genodata = snp.get_genotype_data(snp_filter)
                self.assertEqual(int(self.nonmissing_mapdata[index][0]), snp.chr)
                self.assertEqual(int(self.nonmissing_mapdata[index][1]), snp.pos)
                self.assertEqual(self.nonmissing_mapdata[index][2], snp.rsid)
                self.assertEqual(self.genotypes[index], list(genodata.genotypes))
            except TooMuchMissing as e:
                pass
            except InvalidFrequency as e:
                pass
            index += 1
        self.assertEqual(6, index)

    def testRegionBoundaryWithExclusions(self):
        pc = PhenoCovar()
        DataParser.boundary = SnpBoundaryCheck(snps=["rs0005-rs0007"])
        DataParser.boundary.LoadExclusions(snps=["rs0007"])
        BoundaryCheck.chrom = 2
        parser = Parser(self.nonmissing, data_field='GT')
        parser.init_subjects(pc)
        parser.load_genotypes()


        index = 4
        self.assertEqual(2, parser.locus_count)
        for snp in parser:
            for y in pc:
                snp_filter = numpy.ones(snp.missing_genotypes.shape[0]) == 1
                try:
                    genodata = snp.get_genotype_data(snp_filter)
                    self.assertEqual(int(self.nonmissing_mapdata[index][0]), snp.chr)
                    self.assertEqual(int(self.nonmissing_mapdata[index][1]), snp.pos)
                    self.assertEqual(self.nonmissing_mapdata[index][2], snp.rsid)
                    self.assertEqual(self.genotypes[index], list(genodata.genotypes))
                except TooMuchMissing as e:
                    pass
                except InvalidFrequency as e:
                    pass
                index += 1
        self.assertEqual(6, index)

    def testMissingWithExclusions(self):
        DataParser.ind_exclusions = ["2", "3"]

        genotypes_w_missing = [
            [0, 1],
            [1, 0, 0, 1, 1, 1, 0, 0, 0, 1],
            [0, 1, 0, 0, 0, 2, 1, 1, 0, 0],
            [0, 1, 1, 0, 0, 1, 2, 1, 1, 0],
            [1, 1, 0, 0, 1, 2, 0, 1, 0, 0],
            [1, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 1, 0, 0, 0]
        ]
        pc = PhenoCovar()
        parser = Parser(self.missing, data_field='GT')
        parser.init_subjects(pc)
        parser.load_genotypes()

        self.assertEqual(7, parser.locus_count)
        index = 0
        for snp in parser:
            snp_filter = numpy.ones(snp.missing_genotypes.shape[0]) == 1
            try:
                genodata = snp.get_genotype_data(snp_filter)
                self.assertEqual(int(self.nonmissing_mapdata[index][0]), snp.chr)
                self.assertEqual(int(self.nonmissing_mapdata[index][1]), snp.pos)
                self.assertEqual(self.nonmissing_mapdata[index][2], snp.rsid)
                self.assertEqual(genotypes_w_missing[index], list(genodata.genotypes))
            except TooMuchMissing as e:
                pass
            except InvalidFrequency as e:
                pass
            index += 1
        self.assertEqual(7, index)

    def testCompleteWithIndExclusions(self):
        DataParser.ind_exclusions = ["1", "3"]

        genotypes = [
            [1, 0, 1, 0, 0, 1, 0, 0, 1, 0],
            [1, 0, 0, 1, 1, 1, 0, 0, 0, 1],
            [2, 1, 0, 0, 0, 2, 1, 1, 0, 0],
            [1, 1, 1, 0, 0, 1, 2, 1, 1, 0],
            [2, 1, 0, 0, 1, 2, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            [1, 0, 0, 0, 0, 1, 1, 0, 0, 0]
        ]

        pc = PhenoCovar()
        parser = Parser(self.nonmissing, data_field='GT')
        parser.init_subjects(pc)
        parser.load_genotypes()

        index = 0
        for snp in parser:
            snp_filter = numpy.ones(snp.missing_genotypes.shape[0]) == 1
            try:
                genodata = snp.get_genotype_data(snp_filter)
                self.assertEqual(int(self.nonmissing_mapdata[index][0]), snp.chr)
                self.assertEqual(int(self.nonmissing_mapdata[index][1]), snp.pos)
                self.assertEqual(self.nonmissing_mapdata[index][2], snp.rsid)
                self.assertEqual(genotypes[index], list(genodata.genotypes))
            except TooMuchMissing as e:
                pass
            except InvalidFrequency as e:
                pass

            index += 1
        self.assertEqual(7, index)

    def testPedWithMissingMxIndExclusionsToo(self):
        pc = PhenoCovar()
        DataParser.ind_exclusions = ["3", "4"]
        DataParser.ind_miss_tol = 0.5       # We should lose "2"

        pc = PhenoCovar()
        parser = Parser(self.missing, data_field='GT')
        parser.init_subjects(pc)
        parser.load_genotypes()

        genotypes_w_missing = [[0, 1],
            [1, 0, 1, 1, 1, 0, 0, 0, 1],
            [0, 0, 0, 0, 2, 1, 1, 0, 0],
            [0, 1, 0, 0, 1, 2, 1, 1, 0],
            [1, 0, 0, 1, 2, 0, 1, 0, 0],
            [1, 0, 0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 1, 0, 0, 0]
        ]
        index = 0
        for snp in parser:
            snp_filter = numpy.ones(snp.missing_genotypes.shape[0]) == 1
            try:
                genodata = snp.get_genotype_data(snp_filter)
                self.assertEqual(int(self.nonmissing_mapdata[index][0]), snp.chr)
                self.assertEqual(int(self.nonmissing_mapdata[index][1]), snp.pos)
                self.assertEqual(self.nonmissing_mapdata[index][2], snp.rsid)
                self.assertEqual(genotypes_w_missing[index], list(genodata.genotypes))
            except TooMuchMissing as e:
                pass
            except InvalidFrequency as e:
                pass

            index += 1
        self.assertEqual(7, index)

    def testEmptyPhenoCovar(self):
        pc = PhenoCovar()

        pc = PhenoCovar()
        parser = Parser(self.missing, data_field='GT')
        parser.init_subjects(pc)
        parser.load_genotypes()

        index = 0
        missing_count = 0
        self.assertEqual(7, parser.locus_count)

        for snp in parser:
            for y in pc:
                try:
                    (pheno, covars, non_missing) = y.get_variables(snp.missing_genotypes)
                    genodata = snp.get_genotype_data(non_missing)
                    self.assertEqual(int(self.nonmissing_mapdata[index][0]), snp.chr)
                    self.assertEqual(int(self.nonmissing_mapdata[index][1]), snp.pos)
                    self.assertEqual(self.nonmissing_mapdata[index][2], snp.rsid)
                    self.assertEqual(self.genotypes[index], list(genodata.genotypes))
                except TooMuchMissingpPhenoCovar as e:
                    missing_count += 1
                    self.assertAlmostEqual(1.0, e.pct, places=4)
                except InvalidFrequency as e:
                    pass
                index += 1
        self.assertEqual(7, index)
        self.assertEqual(7, missing_count)
if __name__ == "__main__":
    unittest.main()
