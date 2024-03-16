from PyPDF4 import PdfFileReader, PdfFileWriter
from pdf2image import convert_from_path
import pytesseract
from tempfile import NamedTemporaryFile

## local import
from table import Table
import utils
from box import update_tesseract_rec_with_boxes

#print("TESSDATA_PREFIX : {}".format(os.environ["TESSDATA_PREFIX"]))
#print(" cur directory : {}".format(os.getcwd()))


def extract_information(pdf_path):
    with open(pdf_path, 'rb') as f:
        pdf = PdfFileReader(f)
        information = pdf.getDocumentInfo()
        number_of_pages = pdf.getNumPages()

    txt = f"""
    Information about {pdf_path}: 

    Author: {information.author}
    Creator: {information.creator}
    Producer: {information.producer}
    Subject: {information.subject}
    Title: {information.title}
    Number of pages: {number_of_pages}
    """

    print(txt)
    return information


def image_improvement(img_orig, data_rec, cfg_json):
    from headers import get_angle_from_headers_line
    from PIL import Image, ImageMorph, ImageFilter
    from PIL.ImageMorph import LutBuilder, MorphOp

    new_image = img_orig
    cur_angle = get_angle_from_headers_line(data_rec, cfg_json, verbose)
    if abs(cur_angle) > 0.5:
        rotated_image = img_orig.rotate(cur_angle, expand=True, fillcolor=(255, 255, 255))
    else:
        rotated_image = img_orig

    if "image_graysacle_opening_coeff" in cfg_json and cfg_json["image_graysacle_opening_coeff"] > 0\
            and cfg_json["image_graysacle_opening_coeff"] <= 1.0:
        coeff = cfg_json["image_graysacle_opening_coeff"]
        gs_image = rotated_image.convert("L")
        if coeff == 1:
            temp_image = gs_image.filter(ImageFilter.MaxFilter(3))
            new_image = temp_image.filter(ImageFilter.MinFilter(3))
        else:
            from PIL import ImageMath
            max_val = 1
            int_coeff = coeff
            while int(int_coeff) != int_coeff:
                max_val *= 10
                int_coeff *= 10
            imageMath_txt = "convert(({} * A + {} * B)/{}, 'L')".format(int(int_coeff), int(max_val-int_coeff), max_val)
            max_image = gs_image.filter(ImageFilter.MaxFilter(3))
            temp_image = ImageMath.eval(imageMath_txt, A=max_image, B=gs_image)
            new_image = ImageMath.eval(imageMath_txt, A=temp_image.filter(ImageFilter.MinFilter(3)), B=temp_image)
        #temp_image.show()
        #new_image.show()
    else:
        new_image = rotated_image.convert("L")
    return new_image


def analyze_data_dict(data_rec, cfg_json, verbose=0):
    from headers import search_headers
    headers_list = search_headers(data_rec, cfg_json, resize_hdr=True, verbose=verbose)
    if not headers_list:
        print("No headers found go to next page")
        return False

    if verbose > 0:
        print("headers : {}".format(headers_list))

    package_table = Table(headers_list, headers_of_columns=True)
    indexes_col_rec_list = package_table.search_rec_in_headed_columns(data_rec)
    horiz_lines = utils.get_rows_from_selected_rec(data_rec, indexes_col_rec_list, threshold=cfg_json["min_pixels_for_a_line"], verbose=verbose)
    for h_line in horiz_lines:
        l_top = h_line[0]
        l_bottom = h_line[1]
        idx_rec_list = [idx for idx, c_box in enumerate(data_rec["box"]) if c_box.top >= l_top and c_box.bottom <= l_bottom]
        #print(idx_rec_list)
        package_table.add_new_line_from_idx_rec(data_rec, idx_rec_list, True, verbose=verbose)

    print("Package table found : ")
    print(package_table.get_csv_string(separator=";"))
    print("----------------")
    return True


