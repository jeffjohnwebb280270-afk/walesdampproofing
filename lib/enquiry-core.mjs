/**
 * enquiry-core.mjs
 *
 * Pure logic for the survey-request form. No network, no process.env reads at
 * module scope. Everything here is synchronous and testable.
 *
 * Transport is SMTP through the site's own mailbox (IONOS by default) — the
 * provider the domain's SPF already authorises — so no third-party sender
 * needs SPF/DKIM records and there is no second supplier to hold an account
 * with.
 *
 * The payload shape is this site's own: tenure / propertyType / message.
 * It is NOT the Scottish site's schema, and the two must not be merged.
 */

export const LIMITS = Object.freeze({
  name: 120,
  email: 254, // RFC 5321 practical maximum
  phone: 40,
  postcode: 12,
  message: 4000,
  tenure: 80,
  propertyType: 80,
});

/* ------------------------------------------------------------------ *
 * Config
 * ------------------------------------------------------------------ */

export function resolveConfig(env = {}) {
  const missing = [];
  const warnings = [];

  const user = str(env.SMTP_USER);
  const pass = str(env.SMTP_PASS);

  if (!user) missing.push('SMTP_USER');
  else if (!isEmail(user)) missing.push('SMTP_USER (present but not a valid mailbox address)');
  if (!pass) missing.push('SMTP_PASS');

  if (pass && /^(xkeysib|xsmtpsib)-/.test(pass)) {
    warnings.push('SMTP_PASS looks like a Brevo API key, not the mailbox password.');
  }

  const host = str(env.SMTP_HOST) || 'smtp.ionos.co.uk';
  const port = int(env.SMTP_PORT, 587, 1, 65535);
  if (port !== 587 && port !== 465) {
    warnings.push(`SMTP_PORT is ${port}; expected 587 (STARTTLS) or 465 (implicit TLS).`);
  }

  const toEmail = str(env.SMTP_TO) || str(env.ENQUIRY_TO_EMAIL) || user;
  if (toEmail && !isEmail(toEmail)) missing.push('SMTP_TO (present but not a valid address)');

  // From MUST be the authenticated mailbox — IONOS, like every provider,
  // rejects a sender it did not authenticate. The enquirer goes in Reply-To.
  const fromEmail = user;
  const declaredFrom = str(env.ENQUIRY_FROM_EMAIL);
  if (declaredFrom && declaredFrom.toLowerCase() !== user.toLowerCase()) {
    warnings.push(
      `ENQUIRY_FROM_EMAIL (${declaredFrom}) is ignored: From must be the authenticated mailbox, so ${user} is used.`,
    );
  }

  return {
    ok: missing.length === 0,
    missing,
    warnings,
    config: {
      host,
      port,
      secure: port === 465,
      user,
      pass,
      toEmail,
      fromEmail,
      fromName: str(env.ENQUIRY_FROM_NAME) || 'Wales Damp Proofing Website',
      siteName: str(env.ENQUIRY_SITE_NAME) || 'Wales Damp Proofing',
      replyPhone: str(env.ENQUIRY_PHONE) || '07446 522034',
      sendAck: str(env.ENQUIRY_SEND_ACK) === '1',
      timeoutMs: int(env.ENQUIRY_TIMEOUT_MS, 10_000, 1_000, 30_000),
      maxAttempts: int(env.ENQUIRY_MAX_ATTEMPTS, 3, 1, 5),
    },
  };
}

/* ------------------------------------------------------------------ *
 * Validation
 * ------------------------------------------------------------------ */

/**
 * Validate and normalise a raw form payload.
 *
 * A postcode that does not match the UK pattern is NOT rejected. A lead with
 * a mistyped postcode is still a lead — you have their phone and email — and
 * turning a customer away over a formatting quirk costs more than flagging
 * it. It is normalised, accepted, and marked so the notification can say so.
 */
