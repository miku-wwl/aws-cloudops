#!/bin/bash
# 第 03 讲：在私有子网的服务器上用 systemd 启动一个监听 8080 的最小 HTTP 服务（AL2023 自带 python3）
set -euo pipefail
mkdir -p /opt/a02
echo "A02_OK" > /opt/a02/index.html
cat > /etc/systemd/system/a02-http.service <<'UNIT'
[Unit]
Description=A02 lab HTTP server on 8080
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/bin/python3 -m http.server 8080 --bind 0.0.0.0 --directory /opt/a02
Restart=always

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now a02-http.service
