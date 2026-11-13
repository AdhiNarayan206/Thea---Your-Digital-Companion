from thea.animation import Thea


class FakeParticles:
    def __init__(self):
        self.items = []

    def spawn(self, *a, **k):
        pass

    def update(self, dt):
        pass

    def clear(self):
        pass

    def bounds(self):
        return None


class FakeAudio:
    def blip(self, *a, **k):
        pass

    def chime(self, *a, **k):
        pass

    def sing(self):
        pass

    def stop(self):
        pass


class FakeStats:
    fullness = 80.0
    joy = 70.0
    energy = 80.0
    fed = 0

    def decay(self, dt):
        pass

    def cheer(self, amount=7.0):
        pass

    def feed(self):
        self.fed += 1

    def sing(self):
        pass

    def rest(self, dt):
        pass


def make_thea():
    return Thea((0, 0, 1200, 900), FakeStats(), FakeParticles(), FakeAudio(), scale=5)


def test_starts_on_the_floor_and_centered():
    thea = make_thea()
    assert thea.y == thea.floor()
    assert 400 < thea.x < 700
    assert thea.state == "idle"


def test_hitbox_is_the_silhouette_not_the_square():
    thea = make_thea()
    cx, cy = thea.center()
    assert thea.hit(cx, cy)
    assert not thea.hit(thea.x + 2, thea.y + 2)


def test_space_runs_toward_the_cursor_side():
    thea = make_thea()
    start = thea.x
    cursor = (thea.x + thea.size * 0.62, 600)  # right half of his body
    thea.interact(cursor)
    assert thea.state == "run"
    for _ in range(60):
        thea.update(1 / 60, cursor)
    assert thea.x > start


def test_jump_returns_to_the_floor():
    thea = make_thea()
    thea.tap()
    assert thea.state == "jump"
    for _ in range(180):
        thea.update(1 / 60, (0, 0))
    assert thea.state == "idle"
    assert abs(thea.y - thea.floor()) < 0.01


def test_double_tap_makes_him_happy_then_calms_down():
    thea = make_thea()
    thea.double_tap()
    assert thea.state == "happy"
    for _ in range(150):
        thea.update(1 / 60, (0, 0))
    assert thea.state == "idle"


def test_feeding_on_the_shelf_and_then_he_comes_down():
    thea = make_thea()
    thea.start_eat(400, thea.shelf_y, on_shelf=True)
    assert thea.state == "eat"
    assert thea.y == thea.shelf_y
    assert thea.stats.fed == 1
    for _ in range(60 * 6):
        thea.update(1 / 60, (0, 0))
    assert thea.state in ("idle", "fall", "jump")


def test_hunger_makes_him_sad():
    thea = make_thea()
    thea.stats.fullness = 10
    assert thea.expression() == "sad"


def test_overlong_drag_makes_him_angry():
    thea = make_thea()
    thea.begin_drag()
    thea.dragging = True
    thea.drag_time = 5.0
    thea.release(0, 0)
    assert thea.expression() in ("angry", "surprised")


def test_holding_still_counts_as_holding():
    """Anger must follow the real clock, not pointer-move events."""
    thea = make_thea()
    thea.begin_drag()
    thea.drag_to(thea.x + thea.size / 2, thea.y + thea.size * 0.45)
    thea.release(0, 0, held=4.5)
    assert thea.expression() == "angry"


def test_sleep_and_wake():
    thea = make_thea()
    thea.sleep()
    assert thea.expression() == "sleep"
    thea.wake()
    assert thea.state == "idle"


def test_render_is_a_contiguous_rgba_frame():
    thea = make_thea()
    thea.facing = -1
    frame = thea.render()
    assert frame.flags["C_CONTIGUOUS"]
    assert frame.shape == (40, 40, 4)
