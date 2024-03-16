
import pdfminer


def mining_infos_pdf(path):
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextContainer

    for page_layout in extract_pages(path):
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                print(element.get_text())
    return


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Recognition of pdf file')
    parser.add_argument('-f', '--file', type=str, help='pdf filename without extension')
    parser.add_argument('-c', '--config', type=str, help='config filename', default='')
    parser.add_argument('-v', '--verbose', type=int, default=0, help='verbose mode')

    args = parser.parse_args()
    verbose = args.verbose
    config_filename = args.config
    config_json = {}
    if config_filename:
        import json
        with open(config_filename) as f:
            config_json = json.load(f)

    if args.file.endswith(".pdf"):
        root_file = args.file[0:-4]
    else:
        root_file = args.file
    path = '{}.pdf'.format(root_file)

    mining_infos_pdf(path)
