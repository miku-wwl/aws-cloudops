#!/usr/bin/env python3
"""用 AWS Price List API（免费、只读）刷新 prices.json（第 19 讲实验 19-2）。

    python fetch_prices.py > prices.json
"""
import json
import subprocess
from datetime import date

LOC = "US East (N. Virginia)"
ITEMS = {
    "ec2_t4g_nano_hour": ("AmazonEC2", {"location": LOC, "instanceType": "t4g.nano", "operatingSystem": "Linux",
                                        "tenancy": "Shared", "preInstalledSw": "NA", "capacitystatus": "Used"}),
    "ebs_gp3_gb_month": ("AmazonEC2", {"location": LOC, "usagetype": "EBS:VolumeUsage.gp3"}),
    "ebs_snapshot_gb_month": ("AmazonEC2", {"location": LOC, "usagetype": "EBS:SnapshotUsage"}),
    "public_ipv4_hour": ("AmazonVPC", {"location": LOC, "usagetype": "USE1-PublicIPv4:InUseAddress"}),
    "logs_ingest_gb": ("AmazonCloudWatch", {"location": LOC, "usagetype": "USE1-DataProcessing-Bytes"}),
    "logs_storage_gb_month": ("AmazonCloudWatch", {"location": LOC, "usagetype": "USE1-TimedStorage-ByteHrs"}),
}


def price(service, filters):
    cmd = ["aws", "pricing", "get-products", "--region", "us-east-1", "--service-code", service,
           "--output", "json", "--query", "PriceList", "--filters"]
    cmd += [f"Type=TERM_MATCH,Field={k},Value={v}" for k, v in filters.items()]
    for s in json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout):
        p = json.loads(s)
        for t in p["terms"].get("OnDemand", {}).values():
            for d in t["priceDimensions"].values():
                return float(d["pricePerUnit"]["USD"]), d["unit"], p["product"]["attributes"]["usagetype"]
    raise SystemExit(f"no price for {filters}")


out = {"source": "AWS Price List API", "region": "us-east-1", "date": date.today().isoformat(), "prices": {}}
for key, (svc, f) in ITEMS.items():
    usd, unit, usage_type = price(svc, f)
    out["prices"][key] = {"usd": usd, "unit": unit, "usage_type": usage_type}
print(json.dumps(out, ensure_ascii=False, indent=2))
