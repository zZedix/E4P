# Encryption 4 People (E4P)

A secure, modern web application for encrypting files with strong cryptography. E4P provides client-side encryption using industry-standard algorithms and key derivation functions, ensuring your files remain secure even if the server is compromised.

## 🔐 Security Features

- **Strong Encryption**: AES-256-GCM and XChaCha20-Poly1305 algorithms
- **Secure Key Derivation**: Argon2id with configurable parameters
- **No Key Storage**: Keys are never stored on the server
- **Streaming Encryption**: Handles large files without memory issues
- **Authenticated Encryption**: Prevents tampering and ensures integrity
- **Secure Download Tokens**: Time-limited, HMAC-signed download links

## 🚀 Quick Start

### One-Line Installation & Run

**Linux/macOS:**
```bash
git clone https://github.com/zZedix/E4P.git && cd E4P && chmod +x install.sh && ./install.sh
```

**Windows:**
```cmd
git clone https://github.com/zZedix/E4P.git && cd E4P && install.bat
```


### Manual Installation

1. **Clone and setup**:
   ```bash
   git clone https://github.com/zZedix/E4P.git
   cd E4P
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your settings
   ```

3. **Run the application**:
   ```bash
   python run.py
   ```

4. **Access the application**:
   Open http://localhost:8080 in your browser

### Docker Deployment

1. **Using Docker Compose** (recommended):
   ```bash
   # Generate a secure secret key
   openssl rand -base64 32
   
   # Set the secret key in .env
   echo "SECRET_KEY=your_generated_secret_key" > .env
   
   # Start the application
   docker-compose up -d
   ```

2. **Using Docker directly**:
   ```bash
   # Build the image
   docker build -t e4p .
   
   # Run the container
   docker run -p 8080:8080 \
     -e SECRET_KEY=your_generated_secret_key \
     -v e4p_temp:/tmp/e4p \
     e4p
   ```

## 📁 E4P File Format

E4P uses a custom binary container format with the following structure:

```
+------------------+
| Magic: "E4P1"    | 4 bytes
+------------------+
| Header Length    | 4 bytes (little-endian uint32)
+------------------+
| Header JSON      | Variable length
+------------------+
| Encrypted Data   | Variable length
+------------------+
```

### Header JSON Structure

```json
{
  "alg": "AES-256-GCM" | "XCHACHA20-POLY1305",
  "kdf": "argon2id",
  "kdf_params": {
    "m": 262144,  // Memory cost in KB
    "t": 3,       // Time cost
    "p": 2        // Parallelism
  },
  "salt": "base64_encoded_salt",
  "nonce": "base64_encoded_nonce",
  "orig_name": "original_filename.txt",
  "orig_size": 1024,
  "ts": "2024-01-01T00:00:00Z"
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_HOST` | `0.0.0.0` | Server host |
| `APP_PORT` | `8080` | Server port |
| `MAX_FILE_SIZE_MB` | `2048` | Maximum file size in MB |
| `MAX_CONCURRENCY` | `2` | Maximum concurrent encryption tasks |
| `ARGON2_MEMORY_MB` | `256` | Argon2id memory cost in MB |
| `ARGON2_TIME_COST` | `3` | Argon2id time cost |
| `ARGON2_PARALLELISM` | `2` | Argon2id parallelism |
| `ARGON2_KEY_LEN` | `32` | Derived key length in bytes |
| `CLEAN_INTERVAL_MIN` | `5` | Cleanup interval in minutes |
| `FILE_TTL_MIN` | `60` | File time-to-live in minutes |
| `DOWNLOAD_TOKEN_TTL_S` | `900` | Download token TTL in seconds |
| `SECRET_KEY` | `change_me_to_random_base64` | Secret key for token signing |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | `60` | Rate limit for API requests |

### Tuning KDF Parameters

The Argon2id parameters can be tuned based on your hardware:

**For faster encryption (less secure)**:
```env
ARGON2_MEMORY_MB=64
ARGON2_TIME_COST=2
ARGON2_PARALLELISM=1
```

**For maximum security (slower)**:
```env
ARGON2_MEMORY_MB=512
ARGON2_TIME_COST=5
ARGON2_PARALLELISM=4
```

