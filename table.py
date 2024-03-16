
from box import BoxFormats, Box

class Type:
    """
    Different types of objects that can be found in tables
    Can be used for word, cell or line type
    HEADER : for headers of rows and columns
    PACKAGE : for a line containing package information
    ADDRESS : object dedicated to address information
    WEIGHT : object dedicated to package weight information
    INT : object dedicated to integer information
    STR : object dedicated to string information
    UNKNOWN : object with non specifed information
    """
    HEADER = "header"
    PACKAGE = "package"
    ADDRESS = "address"
    WEIGHT = "weight"
    INT = "int"
    STR = "str"
    UNKNOWN = "unknown"


class Word:
    """
    Recognised words in cells
    """
    def __init__(self, info_dict, type: Type):
        """
        Constructor
        :param info_dict: recognition information (dictionary)
        :param type: type of word (Type)
        """
        self.type = type
        self.box = Box(BoxFormats.EMPTY)
        self.value = None
        self.score = 0.0

        if "box" in info_dict:
            self.box = Box(BoxFormats.BOX_CLASS, box_class=info_dict["box"])
        if "conf" in info_dict:
            self.score = float(info_dict["conf"])
        if "text" in info_dict:
            self.value = info_dict["text"]

class Cell:
    """
    Cell inside a Table
    """
    def __init__(self, info_dict, is_header=False):
        """
        Constructor
        :param info_dict: recognition information (dictionary)
        :param is_header: is the new cell a header cell (boolean)
        """
        self.type = Type.UNKNOWN
        self.box = Box(BoxFormats.EMPTY)
        self.value = None
        self.score = 0.0
        self.words = []

        if "box" in info_dict:
            self.box = Box(BoxFormats.BOX_CLASS, box_class=info_dict["box"])
        if is_header:
            self.type = Type.HEADER
            self.value = info_dict["name"]  # force standard name, and not recognized

        self.words.append(Word(info_dict, Type.UNKNOWN))
        self.words.sort(key=lambda x: x.box.left)

    def __str__(self):
        """
        :return: string representation of a Cell object
        """
        if self.type == Type.HEADER:
            return "{self.value}".format(self=self)
        else:
            rtn = ""
            first = True
            for w in self.words:
                if first:
                    first = False
                else:
                    rtn += " "
                rtn += "{}".format(w.value)
            return rtn

    def add_word(self, info_dict):
        """
        Add a new word in a cell
        :param info_dict: recognition information of the new word (dictionary)
        :return:
        """
        new_word = Word(info_dict, Type.UNKNOWN)
        # next line should verify positions
        self.words.append(new_word)
        self.box.union(new_word.box)


class Line:
    """
    row or column line in a Table
    """
    def __init__(self, is_row=False, is_header_line=False, cells_list=None, type=Type.UNKNOWN):
        """
        Constructor
        :param is_row: is this a row (True) or a column (False) (boolean) (default False)
        :param is_header_line: is this a header line (True) (boolean) (default False)
        :param cells_list: list of cells to insert in line
        :param type: type of line (Type)
        """
        self.isRow = is_row
        self.type = type
        if is_header_line:
            self.type = Type.HEADER
        self.box = Box(BoxFormats.EMPTY)
        self.cells = []

        if cells_list:
            for cell in cells_list:
                self.cells.append(cell)
                if cell:
                    self.box.union(cell.box)

    def get_csv_string(self, separator=","):
        """
        get csv string for a line object
        :param separator: separator to use between cells
        :return: a string with str value of each cell separated by separator
        """
        out_csv = ""
        first = True
        for cell in self.cells:
            if first:
                first = False
            else:
                out_csv += separator
            if cell:
                out_csv += str(cell)

        return out_csv

