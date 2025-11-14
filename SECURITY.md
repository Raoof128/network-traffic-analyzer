# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.1.x   | :white_check_mark: |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of Network Traffic Analyzer seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Please Do NOT:

- Open a public GitHub issue for security vulnerabilities
- Disclose the vulnerability publicly before it has been addressed
- Exploit the vulnerability beyond what is necessary to demonstrate it

### Please DO:

**Report security vulnerabilities privately** using one of these methods:

1. **GitHub Security Advisories** (Preferred)
   - Go to the [Security tab](https://github.com/Raoof128/network-traffic-analyzer/security)
   - Click "Report a vulnerability"
   - Fill out the advisory form

2. **Email**
   - Send an email to: [security@example.com] (Replace with actual contact)
   - Use PGP encryption if possible (key available on request)

### What to Include in Your Report

Please provide the following information:

- **Type of vulnerability** (e.g., SQL injection, XSS, command injection, etc.)
- **Full paths** of source file(s) related to the vulnerability
- **Location** of the affected source code (tag/branch/commit or direct URL)
- **Step-by-step instructions** to reproduce the issue
- **Proof-of-concept or exploit code** (if available)
- **Impact** of the vulnerability and how an attacker might exploit it
- **Potential mitigations** if you have any suggestions

### What to Expect

After you submit a vulnerability report:

1. **Acknowledgment**: We will acknowledge receipt within 48 hours
2. **Initial Assessment**: We will provide an initial assessment within 7 days
3. **Updates**: We will keep you informed about our progress
4. **Resolution**: We aim to resolve critical issues within 30 days
5. **Disclosure**: We will coordinate with you on public disclosure timing

### Vulnerability Disclosure Timeline

- **Day 0**: Vulnerability reported privately
- **Day 1-2**: Acknowledgment sent to reporter
- **Day 3-7**: Initial assessment and severity classification
- **Day 7-30**: Development and testing of fix
- **Day 30-45**: Release of patched version
- **Day 45-60**: Public disclosure (coordinated with reporter)

## Security Best Practices

When using Network Traffic Analyzer, please follow these security best practices:

### 1. Secure Model Files

- Always use secure pickle loading (enabled by default in v1.1.0+)
- Only load model files from trusted sources
- Verify model integrity using HMAC if handling sensitive data
- Never load pickle files from untrusted or unverified sources

```python
# Good - uses secure loading
from utils.secure_pickle import safe_load
model = safe_load('model.pkl', restricted=True)

# Bad - unsafe loading (deprecated)
import pickle
with open('model.pkl', 'rb') as f:
    model = pickle.load(f)  # Vulnerable to code injection!
```

### 2. Input Validation

- Always validate input files, interfaces, and parameters
- Use the built-in InputValidator class
- Never trust user-provided file paths without validation

```python
from utils.validators import InputValidator, ValidationError

# Validate PCAP file before processing
try:
    pcap_path = InputValidator.validate_pcap_file(user_provided_path)
except ValidationError as e:
    print(f"Invalid input: {e}")
```

### 3. Network Capture Permissions

- Run packet capture with minimum required privileges
- Use capabilities instead of running as root when possible
- Limit capture interfaces to specific interfaces

```bash
# Good - use capabilities
sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/python3.x
python analyzer.py --mode realtime --interface eth0

# Avoid - running as root
sudo python analyzer.py  # Not recommended
```

### 4. Configuration Security

- Never commit `.env` files or configuration files with secrets
- Use environment variables for sensitive data
- Rotate credentials regularly
- Use app-specific passwords for email alerts

```bash
# Good - use environment variables
export NTA_EMAIL_PASSWORD="app_specific_password"
export NTA_WEBHOOK_TOKEN="secret_token"

# Bad - hardcoding secrets
EMAIL_PASSWORD = "mypassword123"  # Never do this!
```

### 5. API Security

- Always use HTTPS in production
- Implement rate limiting
- Use authentication tokens
- Validate all API inputs
- Enable CORS only for trusted origins

```python
# Example secure API configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://trusted-domain.com"],  # Not "*"
    allow_credentials=True,
)
```

### 6. Docker Security

- Run containers as non-root user (already configured)
- Keep base images updated
- Scan images for vulnerabilities
- Use secrets management for sensitive data
- Limit container capabilities

```bash
# Scan Docker image for vulnerabilities
docker scan network-traffic-analyzer:latest

# Run with limited capabilities
docker run --cap-drop=ALL --cap-add=NET_RAW network-traffic-analyzer
```

### 7. Dependency Management

- Keep all dependencies up to date
- Use Dependabot for automated updates (configured)
- Review security advisories regularly
- Pin dependency versions in production

```bash
# Check for vulnerable dependencies
pip install safety
safety check -r requirements.txt

# Update dependencies
pip install --upgrade -r requirements.txt
```

## Known Security Features

### v1.1.0 Security Enhancements

- **Secure Pickle Loading**: Whitelist-based class loading prevents arbitrary code execution
- **HMAC Verification**: Optional integrity verification for model files
- **Input Validation**: Comprehensive validation system prevents path traversal and injection attacks
- **Bandit Integration**: Automated security scanning in pre-commit hooks
- **Non-root Containers**: Docker containers run as non-root user by default
- **Secrets Management**: Environment variable-based configuration

### Security Tools Integrated

- **Bandit**: Python security linter (SAST)
- **Safety**: Dependency vulnerability scanner
- **Pre-commit hooks**: Automated security checks
- **MyPy**: Type checking to prevent type-related bugs

## Security Advisories

Security advisories for this project will be published at:
- [GitHub Security Advisories](https://github.com/Raoof128/network-traffic-analyzer/security/advisories)
- [CHANGELOG.md](CHANGELOG.md) (Security section)

## Bug Bounty Program

We do not currently have a bug bounty program. However, we deeply appreciate security researchers who responsibly disclose vulnerabilities and will publicly acknowledge your contribution (with your permission) in:

- Security advisories
- Release notes
- CHANGELOG.md
- AUTHORS.md

## Security Hardening Checklist

Before deploying to production:

- [ ] Use secure pickle loading (v1.1.0+)
- [ ] Enable HMAC verification for model files
- [ ] Validate all user inputs
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS for API endpoints
- [ ] Implement rate limiting
- [ ] Configure firewall rules
- [ ] Set up log monitoring and alerting
- [ ] Keep dependencies updated
- [ ] Run security scans (Bandit, Safety)
- [ ] Review OWASP Top 10 vulnerabilities
- [ ] Conduct penetration testing (if applicable)
- [ ] Enable Docker security scanning
- [ ] Use secrets management system
- [ ] Implement intrusion detection
- [ ] Regular security audits

## Common Vulnerabilities and Mitigations

### 1. Arbitrary Code Execution via Pickle

**Vulnerability**: Malicious pickle files can execute arbitrary code
**Mitigation**: Use `safe_load()` from `utils.secure_pickle` (v1.1.0+)
**Status**: ✅ Fixed in v1.1.0

### 2. Path Traversal

**Vulnerability**: User-provided file paths could access arbitrary files
**Mitigation**: Use `InputValidator.validate_file_exists()` with path normalization
**Status**: ✅ Fixed in v1.1.0

### 3. Command Injection via BPF Filters

**Vulnerability**: Malicious BPF filters could be exploited
**Mitigation**: Use `InputValidator.validate_bpf_filter()` with pattern matching
**Status**: ✅ Fixed in v1.1.0

### 4. Credential Exposure in Logs

**Vulnerability**: Passwords/tokens could be logged
**Mitigation**: Sanitize logs, use environment variables, never log secrets
**Status**: ✅ Mitigated in v1.1.0

## Security Update Policy

- **Critical vulnerabilities**: Patched within 7 days
- **High severity**: Patched within 30 days
- **Medium severity**: Patched within 90 days
- **Low severity**: Patched in next scheduled release

## Security Contacts

- **Security Team**: [INSERT EMAIL]
- **GitHub Security**: https://github.com/Raoof128/network-traffic-analyzer/security

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/archive/2023/2023_top25_list.html)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)

---

**Last Updated**: November 14, 2025
**Version**: 1.1.0
