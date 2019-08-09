#!/usr/bin/env python
import sys
# For debug, preference local install over all else
if "DEBUG" in sys.argv:
    sys.path.insert(0, "../../")
    sys.path.insert(0, "../")
    sys.path.insert(0, ".")
    sys.argv.remove("DEBUG")

import unittest
import numpy
import os

import libgwas
from libgwas.exceptions import InvariantVar
from libgwas.data_parser import DataParser
import libgwas.data_parser as data_parser
from libgwas.pheno_covar import PhenoCovar
from libgwas.pedigree_parser import Parser as PedigreeParser
from libgwas.boundary import BoundaryCheck
from libgwas.snp_boundary_check import SnpBoundaryCheck
import libgwas.standardizer
from libgwas.exceptions import InvalidFrequency
from libgwas.exceptions import TooMuchMissing
from libgwas.exceptions import TooMuchMissingpPhenoCovar

from libgwas.tests import remove_file
class TestBase(unittest.TestCase):
    def setUp(self):
        self.WriteTestFiles()

        self.ped            = libgwas.get_lines(self.ped_filename)

        self.phenotypes     = [0.1, 0.4, 1.0, 0.5, 0.9, 1.0, 0.1, 0.4, 1.0, 0.5, 0.9, 1.0]
        self.sex            = [1,1,2,2,1,1,1,1,2,2,1,1]

        self.chrom          = BoundaryCheck.chrom
        self.boundary       = DataParser.boundary
        DataParser.boundary = BoundaryCheck()
        self.min_maf        = DataParser.min_maf
        self.max_maf        = DataParser.max_maf
        self.snp_miss_tol   = DataParser.snp_miss_tol
        self.ind_miss_tol   = DataParser.ind_miss_tol
        DataParser.ind_exclusions = []
        DataParser.ind_inclusions = []
        self.sex_as_covar = PhenoCovar.sex_as_covariate
        self.has_sex        = DataParser.has_sex
        self.has_pheno      = DataParser.has_pheno
        self.has_parents    = DataParser.has_parents
        self.has_fid        = DataParser.has_fid
        self.has_liability  = DataParser.has_liability
        self.sex_as_covariate = PhenoCovar.sex_as_covariate
        self.standardizer = libgwas.standardizer.get_standardizer()
        libgwas.standardizer.set_standardizer(libgwas.standardizer.NoStandardization)

    def tearDown(self):

        for file in self.filenames:
            remove_file(file)
            
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
        PhenoCovar.sex_as_covariate = self.sex_as_covariate
        libgwas.standardizer.set_standardizer(self.standardizer)

    def WriteTestFiles(self, prefix = "__test_pedigree"):
        self.filenames = []

        self.genotypes_by_inds_ = [
            [2,1,2,2,1,1,2],
            [1,1,0,1,0,2,1],
            [2,2,1,0,2,1,1],
            [2,2,1,1,1,2,2],
            [1,2,2,1,2,2,2],
            [2,1,2,2,2,2,2],
            [2,1,2,2,1,2,2],
            [1,1,0,1,0,2,1],
            [2,2,1,0,2,1,1],
            [2,2,1,1,1,2,2],
            [1,2,2,1,2,2,2],
            [2,1,2,2,2,2,2]
        ]
        self.genotypes = [
            [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
            [1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1],
            [0, 2, 1, 1, 0, 0, 0, 2, 1, 1, 0, 0],
            [2, 1, 0, 1, 1, 2, 2, 1, 0, 1, 1, 2],
            [1, 2, 0, 1, 0, 0, 1, 2, 0, 1, 0, 0],
            [1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            [2, 1, 1, 2, 2, 2, 2, 1, 1, 2, 2, 2]
        ]
        self.genotypes = [
            [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
            [1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1],
            [0, 2, 1, 1, 0, 0, 0, 2, 1, 1, 0, 0],
            [0, 1, 2, 1, 1, 0, 0, 1, 2, 1, 1, 0],
            [1, 2, 0, 1, 0, 0, 1, 2, 0, 1, 0, 0],
            [1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            [0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0]
        ]
        self.missing_genotypes = [
            [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
            [-1, -1, -1, -1, -1, 1, -1, -1, -1, 0, 0, 1],
            [-1, 2, 1, 1, 0, 0, 0, 2, 1, 1, 0, 0],
            [-1, 1, 2, 1, 1, 0, 0, 1, 2, 1, 1, 0],
            [-1, 2, 0, 1, 0, 0, 1, 2, 0, 1, 0, 0],
            [-1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            [0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0]
        ]
        self.ped_filename = "%s.ped" % (prefix)
        with open(self.ped_filename, "w") as f:
            self.filenames.append(self.ped_filename)
            f.write("""
1 1 0 0 1 0.1 A A G T A A G G C T G T T T
2 2 0 0 1 0.4 A C G T G G C G T T G G C T
3 3 0 0 2 1.0 A A G G A G C C C C G T C T
4 4 0 0 2 0.5 A A G G A G C G C T G G T T
5 5 0 0 1 0.9 A C G G A A C G C C G G T T
6 6 0 0 1 1.0 A A G T A A G G C C G G T T
7 7 0 0 1 0.1 A A G T A A G G C T G G T T
8 8 0 0 1 0.4 A C G T G G C G T T G G C T
9 9 0 0 2 1.0 A A G G A G C C C C G T C T
10 10 0 0 2 0.5 A A G G A G C G C T G G T T
11 11 0 0 1 0.9 A C G G A A C G C C G G T T
12 12 0 0 1 1.0 A A G T A A G G C C G G T T""")

        self.map_filename = "%s.map" % (prefix)
        self.filenames.append(self.map_filename)
        with open(self.map_filename, "w") as f:
            f.write("""1 rs0001 0 500
1 rs0002 0 10000
1 rs0003 0 25000
1 rs0004 0 45000
2 rs0005 0 750
2 rs0006 0 10000
2 rs0007 0 25000
""")

        self.ped_filename_missing = "%s-miss.ped" % (prefix)
        
        with open(self.ped_filename_missing, "w") as f:
            self.filenames.append(self.ped_filename_missing)
            f.write("""
1 1 0 0 1 0.1 A A 0 0 0 0 0 0 0 0 0 0 T T
2 2 0 0 1 0.4 A C 0 0 G G C G T T G G C T
3 3 0 0 2 1.0 A A 0 0 A G C C C C G T C T
4 4 0 0 2 0.5 A A 0 0 A G C G C T G G T T
5 5 0 0 1 0.9 A C 0 0 A A C G C C G G T T
6 6 0 0 1 1.0 A A G T A A G G C C G G T T
7 7 0 0 1 0.1 A A 0 0 A A G G C T G G T T
8 8 0 0 1 0.4 A C 0 0 G G C G T T G G C T
9 9 0 0 2 1.0 A A 0 0 A G C C C C G T C T
10 10 0 0 -9 0.5 A A G G A G C G C T G G T T
11 11 0 0 -9 0.9 A C G G A A C G C C G G T T
12 12 0 0 -9 1.0 A A G T A A G G C C G G T T""")

        self.map3_filename = "%s.map3" % (prefix)
        self.filenames.append(self.map3_filename)
        with open(self.map3_filename, "w") as f:
            f.write("""1 rs0001 500
1 rs0002 10000
1 rs0003 25000
1 rs0004 45000
2 rs0005 750
2 rs0006 10000
2 rs0007 25000
""")

        self.map_miss_filename = "%s-miss.map" % (prefix)
        self.filenames.append(self.map_miss_filename)
        with open(self.map_miss_filename, "w") as f:
            f.write("""1 rs0001 0 -500
1 rs0002 0 -10000
1 rs0003 0 25000
1 rs0004 0 45000
2 rs0005 0 750
2 rs0006 0 10000
2 rs0007 0 25000
""")

        self.miniped_filename = "%s-mini.ped" % (prefix)
        with open(self.miniped_filename, "w") as f:
            self.filenames.append(self.miniped_filename)
            f.write("""
1 1 0 0 1 0.1 A A G T A A G G C T G T T T
2 2 0 0 1 0.4 A C G T G G C G T T G G C T
3 3 0 0 2 1.0 A A G G A G C G T C G T C T""")

        self.pheno_file = "%s_mch.txt" % (prefix)
        with open(self.pheno_file, "w") as f:
            self.filenames.append(self.pheno_file)
            f.write("""FID\tIID\tBMI\tIBM\tMSA
1\t1\t0.1\t1.0\t0.5
2\t2\t0.2\t0.5\t1.0
3\t3\t0.3\t0.6\t0.1
4\t4\t0.4\t0.5\t0.5
5\t5\t0.5\t1.0\t1.0
6\t6\t0.6\t0.1\t0.2
17\t7\t0.1\t1.0\t0.5
8\t8\t0.2\t0.5\t1.0
9\t9\t0.3\t0.6\t0.1
10\t10\t0.4\t0.5\t0.5
11\t11\t0.5\t1.0\t1.0
12\t12\t0.6\t0.1\t0.2""")

        self.ped_parser = PedigreeParser(self.map_filename, self.ped_filename)



class TestIndIncRem(TestBase):
    def testBasics(self):
        inc = ["1:1", "1:2", "3:3", "5:5"]
        rmv = ["4:4", "5:5"]
        self.assertTrue(data_parser.check_inclusions("1:1"))
        self.assertTrue(data_parser.check_inclusions("1:2"))
        self.assertTrue(data_parser.check_inclusions("4:4"))
        self.assertTrue(data_parser.check_inclusions("4:4", []))
        self.assertFalse(data_parser.check_inclusions("4:4", inc))
        self.assertTrue(data_parser.check_inclusions("1:1", inc))
        self.assertTrue(data_parser.check_inclusions("5:5", inc))
        self.assertTrue(data_parser.check_inclusions("5:5", inc, rmv))
        self.assertFalse(data_parser.check_inclusions("4:4", inc, rmv))
        self.assertFalse(data_parser.check_inclusions("5:5", [], rmv))

    def testValidIndID(self):
        indexc = DataParser.ind_exclusions
        indinc = DataParser.ind_inclusions
        DataParser.ind_exclusions  = ["4:4", "5:5"]
        DataParser.ind_inclusions  = ["1:1", "1:2", "3:3", "5:5"]
        self.assertTrue(DataParser.valid_indid("1:1"))
        self.assertTrue(DataParser.valid_indid("1:2"))
        self.assertFalse(DataParser.valid_indid("4:4"))
        self.assertTrue(DataParser.valid_indid("5:5"))
        self.assertTrue(DataParser.valid_indid("1:1"))
        self.assertTrue(DataParser.valid_indid("5:5"))
        self.assertFalse(DataParser.valid_indid("4:4"))
        DataParser.ind_exclusions  = indexc
        DataParser.ind_inclusions  = indinc


class TestPedigreeVariedColumns(TestBase):
    def setUp(self):
        super(TestPedigreeVariedColumns, self).setUp()
        self.sex_as_covar = PhenoCovar.sex_as_covariate
        self.has_sex = DataParser.has_sex
        self.has_parents = DataParser.has_parents
        self.has_fid = DataParser.has_fid
        self.has_pheno = DataParser.has_pheno
        self.has_liability = DataParser.has_liability

    def tearDown(self):
        super(TestPedigreeVariedColumns, self).tearDown()
        PhenoCovar.sex_as_covariate = self.sex_as_covar
        DataParser.has_sex = self.has_sex
        DataParser.has_parents = self.has_parents
        DataParser.has_fid = self.has_fid
        DataParser.has_pheno = self.has_pheno
        DataParser.has_liability = self.has_liability

    def testPedigreeNoSex(self):
        DataParser.has_sex = False
        with open(self.ped_filename, "w") as f:
            f.write("""1 1 0 0 0.1 A A G T A A G G C T G T T T
2 2 0 0 0.4 A C G T G G C G T T G G C T
3 3 0 0 1.0 A A G G A G C C C C G T C T
4 4 0 0 0.5 A A G G A G C G C T G G T T
5 5 0 0 0.9 A C G G A A C G C C G G T T
6 6 0 0 1.0 A A G T A A G G C C G G T T
7 7 0 0 0.1 A A G T A A G G C T G G T T
8 8 0 0 0.4 A C G T G G C G T T G G C T
9 9 0 0 1.0 A A G G A G C C C C G T C T
10 10 0 2 0.5 A A G G A G C G C T G G T T
11 11 0 1 0.9 A C G G A A C G C C G G T T
12 12 0 1 1.0 A A G T A A G G C C G G T T""")

        pc = PhenoCovar()
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)

        mapdata = libgwas.get_lines(self.map_filename, split=True)

        index = 0
        for snp in ped_parser:
            for y in pc:
                (pheno, covars, nonmissing) = y.get_variables(snp.missing_genotypes)
                try:
                    genodata = snp.get_genotype_data(nonmissing)
                    self.assertEqual(int(mapdata[index][0]), snp.chr)
                    self.assertEqual(int(mapdata[index][3]), snp.pos)
                    self.assertEqual(mapdata[index][1], snp.rsid)
                    self.assertEqual(self.genotypes[index], list(genodata.genotypes))
                except TooMuchMissing as e:
                    pass
                except InvalidFrequency as e:
                    pass

            index += 1
        self.assertEqual(7, index)

    def testPedigreeWithLiability(self):
        DataParser.has_liability = True
        with open(self.ped_filename, "w") as f:
            f.write("""1 1 0 0 1 0.1 1 A A G T A A G G C T G T T T
2 2 0 0 1 0.4 1 A C G T G G C G T T G G C T
3 3 0 0 2 1.0 1 A A G G A G C C C C G T C T
4 4 0 0 2 0.5 1 A A G G A G C G C T G G T T
5 5 0 0 1 0.9 1 A C G G A A C G C C G G T T
6 6 0 0 1 1.0 1 A A G T A A G G C C G G T T
7 7 0 0 1 0.1 1 A A G T A A G G C T G G T T
8 8 0 0 1 0.4 1 A C G T G G C G T T G G C T
9 9 0 0 2 1.0 1 A A G G A G C C C C G T C T
10 10 0 0 2 0.5 1 A A G G A G C G C T G G T T
11 11 0 0 1 0.9 1 A C G G A A C G C C G G T T
12 12 0 0 1 1.0 1 A A G T A A G G C C G G T T""")

        pc = PhenoCovar()
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)

        mapdata = libgwas.get_lines(self.map_filename, split=True)

        index = 0
        for snp in ped_parser:
            for y in pc:
                (pheno, covars, nonmissing) = y.get_variables(snp.missing_genotypes)
                try:
                    genodata = snp.get_genotype_data(nonmissing)
                    self.assertEqual(int(mapdata[index][0]), snp.chr)
                    self.assertEqual(int(mapdata[index][3]), snp.pos)
                    self.assertEqual(mapdata[index][1], snp.rsid)
                    self.assertEqual(self.genotypes[index], list(genodata.genotypes))
                except TooMuchMissing as e:
                    pass
                except InvalidFrequency as e:
                    pass

            index += 1
        self.assertEqual(7, index)

    def testPedigreeNoParents(self):
        DataParser.has_parents = False
        with open(self.ped_filename, "w") as f:
            f.write("""1 1 1 0.1 A A G T A A G G C T G T T T
2 2 1 0.4 A C G T G G C G T T G G C T
3 3 2 1.0 A A G G A G C C C C G T C T
4 4 2 0.5 A A G G A G C G C T G G T T
5 5 1 0.9 A C G G A A C G C C G G T T
6 6 1 1.0 A A G T A A G G C C G G T T
7 7 1 0.1 A A G T A A G G C T G G T T
8 8 1 0.4 A C G T G G C G T T G G C T
9 9 2 1.0 A A G G A G C C C C G T C T
10 10 2 0.5 A A G G A G C G C T G G T T
11 11 1 0.9 A C G G A A C G C C G G T T
12 12 1 1.0 A A G T A A G G C C G G T T""")

        pc = PhenoCovar()
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)

        mapdata = libgwas.get_lines(self.map_filename, split=True)

        index = 0
        for snp in ped_parser:
            for y in pc:
                (pheno, covars, nonmissing) = y.get_variables(snp.missing_genotypes)
                try:
                    genodata = snp.get_genotype_data(nonmissing)
                    self.assertEqual(int(mapdata[index][0]), snp.chr)
                    self.assertEqual(int(mapdata[index][3]), snp.pos)
                    self.assertEqual(mapdata[index][1], snp.rsid)
                    self.assertEqual(self.genotypes[index], list(genodata.genotypes))
                except TooMuchMissing as e:
                    pass
                except InvalidFrequency as e:
                    pass

            index += 1
        self.assertEqual(7, index)

    def testPedigreeNoPheno(self):
        DataParser.has_pheno = False
        with open(self.ped_filename, "w") as f:
            f.write("""1 1 0 0 1 A A G T A A G G C T G T T T
2 2 0 0 1 A C G T G G C G T T G G C T
3 3 0 0 2 A A G G A G C C C C G T C T
4 4 0 0 2 A A G G A G C G C T G G T T
5 5 0 0 1 A C G G A A C G C C G G T T
6 6 0 0 1 A A G T A A G G C C G G T T
7 7 0 0 1 A A G T A A G G C T G G T T
8 8 0 0 1 A C G T G G C G T T G G C T
9 9 0 0 2 A A G G A G C C C C G T C T
10 10 0 0 2 A A G G A G C G C T G G T T
11 11 0 0 1 A C G G A A C G C C G G T T
12 12 0 0 1 A A G T A A G G C C G G T T""")

        PhenoCovar.sex_as_covariate = True
        pc = PhenoCovar()
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)

        mapdata = libgwas.get_lines(self.map_filename, split=True)

        index = 0
        missing_count = 0
        for snp in ped_parser:
            try:
                for y in pc:
                    (pheno, covars, nonmissing) = y.get_variables(snp.missing_genotypes)
                    genodata = snp.get_genotype_data(nonmissing)
                    self.assertEqual(int(mapdata[index][0]), snp.chr)
                    self.assertEqual(int(mapdata[index][3]), snp.pos)
                    self.assertEqual(mapdata[index][1], snp.rsid)
                    self.assertEqual(genotypes[index], list(genodata.genotypes))
            except TooMuchMissingpPhenoCovar as e:
                missing_count += 1
            except TooMuchMissing as e:
                pass
            except InvalidFrequency as e:
                pass

            index += 1
        self.assertEqual(7, index)
        self.assertEqual(7, missing_count)
    def testPedigreeNoPhenoNoFam(self):
        DataParser.has_fid = False
        DataParser.has_pheno = False
        with open(self.ped_filename, "w") as f:
            f.write("""1 0 0 1 A A G T A A G G C T G T T T
2 0 0 1 A C G T G G C G T T G G C T
3 0 0 2 A A G G A G C C C C G T C T
4 0 0 2 A A G G A G C G C T G G T T
5 0 0 1 A C G G A A C G C C G G T T
6 0 0 1 A A G T A A G G C C G G T T
7 0 0 1 A A G T A A G G C T G G T T
8 0 0 1 A C G T G G C G T T G G C T
9 0 0 2 A A G G A G C C C C G T C T
10 0 0 2 A A G G A G C G C T G G T T
11 0 0 1 A C G G A A C G C C G G T T
12 0 0 1 A A G T A A G G C C G G T T""")

        pc = PhenoCovar()
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)

        mapdata = libgwas.get_lines(self.map_filename, split=True)

        index = 0
        missing_count = 0
        for snp in ped_parser:
            try:
                for y in pc:
                    (pheno, covars, nonmissing) = y.get_variables(snp.missing_genotypes)

                    genodata = snp.get_genotype_data(nonmissing)
                    self.assertEqual(int(mapdata[index][0]), snp.chr)
                    self.assertEqual(int(mapdata[index][3]), snp.pos)
                    self.assertEqual(mapdata[index][1], snp.rsid)
                    self.assertEqual(self.genotypes[index], list(genodata.genotypes))

            except TooMuchMissingpPhenoCovar as e:
                missing_count += 1
                self.assertAlmostEqual(1.0, e.pct, places=4)
            except InvalidFrequency as e:
                pass
            except TooMuchMissing as e:
                pass

            index += 1
        self.assertEqual(7, index)
        self.assertEqual(7, missing_count)


    def testPedigreeNoFamId(self):
        DataParser.has_fid = False
        with open(self.ped_filename, "w") as f:
            f.write("""1 0 0 1 0.1 A A G T A A G G C T G T T T
2 0 0 1 0.4 A C G T G G C G T T G G C T
3 0 0 2 1.0 A A G G A G C C C C G T C T
4 0 0 2 0.5 A A G G A G C G C T G G T T
5 0 0 1 0.9 A C G G A A C G C C G G T T
6 0 0 1 1.0 A A G T A A G G C C G G T T
7 0 0 1 0.1 A A G T A A G G C T G G T T
8 0 0 1 0.4 A C G T G G C G T T G G C T
9 0 0 2 1.0 A A G G A G C C C C G T C T
10 0 0 2 0.5 A A G G A G C G C T G G T T
11 0 0 1 0.9 A C G G A A C G C C G G T T
12 0 0 1 1.0 A A G T A A G G C C G G T T""")

        pc = PhenoCovar()
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)

        mapdata = libgwas.get_lines(self.map_filename, split=True)

        index = 0
        for snp in ped_parser:
            for y in pc:
                (pheno, covars, nonmissing) = y.get_variables(snp.missing_genotypes)
                try:
                    genodata = snp.get_genotype_data(nonmissing)
                    self.assertEqual(int(mapdata[index][0]), snp.chr)
                    self.assertEqual(int(mapdata[index][3]), snp.pos)
                    self.assertEqual(mapdata[index][1], snp.rsid)
                    self.assertEqual(self.genotypes[index], list(genodata.genotypes))
                except TooMuchMissing as e:
                    pass
                except InvalidFrequency as e:
                    pass

            index += 1
        self.assertEqual(7, index)

    def testPedigreeNoFamSexOrParents(self):
        DataParser.has_fid = False
        DataParser.has_sex = False
        DataParser.has_parents = False
        with open(self.ped_filename, "w") as f:
            f.write("""1 0.1 A A G T A A G G C T G T T T
2 0.4 A C G T G G C G T T G G C T
3 1.0 A A G G A G C C C C G T C T
4 0.5 A A G G A G C G C T G G T T
5 0.9 A C G G A A C G C C G G T T
6 1.0 A A G T A A G G C C G G T T
7 0.1 A A G T A A G G C T G G T T
8 0.4 A C G T G G C G T T G G C T
9 1.0 A A G G A G C C C C G T C T
10 0.5 A A G G A G C G C T G G T T
11 0.9 A C G G A A C G C C G G T T
12 1.0 A A G T A A G G C C G G T T""")

        pc = PhenoCovar()
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)

        mapdata = libgwas.get_lines(self.map_filename, split=True)

        index = 0
        for snp in ped_parser:
            for y in pc:
                (pheno, covars, nonmissing) = y.get_variables(snp.missing_genotypes)
                try:
                    genodata = snp.get_genotype_data(nonmissing)
                    self.assertEqual(int(mapdata[index][0]), snp.chr)
                    self.assertEqual(int(mapdata[index][3]), snp.pos)
                    self.assertEqual(mapdata[index][1], snp.rsid)
                    self.assertEqual(self.genotypes[index], list(genodata.genotypes))
                except TooMuchMissing as e:
                    pass
                except InvalidFrequency as e:
                    pass

            index += 1
        self.assertEqual(7, index)
