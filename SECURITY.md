# Security policy

B-CAD has an experimental local CAD workbench and Blender adapter. **There is no supported production release or runtime security support promise.** Reports about the implementation, native parsing boundary, documentation tooling, workflows and published website are welcome.

## Report a vulnerability privately

If GitHub shows **Security → Report a vulnerability** for this repository, use that private reporting route. Start at the [repository security page](https://github.com/Ramses13th/B-CAD/security).

If private reporting is unavailable, use a contact method published by [@Ramses13th](https://github.com/Ramses13th). If no private channel is listed, open a minimal public issue requesting a confidential security contact **without exploit details, secrets, personal information, or private models**. Do not place an active credential in an issue or pull request. If you discover an exposed credential, notify its owner privately so it can be revoked.

Include the affected commit or URL, impact, prerequisites, safe reproduction steps, and any proposed fix. Use synthetic or appropriately licensed inputs. We will review reports as volunteer capacity allows; there is no guaranteed response time, bounty, or service-level agreement.

## Supported versions

| Version | Security support |
| --- | --- |
| Current experimental source | Best-effort review of repository, runtime and website issues. |
| Production add-on / CAD core | Not released; no supported versions. |

Before runtime releases, this policy must be updated with supported versions, distribution verification, and a response process for native dependencies and file parsers.

## Experimental runtime boundary

The workbench binds to `127.0.0.1`, checks the HTTP Host and API Origin/fetch context, and requires a random per-process token for document access and mutations. It exposes no remote-file-path API or CORS permissions. It is a local development service; do not publish it through a tunnel or bind it to a public interface. Stop it when finished.

Length expressions use a restricted AST interpreter, not Python evaluation. Document/STEP bytes, imported topology and preview triangles are bounded. The host starts a separate worker with a deadline; failed validation or native evaluation cannot commit a new document. Native file parsing still runs with the current user's OS privileges: process separation is not an OS sandbox, and byte limits do not bound every native allocation. Review imported files and native dependency provenance accordingly.

The add-on archive contains original Python source and repository license notices; users install pinned native wheels separately. Binary redistribution, signed artifacts, clean-machine installation and a full native dependency inventory remain release gates.

## Security requirements for further implementation

These broader requirements remain review criteria, beyond the bounded protections above:

- Treat CAD files, `.blend` data, external references, archives, and core-protocol messages as untrusted input. Bound resource use and diagnose malformed data.
- Parse user expressions through a restricted, typed language; do not use Python `eval()`.
- Define authentication or local-access constraints for the Blender-to-core boundary. Avoid exposing an unauthenticated CAD service to a network.
- Make dependency provenance, licenses, release checksums, and update behavior explicit.
- Avoid implicit script execution, unexpected network access, and leakage through logs, crash reports, or AI tools.
- Keep the canonical document recoverable after failed operations, undo, or a core crash.

Architecture changes in these areas should include a threat model and a [Design RFC](https://github.com/Ramses13th/B-CAD/issues/new?template=design_rfc.yml).
