# SaveOnSub Cloud Work Computer: implementation runbook (NO LIVE CHANGES)

## Tenant and source of truth
SaveOnSub only; no raw access to SYSmoAI, AIPS, AITP, SOFT SUPERSHOP or personal finance. Public site and staff Admin remain on Cloudflare Pages/Functions/Access. Orders, product versions, approvals, customer consent and costs use dedicated SOS D1. Media source and approved exports use private SOS R2. GitHub owns code and release evidence. Drive holds non-secret governance/handoffs. The Cloud PC is **replaceable compute**, never sole owner of transactional truth.

Current Corporate State previously verified a Google Cloud VM named sysmoaiprivatelimited (Debian 13, e2-standard-2, 2 vCPU / 8 GiB RAM, 50 GB disk), reachable then via Tailscale/XRDP. Live VM billing, access, free-trial remaining and Hermes runtime **must be reverified**.

## Why no new VPS or shared login now
Two humans and AI agents must not share a desktop browser, cloud owner password or operating-system root account. One already-paid VM may be sufficient for isolated, light jobs. A dedicated SOS VM is a later option if multi-tenant isolation fails, resource measurements justify it, contractual requirements demand it or expected costs support it.

## Authentication and build order
1. CEO independently signs in to Google Cloud, verifies billing project, instance, disk, backup, allowed principals, network/firewall and spend alerts. No surprise 24/7 charges.
2. From CEO-authorized SSH on the actual VM, run the read-only command: sh ops/sos-work-computer/sos_vm_preflight.sh . This outputs OS/CPU/RAM/disk/service state without secrets, IP addresses or credentials; it does not install or modify anything.
3. Choose private access. Preferred: Cloudflare Tunnel + Cloudflare Access to an isolated private web workspace or browser SSH. Do NOT open public TCP 22/3389. If actual Linux XRDP is necessary, verify per-user sessions and use approved commercial network access. Tailscale Personal free is NONCOMMERCIAL; business Standard has a seat price.
4. CEO approves distinct role-controlled identities:
   CEO owner: GCP billing/VM admin, SOS app ownership, secure recovery, release controls.
   Operator: separate non-sudo Unix account and mobile web Admin login, SOS-only directories. No root, sudo, shared browser profile, cloud owner account or other tenant access.
   Agent service: no interactive login, restricted container/mounts, CPU/RAM/egress budgets, separate scoped D1/R2 service tokens, audit and kill switch.
5. Only after security review, create a restrictive SOS workspace inside /srv/tenants/sos with private work/exports/logs/tmp directories. Never chmod 777, never copy other tenant secrets or grant root passwordless sudo.
6. Test parallel owner PC and operator iPhone sessions and revocation. Browser Admin is preferred for Ripon; a full remote desktop is optional and should be justified by concrete tasks.
7. Activate Cloudflare staging D1/R2/Access, migrations and the order system. Verify a synthetic customer order and product/image/video draft end-to-end before promoting any production route or changing customer checkouts.

## Safe command for initial preflight
sh ops/sos-work-computer/sos_vm_preflight.sh

The script is observational only. It does not create users, add network rules, install packages, change billing, start services or expose passwords.

## Compute / profitability considerations
- E2-standard-2 has 2 vCPU and 8 GiB; E2 instances do not support GPU. Do not promise on-box heavy video generation/transcoding on this host.
- Example US-region Google on-demand e2-standard-2 CPU+RAM ≈ USD 0.067/hour or USD 49 per 730-hour month, excluding disk, egress, local taxes, and variable region price. Real GCP project and billing must be checked.
- Cloudflare Zero Trust has Free offering for under 50 users and browser-protected SSH/private web apps. Use when the capabilities satisfy the task, subject to account policy and free limits.
- Tailscale commercial Standard advertised at USD 8/user/month; Personal free is not for commercial business use. Only select Tailscale after real remote desktop requirements are confirmed.
- All SaaS API/video model spending needs monthly cap and automatic alerts. No new VM or paid upgrade without CEO authorization.

## Roles, approvals and memory
Ripon: existing approved SOP, real payment review, fulfilment, renewals, product/creative drafts, documented exceptions, aggregate shift reports. CEO: pricing, unusual refund, provider authorization, money destinations, DNS, security, production publishing. AI agents: content research/creative previews, SEO drafts, code PR, tests, data quality without autonomous financial or live-publishing power.

Each agent job: tenant SOS, task id, owner, exact source evidence and approved policy version, idempotency key, cost budget, input/output reference, human review state, final live verification and resumable next action. Slack is NOT order memory. On restart consult SOS Brand Charter, Agent Permission Manifest, CEO Current State, D1 jobs, GitHub and sanitized handoff. Revoke service accounts per tenant.

## Acceptance gates
- [ ] Owner live VM and invoice/credit state verified; budget alerts enabled.
- [ ] Preflight performed on actual VM, not GitHub runner.
- [ ] Secrets/security history audited and old exposed keys rotated.
- [ ] Private access configured, no inbound public RDP/SSH, individual MFA.
- [ ] Non-sudo operator cannot view any other brand or CEO credentials.
- [ ] Agent sandbox cannot impersonate a human and can be stopped.
- [ ] Two independent parallel sessions tested.
- [ ] Synthetic product/image/video/order writes leave D1/R2 audit references.
- [ ] Agent can resume after reboot; VM shutdown leaves website/order system healthy.
- [ ] Backup/restore, emergency rollback and expense monitoring tested.
- [ ] CEO signs off production release.

## Related tasks
Parent SOS admin epic: https://github.com/sysmoai/saveonsub-store/issues/52
Cloudflare named access: https://github.com/sysmoai/saveonsub-store/issues/54
Business orders: https://github.com/sysmoai/saveonsub-store/issues/55
Media: https://github.com/sysmoai/saveonsub-store/issues/56
SEO/agents: https://github.com/sysmoai/saveonsub-store/issues/57
SOS VM pilot: https://github.com/sysmoai/saveonsub-store/issues/58

## Official references
Cloudflare private apps: https://developers.cloudflare.com/cloudflare-one/setup/secure-private-apps/
Cloudflare browser SSH: https://developers.cloudflare.com/cloudflare-one/setup/secure-private-apps/clientless-ssh/
Cloudflare plans: https://www.cloudflare.com/plans/zero-trust-services/
Cloudflare Pages D1/R2: https://developers.cloudflare.com/pages/functions/bindings/
Google GCE pricing: https://cloud.google.com/products/compute/pricing/general-purpose
Tailscale business licensing: https://tailscale.com/pricing
