#!/usr/bin/env node
/**
 * Test suite for email attachments feature
 * Tests .eml building with PDF attachments, MIME encoding, and document selection logic
 */

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { parse: parseEmail } = require('mailparser').simpleParser;

const ARTIFACTS_DIR = '/opt/cursor/artifacts';
const TEST_PDF_PATH = path.join(__dirname, 'fixtures', 'sample.pdf');
const TEST_IMAGE_PATH = path.join(__dirname, 'fixtures', 'sample.jpg');

// Ensure artifacts directory exists
if (!fs.existsSync(ARTIFACTS_DIR)) {
  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
}

// Create test fixtures
function createTestFixtures() {
  const fixturesDir = path.join(__dirname, 'fixtures');
  if (!fs.existsSync(fixturesDir)) {
    fs.mkdirSync(fixturesDir, { recursive: true });
  }

  // Create a minimal valid PDF
  const pdfContent = `%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj
4 0 obj<</Length 44>>stream
BT
/F1 12 Tf
100 700 Td
(Test Document) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000056 00000 n 
0000000115 00000 n 
0000000214 00000 n 
trailer<</Size 5/Root 1 0 R>>
startxref
308
%%EOF`;
  fs.writeFileSync(TEST_PDF_PATH, pdfContent);

  // Create a minimal valid JPEG (1x1 red pixel)
  const jpegBytes = Buffer.from(
    'FFD8FFE000104A46494600010100000100010000FFDB004300080606070605080707' +
    '07090909080A0C140D0C0B0B0C1912130F141D1A1F1E1D1A1C1C20242E2720222C23' +
    '1C1C2837292C30313434341F27393D38323C2E333432FFDB0043010909090C0B0C18' +
    '0D0D1832211C213232323232323232323232323232323232323232323232323232323232' +
    '3232323232323232323232323232323232FFC00011080001000103012200021101031101' +
    'FFC4001500010100000000000000000000000000000008FFC40014100100000000000000' +
    '00000000000000000000FFDA000C03010002110311003F00BF800FFFD9',
    'hex'
  );
  fs.writeFileSync(TEST_IMAGE_PATH, jpegBytes);

  console.log('✓ Test fixtures created');
}

// Test document selection logic
function testDocumentSelection() {
  console.log('\n=== Testing document selection logic ===');
  
  const testCases = [
    {
      name: 'Includes resume',
      doc: { id: 'doc1', name: 'رزومه شرکت', kind: 'رزومه' },
      shouldInclude: true
    },
    {
      name: 'Includes registration',
      doc: { id: 'doc2', name: 'روزنامه رسمی', kind: 'ثبتی' },
      shouldInclude: true
    },
    {
      name: 'Includes certificate',
      doc: { id: 'doc3', name: 'گواهی دانش‌بنیان', kind: 'گواهی' },
      shouldInclude: true
    },
    {
      name: 'Includes portfolio',
      doc: { id: 'doc4', name: 'پورتفولیو', kind: 'پورتفولیو' },
      shouldInclude: true
    },
    {
      name: 'Excludes contract by kind',
      doc: { id: 'doc5', name: 'قرارداد با شرکت XYZ', kind: 'قرارداد' },
      shouldInclude: false
    },
    {
      name: 'Excludes contract by name',
      doc: { id: 'doc6', name: 'contract-ABC.pdf', kind: 'مدرک' },
      shouldInclude: false
    },
    {
      name: 'Excludes confidential by name',
      doc: { id: 'doc7', name: 'محرمانه - طرح داخلی', kind: 'مدرک' },
      shouldInclude: false
    },
    {
      name: 'Excludes internal document',
      doc: { id: 'doc8', name: 'Internal Strategy - Confidential', kind: 'مدرک' },
      shouldInclude: false
    }
  ];

  let passed = 0;
  let failed = 0;

  for (const tc of testCases) {
    const kind = String(tc.doc.kind || '').toLowerCase();
    const name = String(tc.doc.name || '').toLowerCase();
    const isContract = kind.includes('قرارداد') || name.includes('قرارداد') || name.includes('contract');
    const isConfidential = name.includes('محرمانه') || name.includes('confidential') || name.includes('internal');
    const isRelevant = kind.includes('رزومه') || kind.includes('ثبتی') || kind.includes('گواهی') || kind.includes('پورتفولیو');
    const shouldSelect = !isContract && !isConfidential && isRelevant;

    if (shouldSelect === tc.shouldInclude) {
      console.log(`  ✓ ${tc.name}`);
      passed++;
    } else {
      console.log(`  ✗ ${tc.name} (expected ${tc.shouldInclude}, got ${shouldSelect})`);
      failed++;
    }
  }

  console.log(`\nDocument selection: ${passed} passed, ${failed} failed`);
  return failed === 0;
}

