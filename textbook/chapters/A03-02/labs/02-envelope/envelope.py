#!/usr/bin/env python3
"""envelope：在本地复现 Secrets Manager 的信封加密（第 07 讲实验 7-2，零费用）。

    python envelope.py

FakeKMS 用一个永不离开它的“根密钥”模拟 KMS 密钥：
  GenerateDataKey → 返回明文数据密钥 + 用根密钥加密后的数据密钥（加密上下文作为 AAD 绑定）
  Decrypt        → 只有加密上下文完全一致时才能解开数据密钥
SecretStore 模拟 Secrets Manager：用数据密钥（AES-256-GCM）在“KMS 之外”加密秘密值，
只保存密文与“加密后的数据密钥”，明文数据密钥用完即丢。
"""
from __future__ import annotations

import json
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class AccessDenied(Exception):
    pass


class FakeKMS:
    def __init__(self):
        self._root = AESGCM.generate_key(bit_length=256)    # 永不导出
        self.allowed_decrypt: set[str] = set()              # 模拟“谁有 kms:Decrypt”
        self.log: list[str] = []

    @staticmethod
    def _aad(ctx: dict) -> bytes:
        return json.dumps(ctx, sort_keys=True).encode()

    def generate_data_key(self, ctx: dict) -> tuple[bytes, bytes]:
        dk = AESGCM.generate_key(bit_length=256)
        nonce = os.urandom(12)
        self.log.append(f"GenerateDataKey ctx={ctx['SecretVersionId']}")
        return dk, nonce + AESGCM(self._root).encrypt(nonce, dk, self._aad(ctx))

    def decrypt(self, caller: str, blob: bytes, ctx: dict) -> bytes:
        self.log.append(f"Decrypt caller={caller}")
        if caller not in self.allowed_decrypt:
            raise AccessDenied(f"{caller} 没有 kms:Decrypt")
        try:
            return AESGCM(self._root).decrypt(blob[:12], blob[12:], self._aad(ctx))
        except InvalidTag:
            raise ValueError("InvalidCiphertextException：加密上下文不匹配") from None


class SecretStore:
    def __init__(self, kms: FakeKMS, arn: str):
        self.kms, self.arn, self.versions = kms, arn, {}
        self.readers: set[str] = set()                      # 模拟“谁有 secretsmanager:GetSecretValue”

    def put(self, version_id: str, value: str) -> None:
        ctx = {"SecretARN": self.arn, "SecretVersionId": version_id}
        dk, enc_dk = self.kms.generate_data_key(ctx)
        nonce = os.urandom(12)
        ct = nonce + AESGCM(dk).encrypt(nonce, value.encode(), None)
        del dk                                              # 明文数据密钥用完即丢
        self.versions[version_id] = (ct, enc_dk)

    def get(self, caller: str, version_id: str, tamper_ctx: bool = False) -> str:
        if caller not in self.readers:
            raise AccessDenied(f"{caller} 没有 secretsmanager:GetSecretValue")
        ct, enc_dk = self.versions[version_id]
        ctx = {"SecretARN": self.arn + ("-other" if tamper_ctx else ""), "SecretVersionId": version_id}
        dk = self.kms.decrypt(caller, enc_dk, ctx)
        return AESGCM(dk).decrypt(ct[:12], ct[12:], None).decode()


def demo() -> None:
    kms = FakeKMS()
    sm = SecretStore(kms, "arn:aws:secretsmanager:us-east-1:111122223333:secret:a07/demo-AbCdEf")
    sm.put("v1", "DEMO-NOT-A-PASSWORD")
    ct, enc_dk = sm.versions["v1"]
    print(f"存储内容：密文 {len(ct)} 字节 + 加密后的数据密钥 {len(enc_dk)} 字节（没有明文、没有明文数据密钥）")
    role = "assumed-role/a07-gh-reader"
    sm.readers.add(role)
    for step, fn in [
        ("① 有 GetSecretValue、没有 kms:Decrypt", lambda: sm.get(role, "v1")),
        ("② 补上 kms:Decrypt", lambda: (kms.allowed_decrypt.add(role), sm.get(role, "v1"))[1]),
        ("③ 加密上下文被篡改", lambda: sm.get(role, "v1", tamper_ctx=True)),
    ]:
        try:
            print(f"{step}：读取成功 → {fn()}")
        except (AccessDenied, ValueError) as e:
            print(f"{step}：失败 → {e}")
    print("KMS 调用记录：" + " | ".join(kms.log))


if __name__ == "__main__":
    demo()
