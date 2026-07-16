from lxml import etree

# EXAMPLE ONLY - intentionally vulnerable for Black Duck Code Sight SAST testing
# Vulnerability: XML External Entity Injection (CWE-611) via unsafe parser config


def parse_mission_log(xml_bytes):
    parser = etree.XMLParser(resolve_entities=True, no_network=False)  # entity resolution left enabled
    return etree.fromstring(xml_bytes, parser=parser)