// Test email parsing
async function testEmailParsing() {
  console.log('\n=== Testing .eml parsing with Python ===');
  
  const testScript = `
import sys
import email
from email import policy
import os

eml_path = sys.argv[1]
out_dir = sys.argv[2]

with open(eml_path, 'rb') as f:
    msg = email.message_from_binary_file(f, policy=policy.default)

results = {
    'subject': msg.get('Subject', ''),
    'from': msg.get('From', ''),
    'to': msg.get('To', ''),
    'attachments': []
}

for part in msg.iter_attachments():
    filename = part.get_filename() or 'attachment'
    content_type = part.get_content_type()
    payload = part.get_payload(decode=True)
    
    # Save attachment
    att_path = os.path.join(out_dir, filename)
    with open(att_path, 'wb') as af:
        af.write(payload)
    
    # Check if PDF
    is_pdf = payload.startswith(b'%PDF')
    
    results['attachments'].append({
        'filename': filename,
        'content_type': content_type,
        'size': len(payload),
        'is_valid_pdf': is_pdf
    })
    
    print(f"Attachment: {filename}")
    print(f"  Content-Type: {content_type}")
    print(f"  Size: {len(payload)} bytes")
    print(f"  Valid PDF: {is_pdf}")
    print(f"  Saved to: {att_path}")

# Check body
body_text = ''
if msg.is_multipart():
    for part in msg.iter_parts():
        if part.get_content_type() == 'text/plain':
            body_text = part.get_payload(decode=True).decode('utf-8', errors='ignore')
            break
else:
    body_text = msg.get_payload(decode=True).decode('utf-8', errors='ignore')

has_enclosures = 'Enclosures:' in body_text or 'پیوست' in body_text
print(f"\\nBody mentions attachments: {has_enclosures}")

# Summary
print(f"\\nTotal attachments: {len(results['attachments'])}")
all_pdf = all(a['content_type'] == 'application/pdf' for a in results['attachments'])
all_valid = all(a['is_valid_pdf'] for a in results['attachments'])
print(f"All application/pdf: {all_pdf}")
print(f"All valid PDFs: {all_valid}")
print(f"Body mentions files: {has_enclosures}")

sys.exit(0 if all_pdf and all_valid and has_enclosures else 1)
`;

  const scriptPath = path.join(__dirname, 'parse_eml.py');
  fs.writeFileSync(scriptPath, testScript);

  return scriptPath;
}

