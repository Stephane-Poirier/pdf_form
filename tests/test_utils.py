import unittest
import os
from collections import Counter

# local imports
from utils import get_line_tuple_from_index, is_same_line, get_min_max_line_idx, get_best_count, is_simple_reg_ex_ok, \
    count_objects_by_rows, get_rows_from_selected_rec
import box

class TestUtils(unittest.TestCase):
    def setUp(self) -> None:
        import json
        with open(os.path.join(os.environ["METADOC_ROOT"], "tests", "data_rec.json"), "r") as f:
            self.data_rec = json.load(f)
            box.update_tesseract_rec_with_boxes(self.data_rec)

    def test_lines(self):
        line = (1, 1, 1, 1)
        self.assertEqual(get_line_tuple_from_index(self.data_rec, 4), line)
        self.assertTrue(is_same_line(self.data_rec, 5, line))
        self.assertFalse(is_same_line(self.data_rec, 9, line))

        self.assertEqual(get_min_max_line_idx(self.data_rec, line), (4, 5))

    def test_counting_objects(self):
        idx_list = [(0, [x]) for x in range(20, 100) if self.data_rec["level"][x] == 5]
        h_count = count_objects_by_rows(self.data_rec, idx_list)
        #print(h_count)
        self.assertEqual(h_count[420], 31)
        self.assertEqual(h_count[967], 1)

        expected_h_lines = [(322, 363), (407, 434), (564, 567), (569, 624)]
        h_lines = get_rows_from_selected_rec(self.data_rec, idx_list, threshold=1000, verbose=0)
        self.assertEqual(h_lines, expected_h_lines)

        # test counter functions
        inputCounter = Counter({'red': 5, 'blue': 2, 'green':3})
        self.assertEqual(get_best_count(inputCounter, 2), 'red')
        self.assertEqual(get_best_count(inputCounter, 3), None)

    def test_reg_ex(self):
        search_txt = "toto"
        rec_txt_list = ["toto", "totokk", "tata"]
        expected_res = [True, False, False]
        for (rec, exp) in zip(rec_txt_list, expected_res):
            with self.subTest(rec=rec):
                self.assertEqual(is_simple_reg_ex_ok(search_txt, rec), exp)

        search_txt = "toto*"
        expected_res = [True, True, False]
        for (rec, exp) in zip(rec_txt_list, expected_res):
            with self.subTest(rec=rec):
                self.assertEqual(is_simple_reg_ex_ok(search_txt, rec), exp)

if __name__ == '__main__':
    unittest.main()