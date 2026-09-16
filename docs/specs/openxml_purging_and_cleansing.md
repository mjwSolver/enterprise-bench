# OpenXML Sanitization & Document Cleansing Guide

> **Scope:** Microsoft Word (.docx) Comment Removal, Highlight Stripping, Tracked Revision Normalization, and Zero-Corruption Packaging.  
> **Target Audience:** Platform Engineers, Deliverable Producers, and Autonomous Agents working in `enterprise-bench`.

---

## 1. Executive Problem Summary

When enterprise templates or deliverables undergo PII substitution and are opened in Microsoft Word on desktop devices, two severe failure modes frequently manifest:

1. **"Ghost Comments" & Balloon Proliferation:**
   - Even when comment text or highlighting is stripped, Word continues displaying hundreds of margin callout balloons with author names (e.g., `Dian Eka Kusumawaty`).
   - **Diagnosis:** These margin balloons are **not standard comment objects**—they are **Tracked Revisions (Track Changes)** (`<w:ins>`, `<w:del>`, `<w:rPrChange>`, `<w:pPrChange>`), combined with author presence profiles in `word/people.xml`. Word's default "All Markup" view renders tracked changes in identical margin callouts.
2. **"Word Found Unreadable Content" (Document Corruption):**
   - Naive manipulation of the `.docx` zip package (e.g., using Python's standard `xml.etree.ElementTree` to modify `[Content_Types].xml` or `word/_rels/document.xml.rels`) causes Word to refuse to open the file or prompt for recovery.
   - **Diagnosis:** `ElementTree` serializes default package namespaces with synthetic prefixes (e.g., `<ns0:Types xmlns:ns0="...">` or `<ns0:Relationships>`). The OpenXML specification strictly forbids namespace prefixes on root package files.

---

## 2. Technical Root Causes & Anatomy

```
                              ┌──────────────────────────────────────────────┐
                              │          MICROSOFT WORD .DOCX ZIP            │
                              └──────────────────────┬───────────────────────┘
                                                     │
                     ┌───────────────────────────────┼───────────────────────────────┐
                     ▼                               ▼                               ▼
      [Content_Types].xml & .rels           word/document.xml & headers             word/comments*.xml & people.xml
      ───────────────────────────           ───────────────────────────             ───────────────────────────────
      • Strict default namespace            • <w:highlight> (run styling)           • comments.xml (comment bodies)
        without prefixes (NO ns0:)          • <w:commentRangeStart/End/Ref>         • commentsExtended/Extensible
      • Never re-serialize with             • <w:del> (deleted text)                • people.xml (author profiles)
        standard ElementTree                • <w:ins> (inserted text)               • Must empty children while
                                            • <w:rPrChange> (format changes)          preserving container tags
```

### Why Standard XML Parsers Corrupt OpenXML Packages
1. **`[Content_Types].xml`:**
   - Must begin with `<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">`.
   - If converted to `<ns0:Types xmlns:ns0="...">`, Microsoft Word immediately rejects the file as corrupt.
2. **`word/_rels/document.xml.rels`:**
   - Must begin with `<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">`.
   - Prefixing with `ns0:` or dropping relationship IDs without updating parts breaks document unmarshalling.

### Why "Comments" Were Still Visible
1. Word's **Track Changes** feature logs every insertion and deletion with author tags:
   - `<w:del w:author="AuthorName" w:date="...">...<w:delText>old text</w:delText></w:del>`
   - `<w:ins w:author="AuthorName" w:date="...">...<w:r><w:t>new text</w:t></w:r></w:ins>`
2. When Word opens a document containing `<w:del>` or `<w:ins>`, it displays them as redline balloons in the right-hand margin with the author's name.
3. `word/people.xml` caches contributor contact records, causing Word to link balloons to author cards.

---

## 3. The Zero-Corruption Architecture (`src/core/docx_purger.py`)

The robust solution implemented in `src/core/docx_purger.py` enforces three core principles:

### Principle 1: Never Touch Package Files (`[Content_Types].xml` & `.rels`)
- Leave `[Content_Types].xml` and `word/_rels/document.xml.rels` **100% untouched**.
- Leaving relationship entries pointing to `word/comments.xml` is completely valid in OpenXML as long as `word/comments.xml` exists as a valid empty XML container.

### Principle 2: Empty Children of Part Containers
- For `word/comments.xml`, `word/commentsExtended.xml`, `word/commentsExtensible.xml`, `word/commentsIds.xml`, and `word/people.xml`:
- Parse with `lxml.etree`, remove all child nodes (`for child in list(root): root.remove(child)`), and write back with the original standalone XML declaration.
- This results in `<w:comments .../>` and `<w15:people .../>` with zero comments and zero author identities, preserving valid XML schema structures.

### Principle 3: Targeted `lxml` Strip & Unwrap on Document Parts
For `word/document.xml`, `word/header*.xml`, and `word/footer*.xml`:
1. **Accept Deletions (Drop `<w:del>`):**
   ```python
   etree.strip_elements(root, f"{{{W_NS}}}del", with_tail=False)
   ```
2. **Accept Insertions (Unwrap `<w:ins>`):**
   ```python
   etree.strip_tags(root, f"{{{W_NS}}}ins")
   ```
   *Note: `strip_tags` removes the `<w:ins>` boundary tag while keeping all child `<w:r>` runs and text intact!*
3. **Strip Format Changes:**
   ```python
   for chg in ["rPrChange", "pPrChange", "tblPrChange", "tcPrChange", "sectPrChange", "tblGridChange"]:
       etree.strip_elements(root, f"{{{W_NS}}}{chg}", with_tail=False)
   ```
4. **Strip Comment Anchors & Highlights:**
   ```python
   etree.strip_elements(root, f"{{{W_NS}}}commentRangeStart", with_tail=False)
   etree.strip_elements(root, f"{{{W_NS}}}commentRangeEnd", with_tail=False)
   etree.strip_elements(root, f"{{{W_NS}}}commentReference", with_tail=False)
   etree.strip_elements(root, f"{{{W_NS}}}highlight", with_tail=False)
   ```
5. **Disable Revision Tracking in `word/settings.xml`:**
   ```python
   etree.strip_elements(root, f"{{{W_NS}}}trackRevisions", with_tail=False)
   ```

---

## 4. CLI Runbook & Operational Verification

### Execute Purge via CLI
```bash
# Single deliverable:
uv run bench doc purge --file output/proj-xyz/documents/01_PKS_Contract_Apex_Global.docx

# Batch directory (e.g. all clean templates or project outputs):
uv run bench doc purge --dir clean_workspace/
uv run bench doc purge --dir output/proj-xyz/documents/
```

### Verification via Python & macOS AppleScript
To verify zero comments and zero revisions directly from Microsoft Word's live object model:
```bash
osascript -e 'tell application "Microsoft Word"
    set cCount to count of comments of active document
    set rCount to count of revisions of active document
    return "Comments: " & cCount & " | Revisions: " & rCount
end tell'
# Expected output: Comments: 0 | Revisions: 0
```

---

## 5. Summary Checklist for Future Agents

- [x] Did you run `uv run bench doc purge` after PII substitution?
- [x] Are `[Content_Types].xml` and `document.xml.rels` uncorrupted (no `ns0:` prefixes)?
- [x] Are `<w:ins>` tags unwrapped and `<w:del>` elements stripped?
- [x] Is `word/people.xml` cleared of author presence metadata?
- [x] Did `uv run bench doc lint --file <path.docx>` pass with 0 critical errors?
