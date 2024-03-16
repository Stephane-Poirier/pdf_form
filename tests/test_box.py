import unittest
from box import BoxFormats, Box, horizontal_overlapping, vertical_overlapping

class TestBox(unittest.TestCase):

    def test_create(self):
        # create empty box
        bx = Box(BoxFormats.EMPTY)
        self.assertEqual((bx.top, bx.bottom, bx.left, bx.right), (-1, -1, -1, -1))
        self.assertTrue(bx.is_empty())

        # create box from TBLR tuple
        bx_tuple = (30, 40, 50, 60)
        bx2 = Box(BoxFormats.TUPLE_TBLR, bx_tuple)
        self.assertEqual((bx2.top, bx2.bottom, bx2.left, bx2.right), bx_tuple)
        self.assertFalse(bx2.is_empty())
        # create box from Left, Top, Width, Height tuple
        bx3 = Box(BoxFormats.TUPLE_LTWH, bx_tuple)
        self.assertEqual((bx3.top, bx3.bottom, bx3.left, bx3.right), (bx_tuple[1], bx_tuple[1] + bx_tuple[3] - 1,
                                                                      bx_tuple[0], bx_tuple[0] + bx_tuple[2] - 1))
        # create box from another box
        bx4 = Box(BoxFormats.BOX_CLASS, box_class=bx3)
        self.assertEqual("{}".format(bx4), "{}".format(bx3))

    def test_union(self):
        bx1_tuple = (30, 40, 50, 70)
        bx1 = Box(BoxFormats.TUPLE_TBLR, bx1_tuple)

        bx2_tuple = (35, 50, 45, 65)
        bx2 = Box(BoxFormats.TUPLE_TBLR, bx2_tuple)

        bx1.union(bx2)
        self.assertEqual((bx1.top, bx1.bottom, bx1.left, bx1.right),
                          (min(bx1.top, bx2.top), max(bx1.bottom, bx2.bottom),
                           min(bx1.left, bx2.left), max(bx1.right, bx2.right)))

    def test_span(self):
        bx_tuple = (35, 50, 45, 65)
        bx = Box(BoxFormats.TUPLE_TBLR, bx_tuple)
        self.assertEqual(bx.get_horizontal_span(), bx_tuple[3] - bx_tuple[2] + 1)
        self.assertEqual(bx.get_vertical_span(), bx_tuple[1] - bx_tuple[0] + 1)

    def test_overlapp(self):
        bx1_tuple = (30, 40, 50, 60)
        bx1 = Box(BoxFormats.TUPLE_TBLR, bx1_tuple)

        bx2_tuple = (35, 50, 45, 65)
        bx2 = Box(BoxFormats.TUPLE_TBLR, bx2_tuple)

        self.assertEqual(horizontal_overlapping(bx1, bx2),
                         (bx1_tuple[3] - bx1_tuple[2] + 1, 1.0, (bx1_tuple[3] - bx1_tuple[2] + 1) / (bx2_tuple[3] - bx2_tuple[2] + 1)))

        self.assertEqual(vertical_overlapping(bx1, bx2),
                         (bx1_tuple[1] - bx2_tuple[0] + 1, (bx1_tuple[1] - bx2_tuple[0] + 1) / (bx1_tuple[1] - bx1_tuple[0] + 1), (bx1_tuple[1] - bx2_tuple[0] + 1) / (bx2_tuple[1] - bx2_tuple[0] + 1)))


if __name__ == '__main__':
    unittest.main()
