"""Offline numerical evaluation of existing HIL evidence; no hardware access."""
import argparse
import csv
import json
import math


def _real(row,key):
    try:
        value=float(row[key])
    except (ValueError,TypeError,KeyError) as exc:
        raise ValueError(f"invalid {key}") from exc
    if not math.isfinite(value):
        raise ValueError(f"nonfinite {key}")
    return value


def accuracy_report(rows):
    failures=[]
    errors=[]
    maximum=0.
    count=0
    for i,row in enumerate(rows):
        count+=1
        try:
            expected,observed,tolerance,uncertainty=(_real(row,k) for k in
                ("expected","observed","abs_tolerance","uncertainty"))
            if tolerance<0 or uncertainty<0:
                raise ValueError("negative tolerance or uncertainty")
            error=abs(observed-expected)
            if not math.isfinite(error):
                raise ValueError("overflow")
            maximum=max(maximum,error)
            if error+uncertainty>tolerance:
                failures.append(i)
        except ValueError as exc:
            errors.append(f"row {i}: {exc}")
    return dict(passed=count>0 and not failures and not errors,rows=count,
                max_abs_error=maximum,failed_rows=failures,errors=errors)


def soak_report(rows,*,max_gap,max_latency):
    if not all(math.isfinite(v) and v>0 for v in (max_gap,max_latency)):
        raise ValueError("positive finite limits required")
    errors=[]
    count=0
    first=previous=None
    initial_generation=None
    failed=0
    reconnects=0
    observed_gap=observed_latency=0.
    for i,row in enumerate(rows):
        count+=1
        try:
            sequence=int(row["sequence"])
            generation=int(row["generation"])
            elapsed=_real(row,"elapsed_s")
            latency=_real(row,"latency_s")
            status=row["status"]
            if sequence!=i or generation<0 or elapsed<0 or latency<0:
                raise ValueError("invalid sequence/generation/time")
            if status not in ("OK","ERROR","TIMEOUT"):
                raise ValueError("unknown status")
            if first is None:
                first=elapsed
                initial_generation=generation
            if previous is not None:
                gap=elapsed-previous
                observed_gap=max(observed_gap,gap)
                if not 0<gap<=max_gap:
                    errors.append(f"row {i}: invalid cadence")
            previous=elapsed
            if generation!=initial_generation:
                reconnects+=1
            observed_latency=max(observed_latency,latency)
            if latency>max_latency or status!="OK":
                failed+=1
        except (ValueError,TypeError,KeyError) as exc:
            errors.append(f"row {i}: {exc}")
    span=0. if first is None else previous-first
    return dict(passed=count>=2 and span>=86400 and not errors and not failed and not reconnects,
                rows=count,span_s=span,failed_attempts=failed,changed_generation_rows=reconnects,
                max_gap_s=observed_gap,max_latency_s=observed_latency,errors=errors)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind",choices=("accuracy","soak"))
    parser.add_argument("csv_file")
    parser.add_argument("--max-gap",type=float)
    parser.add_argument("--max-latency",type=float)
    args=parser.parse_args()
    with open(args.csv_file,newline="",encoding="utf-8") as f:
        rows=csv.DictReader(f)
        if args.kind=="accuracy":
            report=accuracy_report(rows)
        else:
            if args.max_gap is None or args.max_latency is None:
                parser.error("soak requires explicit gap and latency limits")
            report=soak_report(rows,max_gap=args.max_gap,max_latency=args.max_latency)
    print(json.dumps(report,indent=2))
    return int(not report["passed"])


if __name__=="__main__":
    raise SystemExit(main())
