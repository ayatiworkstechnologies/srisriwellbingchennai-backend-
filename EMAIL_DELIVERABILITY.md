# Email Deliverability Setup

Use a real transactional SMTP provider and authenticate the sending domain. Code changes alone cannot guarantee inbox delivery.

## Backend SMTP

Set these environment values in the backend host:

```env
MAIL_ENABLED=true
SMTP_HOST=smtp.your-provider.com
SMTP_PORT=587
SMTP_USERNAME=your-smtp-user
SMTP_PASSWORD=your-smtp-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_FROM_EMAIL=bookings@srisriwellbeingchennai.com
SMTP_FROM_NAME=Sri Sri Wellbeing Chennai
SMTP_REPLY_TO_EMAIL=admin@srisriwellbeingchennai.com
```

Use a `SMTP_FROM_EMAIL` address from your own verified domain. Do not send production mail from a personal Gmail/Yahoo address.

## DNS Records

Add these records in the DNS panel for the sending domain.

SPF:

```txt
v=spf1 include:YOUR_SMTP_PROVIDER_SPF -all
```

DKIM:

```txt
YOUR_SELECTOR._domainkey  TXT  provider-generated-dkim-value
```

DMARC:

```txt
_dmarc  TXT  v=DMARC1; p=quarantine; rua=mailto:admin@srisriwellbeingchennai.com; adkim=s; aspf=s
```

Start DMARC with `p=none` if you are still testing, then move to `quarantine` or `reject` after SPF/DKIM pass reliably.

## Sending Rules

- Keep `From` domain aligned with SPF/DKIM.
- Send booking/customer emails only after a real user action.
- Avoid spam words, all-caps subjects, and link-heavy content.
- Keep a plain-text version with every HTML email.
- Use one trusted SMTP provider consistently so sender reputation can build.