def get_config_info(cfg_filename):
    from headers import ConfigHeader
    cfg_json = {}
    if cfg_filename:
        import json
        with open(cfg_filename) as f:
            cfg_json_in = json.load(f)

    # transforms format for some known keys
    for key in cfg_json_in:
        if key == "headers":
            cfg_json[key] = []
            for hdr in cfg_json_in[key]:
                cfg_json[key].append(ConfigHeader(hdr))
        else:
            cfg_json[key] = cfg_json_in[key]
    return cfg_json


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Recognition of pdf file')
    parser.add_argument('-f', '--file', type=str, help='pdf filename without extension')
    parser.add_argument('-c', '--config', type=str, help='config filename', default='')
    parser.add_argument('-v', '--verbose', type=int, default=0, help='verbose mode')

    args = parser.parse_args()
    verbose = args.verbose
    config_filename = args.config
    config_json = get_config_info(config_filename)
    extract_pdf = True
    extract_hocr = True

    if args.file.endswith(".pdf"):
        root_file = args.file[0:-4]
    else:
        root_file = args.file
    path = '{}.pdf'.format(root_file)
    output_path_pdf = '{}_output.pdf'.format(root_file)
    temp_image_path = '{}_temp.png'.format(root_file)
    info = extract_information(path)

    images_list = convert_from_path(path, dpi=300)

    output_pdf = PdfFileWriter()
    output_hocr = []
    for (np, img) in enumerate(images_list):
        print(" computing page {} of {}".format(np+1, len(images_list)))
        # rotate image if necessary
        if "orientation" in config_json:
            width, height = img.size
            if (width < height and config_json["orientation"] == 'landscape') or\
                (width > height and config_json["orientation"] == 'portrait'):
                angle = 90
                img = img.rotate(angle, expand=True)
        #img = img.convert("L")

        #rotated.save(temp_image_path, 'ppm')
        #print(pytesseract.image_to_osd(temp_image_path, lang='fra', output_type=pytesseract.Output.DICT))

        # create tesseract data buffer
        data_dict = pytesseract.image_to_data(img, lang='fra', output_type=pytesseract.Output.DICT)
        update_tesseract_rec_with_boxes(data_dict)
        info_found = False
        if config_json:
            recognition_img = image_improvement(img, data_dict, config_json)
            data_dict = pytesseract.image_to_data(recognition_img, lang='fra', output_type=pytesseract.Output.DICT)
            #import json
            #json.dump(data_rec, open("/Users/stephane/workarea/Pickare/BTL/documents/tests/data_rec.json", "w"))

            update_tesseract_rec_with_boxes(data_dict)
            info_found = analyze_data_dict(data_dict, config_json, verbose)

        if info_found:
            recognition_img.save(temp_image_path, 'png')

        if info_found and extract_pdf:
            cur_pdf = pytesseract.image_to_pdf_or_hocr(recognition_img, extension='pdf', lang='fra',
                                        config='./configs/pdf')
            # add page to searchable pdf
            tmp_pdf_file = NamedTemporaryFile()
            with open(tmp_pdf_file.name, 'w+b') as f:
                f.write(cur_pdf)
                pdf_reader = PdfFileReader(tmp_pdf_file.name)
                output_pdf.addPage(pdf_reader.getPage(0))

        # create html file from hocr
        if info_found and extract_hocr:
            cur_hocr = pytesseract.image_to_pdf_or_hocr(recognition_img, extension='hocr', lang='fra',
                                        config='./configs/hocr')
            output_path_hocr = '{}_p{}.html'.format(root_file, np+1)
            with open(output_path_hocr, 'w') as f:
                f.write(cur_hocr.decode('utf-8').replace('\\n', '\n').replace('\\t', '\t'))

    # Write out the searchable PDF
    if extract_pdf:
        with open(output_path_pdf, 'wb') as out:
            output_pdf.write(out)