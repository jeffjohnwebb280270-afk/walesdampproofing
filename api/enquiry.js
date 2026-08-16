// Vercel serverless function — receives the request form and sends it on via Brevo.
const BREVO_ENDPOINT = 'https://api.brevo.com/v3/smtp/email';
const BUSINESS_EMAIL = 'contact@walesdampproofing.co.uk';
const BUSINESS_NAME = 'Wales Damp Proofing';

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
function isValidEmail(email) {
  return typeof email === 'string' && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
}
function readBody(req) {
  if (req.body && typeof req.body === 'object') return req.body;
  if (typeof req.body === 'string') { try { return JSON.parse(req.body); } catch (e) { return {}; } }
  return {};
}

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed' });
  }
  const data = readBody(req);

  // honeypot — bots that fill this get a silent success and no email
  if (data.hp) return res.status(200).json({ ok: true });

  const name = typeof data.name === 'string' ? data.name.trim() : '';
  const email = typeof data.email === 'string' ? data.email.trim() : '';
  const postcode = typeof data.postcode === 'string' ? data.postcode.trim() : '';

  if (!name || !email || !postcode) {
    return res.status(400).json({ error: 'Name, email and postcode are required.' });
  }
  if (!isValidEmail(email)) {
    return res.status(400).json({ error: 'Please provide a valid email address.' });
  }

  const apiKey = process.env.BREVO_API_KEY;
  if (!apiKey) {
    console.error('BREVO_API_KEY is not set');
    return res.status(500).json({ error: 'Server is not configured to send enquiries yet.' });
  }

  const tenure = data.tenure || '';
  const isSocial = /council|housing association/i.test(tenure);
  const subject = `${isSocial ? 'WHQS — ' : ''}Survey enquiry — ${name} (${postcode})`;

  const rows = [
    ['Name', name], ['Email', email], ['Phone', data.phone || ''],
    ['Postcode', postcode], ['They are', tenure],
    ['Property type', data.propertyType || ''], ['What they are seeing', data.message || ''],
  ];

  const htmlContent = `
    <div style="font-family:Arial,sans-serif;font-size:15px;color:#15131B;">
      ${isSocial ? '<p style="color:#8A1220;font-weight:bold;">Social landlord — WHQS damp and mould timescales may apply.</p>' : ''}
      <h2 style="margin:0 0 14px;">New survey enquiry</h2>
      <table cellpadding="6" cellspacing="0" style="border-collapse:collapse;">
        ${rows.filter(([, v]) => v).map(([label, value]) =>
          `<tr><td style="font-weight:bold;vertical-align:top;padding-right:12px;">${escapeHtml(label)}</td><td>${escapeHtml(value).replace(/\n/g, '<br>')}</td></tr>`
        ).join('')}
      </table>
    </div>`;

  try {
    const brevoRes = await fetch(BREVO_ENDPOINT, {
      method: 'POST',
      headers: { 'api-key': apiKey, 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({
        sender: { name: `${BUSINESS_NAME} Website`, email: BUSINESS_EMAIL },
        to: [{ email: BUSINESS_EMAIL, name: BUSINESS_NAME }],
        replyTo: { email, name: name || email },
        subject, htmlContent,
      }),
    });
    if (!brevoRes.ok) {
      const errText = await brevoRes.text().catch(() => '');
      console.error('Brevo send failed', brevoRes.status, errText);
      return res.status(502).json({ error: 'Could not send your enquiry right now. Please call or email us directly.' });
    }
    return res.status(200).json({ ok: true });
  } catch (err) {
    console.error('Enquiry send error', err);
    return res.status(502).json({ error: 'Could not send your enquiry right now. Please call or email us directly.' });
  }
};
