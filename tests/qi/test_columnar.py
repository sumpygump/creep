"""Tests for columnar"""

from qi.columnar import Columnar, ColumnarRow


def test_columnar_init():
    obj = Columnar()
    assert obj.data == []
    assert obj.headers == []
    assert obj.fillchars == []
    assert not obj.widths


def test_data(capsys):
    data = [
        ["109", "far"],
        ["2", "nearest"],
    ]
    obj = Columnar(data)
    assert obj.widths == [3, 7]
    assert obj.get_widths() == [3, 7]
    assert obj.get_rows() == data

    result = obj.render()
    captured = capsys.readouterr()
    assert result is None
    assert captured.out == "\n109 far    \n2   nearest\n"

    result = obj.render(do_print=False)
    assert result == "\n109 far    \n2   nearest\n"


def test_data_with_headers(capsys):
    data = [
        ["109", "far"],
        ["2", "nearest"],
    ]
    obj = Columnar(data, headers=["id", "label"])
    assert obj.widths == [3, 7]

    result = obj.render()
    captured = capsys.readouterr()
    assert result is None
    assert captured.out == "id  label  \n109 far    \n2   nearest\n"

    result = obj.render(do_print=False)
    assert result == "id  label  \n109 far    \n2   nearest\n"


def test_fillchars():
    data = [
        ["109", "far"],
        ["2", "nearest"],
    ]
    obj = Columnar(data, headers=["id", "label"], fillchars=["*", "%"])
    assert obj.widths == [3, 7]

    result = obj.render(do_print=False)
    assert result == "id  label  \n109 far%%%%\n2** nearest\n"


def test_add_row():
    obj = Columnar()
    assert not obj.widths

    obj.add_row(["2", "Charlie"])
    assert obj.widths == [1, 7]

    obj.add_row(["74", "Molly Brown"])
    assert obj.widths == [2, 11]

    assert obj.data == [["2", "Charlie"], ["74", "Molly Brown"]]


def test_row():
    obj = ColumnarRow()
    assert obj.data == []
    assert obj.widths == []
    assert obj.fillchars == []


def test_row_with_content():
    obj = ColumnarRow(["34", "Kirby"])
    # A single row cannot calculate the widths
    assert obj.widths == []
    assert obj.render() == "34 Kirby"

    assert obj.get(1) == "Kirby"
    assert obj.get(25) == ""

    obj.set(1, "Superman")
    assert obj.get(1) == "Superman"
    assert obj.render() == "34 Superman"