export function validateEnquiry(raw) {
  const errors = [];

  if (raw === null || typeof raw !== 'object' || Array.isArray(raw)) {
    return { ok: false, errors: ['Request body must be a JSON object.'] };
  }

  const name = trunc(str(raw.name), LIMITS.name);
  const email = trunc(str(raw.email), LIMITS.email).toLowerCase();
  const postcode = normalisePostcode(str(raw.postcode));

  if (!name) errors.push('name is required');
  if (!email) errors.push('email is required');
  else if (!isEmail(email)) errors.push('email is not a valid address');
  if (!postcode) errors.push('postcode is required');

  if (errors.length) return { ok: false, errors };

  return {
    ok: true,
    lead: {
      name,
      email,
      postcode,
      postcodeLooksOdd: !isUkPostcode(postcode),
      phone: trunc(str(raw.phone), LIMITS.phone),
      tenure: trunc(str(raw.tenure), LIMITS.tenure),
      propertyType: trunc(str(raw.propertyType), LIMITS.propertyType),
      message: trunc(str(raw.message), LIMITS.message),
    },
  };
}

/** Honeypot: the form ships a hidden `hp` input that humans never fill. */
export function isBot(raw) {
  return typeof raw?.hp === 'string' && raw.hp.trim() !== '';
}

/**
 * A council or housing association landlord brings the Welsh Housing Quality
 * Standard damp and mould timescales into play, so those enquiries are
 * flagged for scheduling first.
 */
export function isSocial(lead) {
  return /council|housing association/i.test(lead.tenure || '');
}

/* ------------------------------------------------------------------ *
 * Escaping
 * ------------------------------------------------------------------ */

const HTML_ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };

export function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (c) => HTML_ESCAPES[c]);
}

/** Strip CR/LF from a value bound for a mail header. Prevents injection. */
export function escapeHeader(value) {
  return String(value ?? '').replace(/[\r\n]+/g, ' ').trim();
}

/* ------------------------------------------------------------------ *
 * Rendering
 * ------------------------------------------------------------------ */

const FIELD_LABELS = [
  ['phone', 'Phone'],
  ['postcode', 'Postcode'],
  ['tenure', 'They are'],
  ['propertyType', 'Property type'],
  ['message', 'What they are seeing'],
];

/** Build the nodemailer message for the internal notification email. */
export function buildNotificationEmail(lead, config, meta = {}) {
  const social = isSocial(lead);
  const subject = escapeHeader(
    `${social ? 'WHQS — ' : ''}Survey enquiry — ${lead.name} (${lead.postcode})`,
  );

  const rows = FIELD_LABELS.filter(([k]) => lead[k])
    .map(([k, label]) => {
      const flag = k === 'postcode' && lead.postcodeLooksOdd
        ? ' <span style="color:#8A1220">(not a standard UK format — worth confirming)</span>'
        : '';
      return `<tr><td style="padding:4px 14px 4px 0;color:#6B6577;white-space:nowrap;vertical-align:top">${escapeHtml(label)}</td>` +
             `<td style="padding:4px 0"><b>${escapeHtml(lead[k]).replace(/\n/g, '<br>')}</b>${flag}</td></tr>`;
    })
    .join('');

  const banner = social
    ? '<p style="margin:0 0 16px;color:#8A1220;font-weight:bold">Social landlord — WHQS damp and mould timescales may apply.</p>'
    : '';

  const footer = meta.receivedAt
    ? `<p style="margin:22px 0 0;font-size:12px;color:#9A94A5">Received ${escapeHtml(meta.receivedAt)}${
        meta.requestId ? ` · req ${escapeHtml(meta.requestId)}` : ''
      }</p>`
    : '';

  return {
    from: { name: escapeHeader(config.fromName), address: config.fromEmail },
    to: config.toEmail,
    replyTo: { name: escapeHeader(lead.name) || lead.email, address: lead.email },
    subject,
    html:
      `<div style="font-family:Arial,sans-serif;font-size:15px;line-height:1.6;color:#15131B">` +
      banner +
      `<h2 style="margin:0 0 14px">New survey enquiry</h2>` +
      `<table cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:14px">` +
      `<tr><td style="padding:4px 14px 4px 0;color:#6B6577">Name</td><td style="padding:4px 0"><b>${escapeHtml(lead.name)}</b></td></tr>` +
      `<tr><td style="padding:4px 14px 4px 0;color:#6B6577">Email</td><td style="padding:4px 0"><a href="mailto:${escapeHtml(lead.email)}">${escapeHtml(lead.email)}</a></td></tr>` +
      rows +
      `</table>` + footer + `</div>`,
    text: buildNotificationText(lead, meta),
  };
}

