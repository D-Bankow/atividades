#!/usr/bin/env python3
"""
secure_msg.py

Exemplo: Cliente/Servidor TCP com criptografia simétrica (AES-CBC) + HMAC-SHA256.
Modo: execute o arquivo e escolha '1' para servidor ou '2' para cliente.

Requer: cryptography
pip install cryptography
"""

import socket
import json
import struct
import base64
import os
import sys
from hashlib import sha256
from cryptography.hazmat.primitives import padding, hashes, hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

# --------------------------
# Helpers criptográficos
# --------------------------

def derive_keys_from_password(password: bytes, salt: bytes = None):
    """
    Deriva 64 bytes (512 bits) e separa em duas chaves:
    - enc_key (32 bytes) para AES-256
    - mac_key (32 bytes) para HMAC-SHA256
    Usa PBKDF2-HMAC-SHA256.
    """
    if salt is None:
        salt = b"static_salt_educacional"  # em produção gere aleatório e compartilhe
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=64,
        salt=salt,
        iterations=200_000,
        backend=default_backend()
    )
    key_material = kdf.derive(password)
    return key_material[:32], key_material[32:], salt

def aes_cbc_encrypt(plaintext: bytes, key: bytes):
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    pt_padded = padder.update(plaintext) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ct = encryptor.update(pt_padded) + encryptor.finalize()
    return iv, ct

def aes_cbc_decrypt(iv: bytes, ciphertext: bytes, key: bytes):
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    pt_padded = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    pt = unpadder.update(pt_padded) + unpadder.finalize()
    return pt

def compute_hmac(key: bytes, data: bytes):
    h = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
    h.update(data)
    return h.finalize()

def verify_hmac(key: bytes, data: bytes, tag: bytes):
    h = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
    h.update(data)
    try:
        h.verify(tag)
        return True
    except Exception:
        return False

# --------------------------
# Helpers de rede
# --------------------------

def send_json_with_len(sock: socket.socket, obj: dict):
    payload = json.dumps(obj).encode('utf-8')
    header = struct.pack("!I", len(payload))
    sock.sendall(header + payload)

def recv_json_with_len(sock: socket.socket):
    header = recvall(sock, 4)
    if not header:
        return None
    (length,) = struct.unpack("!I", header)
    payload = recvall(sock, length)
    if not payload:
        return None
    return json.loads(payload.decode('utf-8'))

def recvall(sock: socket.socket, n: int):
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

# --------------------------
# Servidor
# --------------------------

def server_main(host='127.0.0.1', port=8000, password="senha_compartilhada"):
    password_b = password.encode('utf-8')
    enc_key, mac_key, salt = derive_keys_from_password(password_b)

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(5)
    print(f"[Servidor] Ouvindo em {host}:{port}")

    try:
        while True:
            conn, addr = srv.accept()
            print(f"[Servidor] Conexão de {addr}")
            handle_client_connection(conn, enc_key, mac_key, salt)
    except KeyboardInterrupt:
        print("\n[Servidor] Encerrando")
    finally:
        srv.close()

def handle_client_connection(conn: socket.socket, enc_key: bytes, mac_key: bytes, salt: bytes):
    with conn:
        # primeiro, opcional, cliente pode enviar salt (se estiver usando salt aleatório)
        # neste exemplo salt é fixo; se quiser dinamizar, negocie salt aqui.
        while True:
            msg = recv_json_with_len(conn)
            if msg is None:
                print("[Servidor] Cliente desconectou")
                break

            # msg deve ter: iv, ciphertext, hmac (todos em base64)
            try:
                iv = base64.b64decode(msg['iv'])
                ct = base64.b64decode(msg['ciphertext'])
                tag = base64.b64decode(msg['hmac'])
            except Exception:
                print("[Servidor] Formato inválido")
                continue

            # Verifica integridade: HMAC sobre iv || ciphertext
            data_to_mac = iv + ct
            if not verify_hmac(mac_key, data_to_mac, tag):
                print("[Servidor] HMAC inválido! Mensagem rejeitada (integridade falhou).")
                # opcional: enviar resposta de falha
                send_json_with_len(conn, {"status": "error", "reason": "integrity_failed"})
                continue

            # Se HMAC OK, decripta
            try:
                pt = aes_cbc_decrypt(iv, ct, enc_key)
                texto = pt.decode('utf-8')
                print(f"[Servidor] Mensagem segura recebida: {texto}")
                send_json_with_len(conn, {"status": "ok", "message": "received"})
            except Exception as e:
                print("[Servidor] Erro ao decriptar:", e)
                send_json_with_len(conn, {"status": "error", "reason": "decrypt_failed"})

# --------------------------
# Cliente
# --------------------------

def client_main(host='127.0.0.1', port=8000, password="senha_compartilhada"):
    password_b = password.encode('utf-8')
    enc_key, mac_key, salt = derive_keys_from_password(password_b)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    print(f"[Cliente] Conectado a {host}:{port}")
    try:
        while True:
            texto = input("Texto a enviar (ou 'sair'): ")
            if texto.lower() in ('sair', 'exit'):
                break
            pt = texto.encode('utf-8')
            iv, ct = aes_cbc_encrypt(pt, enc_key)
            data_to_mac = iv + ct
            tag = compute_hmac(mac_key, data_to_mac)

            msg = {
                "iv": base64.b64encode(iv).decode('utf-8'),
                "ciphertext": base64.b64encode(ct).decode('utf-8'),
                "hmac": base64.b64encode(tag).decode('utf-8'),
                # "salt": base64.b64encode(salt).decode('utf-8')  # opcional
            }
            send_json_with_len(s, msg)

            # espera resposta do servidor
            resp = recv_json_with_len(s)
            if resp is None:
                print("[Cliente] Servidor desconectou")
                break
            print("[Cliente] Servidor respondeu:", resp)
    finally:
        s.close()

# --------------------------
# Main: escolha modo
# --------------------------

if __name__ == "__main__":
    print("Secure Messaging (AES-CBC + HMAC-SHA256)")
    print("1 - Servidor")
    print("2 - Cliente")
    choice = input("Escolha: ").strip()
    if choice == "1":
        server_main()
    elif choice == "2":
        client_main()
    else:
        print("Opção inválida.")
