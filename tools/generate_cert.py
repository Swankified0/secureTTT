"""Generate a self-signed certificate for SecureTTT demos on one computer."""

from datetime import datetime, timedelta, timezone
from ipaddress import ip_address
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


CERT_DIR = Path(__file__).resolve().parent.parent / "certs"


def main():
    cert_path = CERT_DIR / "server.crt"
    key_path = CERT_DIR / "server.key"
    if cert_path.exists() or key_path.exists():
        print("Certificate or key already exists; nothing was overwritten.")
        print("To replace them, move both files out of certs/ and run again.")
        return

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=365)

    # This server signs its own certificate. Clients explicitly trust its
    # public certificate; the private key stays on this demo computer.
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(expires)
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ip_address("127.0.0.1")),
            ]),
            critical=False,
        )
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=True,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(key.public_key()),
            critical=False,
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(key.public_key()),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    CERT_DIR.mkdir(exist_ok=True)
    # Exclusive creation also prevents accidentally overwriting existing files.
    # No password is used so the demo server can load the key without a prompt.
    with key_path.open("xb") as key_file:
        key_file.write(key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ))
    with cert_path.open("xb") as cert_file:
        cert_file.write(certificate.public_bytes(serialization.Encoding.PEM))

    print(f"Public certificate: {cert_path}")
    print(f"Private key (keep local): {key_path}")
    print(f"Expires: {expires:%Y-%m-%d %H:%M UTC}")


if __name__ == "__main__":
    main()