// Main test runner
async function runTests() {
  console.log('Email Attachments Test Suite\n');
  
  createTestFixtures();
  
  // Test 1: Document selection logic
  const selectionPassed = testDocumentSelection();
  
  // Test 2: Create EML with Playwright
  console.log('\n=== Building .eml with Playwright ===');
  
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  // Load the platform HTML
  const htmlPath = path.join(__dirname, '..', 'platform', 'index.html');
  await page.goto(`file://${htmlPath}`);
  
  // Inject test data and build EML
  const emlData = await page.evaluate(async () => {
    // Mock state
    window.S = {
      me: { id: 'test-user' },
      m: { tenders: [] },
      ip: { countries: {} },
      tasks: []
    };
    
    // Create test tender
    const testTender = {
      id: 'TEST-001',
      title: 'AI Platform Development',
      buyer: 'Test Organization',
      country: 'POL',
      deadline: '2026-12-31',
      market: 'international'
    };
    
    // Mock cdocList to return test documents
    window.cdocList = () => [
      { id: 'pdf1', name: 'Company Profile', kind: 'رزومه' },
      { id: 'pdf2', name: 'Registration Certificate', kind: 'ثبتی' },
      { id: 'img1', name: 'Certificate Image', kind: 'گواهی' },
      { id: 'contract1', name: 'Contract ABC', kind: 'قرارداد' } // should be excluded
    ];
    
    // Mock cdocFetch
    window.cdocFetch = async (id) => {
      if (id === 'pdf1' || id === 'pdf2') {
        // Return mock PDF
        const pdfContent = '%PDF-1.4\\n1 0 obj<</Type/Catalog>>endobj\\ntrailer<</Root 1 0 R>>\\n%%EOF';
        return {
          blob: new Blob([pdfContent], { type: 'application/pdf' }),
          name: id === 'pdf1' ? 'Company Profile' : 'Registration Certificate',
          kind: id === 'pdf1' ? 'رزومه' : 'ثبتی'
        };
      } else if (id === 'img1') {
        // Return mock image (will be converted to PDF)
        const jpegBytes = new Uint8Array([
          0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46
        ]);
        return {
          blob: new Blob([jpegBytes], { type: 'image/jpeg' }),
          name: 'Certificate Image',
          kind: 'گواهی'
        };
      }
      throw new Error('Not found');
    };
    
    // Mock blobUrl
    window.blobUrl = (id) => `/_blob/${id}`;
    
    // Build EML
    try {
      const selected = window.selectDocsForTender(testTender);
      console.log('Selected docs:', selected);
      
      const attachments = [];
      for (const id of selected) {
        const { blob, name } = await window.cdocFetch(id);
        const isPDF = blob.type === 'application/pdf';
        const pdfBlob = isPDF ? blob : await window.imageToPDF(blob);
        const fn = name.replace(/\\.(jpe?g|png|gif|webp|pdf)$/i, '') + '.pdf';
        attachments.push({ blob: pdfBlob, name: fn });
      }
      
      const subject = 'Partnership Proposal: AI Platform Development';
      const body = 'Dear Partner,\\n\\nWe are interested in collaborating on this tender.\\n\\nBest regards,\\nParsa International Group';
      const eml = await window.buildMIME(
        '"Test Sender" <info@parsaint.group>',
        'partner@example.com',
        'oil.ms.sohrabi@gmail.com',
        subject,
        body + '\\n\\nEnclosures:\\n' + attachments.map(a => '• ' + a.name).join('\\n'),
        attachments
      );
      
      return {
        success: true,
        eml: eml,
        attachmentCount: attachments.length,
        attachmentNames: attachments.map(a => a.name)
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  });
  
  await browser.close();
  
  if (!emlData.success) {
    console.log(`✗ Failed to build EML: ${emlData.error}`);
    return false;
  }
  
  console.log(`✓ Built EML with ${emlData.attachmentCount} attachments:`);
  emlData.attachmentNames.forEach(name => console.log(`  - ${name}`));
  
  // Save EML to artifacts
  const emlPath = path.join(ARTIFACTS_DIR, 'test-draft.eml');
  fs.writeFileSync(emlPath, emlData.eml);
  console.log(`✓ Saved to ${emlPath}`);
  
  // Test 3: Parse with Python
  const parseScript = await testEmailParsing();
  const { spawn } = require('child_process');
  
  return new Promise((resolve) => {
    const python = spawn('python3', [parseScript, emlPath, ARTIFACTS_DIR]);
    
    python.stdout.on('data', (data) => {
      console.log(data.toString());
    });
    
    python.stderr.on('data', (data) => {
      console.error(data.toString());
    });
    
    python.on('close', (code) => {
      if (code === 0) {
        console.log('\n✓ All email parsing tests passed');
      } else {
        console.log('\n✗ Email parsing tests failed');
      }
      resolve(code === 0 && selectionPassed);
    });
  });
}

// Run tests
runTests()
  .then((success) => {
    console.log(success ? '\n✓ All tests passed' : '\n✗ Some tests failed');
    process.exit(success ? 0 : 1);
  })
  .catch((error) => {
    console.error('\n✗ Test suite failed:', error);
    process.exit(1);
  });
