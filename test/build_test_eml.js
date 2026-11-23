#!/usr/bin/env node
/**
 * Build a test .eml file with PDF attachments
 */
const fs = require('fs');
const path = require('path');

const OUTPUT_PATH = '/opt/cursor/artifacts/test-email.eml';

// Create a minimal valid PDF
function createSamplePDF(title) {
  const content = `Test ${title}`;
  return `%PDF-1.4
1 0 obj
<</Type/Catalog/Pages 2 0 R>>
endobj
2 0 obj
<</Type/Pages/Count 1/Kids[3 0 R]>>
endobj
3 0 obj
<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>
endobj
4 0 obj
<</Length 55>>
stream
BT
/F1 12 Tf
100 700 Td
(${content}) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000117 00000 n 
0000000218 00000 n 
trailer
<</Size 5/Root 1 0 R>>
startxref
333
%%EOF`;
}

// Create a minimal JPEG (1x1 red pixel)
function createSampleJPEG() {
  return Buffer.from(
    'FFD8FFE000104A46494600010100000100010000FFDB004300080606070605080707' +
    '07090909080A0C140D0C0B0B0C1912130F141D1A1F1E1D1A1C1C20242E2720222C23' +
    '1C1C2837292C30313434341F27393D38323C2E333432FFDB0043010909090C0B0C18' +
    '0D0D1832211C213232323232323232323232323232323232323232323232323232323232' +
    '3232323232323232323232323232323232FFC00011080001000103012200021101031101' +
    'FFC4001500010100000000000000000000000000000008FFC40014100100000000000000' +
    '00000000000000000000FFDA000C03010002110311003F00BF800FFFD9',
    'hex'
  );
}

// Encode filename for RFC 2231/5987
function encodeRFC2231(str) {
  const enc = encodeURIComponent(str).replace(/[!'()*]/g, c => `%${c.charCodeAt(0).toString(16).toUpperCase()}`);
  return `utf-8''${enc}`;
}

// Build MIME multipart/mixed email
function buildMIME(from, to, cc, subject, body, attachments) {
  const CRLF = '\r\n';
  const boundary = `----=iPetro_${Date.now()}_${Math.random().toString(36).slice(2)}`;
  
  const lines = [
    'X-Unsent: 1',
    `From: ${from}`,
    `To: ${to}`,
    cc ? `Cc: ${cc}` : '',
    `Subject: ${subject}`,
    'MIME-Version: 1.0',
    `Content-Type: multipart/mixed; boundary="${boundary}"`,
    '',
    'This is a multi-part message in MIME format.',
    '',
    `--${boundary}`,
    'Content-Type: text/plain; charset=utf-8',
    'Content-Transfer-Encoding: base64',
    '',
    Buffer.from(body, 'utf-8').toString('base64').match(/.{1,76}/g).join(CRLF)
  ].filter(Boolean);
  
  for (const att of attachments) {
    const b64 = att.content.toString('base64').match(/.{1,76}/g) || [];
    lines.push(
      '',
      `--${boundary}`,
      `Content-Type: application/pdf; name="${att.name}"`,
      'Content-Transfer-Encoding: base64',
      `Content-Disposition: attachment; filename*=${encodeRFC2231(att.name)}`,
      '',
      ...b64
    );
  }
  
  lines.push('', `--${boundary}--`, '');
  return lines.join(CRLF);
}

// Main
function main() {
  console.log('Building test .eml file with PDF attachments...\n');
  
  // Create test PDFs and images
  const pdf1 = createSamplePDF('Company Profile');
  const pdf2 = createSamplePDF('Registration Certificate');
  const pdf3 = createSamplePDF('گواهی دانش‌بنیان'); // Persian name test
  const jpeg = createSampleJPEG();
  
  const attachments = [
    { name: 'Company_Profile.pdf', content: Buffer.from(pdf1) },
    { name: 'Registration.pdf', content: Buffer.from(pdf2) },
    { name: 'گواهی.pdf', content: Buffer.from(pdf3) }
  ];
  
  const subject = 'Partnership Proposal: AI Platform Development';
  const body = `Dear Partner,

We are writing to propose a collaboration on the tender "AI Platform Development" published by Test Organization (deadline: 2026-12-31).

Division of work: your company would present the buyer's requirements to us for this tender, including all documents requested in the tender documentation (company registration, references, certificates, guarantees and forms) and the project requirements. Parsa International Group would then carry out the software development, coding and technical implementation of the project.

Enclosures:
• Company_Profile.pdf
• Registration.pdf
• گواهی.pdf

Kind regards,
Test Sender
Parsa International Group
Türkiye`;
  
  const eml = buildMIME(
    '"Test Sender" <info@parsaint.group>',
    'partner@example.com',
    'oil.ms.sohrabi@gmail.com',
    subject,
    body,
    attachments
  );
  
  // Ensure output directory exists
  const outputDir = path.dirname(OUTPUT_PATH);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  // Write EML file
  fs.writeFileSync(OUTPUT_PATH, eml);
  
  console.log(`✓ Created test .eml file:`);
  console.log(`  Path: ${OUTPUT_PATH}`);
  console.log(`  Size: ${eml.length} bytes`);
  console.log(`  Attachments: ${attachments.length}`);
  attachments.forEach(att => {
    console.log(`    - ${att.name} (${att.content.length} bytes)`);
  });
  
  console.log(`\n✓ Test .eml file created successfully!`);
  return OUTPUT_PATH;
}

const emlPath = main();
console.log(`\nRun: python3 test/test_mime_attachments.py "${emlPath}"`);
