import unittest

# local imports
from headers import ConfigHeader

class TestHeaders(unittest.TestCase):
    def setUp(self) -> None:
        from reco_pdf import get_config_info
        self.config_info = get_config_info(os.path.join(os.environ["METADOC_ROOT"], "tests", "test_header_config.json"))

    def test_configHeader(self):
        cfg_id = 3
        cfg_search = 'VILLE'
        cfg_length = 12
        cfg_dict = {'id':cfg_id, 'search_text':cfg_search, 'length':cfg_length}

        hdr = ConfigHeader(cfg_dict)
        self.assertEqual(hdr.id, cfg_id)
        self.assertEqual(hdr.search_text, cfg_search.lower())
        self.assertEqual(hdr.length, cfg_length)

    def test_(self):
        return

if __name__ == '__main__':
    unittest.main()