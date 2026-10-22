# Security policy

B-CAD is currently a blueprint and contributor hub. **There is no supported add-on or native CAD-core release, and no runtime security support is claimed.** Security reports about this repository, its documentation tooling, workflows, or published website are still welcome.

## Report a vulnerability privately

If GitHub shows **Security → Report a vulnerability** for this repository, use that private reporting route. Start at the [repository security page](https://github.com/Ramses13th/B-CAD/security).

If private reporting is unavailable, use a contact method published by [@Ramses13th](https://github.com/Ramses13th). If no private channel is listed, open a minimal public issue requesting a confidential security contact **without exploit details, secrets, personal information, or private models**. Do not place an active credential in an issue or pull request. If you discover an exposed credential, notify its owner privately so it can be revoked.

Include the affected commit or URL, impact, prerequisites, safe reproduction steps, and any proposed fix. Use synthetic or appropriately licensed inputs. We will review reports as volunteer capacity allows; there is no guaranteed response time, bounty, or service-level agreement.

## Supported versions

| Version | Security support |
| --- | --- |
| Current planning repository | Best-effort review of repository and website issues. |
| B-CAD add-on / CAD core | Not released; no supported versions. |

Before runtime releases, this policy must be updated with supported versions, distribution verification, and a response process for native dependencies and file parsers.

## Security requirements for future implementation

These are design requirements to evaluate, not implemented protections:

- Treat CAD files, `.blend` data, external references, archives, and core-protocol messages as untrusted input. Bound resource use and diagnose malformed data.
- Parse user expressions through a restricted, typed language; do not use Python `eval()`.
- Define authentication or local-access constraints for the Blender-to-core boundary. Avoid exposing an unauthenticated CAD service to a network.
- Make dependency provenance, licenses, release checksums, and update behavior explicit.
- Avoid implicit script execution, unexpected network access, and leakage through logs, crash reports, or AI tools.
- Keep the canonical document recoverable after failed operations, undo, or a core crash.

Architecture changes in these areas should include a threat model and a [Design RFC](https://github.com/Ramses13th/B-CAD/issues/new?template=design_rfc.yml).
