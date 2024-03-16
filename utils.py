
from collections import Counter


def get_line_tuple_from_index(data_rec, index):
    """
    :param data_rec: recognition results in tesseract format
    :param index: index of object to analyse
    :return: line tuple of index object
    """
    return (data_rec["page_num"][index], data_rec["block_num"][index],
                      data_rec["par_num"][index], data_rec["line_num"][index])


def is_same_line(data_rec, index, line):
    """
    :param data_rec: recognition results in tesseract format
    :param index: index of object to analyse
    :param line: line in tuple format (page num, block num, paragraph num, line num)
    :return: True if lines are equal, False otherwise
    """
    line_tuple = get_line_tuple_from_index(data_rec, index)
    return line_tuple == line


def get_min_max_line_idx(data_rec, line):
    """
    get min and max indexes in data_rec reco for words that are in given line
    :param data_rec: recognition results in tesseract format
    :param line: line in tuple format (page num, block num, paragraph num, line num)
    :return: tuple min, ma  x indexes
    """
    min_line_idx = -1
    max_line_idx = -1
    for idx, lvl in enumerate(data_rec["level"]):
        if lvl >= 5: # word level
            if is_same_line(data_rec, idx, line):
                if min_line_idx == -1:
                    min_line_idx = idx
                max_line_idx = idx
    return min_line_idx, max_line_idx


def get_best_count(line_cnt, min_diff):
    """
    get key of mostly present object in a Counter
    :param line_cnt: input counter
    :param min_diff: minimal difference between first and second objects to decide
    :return: None if difference between two first objects is less than min_diff
    """
    headers_line = None
    lines = line_cnt.most_common(2)
    if len(lines) > 1 and lines[0][1] >= lines[1][1] + min_diff:
        headers_line = lines[0][0]
    elif len(lines) == 1 and lines[0][1] >= min_diff:
        headers_line = lines[0][0]

    return headers_line


def is_simple_reg_ex_ok(search_txt, rec_txt):
    """
    search if recognized text maatch with a simple system of regular expression
    :param search_txt: reg exp to search
    :param rec_txt: recognized text
    :return: Boolean True if match is ok
    """
    if search_txt[-1] == '*':
        brut_txt = search_txt[:-1]
        return rec_txt.startswith(brut_txt)
    elif search_txt == rec_txt:
        return True
    else:
        return False


def count_objects_by_rows(data_rec, indexes_any_rec, use_size=False, verbose=0):
    """
    count objects in the recognition structure and list of indexes by rows
    :param data_rec: recognition results in tesseract format
    :param indexes_any_rec: list of indexes to consider
    :param use_size: use horizontal length of object (if True) or one by object (if False [default])
    :param verbose: verbose mode
    :return: a counter with pixel rows values as keys
    """
    horizontal_cnt = Counter()
    for indexes in indexes_any_rec:
        for data_idx in indexes[1]:
            top = data_rec["box"][data_idx].top
            bottom = data_rec["box"][data_idx].bottom
            cnt = data_rec["box"][data_idx].get_horizontal_span() if use_size else 1
            for h in range(top, bottom+1):
                horizontal_cnt[h] += cnt
    if verbose:
        print("horizontal count of selected objects : {}".format(horizontal_cnt))

    return horizontal_cnt


def get_rows_from_selected_rec(data_rec, indexes_any_rec, threshold=1, verbose=0):
    """
    get pixels rows concerned by a list of indexes, use horizontal size to count objects and threshold to filter
    :param data_rec: recognition results in tesseract format
    :param indexes_any_rec: list of indexes to consider
    :param threshold: threshold to consider a pixel row
    :param verbose: verbose mode
    :return: a list of rows, each one is a tuple (begin, end) in pixels
    """
    h_lines_begin_end = []
    horiz_count = count_objects_by_rows(data_rec, indexes_any_rec, use_size=True, verbose=verbose)
    sorted_h_pos = sorted([hz_pos for hz_pos in horiz_count if horiz_count[hz_pos] >= threshold])
    begin = last = end = sorted_h_pos[0]
    for h in sorted_h_pos[1:]:
        if h == last + 1:
            end = h
        else:
            h_lines_begin_end.append((begin, end))
            begin = end = h
        last = h
    # last line is not
    h_lines_begin_end.append((begin, end))
    return h_lines_begin_end