class TestPedFiles(TestBase):
    # Test to make sure we can load everything
    def testPedComplete(self):
        pc = PhenoCovar()
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)

        mapdata = libgwas.get_lines(self.map_filename, split=True)

        index = 0
        for snp in ped_parser:
            for y in pc:
                (pheno, covars, nonmissing) = y.get_variables(snp.missing_genotypes)
                try:
                    genodata = snp.get_genotype_data(nonmissing)
                    self.assertEqual(int(mapdata[index][0]), snp.chr)
                    self.assertEqual(int(mapdata[index][3]), snp.pos)
                    self.assertEqual(mapdata[index][1], snp.rsid)
                    self.assertEqual(self.genotypes[index], list(genodata.genotypes))
                except TooMuchMissing as e:
                    pass
                except InvalidFrequency as e:
                    pass

            index += 1
        self.assertEqual(7, index)

    def testPedCompleteAlternateIteration(self):
        """Useful if you need to iterate over these in a more controlled manner"""
        pc = PhenoCovar()
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)

        mapdata = libgwas.get_lines(self.map_filename, split=True)

        index = 0
        snp = next(ped_parser.__iter__())
        try:
            while True:
                for y in pc:
                    (pheno, covars, nonmissing) = y.get_variables(snp.missing_genotypes)
                    try:
                        genodata = snp.get_genotype_data(nonmissing)
                        self.assertEqual(int(mapdata[index][0]), snp.chr)
                        self.assertEqual(int(mapdata[index][3]), snp.pos)
                        self.assertEqual(mapdata[index][1], snp.rsid)
                        self.assertEqual(self.genotypes[index], list(genodata.genotypes))
                    except TooMuchMissing as e:
                        pass
                    except InvalidFrequency as e:
                        pass
                index += 1
                next(snp)

        except StopIteration:
            pass
        self.assertEqual(7, index)

    def testPedMultiPheno(self):
        PhenoCovar.sex_as_covariate = True
        pc = PhenoCovar()
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)
        
        with open(self.pheno_file) as f:
            pc.load_phenofile(f, indices=[2,3])
        mapdata = libgwas.get_lines(self.map_filename, split=True)

        sex = [1,1,2,2,1,1,1,2,2,1,1]
        pheno_data = [[0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
                 [1.0, 0.5, 0.6, 0.5, 1.0, 0.1],
                 [0.5, 1.0, 0.1, 0.5, 1.0, 0.2]]
        dual_pheno = [[1.0, 0.5, 0.6, 0.5, 1.0, 0.1, 0.5, 0.6, 0.5, 1.0, 0.1],
                      [0.5, 1.0, 0.1, 0.5, 1.0, 0.2, 1.0, 0.1, 0.5, 1.0, 0.2]]

        genotypes = [
            [0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0],
            [1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1],
            [0, 2, 1, 1, 0, 0, 2, 1, 1, 0, 0],
            [0, 1, 2, 1, 1, 0, 1, 2, 1, 1, 0],
            [1, 2, 0, 1, 0, 0, 2, 0, 1, 0, 0],
            [1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0],
            [0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0]
        ]

        self.assertEqual(2, len(pc.phenotype_data))
        index = 0

        for snp in ped_parser:
            idx = 0
            for y in pc:
                pheno, covars, nonmissing = y.get_variables(snp.missing_genotypes)
                self.assertEqual(sex, list(covars[0]))
                self.assertAlmostEqual(dual_pheno[idx], list(pheno))

                try:
                    genodata = snp.get_genotype_data(nonmissing)
                    self.assertEqual(int(mapdata[index][0]), snp.chr)
                    self.assertEqual(int(mapdata[index][3]), snp.pos)
                    self.assertEqual(mapdata[index][1], snp.rsid)
                    self.assertEqual(genotypes[index], list(genodata.genotypes))
                except TooMuchMissing as e:
                    pass
                except InvalidFrequency as e:
                    pass
                idx += 1
            self.assertEqual(2, idx)

            index += 1
        self.assertEqual(7, index)

    def testForInvariant(self):
        prefix = "__test_pedigree"
        self.pheno_file = "%s_mch.txt" % (prefix)
        with open(self.pheno_file, "w") as f:
            f.write("""FID\tIID\tBMI\tIBM\tMSA
1\t1\t0.1\t1.0\t1.0
2\t2\t0.2\t0.5\t1.0
3\t3\t0.3\t0.6\t1.0
4\t4\t0.4\t0.5\t1.0
5\t5\t0.5\t1.0\t1.0
6\t6\t0.6\t0.1\t1.0
17\t7\t0.1\t1.0\t1.0
8\t8\t0.2\t0.5\t1.0
9\t9\t0.3\t0.6\t1.0
10\t10\t0.4\t0.5\t1.0
11\t11\t0.5\t1.0\t1.0
12\t12\t0.6\t0.1\t1.0""")

        PhenoCovar.sex_as_covariate = True
        pc = PhenoCovar()
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)
        
        with open(self.pheno_file) as f:
            pc.load_phenofile(f, indices=[3])
        index = 0

        mapdata = libgwas.get_lines(self.map_filename, split=True)


        with self.assertRaises(InvariantVar):
            for snp in ped_parser:
                for y in pc:
                    non_missing = numpy.ones(len(snp.genotype_data), dtype=bool)
                    (pheno, covariates, nonmissing) = y.get_variables(numpy.invert(non_missing))





    def testPedBoundary(self):
        pc = PhenoCovar()
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename)
        DataParser.boundary = BoundaryCheck()
        BoundaryCheck.chrom = 2
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)

        mapdata = libgwas.get_lines(self.map_filename, split=True)

        index = 4
        for snp in ped_parser:
            for y in pc:
                (pheno, covars, nonmissing) = y.get_variables(snp.missing_genotypes)
                try:
                    genodata = snp.get_genotype_data(nonmissing)
                    self.assertEqual(int(mapdata[index][0]), snp.chr)
                    self.assertEqual(int(mapdata[index][3]), snp.pos)
                    self.assertEqual(mapdata[index][1], snp.rsid)
                    self.assertEqual(self.genotypes[index], list(genodata.genotypes))
                except TooMuchMissing as e:
                    pass
                except InvalidFrequency as e:
                    pass

            index += 1
        self.assertEqual(7, index)
