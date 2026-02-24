import os

from adsputils import load_config

from adsenrich.bibcodes import BibcodeGenerator
from adsenrich.data import *
from adsenrich.exceptions import *
from adsenrich.utils import issn2info

proj_home = os.path.realpath(os.path.join(os.path.dirname(__file__), "../"))
conf = load_config(proj_home=proj_home)


class ReferenceWriter(object):
    def __init__(
        self,
        reference_directory="./references/",
        reference_source=None,
        data=None,
        bibcode=None,
        token=None,
        url=None,
        maxtries=None,
        sleeptime=None,
    ):
        self.basedir = reference_directory
        self.bibcode = bibcode
        self.data = data
        self.reference_list = None
        self.reference_source = reference_source
        self.refsource_dict = REFSOURCE_DICT
        self.output_file = None
        if not token:
            token = conf.get("_API_TOKEN", None)
        if not url:
            url = conf.get("_API_URL", None)
        if not maxtries:
            maxtries = conf.get("_API_MAX_RETRIES", None)
        if not sleeptime:
            sleeptime = conf.get("_API_RETRY_SLEEP", None)

        self.api_token = token
        self.api_url = url
        self.maxtries = maxtries
        self.sleeptime = sleeptime

    def _extract_refs_from_record(self):
        try:
            reference_list = self.data.get("references", None)
            if reference_list:
                if type(reference_list) == list:
                    self.reference_list = reference_list
                else:
                    raise BadFormatException("A reference key found, but not in list format!")
        except Exception as err:
            raise ExtractReferencesException("Failed to extract references: %s" % err)

    def _create_output_file_name(self):
        """
        In classic, references get written to individual files with names
        based on the bibstem, the volume number, and the data source (e.g. iop,
        aip, xref, etc).

        To create a refs filename, you need the following:
          * self.basedir
          * self.bibcode (char*19)
          * self.reference_source
          * self.data (the record in ingest data model format)
            * volume (for the path)
            * data to make a bibcode if self.bibcode is None
        """
        try:
            if not self.basedir:
                raise MissingPathException("You have not provided a valid destination directory.")
            if not self.reference_source:
                raise MissingSourceException("You have not provided a valid reference source.")
            if not self.data:
                raise MissingDataException("You have not provided a record to process.")
            if not self.bibcode:
                self.bibcode = BibcodeGenerator(
                    token=self.api_token, url=self.api_url
                ).make_bibcode(self.data)
                if not self.bibcode:
                    raise BibcodeCreationException("Failed to make a bibcode.")
            # Use journals/issn API to get the publisher name using ISSN
            issn_rec = []
            issn = []
            file_ext = None
            if self.data.get("publication").get("ISSN"):
                issn_rec = self.data["publication"]["ISSN"]
                for i in issn_rec:
                    issn = i.get("issnString", None)
                    if issn:
                        if len(issn) == 8:
                            issn = issn[0:4] + "-" + issn[4:]
                        publisher = issn2info(
                            token=self.api_token,
                            url=self.api_url,
                            issn=issn,
                            maxtries=self.maxtries,
                            sleeptime=self.sleeptime,
                            return_info="publisher",
                        )
                    else:
                        publisher = None

                    if publisher:
                        publisher = str(publisher).lower()
                        # fulltext_body = self.data.get("fulltext", {}).get("body", None)
                        # if publisher == "pnas" or not fulltext_body:
                        #     file_ext = publisher + ".xml"
                        file_ext = self.refsource_dict.get(publisher, None)
                        if not file_ext:
                            if publisher == "iop" or publisher == "oup":
                                file_ext = publisher + "ft.xml"
                            else:
                                file_ext = publisher + ".xml"
                        continue

            if not issn or not publisher:
                if not file_ext:
                    file_ext = self.refsource_dict.get(self.reference_source, ".xml")

            bibstem = self.bibcode[4:9].rstrip(".")
            volume = self.data.get("publication", {}).get("volumeNum", "").rjust(4, "0")
            output_dir = self.basedir + bibstem + "/" + volume
            self.output_file = output_dir + "/" + self.bibcode + "." + file_ext
            self.output_file = self.output_file.replace("&", "+")

        except Exception as err:
            pass
            # logger.error("Failed to create valid output filename: %s" % err)

    def write_references_to_file(self):
        try:
            self._extract_refs_from_record()
            if not self.reference_list:
                raise NoReferencesException("There are no references in this record.")
            self._create_output_file_name()

            if not self.output_file:
                raise NoOutFileException("Missing output file name.")

            if not self.bibcode:
                try:
                    self.bibcode = BibcodeGenerator(
                        token=self.api_token, url=self.api_url
                    ).make_bibcode(self.data)
                except Exception as err:
                    raise NoBibcodeException("Missing source bibcode.")

            output_dir = os.path.dirname(os.path.abspath(self.output_file))
            if not os.path.isdir(output_dir):
                # logger.warning("The output directory %s does not exist yet." % outdir)
                os.makedirs(output_dir)

            with open(self.output_file, "w") as fw:
                fw.write("<ADSBIBCODE>%s</ADSBIBCODE>\n" % self.bibcode)
                for reference in self.reference_list:
                    fw.write("%s\n" % reference)

        except Exception as err:
            # logger.error("Failed to write reference file: %s" % err)
            raise RefWriterException("Failed to write reference file: %s" % err)

    def write_refs_to_db(self):
        pass
