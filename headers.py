
from collections import Counter
import numpy

# local imports
from utils import get_line_tuple_from_index, get_min_max_line_idx, is_same_line, get_best_count, is_simple_reg_ex_ok,\
    count_objects_by_rows
from box import BoxFormats, Box


class ConfigHeader:
    """
    headers as they are found in configuration files
    """
    def __init__(self, cfg_dict):
        self.id = cfg_dict["id"]
        self.search_text = cfg_dict["search_text"].lower()
        self.length = int(cfg_dict["length"])

def find_headers_in_line(hdr_list, data_rec, brut_headers_indexes, headers_line, verbose=0):
    headers_info = []
    list_is_complete = True

    min_line_idx, max_line_idx = get_min_max_line_idx(data_rec, headers_line)

    # first search for headers already found
    for hdr, indexes in zip(hdr_list, brut_headers_indexes):
        cur_info = {"name": hdr.id, "cfg_index": indexes[0]}
        found_data_idx = False
        data_idx = None
        if len(indexes[1]):
            for data_idx in indexes[1]:
                if is_same_line(data_rec, data_idx, headers_line):
                    found_data_idx = True
                    break

        if not found_data_idx:
            for data_idx in range(min_line_idx, max_line_idx+1):
                if data_rec["text"][data_idx].lower().startswith(hdr.search_text):
                    found_data_idx = True
                    break

        if found_data_idx:
            cur_info.update({"rec_index": data_idx, "box": data_rec["box"][data_idx],
                                "conf": data_rec["conf"][data_idx], "text": data_rec["text"][data_idx]})
            if data_idx == min_line_idx: # optimize next search
                min_line_idx += 1
        else:
            list_is_complete = False

        headers_info.append(cur_info)

    if not list_is_complete:
        list_is_complete = True
        headers_list_by_pos = find_headers_by_position(hdr_list, data_rec, brut_headers_indexes, verbose=verbose)
        for (hdr_line, hdr_pos) in zip(headers_info, headers_list_by_pos):
            if 'box' not in hdr_line:
                if 'box' in hdr_pos:
                    for key in hdr_pos:
                        if key not in hdr_line:
                            hdr_line[key] = hdr_pos[key]
                else:
                    list_is_complete = False

    return headers_info, list_is_complete


def find_headers_by_position(hdr_list, data_rec, brut_headers_indexes, verbose=0):
    ratio_hdr_nb = 0.25
    min_hdr_nb = int(ratio_hdr_nb * len(hdr_list))
    headers_info = []
    horizontal_cnt = count_objects_by_rows(data_rec, brut_headers_indexes, use_size=False, verbose=verbose)
    starting_min_h_pos = 1000000
    min_h_pos = starting_min_h_pos
    max_h_pos = -100
    # get main positions
    for pos in horizontal_cnt.most_common():
        if pos[1] < min_hdr_nb:
            break
        else:
            if min_h_pos > pos[0]:
                min_h_pos = pos[0]
            if max_h_pos < pos[0]:
                max_h_pos = pos[0]

    if min_h_pos == starting_min_h_pos:
        print("no headers found")
        return headers_info

    # get positions connected to main positions
    sorted_pos = sorted(list(horizontal_cnt))
    min_index = sorted_pos.index(min_h_pos)
    while min_index > 0 and sorted_pos[min_index-1] == min_h_pos - 1:
        min_h_pos -= 1
        min_index -= 1
    max_index = sorted_pos.index(max_h_pos)
    while max_index < len(sorted_pos)-1 and sorted_pos[max_index+1] == max_h_pos + 1:
        max_h_pos += 1
        max_index += 1

    # first search for headers already found
    for hdr, indexes in zip(hdr_list, brut_headers_indexes):
        cur_info = {"name": hdr.id, "cfg_index": indexes[0]}
        found_data_idx = False
        data_idx = None
        if len(indexes[1]):
            for data_idx in indexes[1]:
                min_idx = data_rec["box"][data_idx].top
                if min_h_pos <= min_idx <= max_h_pos:
                    found_data_idx = True
                    break
                max_idx = data_rec["box"][data_idx].bottom
                if min_idx < min_h_pos <= max_idx:
                    found_data_idx = True
                    break
            if found_data_idx:
                cur_info.update({"rec_index": data_idx, "box": data_rec["box"][data_idx],
                                 "conf": data_rec["conf"][data_idx], "text": data_rec["text"][data_idx]})

        headers_info.append(cur_info)
    return headers_info


