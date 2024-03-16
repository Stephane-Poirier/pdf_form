
"""
Contains all usefull code about boxes :
tesseract and pdf formats
class Box
"""

class BoxFormats:
    """
    All box formats used in pdf analysis
    """
    EMPTY = "empty"
    PDF_MINER = "pdf"
    TESSERACT = "tesseract"
    TUPLE_TBLR = "tuple_tblr"
    TUPLE_LTWH = "tuple_ltwr"
    BOX_CLASS = "boxClass"


class Box:
    """Box for position of objects
    ...
    Attributes
    top : upper position of object
    bottom : lower position of object
    left : left position of object
    right : right position of object

    Methods
    """
    def __init__(self, input_format, box_tuple=None, box_class=None):
        if input_format == BoxFormats.EMPTY:
            self.top = self.bottom = self.left = self.right = -1
        elif input_format == BoxFormats.TUPLE_TBLR:
            if box_tuple:
                self.top = box_tuple[0]
                self.bottom = box_tuple[1]
                self.left = box_tuple[2]
                self.right = box_tuple[3]
            else:
                raise Exception("With input_format = BoxFormats.TUPLE_TBLR a 4 values tuple should be given in box_tuple parameter")
        elif input_format == BoxFormats.TUPLE_LTWH:
            if box_tuple:
                self.top = box_tuple[1]
                self.bottom = box_tuple[1] + box_tuple[3] - 1
                self.left = box_tuple[0]
                self.right = box_tuple[0] + box_tuple[2] - 1
            else:
                raise Exception("With input_format = BoxFormats.TUPLE_LTWH a 4 values tuple should be given in box_tuple parameter")
        elif input_format == BoxFormats.BOX_CLASS:
            if box_class:
                self.top = box_class.top
                self.bottom = box_class.bottom
                self.left = box_class.left
                self.right = box_class.right
            else:
                raise Exception("With input_format = BoxFormats.BOX_CLASS a Box object should be given in box_class parameter")
        else:
            raise Exception("Box format {} NOT YET IMPLEMENTED".format(input_format))

    def __str__(self):
        return "({}, {}, {}, {})".format(self.top, self.bottom, self.left, self.right)

    def __repr__(self):
        return self.__str__()

    def is_empty(self):
        """
        :return: True if box is empty False elsewhere
        """
        if self.top == -1 and self.bottom == -1 and self.left == -1 and self.right == -1:
            return True
        else:
            return False

    # setters
    def set_top(self, n_val):
        """
        set top value to n_val
        :param n_val: integer value
        :return: Nothing
        """
        self.top = n_val

    def set_bottom(self, n_val):
        """
        set bottom value to n_val
        :param n_val: integer value
        :return: Nothing
        """
        self.bottom = n_val

    def set_left(self, n_val):
        """
        set left value to n_val
        :param n_val: integer value
        :return: Nothing
        """
        self.left = n_val

    def set_right(self, n_val):
        """
        set right value to n_val
        :param n_val: integer value
        :return: Nothing
        """
        self.right = n_val

    def union(self, u_box):
        """
        makes union of boxes of current object with another Box object (modify current)
        :param u_box: Box object to add to current
        :return:
        """
        if u_box.is_empty():
            # do nothing
            return
        elif self.is_empty():
            # copy new box
            self.top = u_box.top
            self.bottom = u_box.bottom
            self.left = u_box.left
            self.right = u_box.right
        else:
            if self.top > u_box.top:
                self.top = u_box.top
            if self.bottom < u_box.bottom:
                self.bottom = u_box.bottom
            if self.left > u_box.left:
                self.left = u_box.left
            if self.right < u_box.right:
                self.right = u_box.right

    # getters
    def get_horizontal_span(self):
        """
        :return: number of horizontal pixels in the box (right - left + 1)
        """
        return self.right - self.left + 1

    def get_vertical_span(self):
        """
        :return: number of vertical pixels in the box (bottom - top + 1)
        """
        return self.bottom - self.top + 1

def update_tesseract_rec_with_boxes(data_rec):
    """
    Update data_rec dictionary created by tesseract with a box list of key value box
    :param data_rec: tesseract structure
    :return:
    """
    data_rec["box"] = []
    nb_obj = len(data_rec["left"])
    for idx in range(nb_obj):
        data_rec["box"].append(Box(BoxFormats.TUPLE_LTWH,
                                   (data_rec["left"][idx], data_rec["top"][idx], data_rec["width"][idx], data_rec["height"][idx])))

    return


def horizontal_overlapping(box1: Box, box2: Box):
    """
    Compute horizontal overlapping between box1 and box2
    :param box1: first box
    :param box2: second box
    :return: overlapping tuple (nb pixels in common, ratio of first box, ratio of second box)
    """
    overlap = min(box1.right, box2.right) - max(box1.left, box2.left) + 1
    if overlap <= 0:
        return (0, 0, 0)
    else:
        return (overlap, overlap / box1.get_horizontal_span(), overlap / box2.get_horizontal_span())


def vertical_overlapping(box1: Box, box2: Box):
    """
    Compute vertical overlapping between box1 and box2
    :param box1: first box
    :param box2: second box
    :return: overlapping tuple (nb pixels in common, ratio of first box, ratio of second box)
    """
    overlap = min(box1.bottom, box2.bottom) - max(box1.top, box2.top) + 1
    if overlap <= 0:
        return (0, 0, 0)
    else:
        return (overlap, overlap / box1.get_vertical_span(), overlap / box2.get_vertical_span())
