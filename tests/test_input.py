from thea.input import Pointer


def test_single_tap():
    p = Pointer()
    p.press((100, 100), 0.0)
    action = p.release((101, 101), 0.12)
    assert action["tap"] and not action.get("double")


def test_double_tap():
    p = Pointer()
    p.press((100, 100), 0.0)
    p.release((101, 101), 0.1)
    p.press((103, 102), 0.2)
    action = p.release((104, 102), 0.27)
    assert action.get("double")


def test_slow_taps_are_not_double():
    p = Pointer()
    p.press((100, 100), 0.0)
    p.release((101, 101), 0.1)
    p.press((100, 100), 1.0)
    action = p.release((100, 100), 1.1)
    assert action.get("tap")


def test_drag_reports_throw_velocity():
    p = Pointer()
    p.press((100, 100), 0.0)
    assert not p.move((103, 100), 0.02)
    assert p.move((140, 100), 0.06)
    assert p.move((200, 100), 0.10)
    action = p.release((230, 100), 0.14)
    assert "drag" in action
    vx, vy = action["drag"]
    assert vx > 500


def test_tap_after_drag_is_not_a_tap():
    p = Pointer()
    p.press((0, 0), 0.0)
    p.move((50, 50), 0.1)
    action = p.release((50, 50), 0.2)
    assert "tap" not in action and "drag" in action