def resize_headers(headers_list, data_rec, cfg_json, verbose=0):
    """
    Headers are resized to beginning of next header minus margin.
    Positive margin means a gap between headers and negative margin means some covering between headers.
    If next header is not recognized, nothing is done
    Last header is resized to the end of page minus margin
    :param headers_list: list of headers to resize
    :param data_rec: recognition data, to get page size
    :param next_header_margin: margin to use (from config json)
    :param verbose: verbose mode
    :return: nothing
    """
    # resize from next header
    next_header_margin = cfg_json["next_header_margin"]
    for (hdr_c, hdr_n) in zip(headers_list[0:-1], headers_list[1:]):
        if 'box' in hdr_n:
            if 'box' in hdr_c:
                if verbose:
                    print("name: {} begin {} begin next {} length {}".format(hdr_c["name"], hdr_c["box"].left, hdr_n["box"].left, hdr_n["box"].left - hdr_c["box"].left))
                new_right = max(hdr_c['box'].right, hdr_n['box'].left - next_header_margin)
                hdr_c['box'].set_right(new_right)
            else:
                cfg_hdr_c_length = cfg_json["headers"][hdr_c["cfg_index"]].length
                if cfg_hdr_c_length != -1:
                    n_box = hdr_n['box']
                    new_top = n_box.top
                    new_bottom = n_box.bottom
                    new_left = n_box.left - cfg_hdr_c_length
                    new_right = n_box.left - next_header_margin
                    hdr_c['box'] = Box(BoxFormats.TUPLE_TBLR, (new_top, new_bottom, new_left, new_right))
                print("new box for {} : {}".format(hdr_c['name'], hdr_c['box']))
                #print("new box for {} : ".format(hdr_c['name']))
    # last header
    hdr_c = headers_list[-1]
    if 'box' in hdr_c:
        hdr_n_box = data_rec['box'][0]
        if verbose:
            print("name: {} begin {} begin next {} lenght {}".format(hdr_c["name"], hdr_c["box"].left, hdr_n_box.right,
                                                                 hdr_n_box.right - hdr_c["box"].left))

        new_right = max(hdr_c['box'].right, hdr_n_box.right - next_header_margin)
        hdr_c['box'].set_right(new_right)

    # resize from configured length
    for (hdr_rec, hdr_cfg) in zip(headers_list, cfg_json["headers"]):
        if 'box' in hdr_rec:
            # rec is too small
            if hdr_rec['box'].left + hdr_cfg.length + 1 > hdr_rec['box'].right:
                hdr_rec['box'].set_right(hdr_rec['box'].left + hdr_cfg.length + 1)
            elif hdr_rec['box'].left + hdr_cfg.length + 10 < hdr_rec['box'].right:
                hdr_rec['box'].set_right(hdr_rec['box'].left + hdr_cfg.length + 1)

    return


def search_headers(data_rec, cfg_json, resize_hdr=False, verbose=0):
    """
    :param data_rec: data dictionary of recognition
    :param cfg_json: json of configuration for this type of document
    :param verbose: verbose mode in int
    :return: return headers of package table in same format as data_rec
    """
    min_diff_found_in_lines = 5
    hdr_txt_list = [x.search_text for x in cfg_json["headers"]]
    lower_rec_txt = [str(x).lower() for x in data_rec["text"]]
    brut_headers_indexes = []
    line_cnt = Counter()
    for cfg_ind, txt in enumerate(hdr_txt_list):
        rec_ind_list = []
        for rec_ind, rec_txt in enumerate(lower_rec_txt):
            if is_simple_reg_ex_ok(txt, rec_txt):
                rec_ind_list.append(rec_ind)
                line_cnt[get_line_tuple_from_index(data_rec, rec_ind)] += 1

        brut_headers_indexes.append((cfg_ind, rec_ind_list))
        if verbose:
            print("header {} of index {} recognised in {} positions".format(txt, cfg_ind, rec_ind_list))

    if verbose:
        print("headers txt found on lines {}".format(line_cnt))

    if line_cnt:
        headers_line = get_best_count(line_cnt, min_diff_found_in_lines)
        if headers_line:
            headers_list, list_is_complete = find_headers_in_line(cfg_json["headers"], data_rec, brut_headers_indexes, headers_line, verbose=verbose)
        else:
            headers_list = find_headers_by_position(cfg_json["headers"], data_rec, brut_headers_indexes, verbose=verbose)
    else:
        headers_list = []

    if resize_hdr and headers_list and "next_header_margin" in cfg_json and cfg_json["next_header_margin"] is not None:
        resize_headers(headers_list, data_rec, cfg_json, verbose=verbose)

    return headers_list


def get_angle_from_headers_line(data_rec, cfg_json, verbose=0):
    angle = 0.0 # in degrees
    r_l = l_l = -1
    r_t = l_t = -1
    headers_list = search_headers(data_rec, cfg_json, resize_hdr=False, verbose=verbose)
    for hdr in headers_list:
        if "box" in hdr:
            l_l, l_t = hdr["box"].left, hdr["box"].top
            break
    for hdr in reversed(headers_list):
        if "box" in hdr:
            r_l, r_t = hdr["box"].left, hdr["box"].top
            break

    if r_l > l_l:
        angle = numpy.degrees(numpy.arctan2(r_t-l_t, r_l-l_l))
    return angle
