# Security Policy

## Supported Versions

We provide security and reliability updates for the latest code on the `main` branch.

| Branch / Release | Supported |
|------------------|-----------|
| `main`           | Yes       |
| Older releases   | No        |

---

## Reporting a Security Concern

The NovaGhost project prioritizes user privacy and security. Because this application operates strictly as a local-only tool without cloud user management, security considerations primarily relate to:

- Safe local credential storage (`~/.novaghost/settings.json`)
- Safe execution of symbolic expressions without arbitrary code evaluation
- Screen capture boundaries and window display exclusion
- Secure handling of local API requests to vision providers

If you discover a potential vulnerability or security flaw, please do not disclose it publicly in an open issue.

Instead, please report it directly by:
1. Creating a private security advisory through the GitHub repository security tab, or
2. Contacting the project maintainer via GitHub profile contact information.

Please include:
- A description of the vulnerability
- Steps or a minimal script to reproduce the issue
- Potential impact on users or host systems

We will acknowledge receipt of your report promptly and work to address and patch confirmed issues as quickly as possible.
