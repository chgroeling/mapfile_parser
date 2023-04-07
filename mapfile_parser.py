# -*- coding: utf-8 -*-

import re
import logging


class MapfileParser:
    def __init__(self, mapfile):
        self._mapfile = mapfile
        self._sec_dict = {}

    def extract_memory_map(self, mapfile):
        """Diese Funktion extrahiert den Abschnitt Memory Map aus dem Map-File.

        Der Abschnitt Memory Map im Map-File beginnt ab der Überschrift "Linker script and memory map" und
        endet mit der Überschritf "Output ...". Diese Funktion extrahiert den Text zwischen diesen beiden
        Überschriften mit einem regulären Ausdruck.

        Die Funktion gibt drei Werte als Tuple zurück. Der erste Wert ist der Abschnitt vor der Überschrift "Linker script and memory map",
        der zweite ist die Memory Map selbst, der dritte  Abschnitt enthält alles was nach der Memory map folgt.
        """
        headline_regex = "Linker script and memory map\n\n|OUTPUT\(.*\)\n"
        re_headline = re.compile(headline_regex)
        splitted_content = re_headline.split(mapfile)
        assert len(splitted_content) == 3

        return splitted_content[0], splitted_content[1], splitted_content[2]

    @staticmethod
    def siev_load_sections(sections):
        """Ein Generator der alle Sektionen entfernt die mit LOAD beginen"""
        return (i for i in sections if not i.startswith("LOAD"))

    @staticmethod
    def split_regex(resplit, text):
        """Die Funktion zerlegt den String text in eine Liste anhand des regulären Audrucks regx. Im Unterschied
        zu den üblich verfügbaren split Methoden wird der Separator sep nicht entfernt sondern jedem Eintrag vorangestellt.
        """
        matches = list(resplit.finditer(text))

        sections = []

        if len(matches) == 0:
            return []

        # Das erste Element ist in der unteren Iteration nicht enthalten
        sections.append(text[0 : matches[0].start()])

        for i in zip(matches[:-1], matches[1:]):
            sections.append(text[i[0].start() : i[1].start() - 1])

        # Der letzte Treffer wird bis zum ende weitergeführt
        sections.append(text[matches[-1].start() :])
        return sections

    @classmethod
    def split_sections(cls, placement):
        re_placement = re.compile(r"^[^\s].*$", re.MULTILINE)

        sections = cls.split_regex(re_placement, placement)
        filtered_sections = cls.siev_load_sections(sections)
        return list(filtered_sections)

    @classmethod
    def generator_subsections(cls, section):
        re_placement = re.compile(r"^\s[^\s].*$", re.MULTILINE)

        subsections = cls.split_regex(re_placement, section)

        for i in subsections:
            yield i

    @staticmethod
    def generator_placements(sub_sections):

        for placement in sub_sections:
            # Der folgende Reguläre Asdruck dient der Zerlegung von Einträgen mit folgenden Muster
            # " COMMON         0xc056fd60       0x18 C:/workspace/edes/checkout/external/opes_root/opes/lib/STM32MP1A7_embOS/libOPEScored.a(IP_ARP.c.obj)"
            #
            # Man beachte das vorangestellte Leerzeichen.
            regex = r"^\s([\*\.\w\s]+)\s+(0x\w+)[^\S\r\n]+(0x\w+)\s(.+)?\s*\n?\s*(0x\w+)?\s*(.+)?"

            regex_placement = re.compile(regex, re.MULTILINE)
            matches = regex_placement.findall(placement)

            # Das Ergebniss wird als Tuple zurückgegeben. Die Einträge enthalten folgenden
            # 0 - name der Objektes
            # 1 - Address
            # 2 - Size/Größe
            # 3 - Dateiname aus dem das Objekt entnommen wurde
            # 4 - (optional) Addresse in der nächsten Zeile
            # 5 - (optional) Klassenname
            conversions = (
                [i[0].strip(), int(i[1], 16), int(i[2], 16), i[3], i[4], i[5]]
                for i in matches
            )
            ret = list(conversions)

            for i in ret:
                if i[0] == "":
                    i[0] = "*empty*"
                
                #if i[4] != "":
                #    i4_int = int(i[4],16)

                    # check if the address of the first and the second line match. If not continue
                #    if i4_int != i[1]:
                #        continue
                yield i

    @staticmethod
    def generator_remove_reused_placements(placements):
        last_placement = None
        for i in placements:

            if last_placement == None:
                # Das erste Element ist immer korrekt
                last_placement = i
            else:
                last_adr = last_placement[1]
                last_size = last_placement[2]
                adr = i[1]
                if last_adr + last_size == adr:
                    yield last_placement
                last_placement = i
        if last_placement != None:
            yield last_placement

    @classmethod
    def generator_sections(cls, sections):

        # Der folgende reguläre Ausdruck dient der Zerlegung von Einträgen mit folgenden Muster
        # ".mmu_table      0x2fff8000     0x8000"
        # oder
        # ".fast           0x2ffc0380     0x6ac0 load address 0xc0000780"

        regex = r"^([\.\w]+)\s+(0x\w+)\s+(0x\w+).*$"
        regex_section = re.compile(regex)

        for i in sections:
            section_first_line, _, subsections = i.partition("\n")
            matches = regex_section.findall(section_first_line)

            if len(matches) != 1:
                continue

            section_name = matches[0][0]
            position = int(matches[0][1], 16)
            size = int(matches[0][2], 16)

            subsections_generator = cls.generator_remove_reused_placements(
                cls.generator_placements(cls.generator_subsections(subsections))
            )

            yield (section_name, position, size, list(subsections_generator))

    @staticmethod
    def calculate_size_of_section_list(sec_list):
        size_fw = 0
        for i in sec_list:
            size = i[2]
            size_fw += size

        return size_fw

    @staticmethod
    def calculate_size_of_placement_list(placements):
        size_placement = 0
        for i in placements:
            size = i[2]
            size_placement += size

        return size_placement

    @staticmethod
    def helper_check_integrity(placements):
        """Diese Methode überprüft ob die Objekte nacheinander platziert wurden. Ist dies nicht der Fall gibt sie die
        Objekte aus. Sie dient nur zum zweck des debuggings"""
        placed_already = set()
        prev = None
        for i in placements:

            if prev != None:
                calc_adr = prev[1] + prev[2]
                act_adr = i[1]

                if act_adr != calc_adr:
                    print("****")
                    print(prev)
                    print(i, act_adr - calc_adr)
                    print("----")

            prev = i

    def get_section_list(self, ignores=set()):
        """Gibt einer Liste aller Sektionen zurück die gefunden wurden. Das Argument ignores kann verwendetet werden
        um bestimmte Sektionen bei Generierung der Liste zu ignorieren und nicht auszunehmen. Es handelt sich um
        set der die Namen der zu ignorierenden Sektion enthält"""
        section_list = []
        for name, info in self._sec_dict.items():
            if name not in ignores:
                section_list.append([name, info["address"], info["size"]])

        return section_list

    def get_class_info(self):
        """ Return readable info of every placement as List.

        0. Status
        1. ClassInfo (if exists)
        2. Address
        3. Size
        4. Section
        5. objfile
        6. objname
        
        """
        result = []

        for section, info in self._sec_dict.items():
            for placement in info["placements"]:
                classinfo = placement[5]
                size = placement[2]
                address = placement[1]
                objfile = placement[3]
                objname = placement[0]

                address2nd = placement[4]
                status=""
                if (address2nd != ""):

                    address_2nd_int = int(address2nd,16)

                    if address != address_2nd_int:
                        status = "\"ALTERNATE_CLASSINFO\""
                        #classinfo = ""

                if classinfo == "":
                    status = "\"MISSING_CLASSINFO\""
                
                if objfile == "00":
                    objfile =""

                result.append([status, classinfo, address, size, section, objfile, objname])
        return result

    def parse(self):

        # Extrahiere die Memory Map aus dem Map-file.
        _, placement, _ = self.extract_memory_map(self._mapfile)

        sections = MapfileParser.split_sections(placement)

        sections_generator = MapfileParser.generator_sections(sections)

        self._sec_dict = {}
        for *section, placements in sections_generator:
            section_name = section[0]
            section_address = section[1]
            section_size = section[2]

            logging.info("Going through section: %s", section_name)

            # MapfileParser.helper_check_integrity(placements)

            calculated_size = MapfileParser.calculate_size_of_placement_list(placements)

            if section_size != calculated_size:
                logging.error(
                    "Section size is not equal to calculated size {section_name:%s, section_size:%i, calculated_size:%i}",
                    section_name,
                    section_size,
                    calculated_size,
                )
                logging.debug("Placements: %s", placements)

            logging.info("Placements %s", placements)
            self._sec_dict[section_name] = {
                "address": section_address,
                "size": section_size,
                "placements": placements,
            }

