# -*- coding: utf-8 -*-
import sys
import pprint
import logging
import argparse
from mapfile_parser import MapfileParser
from enum import Enum

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

class Modes(Enum):
    SECTIONS = 1
    DETAILS = 2



def main(arguments):

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('mode', type=str, default='sections',
        choices=[i.name.lower() for i in Modes])


    parser.add_argument('infile', help="Input file", type=str)
    
    # Dies öffnet eine Datei zum schreiben
    parser.add_argument('-o', '--outfile', help="Output file",
                        default=sys.stdout, type=argparse.FileType('w', encoding="utf-8"))
    args = parser.parse_args(arguments)

    logging.basicConfig(
        filename="mapfile_parser.log",
        format="%(asctime)s - %(name)s - %(levelname)6s - %(message)s",
        level=logging.DEBUG,
    )
    logging.info("Started parsing map file %s", args.infile)

    # Das Map-File wird in gänze eingelesen und in einen Python string eingetragen
    content = ""
    with open(args.infile, "r") as fp:
        content = fp.read()

    mapfile_parser = MapfileParser(content)
    mapfile_parser.parse()
    
    if (args.mode == Modes.SECTIONS.name.lower()):
        section_list = mapfile_parser.get_section_list(IGNORE_SECTIONS)
        logging.info("Section List %s", section_list)
        size_bin = MapfileParser.calculate_size_of_section_list(section_list)
        pprint.pprint(section_list, stream=args.outfile)
        print("Size of flash sections %i Bytes. Jumps are not considered." % (size_bin), file=args.outfile)

    elif (args.mode == Modes.DETAILS.name.lower()):
        class_info = mapfile_parser.get_class_info()
   
        
        for i in class_info:
            csv_string = ";".join((str(x) for x in i))
            print(csv_string, file=args.outfile)

    else:
        raise Exception("")



if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
    
