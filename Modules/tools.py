from datetime import datetime


def importer(xml_files, sv):
    """
    importer(xml_files, server)

    Used to import multiple XML files from a list containing it's paths
    It is better if you assign string nodeids, is easier to mantain if
    you use adequate strings, something like BrowsePath hints.
    Nodes that doesn't fit their TypeDefinition will throw an error when browsed,
    something like BadAttributeIdInvalid (0x80350000)
    xml_files: List containing the path to XML files
    sv: Server object where XML should be imported
    """
    for progress, filepath in enumerate(xml_files):
        sv.import_xml(filepath)
        print("{} - {}/{} -> \'{}\' has been imported.".format(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"), progress + 1, len(xml_files), filepath))


def ns_printer(ns):
    """
    ns_printer(ns)

    Prints each namespace and its assigned index.
    ns: Object obtained via server.get_namespace_array()
    """
    print("Los namespace son:")
    for nsn, nsu in enumerate(ns):
        print("    {}: {}".format(nsn, nsu))


def argstr(item):
    argl = ""
    for i in item:
        argl += "{},".format(str(i))
    argl = argl[:-1]
    return argl

def argget(txt):
    txt = txt.split(',')
    list = []
    for i in txt:
        if try_int(i):
            list.append(int(i))
        else:
            list.append(i)
    return list


def try_int(i):
    try:
        int(i)
        return True
    except ValueError:
        return False