**Recommended for production**:
```env
ARGON2_MEMORY_MB=256
ARGON2_TIME_COST=3
ARGON2_PARALLELISM=2
```

## 🌐 API Reference

### Encryption Endpoints

#### `POST /api/encrypt`
Encrypt one or more files.

**Request**:
- `files`: List of files (multipart/form-data)
- `password`: User password (form field)
- `algorithm`: "AES-256-GCM" or "XCHACHA20-POLY1305" (form field)

**Response**:
```json
{
  "task_id": "uuid",
  "files": [
    {
      "original_name": "file.txt",
      "size": 1024
    }
  ],
  "algorithm": "AES-256-GCM",
  "status": "pending"
}
```

#### `GET /api/status/{task_id}`
Get encryption task status.

**Response**:
```json
{
  "task_id": "uuid",
  "status": "completed",
  "progress": 100.0,
  "files": [...],
  "created_at": "2024-01-01T00:00:00Z",
  "completed_at": "2024-01-01T00:01:00Z"
}
```

### Decryption Endpoints

#### `POST /api/decrypt`
Decrypt an E4P file.

**Request**:
- `file`: E4P file (multipart/form-data)
- `password`: User password (form field)

**Response**:
```json
{
  "download_token": "base64_token",
  "filename": "original_file.txt",
  "size": 1024,
  "algorithm": "AES-256-GCM",
  "status": "success"
}
```

### Download Endpoints

#### `GET /download/{token}`
Download encrypted or decrypted file using secure token.

#### `GET /download-stream/{token}`
Stream download for large files.

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_encrypt_flow.py -v
```

## 🛡️ Security Considerations

### What E4P Protects Against

- **Server Compromise**: Keys are never stored on the server
- **Network Interception**: All data is encrypted before transmission
- **File Tampering**: Authenticated encryption prevents modification
- **Replay Attacks**: Unique nonces for each encryption operation
- **Brute Force**: Argon2id makes password cracking computationally expensive

### What E4P Does NOT Protect Against

- **Lost Passwords**: Keys are derived from passwords; lost password = lost data
- **Malicious Server**: Server could log passwords or modify client-side code
- **Client-Side Attacks**: Malware on user's device could steal passwords
- **Side-Channel Attacks**: Timing attacks on password verification

### Best Practices

1. **Use Strong Passwords**: At least 12 characters with mixed case, numbers, and symbols
2. **Keep Passwords Safe**: Store in a password manager
3. **Verify Downloads**: Check file integrity after download
4. **Use HTTPS**: Always access over encrypted connections
5. **Regular Updates**: Keep the application updated

## 🌍 Internationalization

E4P supports multiple languages:

- **English** (default)
- **Persian/Farsi** (فارسی)

Language can be switched using the dropdown in the navigation bar. The interface automatically adjusts text direction for RTL languages.

## 🏗️ Architecture

```
e4p/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── crypto/              # Cryptography modules
│   │   ├── kdf.py          # Key derivation functions
│   │   ├── aead.py         # Encryption algorithms
│   │   ├── container.py    # E4P file format
│   │   └── stream.py       # Streaming encryption
│   ├── routes/             # API endpoints
│   │   ├── encrypt.py      # Encryption endpoints
│   │   ├── decrypt.py      # Decryption endpoints
│   │   └── download.py     # Download endpoints
│   ├── services/           # Business logic
│   │   ├── tasks.py        # Task management
│   │   ├── storage.py      # File storage
│   │   └── tokens.py       # Token management
│   ├── templates/          # HTML templates
│   └── static/             # CSS/JS assets
├── tests/                  # Test suite
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose setup
└── requirements.txt       # Python dependencies
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This software is provided "as is" without warranty. The authors are not responsible for any data loss or security breaches. Always backup your data and use strong passwords.

## 🔗 Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Cryptography Library](https://cryptography.io/)
- [Argon2 Specification](https://github.com/P-H-C/phc-winner-argon2)
- [AES-GCM Specification](https://tools.ietf.org/html/rfc5288)
- [XChaCha20-Poly1305 Specification](https://tools.ietf.org/html/draft-irtf-cfrg-xchacha)
