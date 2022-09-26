import time

import xmltodict

from fos.conf import CONF
from utils.mongodb import MongoDB


class Fortigate:
    """FOS Platform parser for parsing platforms.xml from FOS builds of
    info.fortinet.com, all data will store in self._platforms, and accessed
    by get_featuers() function
    """
    def __init__(self, data):
        self._platforms = {}
        self._parse(data)
        self._db = MongoDB(CONF.get("db"), CONF.get("default_db", "fos"))

    @staticmethod
    def _load_platform_xml(xml_str):
        def _format_handler(path, key, value):
            return key.lstrip("@").lstrip("#"), value

        platform_xml = xmltodict.parse(
            xml_str, postprocessor=_format_handler
        )

        if "fortigate" in platform_xml:
            return platform_xml["fortigate"]
        raise KeyError(
            f"fortigate platform category is not in xml platform file"
        )

    def _parse_general_info(self, xml_dict):
        self._platforms = {
            "version": xml_dict["version"],
            "build": xml_dict["build"],
            "build_type": xml_dict["build_type"]
        }

    def _parse_categories(self, xml_dict):
        fc = {}

        for feature in xml_dict["feature_categorys"]["feature_category"]:
            fc[feature.pop("id")] = feature["text"]

        self._platforms["feature_categories"] = fc

    def _parse_features(self, xml_dict):
        """
        Convert list of features in dict to a single dict contains all
        platforms loaded from platform xml

        Args:
            xml_dict (dict): orginal loaded content of xml file

        Returns: None
        """
        features = {}

        for feature in xml_dict["features"]["feature"]:
            features[feature.pop("id")] = feature

        self._platforms["features"] = features

    def _parse_platforms(self, xml_dict):
        """
        Convert list of platfroms in dict to a single dict contains all
        platforms

        Args:
            xml_dict (dict): orginal loaded content of xml file

        Returns: None

        """
        platforms = {}

        for platform in xml_dict["platforms"]["platform"]:
            platforms[platform.pop("name")] = platform

        self._platforms["platforms"] = platforms

    def _parse(self, data):
        self._platforms = self._load_platform_xml(data.pop("data"))
        self._platforms.update({
            "branch": data.pop("branch"),
            "file": data.pop("file")
        })

    def list_all_platforms(self):
        return self._platforms

    def _update_platforms(self, version):
        """
        Update parsed platform information dict to db. Note: if data with same
        version exists, there will be only update. rather than create.
        if record not exist, it will create new one.

        This involved two collections:

        "platforms": storing all platform information
        "versions": storing latest build number for each major version

        """
        self._db.update(version, self._platforms, "platforms")

        features_mapping = {}
        for feature in self._platforms["features"]["feature"]:
            self._db.update({"id": feature["id"]}, feature, "features")
            features_mapping[feature.pop("id")] = feature

        for info in self._platforms["platforms"]["platform"]:
            info.update(version)
            features = {}
            for feature in info.keys():
                if feature not in ["supported_features"]:
                    feature = f"g_{feature}"
                    feature_dict = {
                        "id": feature,
                        "cat": "global",
                        "name": "global feature or values"
                    }
                    self._db.update({"id": feature}, feature_dict, "features")

            for feature in info["supported_features"]["supported_feature"]:
                feature_id = feature["id"]
                value = feature.get("text")
                features[feature_id] = features_mapping[feature_id]
                if value:
                    features[feature_id]["value"] = value
                    if not value.isalpha():
                        if "." in value:
                            value = float(value)
                        else:
                            value = int(value)
                    info[feature_id] = value
            info["supported_features"] = features
            query = version.copy()
            query["name"] = info["name"]
            self._db.update(query, info, "models")

    def update(self):
        major = self._platforms["version"]["major"]
        version = {
            "major_version": major,
            "build": self._platforms["build"],
            "branch": self._platforms["branch"]
        }
        query = version.copy()
        query.pop("build")
        self._update_platforms(version)

        version["update_at"] = time.asctime()
        self._db.update(
            query, version, "versions"
        )