class Table:
    """Tables with headers
    ...
    Attributes
    box : position of table object in image (Box object)
    rows : list of rows in the Table object
    columns : list of columns in the Table object

    Methods

    """
    def __init__(self, headers_list=None, headers_of_columns=True):
        """
        Constructor
        :param headers_list: list of headers to insert in first line
        :param headers_of_columns: given headers for columns and then create a row (boolean) (default True)
        """
        # default values for object
        self.box = Box(BoxFormats.EMPTY)
        self.rows = []
        self.columns = []

        # constructed from headers
        if headers_list:
            cells_list = []
            for hdr in headers_list:
                hdr_cell = Cell(hdr, is_header=True)
                cells_list.append(hdr_cell)
            if headers_of_columns:  # in this case the headers are in a row
                n_line = Line(is_row=True, is_header_line=True, cells_list=cells_list)
                self.rows.append(n_line)
                for cell in cells_list:
                    o_line = Line(is_row=False, is_header_line=False, cells_list=[cell])
                    self.columns.append(o_line)
            else:  # in this case the headers are in a column
                n_line = Line(is_row=False, is_header_line=True, cells_list=cells_list)
                self.columns.append(n_line)
                for cell in cells_list:
                    o_line = Line(is_row=True, is_header_line=False, cells_list=[cell])
                    self.rows.append(o_line)
            self.box.union(n_line.box)
        else:
            print("No headers list given, empty table created")

    def get_nb_columns(self):
        """
        :return: number of columns in the table
        """
        return len(self.columns)

    def get_nb_rows(self):
        """
        :return: number of rows in the table
        """
        return len(self.rows)

    def search_rec_in_headed_columns(self, data_rec):
        """
        search for columns that contain recognised elements that are under headers
        :param data_rec: data recognition structure in tesseract format
        :return: list of tuples (column index, list of recognition indices)
        :note: recognised elements are accepted in a column if they are entirely contained in this column
        """
        idx_col_rec = []
        headers_row = self.rows[0]
        header_bottom = headers_row.box.bottom
        ind_rec_below = [idx for idx, box in enumerate(data_rec["box"]) if box.top >= header_bottom]
        for ind_rec in ind_rec_below:
            if not data_rec["text"][ind_rec]:
                continue
            rec_box = data_rec["box"][ind_rec]
            for idx_col, col in enumerate(self.columns):
                if col.box.left <= rec_box.left \
                        and col.box.right >= rec_box.right:
                    idx_col_rec.append((idx_col, [ind_rec]))
        return idx_col_rec

    def add_new_line_from_idx_rec(self, data_rec, idx_rec_list, is_row, verbose=0):
        """
        add a new line in Table from a list of recognition indices
        :param data_rec: recognition structure in tesseract format
        :param idx_rec_list: list of indices to insert in new line
        :param is_row: is the line a row (boolean)
        :param verbose: verbose mode (int)
        :return:
        """
        if is_row:
            cells_list_for_each_col = [None for i in range(self.get_nb_columns())]
            not_found_idx = []
            at_least_one = False
            for idx in idx_rec_list:
                c_left = data_rec["box"][idx].left
                c_right = data_rec["box"][idx].right
                cols = [idx_c for idx_c, col in enumerate(self.columns) if c_left >= col.box.left and c_right <= col.box.right]
                if len(cols) == 1:
                    c_dict = {'conf': data_rec['conf'][idx], 'text': data_rec['text'][idx], 'box': data_rec['box'][idx]}
                    if not cells_list_for_each_col[cols[0]]:
                        n_cell = Cell(c_dict, False)
                        cells_list_for_each_col[cols[0]] = n_cell
                        at_least_one = True
                    else:
                        if verbose:
                            print("position for text {} already found in cell {}".format(c_dict['text'], cells_list_for_each_col[cols[0]]))
                        cells_list_for_each_col[cols[0]].add_word(c_dict)
                elif len(cols) == 0:
                    not_found_idx.append(idx)
                else:
                    print("ERROR : add_new_line_from_idx_rec : this should not arrive")
            if at_least_one:
                n_line = Line(True, False, cells_list_for_each_col, Type.PACKAGE)
                self.rows.append(n_line)

        else:
            print("ERROR : add_new_line_from_idx_rec for columns is not yet implemented")
        return

    def get_csv_string(self, separator=","):
        """
        get csv string for a table object
        :param separator: separator to use in lines (default ,)
        :return: a string of csv lines separated by \n
        """
        out_csv = ""

        for row in self.rows:
            out_csv += row.get_csv_string(separator)
            out_csv += "\n"
        return out_csv
