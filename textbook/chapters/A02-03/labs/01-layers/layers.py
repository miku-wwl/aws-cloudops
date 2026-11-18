#!/usr/bin/env python3
"""layers：逐层验证“访问一个 AWS API”的五道门（第 05 讲实验 5-1 / 5-3）。

    python layers.py ssm.us-east-1.amazonaws.com                 # DNS → TCP → TLS → HTTP
    python layers.py ssm.us-east-1.amazonaws.com --api ssm       # 再加一层：签名后的 API 调用
同一份代码也是实验 5-3 中 VPC 内 Lambda 探针的 handler（见 handler()）。
任何一层失败就停止：前一层成功，不代表后一层一定成功。
"""
from __future__ import annotations

import argparse
import http.client
import ipaddress
import json
import os
import socket
import ssl
import time


def t_ms(t0: float) -> str:
    return f"{(time.perf_counter() - t0) * 1000:.0f} ms"


def check_dns(host: str):
    t0 = time.perf_counter()
    ips = sorted({a[4][0] for a in socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)})
    private = all(ipaddress.ip_address(i).is_private for i in ips)
    return ips, private, t_ms(t0)


def check_tcp(ip: str, timeout: float = 3.0):
    t0 = time.perf_counter()
    with socket.create_connection((ip, 443), timeout=timeout):
        pass
    return t_ms(t0)


def check_tls(host: str, ip: str, timeout: float = 3.0):
    t0 = time.perf_counter()
    ctx = ssl.create_default_context()
    with socket.create_connection((ip, 443), timeout=timeout) as raw:
        with ctx.wrap_socket(raw, server_hostname=host) as s:
            cert = s.getpeercert()
            names = [v for k, v in cert.get("subjectAltName", []) if k == "DNS"]
            return s.version(), names[:2], t_ms(t0)


def check_http(host: str, timeout: float = 5.0):
    """不带签名的请求：服务若返回任何 HTTP 状态码，说明网络与 TLS 都已打通。"""
    t0 = time.perf_counter()
    c = http.client.HTTPSConnection(host, timeout=timeout)
    c.request("GET", "/")
    r = c.getresponse()
    return r.status, r.reason, t_ms(t0)


def check_api_cli(kind: str, region: str):
    """本机没有 boto3 时，改用 AWS CLI 发出同一个签名请求。"""
    import re
    import subprocess

    name = os.environ.get("PARAM", "/cloudops/a05/does-not-exist")
    cmd = ["aws", "ssm", "get-parameter", "--name", name, "--region", region, "--output", "json"]
    t0 = time.perf_counter()
    r = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ, MSYS_NO_PATHCONV="1"))
    if r.returncode == 0:
        return True, "GetParameter → 成功", t_ms(t0)
    m = re.search(r"\((\w+)\)", r.stderr)
    code = m.group(1) if m else r.stderr.strip()[:60]
    reached = code in ("ParameterNotFound",)
    return reached, f"{code}（{'已到达服务并通过授权' if reached else '服务拒绝'}，AWS CLI）", t_ms(t0)


def check_api(kind: str, region: str):
    try:
        import boto3
        from botocore.config import Config
        from botocore.exceptions import ClientError
    except ImportError:
        if kind == "ssm":
            return check_api_cli(kind, region)
        raise

    cfg = Config(connect_timeout=3, read_timeout=5, retries={"max_attempts": 1})
    t0 = time.perf_counter()
    try:
        if kind == "ssm":
            name = os.environ.get("PARAM", "/cloudops/a05/does-not-exist")
            v = boto3.client("ssm", region_name=region, config=cfg).get_parameter(Name=name)["Parameter"]["Value"]
            return True, f"GetParameter → {v}", t_ms(t0)
        bucket, key = os.environ["BUCKET"], os.environ.get("KEY", "hello.txt")
        body = boto3.client("s3", region_name=region, config=cfg).get_object(Bucket=bucket, Key=key)["Body"].read()
        return True, f"GetObject → {body.decode()[:40]}", t_ms(t0)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        # ParameterNotFound / NoSuchKey：请求已被服务受理并完成授权，只是对象不存在
        reached = code in ("ParameterNotFound", "NoSuchKey")
        return reached, f"{code}（{'已到达服务并通过授权' if reached else '服务拒绝'}）", t_ms(t0)


def run(host: str, api: str | None, region: str) -> list[dict]:
    steps: list[dict] = []

    def add(layer, ok, detail):
        steps.append({"layer": layer, "ok": ok, "detail": detail})
        return ok

    try:
        ips, private, t = check_dns(host)
        add("DNS", True, f"{host} → {', '.join(ips[:4])}（{'私有地址' if private else '公网地址'}，{t}）")
    except OSError as e:
        add("DNS", False, f"解析失败：{e}")
        return steps
    try:
        add("TCP", True, f"{ips[0]}:443 建连成功（{check_tcp(ips[0])}）")
    except OSError as e:
        add("TCP", False, f"{ips[0]}:443 {type(e).__name__}：{e}（查路由 / NACL / 两端安全组）")
        return steps
    try:
        ver, names, t = check_tls(host, ips[0])
        add("TLS", True, f"{ver}，证书 SAN 含 {names}（{t}）")
    except (OSError, ssl.SSLError) as e:
        add("TLS", False, f"握手失败：{e}")
        return steps
    try:
        st, reason, t = check_http(host)
        add("HTTP", True, f"未签名请求得到 HTTP {st} {reason}（{t}）——服务已响应")
    except OSError as e:
        add("HTTP", False, f"{e}")
        return steps
    if api:
        try:
            ok, detail, t = check_api(api, region)
            add("API", ok, f"{detail}（{t}）")
        except Exception as e:  # noqa: BLE001 —— 教学探针：把任何异常都作为证据输出
            add("API", False, f"{type(e).__name__}: {e}")
    return steps


def handler(event, context):
    """Lambda 入口：event = {"mode": "dns" | "s3" | "ssm"}。"""
    region = os.environ.get("AWS_REGION", "us-east-1")
    mode = (event or {}).get("mode", "ssm")
    host = {"s3": f"s3.{region}.amazonaws.com", "ssm": f"ssm.{region}.amazonaws.com", "dns": f"ssm.{region}.amazonaws.com"}[mode]
    steps = run(host, None if mode == "dns" else mode, region)
    if mode == "dns":
        steps = steps[:1]
    return {"mode": mode, "ok": all(s["ok"] for s in steps), "steps": steps}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("host")
    ap.add_argument("--api", choices=["ssm", "s3"])
    ap.add_argument("--region", default="us-east-1")
    a = ap.parse_args()
    for s in run(a.host, a.api, a.region):
        print(f"  {'✓' if s['ok'] else '✗'} {s['layer']:<4} {s['detail']}")


if __name__ == "__main__":
    main()
