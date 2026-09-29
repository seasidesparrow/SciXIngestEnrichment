import json
import os
import unittest

from mock import Mock, patch

from adsenrich.bibcodes import BibcodeGenerator


class TestBibcodeGenerator(unittest.TestCase):
    def setUp(self):
        self.inputdir = os.path.join(os.path.dirname(__file__), "stubdata/input/")

    def test_iop(self):
        test_cases = [
            {"infile": "bibcode_iop_apj_ft_1.json",
             "bibcode": "2026ApJ...666..666X"
            }
        ]

        for t in test_cases:
            test_infile = os.path.join(self.inputdir, t.get("infile", "error.json"))
            expected_bibcode = t.get("bibcode", "")
            
            

            # Mocking the publisher name and bibcode to avoid API calls in testing
            mock_jdb_issn_query = Mock()
            mock_publisher.return_value = filenames_dict[f]["publisher"]

            mock_bibcode = Mock()
            mock_bibcode.return_value = filenames_dict[f]["bibcode"]
            with patch("adsenrich.utils.issn2info", mock_publisher):
                with patch("adsenrich.bibcodes.BibcodeGenerator.make_bibcode", mock_bibcode):
                    refs = ReferenceWriter(
                        data=record,
                        reference_directory=self.tempdir,
                        reference_source=filenames_dict[f]["refsource"],
                        url="http://devapi.adsabs.harvard.edu/v1/",
                    )
                    refs.output_file = refs._create_output_file_name()
                    refs.write_references_to_file()
