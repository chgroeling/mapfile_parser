import sys
import pprint
from mapfile_parser import MapfileParser

IGNORE_SECTIONS = {
    ".stack_irq",
    ".stack_fiq",
    ".stack",
    ".stack_svc",
    ".stack_abt",
    ".stack_und",
    ".bss",
    ".tbss",
    ".no_init",
    ".heap",
    ".mmu_table",
    ".reset_info",
}


def main():
    if len(sys.argv) != 2:
        print("Error: Wrong numer of arguments")
        return -1

    filename = sys.argv[1]
    content = ""

    # Das Map-File wird in gänze eingelesen und in einen Python string eingetragen
    with open(filename, "r") as fp:
        content = fp.read()

    mapfile_parser = MapfileParser(content)
    mapfile_parser.parse()
    section_list = mapfile_parser.get_section_list(IGNORE_SECTIONS)
    size_bin = MapfileParser.calculate_size_of_section_list(section_list)
    pprint.pprint(section_list)
    print("Size of flash sections %i Bytes. Jumps are not considered." % (size_bin))

    devices = ["CMMT-AS-MP-S1", "CMMT-AS-MP-S3", "CMMT-ST-MP-S0"]
    placements_autogen = mapfile_parser.get_placement_list_by_regex_on_file(
        "autogen.*(" + "|".join(devices) + ")"
    )
    size_autogen = MapfileParser.calculate_size_of_placement_list(placements_autogen)

    print("Size(autogen) = %.0f KB" % (size_autogen / 1024.0))

    for i in devices:
        placements_autogen = mapfile_parser.get_placement_list_by_regex_on_file(
            "autogen.*(" + i + ")"
        )
        size_autogen = MapfileParser.calculate_size_of_placement_list(
            placements_autogen
        )

        placements_autogen_components = (
            mapfile_parser.get_placement_list_by_regex_on_file(
                "autogen.*components.*(" + i + ")"
            )
        )
        size_autogen_components = MapfileParser.calculate_size_of_placement_list(
            placements_autogen_components
        )

        placements_autogen_ec = mapfile_parser.get_placement_list_by_regex_on_file(
            "autogen.*ethercat.*(" + i + ")"
        )
        size_autogen_ec = MapfileParser.calculate_size_of_placement_list(
            placements_autogen_ec
        )

        placements_autogen_pn = mapfile_parser.get_placement_list_by_regex_on_file(
            "autogen.*profinet.*(" + i + ")"
        )
        size_autogen_pn = MapfileParser.calculate_size_of_placement_list(
            placements_autogen_pn
        )

        print(
            "- %s : size_all = %3.0f KByte, size_component = %3.0f KByte, size_ec = %3.0f KByte, size_pn = %3.0f KByte"
            % (
                i,
                size_autogen / 1024.0,
                size_autogen_components / 1024.0,
                size_autogen_ec / 1024.0,
                size_autogen_pn / 1024.0,
            )
        )


if __name__ == "__main__":
    main()
