from config.container import ContainersConfig


def test_defaults():
    containerCfg = ContainersConfig()
    num_steps = 16
    # alias private function
    gen_list = containerCfg._ContainersConfig__gen_container_list  # type: ignore[attr-defined]

    # test
    for i in range(1, num_steps + 1):
        assert len(gen_list(i, 1)) == i

    # test most common values
    values = [32, 96, 384, 192, 256, 320, 160]
    for v in values:
        counts = gen_list(v, 1)
        assert len(counts) == num_steps + 1
        assert counts[0] == 1

    # try some odd combinations
    cores_per_container = [2, 3, 7]
    for v in values:
        for c in cores_per_container:
            max = v // c
            counts = gen_list(max, c)
            assert counts[0] == 1
