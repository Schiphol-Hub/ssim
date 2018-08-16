from ssim.ssim import _parse_sir, _parse_sim


def test_sir_parsing(sir_records):

    for record in sir_records:
        assert _parse_sir(record["raw_data"]) == record["records"]


def test_sim_parsing(sim_records):

    for record in sim_records:
        assert _parse_sim(record["raw_data"]) == record["records"]
