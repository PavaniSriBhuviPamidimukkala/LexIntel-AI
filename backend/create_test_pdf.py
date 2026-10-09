from pathlib import Path

# Minimal one-page PDF containing extractable text.
lines = [
    "LexIntel AI Test Legal Document",
    "CHAPTER I - SAMPLE CONTRACT RULES",
    "Section 12. Compensation for delayed delivery",
    "When a supplier fails to deliver goods by the agreed date,",
    "the buyer may document the direct loss caused by the delay.",
    "This is fictional test content and is not legal advice.",
    "Section 13. Notice of delay",
    "A party aware of a likely delivery delay should notify the",
    "other party and preserve relevant records.",
]

def pdf_escape(text):
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

content = ["BT", "/F1 12 Tf", "50 790 Td"]
for i, line in enumerate(lines):
    if i:
        content.append("0 -24 Td")
    content.append(f"({pdf_escape(line)}) Tj")
content.append("ET")
stream = "\n".join(content).encode("ascii")

objects = [
    b"<< /Type /Catalog /Pages 2 0 R >>",
    b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
    b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
]

pdf = bytearray(b"%PDF-1.4\n")
offsets = [0]
for i, obj in enumerate(objects, start=1):
    offsets.append(len(pdf))
    pdf.extend(f"{i} 0 obj\n".encode())
    pdf.extend(obj)
    pdf.extend(b"\nendobj\n")

xref_offset = len(pdf)
pdf.extend(f"xref\n0 {len(objects)+1}\n".encode())
pdf.extend(b"0000000000 65535 f \n")
for offset in offsets[1:]:
    pdf.extend(f"{offset:010d} 00000 n \n".encode())
pdf.extend(
    f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\n"
    f"startxref\n{xref_offset}\n%%EOF\n".encode()
)

output = Path("lexintel_test_upload.pdf")
output.write_bytes(pdf)
print(f"Created {output.resolve()} ({len(pdf)} bytes)")
