import json, re

with open('/workspace/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find start of DATA object
start_marker = "const DATA = "
start = html.find(start_marker)
assert start != -1, "DATA assignment not found"
body_start = start + len(start_marker)
assert html[body_start] == "{", "DATA does not start with brace"

# Extract by brace counting
braces = 0
end = None
in_string = False
escape = False
for i, ch in enumerate(html[body_start:]):
    if in_string:
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = False
        continue
    if ch == '"':
        in_string = True
        continue
    if ch == "{" or ch == "[":
        braces += 1
    elif ch == "}" or ch == "]":
        braces -= 1
        if braces == 0:
            end = body_start + i + 1
            break
assert end, "Could not find end of DATA object"
json_str = html[body_start:end]
data = json.loads(json_str)

# Counts
assert data['summary']['contract_count'] == 49, f"Expected 49 contracts, got {data['summary']['contract_count']}"
assert data['summary']['invoice_count'] == 302, f"Expected 302 invoices, got {data['summary']['invoice_count']}"
assert len(data['contracts']) == 49
assert len(data['invoices']) == 302
assert len(data['findings']) >= 14

# Verify script contains key functions
for fn in ["renderFindings", "renderContracts", "renderInvoices", "openDetail", "runTests"]:
    assert fn in html, f"Function {fn} missing from JS"

# Verify no external requests
assert "<script src=" not in html, "External script detected"
assert "fetch(" not in html, "fetch detected"
assert "XMLHttpRequest" not in html, "XHR detected"
assert "import " not in html or "import(" not in html, "Dynamic import detected"

print("HTML verified: valid embedded JSON, correct counts, self-contained JS, no external dependencies.")
print("File size:", len(html), "bytes")