function buildNotificationText(lead, meta) {
  const lines = [];
  if (isSocial(lead)) lines.push('*** Social landlord — WHQS damp and mould timescales may apply ***', '');
  lines.push(`Name: ${lead.name}`, `Email: ${lead.email}`);
  for (const [k, label] of FIELD_LABELS) {
    if (!lead[k]) continue;
    lines.push(`${label}: ${lead[k]}${k === 'postcode' && lead.postcodeLooksOdd ? '  (not a standard UK format)' : ''}`);
  }
  if (meta.receivedAt) lines.push('', `Received ${meta.receivedAt}`);
  return lines.join('\n');
}

/** Build the nodemailer message for the acknowledgement sent to the enquirer. */
export function buildAckEmail(lead, config) {
  return {
    from: { name: escapeHeader(config.siteName), address: config.fromEmail },
    to: { name: escapeHeader(lead.name) || lead.email, address: lead.email },
    replyTo: { name: escapeHeader(config.siteName), address: config.toEmail },
    subject: escapeHeader(`We've got your survey request — ${config.siteName}`),
    html:
      `<div style="font-family:Arial,sans-serif;font-size:15px;line-height:1.6;color:#15131B">` +
      `<p>Thanks ${escapeHtml(firstName(lead.name))} — your survey request has reached us and a surveyor will come back to you within one working day.</p>` +
      `<p>If it's urgent, call <b>${escapeHtml(config.replyPhone)}</b> rather than waiting on email.</p>` +
      `<p style="margin-top:22px;font-size:13px;color:#6B6577">${escapeHtml(config.siteName)} — PCA-qualified damp and timber surveys across Wales.<br>` +
      `This is an automated acknowledgement; replies go to a monitored inbox.</p></div>`,
    text:
      `Thanks ${firstName(lead.name)} — your survey request has reached us and a surveyor will come back to you within one working day.\n\n` +
      `If it's urgent, call ${config.replyPhone} rather than waiting on email.\n\n` +
      `${config.siteName} — PCA-qualified damp and timber surveys across Wales.`,
  };
}

/* ------------------------------------------------------------------ *
 * Structured lead record (the durable fallback)
 * ------------------------------------------------------------------ */

export function leadRecord(lead, meta = {}) {
  return JSON.stringify({
    tag: 'LEAD_CAPTURE',
    receivedAt: meta.receivedAt ?? new Date().toISOString(),
    requestId: meta.requestId ?? null,
    social: isSocial(lead),
    lead,
  });
}

/* ------------------------------------------------------------------ *
 * Helpers
 * ------------------------------------------------------------------ */

function str(v) { return typeof v === 'string' ? v.trim() : ''; }
function trunc(v, max) { return v.length > max ? v.slice(0, max) : v; }
function int(v, dflt, min, max) {
  const n = Number.parseInt(v ?? '', 10);
  if (!Number.isFinite(n)) return dflt;
  return Math.min(max, Math.max(min, n));
}
function firstName(name) { return (name || '').split(/\s+/)[0] || 'there'; }

/**
 * Pragmatic address check. Deliberately not RFC 5322 — that grammar accepts
 * addresses no provider will route, and rejecting a real customer is a worse
 * failure than accepting an odd-looking address.
 */
export function isEmail(v) {
  if (typeof v !== 'string' || v.length > LIMITS.email) return false;
  if (/[\s<>,;\r\n]/.test(v)) return false;
  const at = v.indexOf('@');
  if (at < 1 || at !== v.lastIndexOf('@')) return false;
  const domain = v.slice(at + 1);
  if (domain.length < 3 || !domain.includes('.')) return false;
  if (domain.startsWith('.') || domain.endsWith('.') || domain.includes('..')) return false;
  if (domain.startsWith('-') || domain.endsWith('-')) return false;
  return /^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+$/.test(v.slice(0, at));
}

export function normalisePostcode(v) {
  const compact = String(v ?? '').toUpperCase().replace(/\s+/g, '');
  if (compact.length < 5 || compact.length > 8) return compact;
  return `${compact.slice(0, -3)} ${compact.slice(-3)}`;
}

const UK_POSTCODE = /^[A-Z]{1,2}\d[A-Z\d]?\s\d[A-Z]{2}$/;

export function isUkPostcode(v) {
  return UK_POSTCODE.test(String(v ?? '').toUpperCase());
}
