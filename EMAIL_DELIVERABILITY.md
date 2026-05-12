# Inbox Delivery Setup

Inbox placement is not controlled by FastAPI alone. The backend can send the email, but inbox delivery depends on DNS authentication, the SMTP server reputation, and the message content.

This project is currently set up to send mail with:

```env
SMTP_HOST=mail.ayatiworks.com
SMTP_PORT=465
SMTP_USERNAME=emailsmtp@ayatiworks.com
SMTP_USER=emailsmtp@ayatiworks.com
SMTP_USE_TLS=false
SMTP_USE_SSL=true
SMTP_FROM_EMAIL=emailsmtp@ayatiworks.com
SMTP_FROM_NAME=Sri Sri Wellbeing Chennai
SMTP_REPLY_TO_EMAIL=rubankumar@ayatiworks.com
```

If you keep `SMTP_FROM_EMAIL=emailsmtp@ayatiworks.com`, then the domain that must be authenticated properly is `ayatiworks.com`.

## What must be set correctly

1. SPF must authorize the actual sending server for `ayatiworks.com`.
2. DKIM must sign outbound email for `emailsmtp@ayatiworks.com`.
3. DMARC must exist for `ayatiworks.com`.
4. The SMTP server must have correct PTR / reverse DNS.
5. The SMTP server HELO / EHLO hostname should match its real mail hostname.
6. The mailbox `emailsmtp@ayatiworks.com` must be a real mailbox, not just an alias with weak relay rules.

## Backend values to keep

Use these values in the backend host and in Render:

```env
MAIL_ENABLED=true
SMTP_HOST=mail.ayatiworks.com
SMTP_PORT=465
SMTP_USERNAME=emailsmtp@ayatiworks.com
SMTP_USER=emailsmtp@ayatiworks.com
SMTP_PASSWORD=your-real-password
SMTP_PASS=your-real-password
SMTP_USE_TLS=false
SMTP_USE_SSL=true
SMTP_TIMEOUT_SECONDS=20
SMTP_LOCAL_HOSTNAME=mail.ayatiworks.com
SMTP_FROM_EMAIL=emailsmtp@ayatiworks.com
SMTP_FROM_NAME=Sri Sri Wellbeing Chennai
SMTP_REPLY_TO_EMAIL=rubankumar@ayatiworks.com
```

Setting `SMTP_LOCAL_HOSTNAME=mail.ayatiworks.com` helps the SMTP handshake look cleaner.

## DNS records for `ayatiworks.com`

### SPF

You need one SPF record for `ayatiworks.com`. It must include the real outbound mail server IP or the provider include value.

If the mail server is hosted directly on your own server, the SPF record usually looks like:

```txt
v=spf1 a mx ip4:YOUR_MAIL_SERVER_PUBLIC_IP -all
```

If your mail host gave you a provider include, use that instead, for example:

```txt
v=spf1 include:provider-example.com -all
```

Do not keep multiple SPF records. Only one SPF TXT record is valid.

### DKIM

Enable DKIM inside the mail hosting panel for `ayatiworks.com`.

Typical cPanel / hosting panels will give you a selector and TXT value like:

```txt
default._domainkey.ayatiworks.com  TXT  provider-generated-dkim-value
```

The exact selector and value must come from the mail host. This is not something the backend can invent.

### DMARC

Start with monitoring first:

```txt
_dmarc.ayatiworks.com  TXT  v=DMARC1; p=none; rua=mailto:rubankumar@ayatiworks.com; adkim=s; aspf=s
```

After SPF and DKIM are passing reliably, tighten it to:

```txt
_dmarc.ayatiworks.com  TXT  v=DMARC1; p=quarantine; rua=mailto:rubankumar@ayatiworks.com; adkim=s; aspf=s
```

Do not jump straight to `reject` until the reports show alignment is healthy.

## Mail server settings that matter

These must be checked on the mail host:

- Reverse DNS / PTR for the outbound IP should point to `mail.ayatiworks.com`.
- Forward DNS for `mail.ayatiworks.com` should resolve back to the same public IP.
- The SMTP banner / HELO should use `mail.ayatiworks.com`.
- Outbound relay must allow mail from `emailsmtp@ayatiworks.com`.
- The server must not be on public blacklists.

If any of these are wrong, mail often lands in spam even when the backend is working.

## Message content rules

The backend already sends plain-text plus HTML, which is good. To improve inbox placement further:

- Keep the `From` name stable: `Sri Sri Wellbeing Chennai`
- Avoid subjects written in all caps
- Avoid too many links in one email
- Avoid large image-only emails
- Keep booking emails transactional and short
- Do not send repeated test emails in bulk from the same mailbox

## Best-practice sender choice

The current sender works only if `ayatiworks.com` is correctly authenticated.

For best branding and alignment, a better long-term setup is:

```env
SMTP_FROM_EMAIL=bookings@srisriwellbeingchennai.com
```

But only do that if the mail host is actually configured to send for `srisriwellbeingchennai.com`. Otherwise it can make spam placement worse.

## How to verify

After DNS and mail-host fixes:

1. Send a test to Gmail.
2. Open the received message.
3. Check `Show original`.
4. Confirm:

- SPF = PASS
- DKIM = PASS
- DMARC = PASS

Also test with:

- `mail-tester.com`
- `gmail.com`
- `outlook.com`

If SPF/DKIM/DMARC pass but mail still goes to spam, the remaining issue is usually server reputation, shared-hosting reputation, or blacklist history on the outbound IP.

## Important limitation

No code change can guarantee inbox delivery.

If you want the highest inbox rate with the least maintenance, use a transactional provider such as:

- Amazon SES
- Resend
- SendGrid
- Postmark

For the current Ayatiworks SMTP setup, the next real work is on the DNS panel and the mail server panel, not in FastAPI.
