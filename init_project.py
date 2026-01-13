import os
import secrets
from pathlib import Path
from datetime import datetime, timedelta

# Configuration
BASE_DIR = Path(__file__).resolve().parent
NGINX_DIR = BASE_DIR / 'nginx'
SSL_DIR = NGINX_DIR / 'ssl'
LOGS_DIR = NGINX_DIR / 'logs'
STATIC_DIRS = [
    BASE_DIR / 'static' / 'css',
    BASE_DIR / 'static' / 'js',
    BASE_DIR / 'static' / 'images',
    BASE_DIR / 'media',
    BASE_DIR / 'logs',
]

def generate_self_signed_cert():
    """Generate self-signed SSL certificate for local development."""
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
    except ImportError:
        print("❌ 'cryptography' library not found. Installing...")
        os.system('pip install cryptography')
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization

    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"California"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"My Grocery Store"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
    ])

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        # Valid for 1 year
        datetime.utcnow() + timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
        critical=False,
    ).sign(key, hashes.SHA256())

    # Write key
    with open(SSL_DIR / "privkey.pem", "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    # Write cert
    with open(SSL_DIR / "fullchain.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"✅ SSL certificates generated in {SSL_DIR}")

def create_directories():
    """Create necessary project directories."""
    directories = [NGINX_DIR, SSL_DIR, LOGS_DIR] + STATIC_DIRS
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"📁 Verified directory: {directory}")

def check_env():
    """Check if .env exists, if not create from example."""
    env_path = BASE_DIR / '.env'
    example_path = BASE_DIR / '.env.example'
    
    if not env_path.exists():
        if example_path.exists():
            content = example_path.read_text(encoding='utf-8')
            # Generate a secure secret key
            secret_key = secrets.token_urlsafe(50)
            content = content.replace('your-super-secret-key-here-change-in-production', secret_key)
            env_path.write_text(content, encoding='utf-8')
            print("✅ Created .env file from .env.example")
        else:
            print("⚠️ .env.example not found, skipping .env creation")
    else:
        print("✅ .env file exists")

def main():
    print("🚀 Initializing project environment...")
    create_directories()
    check_env()
    
    if not (SSL_DIR / "fullchain.pem").exists():
        print("🔒 Generating SSL certificates...")
        generate_self_signed_cert()
    else:
        print("✅ SSL certificates already exist")
        
    print("\n✨ Initialization complete! Now you can run:")
    print("   docker-compose up -d --build")

if __name__ == "__main__":
    main()
