#!/usr/bin/env python3
"""Report a confirmed SaveOnSub order to Meta (Conversions API).

Payment is confirmed by a human (bKash/Nagad/Rocket), so the browser cannot
know when a sale really happened. Run this once per order AFTER payment is
verified, with the details from the WhatsApp order message:

    python marketing/meta_capi.py --order-id SOS-261029-1234 --value 3390 \\
        --phone 01XXXXXXXXX --fbc fb.1.17... --fbp fb.1.17...          # dry run
    ... --send                                                          # really send
    ... --send --test-code TEST12345                                    # Events Manager test

Dry run is the default: it prints the exact payload (phone/email already
hashed) and sends nothing.

Environment (never commit these, never paste them in chat):
  META_PIXEL_ID      the dataset / Pixel ID (same value as assets/meta-pixel.js)
  META_CAPI_TOKEN    Conversions API access token from Events Manager
  META_GRAPH_VERSION optional, default v24.0

Not shipped: stage_deploy.py excludes *.py from _site/.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

DEFAULT_GRAPH_VERSION = 'v24.0'
MAX_AGE_SECONDS = 7 * 24 * 3600  # Meta rejects website events older than 7 days


def sha256(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def normalize_bd_phone(raw):
    """Return E.164 digits without '+', e.g. 8801712345678, or '' if not a BD mobile."""
    digits = re.sub(r'\D', '', raw or '')
    if digits.startswith('00'):
        digits = digits[2:]
    if digits.startswith('01') and len(digits) == 11:
        digits = '88' + digits
    if digits.startswith('8801') and len(digits) == 13:
        return digits
    return ''


def build_event(args, now=None):
    now = int(now if now is not None else time.time())
    event_time = int(args.event_time) if args.event_time else now
    if now - event_time > MAX_AGE_SECONDS:
        raise SystemExit('event_time is older than 7 days; Meta will reject it.')

    user = {'country': [sha256('bd')]}
    if args.phone:
        phone = normalize_bd_phone(args.phone)
        if not phone:
            raise SystemExit(f'Not a Bangladesh mobile number: {args.phone!r}')
        user['ph'] = [sha256(phone)]
    if args.email:
        user['em'] = [sha256(args.email.strip().lower())]
    if args.fbc:
        user['fbc'] = args.fbc.strip()
    if args.fbp:
        user['fbp'] = args.fbp.strip()
    # external_id lets repeat buyers be recognised across orders without plain PII.
    if args.phone:
        user['external_id'] = [sha256('sos:' + normalize_bd_phone(args.phone))]
    if len(user) == 1:
        raise SystemExit('Give at least one of --phone, --email, --fbc, --fbp so Meta can match the order.')

    custom = {'currency': 'BDT', 'value': float(args.value), 'order_id': args.order_id}
    if args.content_ids:
        custom['content_ids'] = [c.strip() for c in args.content_ids.split(',') if c.strip()]
        custom['content_type'] = 'product'
        custom['num_items'] = len(custom['content_ids'])

    event = {
        'event_name': args.event,
        'event_time': event_time,
        # Same order id as the browser Lead's eventID prefix, so a resend is deduplicated.
        'event_id': f'{args.event.lower()}-{args.order_id}',
        'action_source': args.action_source,
        'user_data': user,
        'custom_data': custom,
    }
    if args.action_source == 'website':
        event['event_source_url'] = args.source_url
    return event


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--order-id', required=True, help='SOS-YYMMDD-NNNN from the WhatsApp order')
    ap.add_argument('--value', required=True, type=float, help='confirmed amount paid, in BDT')
    ap.add_argument('--event', default='Purchase', choices=['Purchase', 'Lead', 'Subscribe'])
    ap.add_argument('--phone', help='customer WhatsApp number (hashed before sending)')
    ap.add_argument('--email', help='customer email (hashed before sending)')
    ap.add_argument('--fbc', help='fbc=... value from the [SOS attribution] line')
    ap.add_argument('--fbp', help='fbp=... value from the [SOS attribution] line')
    ap.add_argument('--content-ids', help='comma-separated product ids, e.g. chatgpt-plus,canva-pro')
    ap.add_argument('--event-time', help='unix seconds of the order (default: now)')
    ap.add_argument('--action-source', default='website', choices=['website', 'chat', 'phone_call', 'other'])
    ap.add_argument('--source-url', default='https://saveonsub.com/checkout.html')
    ap.add_argument('--test-code', help='test_event_code from Events Manager > Test events')
    ap.add_argument('--send', action='store_true', help='actually send (default is a dry run)')
    args = ap.parse_args(argv)

    if args.value <= 0:
        raise SystemExit('--value must be the positive BDT amount actually paid.')

    payload = {'data': [build_event(args)]}
    if args.test_code:
        payload['test_event_code'] = args.test_code

    if not args.send:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        print('\nDry run — nothing sent. Add --send to report this order to Meta.', file=sys.stderr)
        return 0

    pixel_id = os.environ.get('META_PIXEL_ID', '').strip()
    token = os.environ.get('META_CAPI_TOKEN', '').strip()
    if not re.fullmatch(r'\d{6,20}', pixel_id) or not token:
        raise SystemExit('Set META_PIXEL_ID and META_CAPI_TOKEN in the environment first.')
    version = os.environ.get('META_GRAPH_VERSION', DEFAULT_GRAPH_VERSION).strip()

    url = f'https://graph.facebook.com/{version}/{pixel_id}/events'
    body = json.dumps(dict(payload, access_token=token)).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        # Meta's error body names the bad field; it never echoes the token.
        print(f'Meta rejected the event (HTTP {e.code}): {e.read().decode("utf-8", "replace")}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
