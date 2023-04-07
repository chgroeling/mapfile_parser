from unittest.mock import patch, MagicMock, Mock
from mapfile_parser import MapfileParser


@patch("mapfile_parser.MapfileParser.generator_remove_reused_placements")
def test_generator_sections(mock_classmethod):
    """Übliche Daten die der Methode generator_sections übergeben werden."""

    # Die Klassenmethode generator_sections ruft weiter Klassenmethoden auf: generator_remove_reused_placements, generator_placements, generator_subsections.
    # Da alle hintereinander aufgerufen werden wird hier nur generator_remove_unused_placement gepatcht.

    mock_result_cls = Mock()
    mock_classmethod.return_value = [mock_result_cls]

    test_string = [
        """.mmu_table      0x2fff8000     0x8000
 *(.mmu_table)
 .mmu_table     0x2fff8000     0x4000 CMakeFiles/EDESapp.dir/drivers/a7/mmu.cpp.obj
                0x2fff8000                drivers::a7::Mmu::translationTable
 *(.page_tables)
 .page_tables   0x2fffc000     0x4000 CMakeFiles/EDESapp.dir/drivers/a7/mmu.cpp.obj
                0x2fffc000                drivers::a7::Mmu::pageTables"""
    ]

    generator = MapfileParser.generator_sections(test_string)
    result_generator = list(generator)

    assert len(result_generator) == 1

    result = result_generator[0]

    assert result[0] == ".mmu_table"  # name
    assert result[1] == 805273600  # address: 0x2fff8000
    assert result[2] == 32768  # size: 0x8000

    assert len(result[3]) == 1
    ret_placements = result[3]

    assert ret_placements[0] == mock_result_cls


def test_generator_subsections_normal():
    """Übliche Daten die der Methode generator_subsections übergeben werden"""
    test_string = """ *(.mmu_table)
 .mmu_table     0x2fff8000     0x4000 CMakeFiles/EDESapp.dir/drivers/a7/mmu.cpp.obj
                0x2fff8000                drivers::a7::Mmu::translationTable
 *(.page_tables)
 .page_tables   0x2fffc000     0x4000 CMakeFiles/EDESapp.dir/drivers/a7/mmu.cpp.obj
                0x2fffc000                drivers::a7::Mmu::pageTables"""

    generator = MapfileParser.generator_subsections(test_string)
    result_generator = list(generator)

    # Die Split Methode führt auch einen Split beim ersten validen Element durch, daher haben wir 5 anstatt 4 Element wobei der erste
    # leer ist.

    assert len(result_generator) == 5

    assert result_generator[0] == ""
    assert result_generator[1] == " *(.mmu_table)"
    assert (
        result_generator[2]
        == """ .mmu_table     0x2fff8000     0x4000 CMakeFiles/EDESapp.dir/drivers/a7/mmu.cpp.obj
                0x2fff8000                drivers::a7::Mmu::translationTable"""
    )
    assert result_generator[3] == " *(.page_tables)"
    assert (
        result_generator[4]
        == """ .page_tables   0x2fffc000     0x4000 CMakeFiles/EDESapp.dir/drivers/a7/mmu.cpp.obj
                0x2fffc000                drivers::a7::Mmu::pageTables"""
    )


def test_generator_placements_normal():
    """Übliche Daten die der Methode generator_placements übergeben werden"""

    test_data = [
        "",
        " *(.mmu_table)",
        """ .mmu_table     0x2fff8000     0x4000 CMakeFiles/EDESapp.dir/drivers/a7/mmu.cpp.obj
                0x2fff8000                drivers::a7::Mmu::translationTable""",
        " *(.page_tables)",
        """ .page_tables   0x2fffc000     0x4000 CMakeFiles/EDESapp.dir/drivers/a7/mmu.cpp.obj
                0x2fffc000                drivers::a7::Mmu::pageTables""",
    ]

    generator = MapfileParser.generator_placements(test_data)
    result_generator = list(generator)
    assert len(result_generator) == 2

    res_mmu_table = result_generator[0]
    assert res_mmu_table[0] == ".mmu_table"
    assert res_mmu_table[1] == 805273600  # address: 0x2fff8000
    assert res_mmu_table[2] == 16384  # size: 0x4000

    res_page_tables = result_generator[1]
    assert res_page_tables[0] == ".page_tables"
    assert res_page_tables[1] == 805289984  # address: 0x2fffc000
    assert res_page_tables[2] == 16384  # size: 0x4000


def test_generator_subsections_fill():
    """Eine fill Sektion muss speziell behandelt werden. Dieser Test überprüft dies."""
    test_string = """ *fill*         0xc056f2c1        0x3 """
    generator = MapfileParser.generator_subsections(test_string)
    result_generator = list(generator)

    # Die Split Methode führt auch einen Split beim ersten validen Element durch, daher haben wir 5 anstatt 4 Element wobei der erste
    # leer ist.

    assert len(result_generator) == 2

    assert result_generator[0] == ""
    assert result_generator[1] == " *fill*         0xc056f2c1        0x3 "


def test_generator_placements_fill():
    """Eine fill Sektion muss speziell behandelt werden. Dieser Test überprüft dies."""

    test_data = [" *fill*         0xc056f2c1        0x3 "]

    generator = MapfileParser.generator_placements(test_data)
    result_generator = list(generator)
    assert len(result_generator) == 1

    res_fill = result_generator[0]
    assert res_fill[0] == "*fill*"
    assert res_fill[1] == 3226923713  # address: 0xc056f2c1
    assert res_fill[2] == 3  # size: 0x3
    assert res_fill[3] == ""


def test_generator_remove_reused_placements_1times():
    """ Der Linker verwendet manche Objekte doppelt. Entferne sie"""

    test_data = [
        ["sect1", 0, 10],
        ["sect2", 10, 20],
        ["sect_", 10, 20],
        ["sect3", 30, 10],
    ]

    res = list(MapfileParser.generator_remove_reused_placements(test_data))
    assert len(res) == 3
    assert res[0] == ["sect1", 0, 10]
    assert res[1] == ["sect_", 10, 20]
    assert res[2] == ["sect3", 30, 10]

def test_generator_remove_reused_placements_2times():
    """ Der Linker verwendet manche Objekte doppelt. Entferne sie"""

    test_data = [
        ["sect1", 0, 10],
        ["sect2", 10, 20],
        ["sect_", 10, 20],
        ["sect__", 10, 20],
        ["sect3", 30, 10],
    ]

    res = list(MapfileParser.generator_remove_reused_placements(test_data))
    assert len(res) == 3
    assert res[0] == ["sect1", 0, 10]
    assert res[1] == ["sect__", 10, 20]
    assert res[2] == ["sect3", 30, 10]