class TestIndExclusions(TestBase):
    def testPedigreeIndExclusionsComplete(self):
        DataParser.ind_exclusions = ["11:11", "12:12"]
        pc = PhenoCovar()

        ped_parser = PedigreeParser(self.map_filename, self.ped_filename)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)

        mapdata = libgwas.get_lines(self.map_filename, split=True)

        index = 0
        for snp in ped_parser:
            for y in pc:
                (pheno, covars, nonmissing) = y.get_variables(snp.missing_genotypes)
                try:
                    genodata = snp.get_genotype_data(nonmissing)
                    self.assertEqual(int(mapdata[index][0]), snp.chr)
                    self.assertEqual(int(mapdata[index][3]), snp.pos)
                    self.assertEqual(mapdata[index][1], snp.rsid)
                    self.assertEqual(self.genotypes[index][0:10], list(genodata.genotypes))
                except TooMuchMissing as e:
                    pass
                except InvalidFrequency as e:
                    pass

            index += 1
        self.assertEqual(7, index)

    def testPedigreeIndExclusionsMissingComplete(self):
        DataParser.ind_exclusions = ["11:11", "12:12"]
        pc = PhenoCovar()
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename_missing)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)

        mapdata = libgwas.get_lines(self.map_filename, split=True)

        genotypes = [
            [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
            [-1, -1, -1, -1, -1, 1, -1, -1, -1, 0, 0, 1],
            [-1, 2, 1, 1, 0, 0, 0, 2, 1, 1, 0, 0],
            [-1, 1, 0, 1, 1, 2, 2, 1, 0, 1, 1, 2],
            [-1, 2, 0, 1, 0, 0, 1, 2, 0, 1, 0, 0],
            [-1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0],
             [0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0]
        ]

        missing_genotypes = [
            [ 0,  1,  0,  0,  1,  0,  0,  1,  0,  0],
            [ 1,  0],
            [ 2,  1,  1,  0,  0,  0,  2,  1,  1],
            [ 1,  0,  1,  1,  2,  2,  1,  0,  1],
            [ 2,  0,  1,  0,  0,  1,  2,  0,  1],
            [ 0,  1,  0,  0,  0,  0,  0,  1,  0],
            [ 0,  1,  1,  0,  0,  0,  0,  1,  1,  0]
            ]
        index = 0
        for snp in ped_parser:
            for y in pc:
                (pheno, covars, nonmissing) = y.get_variables(snp.missing_genotypes)
                try:
                    genodata = snp.get_genotype_data(nonmissing)
                    self.assertEqual(int(mapdata[index][0]), snp.chr)
                    self.assertEqual(int(mapdata[index][3]), snp.pos)
                    self.assertEqual(mapdata[index][1], snp.rsid)
                    self.assertEqual(missing_genotypes[index], list(genodata.genotypes))
                except TooMuchMissing as e:
                    pass
                except InvalidFrequency as e:
                    pass

            index += 1
        self.assertEqual(7, index)

    def testPedigreeIndExclusionsMissingIndThresh(self):
        pc = PhenoCovar()
        DataParser.ind_exclusions = ["11:11", "12:12"]
        DataParser.ind_miss_tol = 0.5       # We should only lose 1
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename_missing)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)

        mapdata = libgwas.get_lines(self.map_filename, split=True)

        # When we dropped 11 and 12, snp #4 becomes perfectly balanced
        # so ut will declare allele[0] to be major (first allele
        # encountered)
        missing_genotypes = [
            [1, 0, 0, 1, 0, 0, 1, 0, 0],
            [1, 0],
            [2, 1, 1, 0, 0, 0, 2, 1, 1],
            [1, 0, 1, 1, 2, 2, 1, 0, 1],
            [2, 0, 1, 0, 0, 1, 2, 0, 1],
            [0, 1, 0, 0, 0, 0, 0, 1, 0],
            [1, 1, 0, 0, 0, 0, 1, 1, 0]
        ]
        index = 0
        map_idx = 0
        for snp in ped_parser:
            for y in pc:
                (pheno, covars, nonmissing) = y.get_variables(snp.missing_genotypes)
                try:
                    genodata = snp.get_genotype_data(nonmissing)
                    self.assertEqual(int(mapdata[index][0]), snp.chr)
                    self.assertEqual(int(mapdata[index][3]), snp.pos)
                    self.assertEqual(mapdata[index][1], snp.rsid)
                    self.assertEqual(missing_genotypes[index], list(genodata.genotypes))
                except TooMuchMissing as e:
                    pass
                except InvalidFrequency as e:
                    pass

            index += 1
            map_idx += 1
        self.assertEqual(7, index)

