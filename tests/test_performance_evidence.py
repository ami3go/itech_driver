from itech_driver.performance_evidence import accuracy_report, soak_report


def test_accuracy_includes_uncertainty():
    good=dict(expected="1",observed="1.05",abs_tolerance=".1",uncertainty=".02")
    assert accuracy_report([good])["passed"]
    assert not accuracy_report([dict(good,uncertainty=".09")])["passed"]
    assert not accuracy_report([dict(good,observed="NaN")])["passed"]
    assert not accuracy_report([])["passed"]


def soak():
    # Synthetic timestamps, NOT a physical 24-hour run.
    return [dict(sequence=str(i),elapsed_s=str(i*3600),latency_s=".1",status="OK",generation="1")
            for i in range(25)]


def test_full_duration_and_cadence():
    rows=soak()
    assert soak_report(rows,max_gap=3600,max_latency=1)["passed"]
    assert not soak_report(rows[:-1],max_gap=3600,max_latency=1)["passed"]
    assert not soak_report(rows,max_gap=3599,max_latency=1)["passed"]


def test_failed_attempt_or_generation_change():
    rows=soak()
    rows[3]["status"]="TIMEOUT"
    assert not soak_report(rows,max_gap=3600,max_latency=1)["passed"]
    rows[3]["status"]="OK"
    rows[4]["generation"]="2"
    assert not soak_report(rows,max_gap=3600,max_latency=1)["passed"]


def test_missing_attempts_or_nonfinite_latency():
    rows=soak()
    assert not soak_report(rows[:2]+rows[3:],max_gap=7200,max_latency=1)["passed"]
    rows[1]["latency_s"]="inf"
    assert not soak_report(rows,max_gap=3600,max_latency=1)["passed"]
