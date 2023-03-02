import tempfile
import unittest

from energyplus_regressions.diffs.mycsv import (
    MyCsv,
    BadInput,
    BadMatrice,
    readcsv,
    writecsv,
    ismatrice,
    transpose2d,
    getlist,
)


class TestExceptions(unittest.TestCase):

    def test_mycsv_is_exception(self):
        self.assertIsInstance(MyCsv(), Exception)

    def test_bad_input_is_exception(self):
        self.assertIsInstance(BadInput(), Exception)

    def test_bad_matrice_is_exception(self):
        self.assertIsInstance(BadMatrice(), Exception)


class TestReadCSV(unittest.TestCase):

    def test_reading_from_file_passes(self):
        csv_file = tempfile.mkstemp(suffix='.csv')[1]
        with open(csv_file, 'w') as f_csv:
            f_csv.write('header_col_1,header_col_2\n')
            f_csv.write('2_1,2_2\n')
            f_csv.write('31,32\n')
            f_csv.write('4.1,4.2\n')
        response = readcsv(csv_file)
        self.assertEqual(4, len(response))
        for row in response:
            self.assertEqual(2, len(row))

    def test_reading_from_string_passes(self):
        csv_string = 'header_col_1,header_col_2\n2_1,2_2\n31,32\n'
        response = readcsv(csv_string)
        self.assertEqual(3, len(response))
        for row in response:
            self.assertEqual(2, len(row))

    def test_reading_from_else_fails(self):
        with self.assertRaises(BadInput):
            readcsv(['hey'])


class TestWriteCSV(unittest.TestCase):

    def test_valid_write_to_file(self):
        this_matrix = [
            ['hi', 'bye'],
            [1, 2],
            [3.14159, 2.71828]
        ]
        csv_file = tempfile.mkstemp(suffix='.csv')[1]
        writecsv(this_matrix, csv_file)  # should just successfully write, no need to re-read it

    def test_valid_write_to_string(self):
        this_matrix = [
            [u'hi', u'bye'],
            [1, 2],
            [3.14159, 2.71828]
        ]
        out_string = writecsv(this_matrix)
        self.assertIsInstance(out_string, str)

    def test_invalid_matrix_fails(self):
        with self.assertRaises(BadMatrice):
            writecsv(0)


class TestIsMatrice(unittest.TestCase):

    def test_valid_matrix_floats(self):
        this_matrix = [
            [1.2, 2.1, 3.1],
            [9.9, 2.4, 5.1]
        ]
        self.assertTrue(ismatrice(this_matrix))

    def test_valid_matrix_ints(self):
        this_matrix = [
            [1, 2, 3],
            [9, 2, 5]
        ]
        self.assertTrue(ismatrice(this_matrix))

    def test_valid_matrix_strings(self):
        this_matrix = [
            ['1.2', '2.1', '3.1'],
            ['9.9', '2.4', '5.1']
        ]
        self.assertTrue(ismatrice(this_matrix))

    def test_valid_matrix_mixed(self):
        this_matrix = [
            ['1.2', 2.1, 3],
            [9, '2.4', 5.1]
        ]
        self.assertTrue(ismatrice(this_matrix))

    def test_invalid_matrix_not_iterable(self):
        self.assertFalse(ismatrice(3))

    def test_invalid_matrix_rows_are_not_lists(self):
        self.assertFalse(ismatrice([1, 2, 3]))
        self.assertFalse(ismatrice('im_also_iterable'))

    def test_invalid_matrix_data_is_invalid(self):
        this_matrix = [
            ['1.2', '2.1', '3.1'],
            ['9.9', ['uh-oh'], '5.1']
        ]
        self.assertFalse(ismatrice(this_matrix))


class TestTranspose(unittest.TestCase):

    def test_valid_transpose(self):
        this_matrix = [
            [1.2, 2.1, 3.1],
            [9.9, 2.4, 5.1]
        ]
        self.assertEqual(2, len(this_matrix))
        self.assertEqual(5.1, this_matrix[1][2])
        transposed = transpose2d(this_matrix)
        self.assertTrue(ismatrice(transposed))
        self.assertEqual(3, len(transposed))
        self.assertEqual(5.1, transposed[2][1])


class TestGetList(unittest.TestCase):

    def test_get_list_one_column(self):
        csv_string = 'header_col_1\n2_1\n2_2\n31\n32\n'
        response = getlist(csv_string)
        self.assertIsInstance(response, list)
        self.assertEqual(5, len(response))
        for row in response:
            self.assertIsInstance(row, str)

    def test_get_list_two_columns(self):
        csv_string = 'header_col_1,header_col_2\n2_1,2_2\n31,32\n'
        response = getlist(csv_string)
        self.assertIsInstance(response, list)
        self.assertEqual(3, len(response))
        for row in response:
            self.assertIsInstance(row, list)

    def test_get_list_one_column_with_extra_whitespace(self):
        csv_string = 'header_col_1 \n2_1\n2_2\n31\n32\n'
        response = getlist(csv_string)
        self.assertIsInstance(response, list)
        self.assertEqual(5, len(response))
        for row in response:
            self.assertIsInstance(row, str)

        self.assertEqual(response[0], 'header_col_1')

    def test_get_list_two_columns_with_extra_whitespace(self):
        csv_string = 'header_col_1 ,header_col_2 \n2_1,2_2\n31,32\n'
        response = getlist(csv_string)
        self.assertIsInstance(response, list)
        self.assertEqual(3, len(response))
        for row in response:
            self.assertIsInstance(row, list)

        self.assertEqual(response[0][0], 'header_col_1')
        self.assertEqual(response[0][1], 'header_col_2')
