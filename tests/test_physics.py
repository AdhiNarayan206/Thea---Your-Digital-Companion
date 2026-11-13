from thea import physics


def test_clamp():
    assert physics.clamp(5, 0, 3) == 3
    assert physics.clamp(-1, 0, 3) == 0
    assert physics.clamp(2, 0, 3) == 2


def test_edges_keep_him_inside():
    x, vx, hit = physics.edges(-10, 200, 0, 1920, -300)
    assert x == 0 and hit and vx > 0


def test_throw_velocity_uses_recent_samples():
    samples = [((0, 0), 1.0), ((100, 0), 1.05), ((220, 0), 1.1)]
    vx, vy = physics.throw_velocity(samples, 1.1)
    assert 900 < vx < 2600
    assert abs(vy) < 1


def test_throw_velocity_needs_two_samples():
    assert physics.throw_velocity([], 2.0) == (0.0, 0.0)


def test_feed_zone_is_the_top_of_the_screen():
    assert physics.feed_zone(0, 1000) == 160
    assert physics.feed_zone(100, 1000) == 260
