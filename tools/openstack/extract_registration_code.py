import os
import re

import PyPDF2
import yaml


LICENSE_PDF_PATH = r"C:\Users\znie\Documents\licenses_FG\LIC-FIS-VM_52593930"
license_code = {}


def extract_license_code(license_pdf_folder, save=False):
    for file in os.listdir(license_pdf_folder):
        full_path = os.path.join(LICENSE_PDF_PATH, file)
        with open(full_path, "rb") as F:
            reader = PyPDF2.PdfFileReader(F)
            page = reader.getPage(0)
            text = page.extractText()

        text_list = re.search(
            r".*Registration Code[ ]*:[ ]*(.*)[ ]*Evaluation", text
        )
        registeration_code = text_list.group(1)
        license_code[registeration_code] = {"file": file}
    if save:
        with open("licenses.yaml", "w") as F:
            licenses = {
                "registration_code": license_code
            }
            yaml.dump(licenses, F)
            print(f"{len(license_code)} licenses saved")

    return license_code


if __name__ == "__main__":
    extract_license_code(LICENSE_PDF_PATH, save=True)