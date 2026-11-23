---
name: sos-mac-qa
description: Use to run and record a Mac/iPhone acceptance test of a staging page or staff feature. Produces Expected / Observed / Device / Time / PASS-FAIL evidence with sensitive data redacted. Requires a human tester on the real device.
---
# sos-mac-qa
An AI cannot claim a device was tested. The human on the device runs each step; this skill structures the record.

For each step capture: `Step | Expected | Observed | Device (Mac Safari/Chrome, iPhone Safari, width) | Time (Dhaka) | PASS/FAIL/BLOCKED | Screenshot (redacted)`.

Always include a negative test: a limited operator must NOT see CEO finance, payment-verification controls or other brands' data; a denied request must be denied server-side (not just hidden in the UI).
Test mobile widths 320-430px. Do not use real customer data; use SYN- records in QA_SANDBOX only.