class TestMissingData(TestBase):
    def testMissingComplete(self):
        pc = PhenoCovar()
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename_missing)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)

        mapdata = libgwas.get_lines(self.map_filename, split=True)
        missing_genotypes = [
            [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
            [1, 0, 0, 1],
            [2, 1, 1, 0, 0, 0, 2, 1, 1, 0, 0],
            [1, 2, 1, 1, 0, 0, 1, 2, 1, 1, 0],
            [2, 0, 1, 0, 0, 1, 2, 0, 1, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            [0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0]
        ]
        index = 0
        for snp in ped_parser:
            for y in pc:
                (pheno, covars, nonmissing) = y.get_variables(snp.missing_genotypes)
                try:
                    genodata = snp.get_genotype_data(nonmissing)
                    self.assertEqual(int(mapdata[index][0]), snp.chr)
                    self.assertEqual(int(mapdata[index][3]), snp.pos)
                    self.assertEqual(mapdata[index][1], snp.rsid)
                    self.assertEqual(missing_genotypes[index], list(genodata.genotypes))
                except TooMuchMissing as e:
                    pass
                except InvalidFrequency as e:
                    pass

            index += 1
        self.assertEqual(7, index)

    # Unit test borrowed from MVtest because it wasn't detected here, where it should
    # have been
    def testPedCmdLineMIND2(self):
        DataParser.ind_miss_tol = 0.1
        pc = PhenoCovar()
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename_missing)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)

        genotypes = [
            [ 0, 0, 1, 0],
            [ 1, 0, 0, 1],
            [ 0, 1, 0, 0],
            [ 0, 1, 1, 0],
            [ 0, 1, 0, 0],
            [ 0, 0, 0, 0],
             [0, 0, 0, 0]
        ]
        mapdata = libgwas.get_lines(self.map_filename, split=True)
        skipped = 0
        index = 0
        for snp in ped_parser:
            snp_filter = numpy.ones(snp.missing_genotypes.shape[0]) == 1
            try:
                genodata = snp.get_genotype_data(snp_filter)
                self.assertEqual(genotypes[index], list(genodata.genotypes))
                self.assertEqual(int(mapdata[index][0]), snp.chr)
                self.assertEqual(int(mapdata[index][3]), snp.pos)
                self.assertEqual(mapdata[index][1], snp.rsid)
                index += 1
            except TooMuchMissing as e:
                pass
            except InvalidFrequency as e:
                skipped += 1
            except TooMuchMissingpPhenoCovar as e:
                pass
        self.assertEqual(0, skipped)
        self.assertEqual(5, index)          # Last two are fixed

    def testMissingIndThresh(self):
        pc = PhenoCovar()
        DataParser.ind_miss_tol = 0.5       # We should only lose 1
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename_missing)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)

        mapdata = libgwas.get_lines(self.map_filename, split=True)

        missing_genotypes = [
            [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
            [-1, -1, -1, -1, -1, 1, -1, -1, -1, 0, 0, 1],
            [-1, 2, 1, 1, 0, 0, 0, 2, 1, 1, 0, 0],
            [-1, 1, 2, 1, 1, 0, 0, 1, 2, 1, 1, 0],
            [-1, 2, 0, 1, 0, 0, 1, 2, 0, 1, 0, 0],
            [-1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            [0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0]
        ]
        genotypes = [
            [1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
            [1, 0, 0, 1],
            [2, 1, 1, 0, 0, 0, 2, 1, 1, 0, 0],
            [1, 2, 1, 1, 0, 0, 1, 2, 1, 1, 0],
            [2, 0, 1, 0, 0, 1, 2, 0, 1, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            [1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0]
        ]
        index = 0
        map_idx = 0
        for snp in ped_parser:
            for y in pc:
                (pheno, covars, nonmissing) = y.get_variables(snp.missing_genotypes)
                try:
                    genodata = snp.get_genotype_data(nonmissing)
                    self.assertEqual(int(mapdata[index][0]), snp.chr)
                    self.assertEqual(int(mapdata[index][3]), snp.pos)
                    self.assertEqual(mapdata[index][1], snp.rsid)
                    self.assertEqual(genotypes[index], list(genodata.genotypes))
                except TooMuchMissing as e:
                    pass
                except InvalidFrequency as e:
                    pass

            index += 1
            map_idx += 1
        self.assertEqual(7, index)


    def testMissingBoth(self):
        pc = PhenoCovar()
        DataParser.ind_miss_tol = 0.5       # We should only lose 1
        DataParser.snp_miss_tol = 0.5       # We should only lose 1
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename_missing)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)

        mapdata = libgwas.get_lines(self.map_filename, split=True)
        genotypes = [
            [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
            [1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1],
            [0, 2, 1, 1, 0, 0, 0, 2, 1, 1, 0, 0],
            [0, 1, 2, 1, 1, 0, 0, 1, 2, 1, 1, 0],
            [1, 2, 0, 1, 0, 0, 1, 2, 0, 1, 0, 0],
            [1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            [0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0]
        ]
        missing_genotypes = [
            [1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
            [0, 0, 1],
            [2, 1, 1, 0, 0, 0, 2, 1, 1, 0, 0],
            [1, 2, 1, 1, 0, 0, 1, 2, 1, 1, 0],
            [2, 0, 1, 0, 0, 1, 2, 0, 1, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            [1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0]
        ]
        self.assertEqual([1,0,0,0,0,0,0,0,0,0,0,0], list(ped_parser.individual_mask))
        index = 0
        valid_evals = 0
        for snp in ped_parser:
            for y in pc:
                (pheno, covars, nonmissing) = y.get_variables(snp.missing_genotypes)
                try:
                    genodata = snp.get_genotype_data(nonmissing)
                    self.assertEqual(int(mapdata[index][0]), snp.chr)
                    self.assertEqual(int(mapdata[index][3]), snp.pos)
                    self.assertEqual(mapdata[index][1], snp.rsid)
                    self.assertEqual(missing_genotypes[index], list(genodata.genotypes))
                    valid_evals += 1
                except TooMuchMissing as e:
                    pass
                except InvalidFrequency as e:
                    pass

            index += 1
        self.assertEqual(6, valid_evals)
        self.assertEqual(7, index)

    def testMissingSnpThresh(self):
        pc = PhenoCovar()
        DataParser.snp_miss_tol = 0.5       # We should only lose 1
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename_missing)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)
        #self.assertEqual([0,1,0,0,0,0,0,0,0,0,0,0], list(ped_parser.individual_mask))
        mapdata = libgwas.get_lines(self.map_filename, split=True)
        missing_genotypes = [
            [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
            [1, 0, 0, 1],
            [2, 1, 1, 0, 0, 0, 2, 1, 1, 0, 0],
            [1, 2, 1, 1, 0, 0, 1, 2, 1, 1, 0],
            [2, 0, 1, 0, 0, 1, 2, 0, 1, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            [0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0]
        ]

        index = 0
        missing = 0
        freq = 0
        valid_evaluations = 0
        for snp in ped_parser:
            for y in pc:
                (pheno, covars, nonmissing) = y.get_variables(snp.missing_genotypes)

                try:
                    genodata = snp.get_genotype_data(nonmissing)                
                    self.assertEqual(int(mapdata[index][0]), snp.chr)
                    self.assertEqual(int(mapdata[index][3]), snp.pos)
                    self.assertEqual(mapdata[index][1], snp.rsid)
                    self.assertEqual(missing_genotypes[index], list(genodata.genotypes))
                    valid_evaluations += 1
                except TooMuchMissing as e:
                    missing += 1
                except InvalidFrequency as e:
                    freq += 1

            index += 1
        self.assertEqual(1, missing)
        self.assertEqual(0, freq)
        self.assertEqual(6, valid_evaluations)
        self.assertEqual(7, index)
class TestWithFewIndividuals(TestBase):
    def testWithFewIndividuals(self):
        pc = PhenoCovar()
        ped_parser = PedigreeParser(self.map_filename, self.miniped_filename)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)

        mapdata = libgwas.get_lines(self.map_filename, split=True)
        genotypes = [
            [0, 1, 0],
            [1, 1, 0],
            [0, 2, 1],
            [0, 1, 1],
            [1, 0, 1],
            [1, 0, 1],
            [0, 1, 1]
        ]
        index = 0
        missing = 0
        freq = 0
        for snp in ped_parser:
            for y in pc:
                (pheno, covars, nonmissing) = y.get_variables(snp.missing_genotypes)
                try:
                    genodata = snp.get_genotype_data(nonmissing)
                    self.assertEqual(int(mapdata[index][0]), snp.chr)
                    self.assertEqual(int(mapdata[index][3]), snp.pos)
                    self.assertEqual(mapdata[index][1], snp.rsid)
                    self.assertEqual(genotypes[index], list(genodata.genotypes))
                except TooMuchMissing as e:
                    missing += 1
                except InvalidFrequency as e:
                    freq += 1
            index += 1
        self.assertEqual(0, missing)
        self.assertEqual(0, freq)
        self.assertEqual(7, index)

class TestMapFile(TestBase):
    def testInitialization(self):
        self.assertEqual(self.map_filename, self.ped_parser.mapfile)
        self.assertEqual(self.ped_filename, self.ped_parser.datasource)
        self.assertEqual(0, len(self.ped_parser.markers))
        self.assertEqual(0, len(self.ped_parser.genotypes))
        self.assertEqual(0, len(self.ped_parser.invalid_loci))
        #self.assertEqual(None, self.ped_parser.strand_1)
        #self.assertEqual(None, self.ped_parser.strand_2)

    def testMapFileNoExclusions(self):
        self.ped_parser.load_mapfile()
        self.assertEqual(7, len(self.ped_parser.markers))
        self.assertEqual(7, len(self.ped_parser.snp_mask))
        self.assertEqual(7, self.ped_parser.locus_count)
        chrom = [int(a) for a in "1,1,1,1,2,2,2".split(",")]
        self.assertEqual(chrom, list(self.ped_parser.markers[:, 0]))
        self.assertEqual("rs0001", self.ped_parser.rsids[0])
        self.assertEqual("rs0005", self.ped_parser.rsids[4])
        self.assertEqual("rs0007", self.ped_parser.rsids[6])
        self.assertEqual([500, 10000, 25000, 45000, 750, 10000, 25000], list(self.ped_parser.markers[:, 1]))
        # Masks are filters, so we should have 7 entries, but none will be 1
        self.assertEqual(0, numpy.sum(self.ped_parser.snp_mask))

    def testMap3File(self):
        ped_parser = PedigreeParser(self.map3_filename, self.ped_filename)
        ped_parser.load_mapfile(map3=True)
        self.assertEqual(7, len(ped_parser.markers))
        self.assertEqual(7, len(ped_parser.snp_mask))
        self.assertEqual(7, ped_parser.locus_count)
        chrom = [int(a) for a in "1,1,1,1,2,2,2".split(",")]
        self.assertEqual(chrom, list(ped_parser.markers[:, 0]))
        self.assertEqual("rs0001", ped_parser.rsids[0])
        self.assertEqual("rs0005", ped_parser.rsids[4])
        self.assertEqual("rs0007", ped_parser.rsids[6])
        self.assertEqual([500, 10000, 25000, 45000, 750, 10000, 25000], list(ped_parser.markers[:, 1]))
        # Masks are filters, so we should have 7 entries, but none will be 1
        self.assertEqual(0, numpy.sum(ped_parser.snp_mask))

    def testMapFileWithChromExclusion(self):
        DataParser.boundary = BoundaryCheck()
        BoundaryCheck.chrom = 2
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename)
        ped_parser.load_mapfile()
        self.assertEqual(3, len(ped_parser.markers))
        self.assertEqual(7, len(ped_parser.snp_mask))
        self.assertEqual(3, ped_parser.locus_count)
        # Masks are filters, so we should have 7 entries, but 4 will be 1
        self.assertEqual(4, numpy.sum(ped_parser.snp_mask[:,0]))
        self.assertEqual(0, ped_parser.snp_mask[4,1])
        self.assertEqual(0, ped_parser.snp_mask[5,0])
        self.assertEqual(0, ped_parser.snp_mask[6,0])


    def testMapFileWithRegionExclusion(self):
        BoundaryCheck.chrom = 2
        DataParser.boundary = BoundaryCheck(bp=[0, 25000])
        DataParser.boundary.LoadExclusions(snps=["rs0007"])
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename)
        ped_parser.load_mapfile()
        self.assertEqual(2, len(ped_parser.markers))
        self.assertEqual(7, len(ped_parser.snp_mask[:,0]))
        self.assertEqual(2, ped_parser.locus_count)
        # Masks are filters, so we should have 7 entries, but 4 will be 1
        self.assertEqual(5, numpy.sum(ped_parser.snp_mask[:,1]))
        self.assertEqual(0, ped_parser.snp_mask[4,1])
        self.assertEqual(0, ped_parser.snp_mask[5,0])


    def testMapFileWithRegionAndSnpExclusion(self):
        BoundaryCheck.chrom = 2
        DataParser.boundary = BoundaryCheck(bp=[0, 10000])
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename)
        ped_parser.load_mapfile()
        self.assertEqual(2, len(ped_parser.markers))
        self.assertEqual(7, len(ped_parser.snp_mask[:,0]))
        self.assertEqual(2, ped_parser.locus_count)
        # Masks are filters, so we should have 7 entries, but 4 will be 1
        self.assertEqual(5, numpy.sum(ped_parser.snp_mask[:,0]))
        self.assertEqual(0, ped_parser.snp_mask[4,1])
        self.assertEqual(0, ped_parser.snp_mask[5,0])

    def testMapFileWithSnpBoundary(self):
        BoundaryCheck.chrom = 1
        DataParser.boundary = SnpBoundaryCheck(snps=["rs0001-rs0003"])
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename)
        ped_parser.load_mapfile()
        self.assertEqual(3, len(ped_parser.markers))
        self.assertEqual(7, len(ped_parser.snp_mask))
        self.assertEqual(3, ped_parser.locus_count)
        # Masks are filters, so we should have 7 entries, but 4 will be 1
        self.assertEqual(4, numpy.sum(ped_parser.snp_mask[:,0]))
        self.assertEqual(0, ped_parser.snp_mask[0,0])
        self.assertEqual(0, ped_parser.snp_mask[1,1])
        self.assertEqual(0, ped_parser.snp_mask[2,1])

    def testMapFileWithSnpExclusions(self):
        BoundaryCheck.chrom = 1
        DataParser.boundary = SnpBoundaryCheck(snps=["rs0001-rs0004"])
        DataParser.boundary.LoadExclusions(snps=["rs0002", "rs0004"])
        ped_parser = PedigreeParser(self.map_filename, self.ped_filename)

        ped_parser.load_mapfile()
        self.assertEqual(2, len(ped_parser.markers))
        self.assertEqual(7, len(ped_parser.snp_mask))
        self.assertEqual(2, ped_parser.locus_count)
        # Masks are filters, so we should have 7 entries, but 4 will be 1
        self.assertEqual(5, numpy.sum(ped_parser.snp_mask[:,0]))
        self.assertEqual(0, ped_parser.snp_mask[0,0])
        self.assertEqual(1, ped_parser.snp_mask[1,0])
        self.assertEqual(0, ped_parser.snp_mask[2,1])
        self.assertEqual(1, ped_parser.snp_mask[3,1])

class TestMapFileNegPos(TestBase):
    def testPedNegativePositions(self):
        pc = PhenoCovar()
        ped_parser = PedigreeParser(self.map_miss_filename, self.ped_filename)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)

        mapdata = libgwas.get_lines(self.map_filename, split=True)

        index = 2
        for snp in ped_parser:
            for y in pc:
                (pheno, covars, nonmissing) = y.get_variables(snp.missing_genotypes)
                try:
                    genodata = snp.get_genotype_data(nonmissing)
                    self.assertEqual(int(mapdata[index][0]), snp.chr)
                    self.assertEqual(int(mapdata[index][3]), snp.pos)
                    self.assertEqual(mapdata[index][1], snp.rsid)
                    self.assertEqual(self.genotypes[index], list(genodata.genotypes))
                except TooMuchMissing as e:
                    pass
                except InvalidFrequency as e:
                    pass
            index += 1
        self.assertEqual(7, index)

    def testPedNegativePositionsOtherChrom(self):
        BoundaryCheck.chrom = 2
        pc = PhenoCovar()
        ped_parser = PedigreeParser(self.map_miss_filename, self.ped_filename)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)

        mapdata = libgwas.get_lines(self.map_filename, split=True)

        index = 4
        for snp in ped_parser:
            for y in pc:
                (pheno, covars, nonmissing) = y.get_variables(snp.missing_genotypes)
                try:
                    genodata = snp.get_genotype_data(nonmissing)
                    self.assertEqual(int(mapdata[index][0]), snp.chr)
                    self.assertEqual(int(mapdata[index][3]), snp.pos)
                    self.assertEqual(mapdata[index][1], snp.rsid)
                    self.assertEqual(self.genotypes[index], list(genodata.genotypes))
                except TooMuchMissing as e:
                    pass
                except InvalidFrequency as e:
                    pass

            index += 1

        self.assertEqual(7, index)

    def testPedNegativePositionsLocalChrom(self):
        BoundaryCheck.chrom = 1
        pc = PhenoCovar()
        ped_parser = PedigreeParser(self.map_miss_filename, self.ped_filename)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)

        mapdata = libgwas.get_lines(self.map_filename, split=True)

        index = 2
        for snp in ped_parser:
            for y in pc:
                (pheno, covars, nonmissing) = y.get_variables(snp.missing_genotypes)
                try:
                    genodata = snp.get_genotype_data(nonmissing)
                    self.assertEqual(int(mapdata[index][0]), snp.chr)
                    self.assertEqual(int(mapdata[index][3]), snp.pos)
                    self.assertEqual(mapdata[index][1], snp.rsid)
                    self.assertEqual(self.genotypes[index], list(genodata.genotypes))
                except TooMuchMissing as e:
                    pass
                except InvalidFrequency as e:
                    pass

            index += 1
        self.assertEqual(4, index)

    def testPedNegativePosLocalChromMissSNP(self):
        BoundaryCheck.chrom = 1
        DataParser.boundary.LoadExclusions(snps=["rs0004"])

        pc = PhenoCovar()
        ped_parser = PedigreeParser(self.map_miss_filename, self.ped_filename)
        ped_parser.load_mapfile()
        ped_parser.load_genotypes(pc)

        mapdata = libgwas.get_lines(self.map_filename, split=True)

        index = 2
        for snp in ped_parser:
            for y in pc:
                (pheno, covars, nonmissing) = y.get_variables(snp.missing_genotypes)
                try:
                    genodata = snp.get_genotype_data(nonmissing)
                    self.assertEqual(int(mapdata[index][0]), snp.chr)
                    self.assertEqual(int(mapdata[index][3]), snp.pos)
                    self.assertEqual(mapdata[index][1], snp.rsid)
                    self.assertEqual(self.genotypes[index], list(genodata.genotypes))
                except TooMuchMissing as e:
                    pass
                except InvalidFrequency as e:
                    pass

            index += 1
        self.assertEqual(3, index)

if __name__ == "__main__":
    unittest.main()
