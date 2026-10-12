"""Final hand-off pass (SKILL.md rule S) on an owner-reviewed tracked .docx.

usage: final_pass.py in.docx out.docx --owner "Owner Name" [--aliases "Alias A,Alias B"]
         [--remove-authors Claude] [--remove-ids 157,819] [--marker CLAUDE]
         [--report report.md] [--date 2026-10-11T10:00:00Z]

Does (mechanical, safe):
  - renames every alias author to --owner (document, comments, people.xml) and dedupes people.xml
  - removes every comment by --remove-authors, plus --remove-ids (the owner's Claude-directed asks,
    once actioned), across comments.xml / commentsExtended / commentsIds / commentsExtensible
  - strips "[<MARKER>: ...]" notes that survive inside deleted runs (accepting that deletion)
Reports (for the agent to act on, never auto-fixed):
  - visible text still naming the marker or remove-authors
  - figure / table caption numbering gaps or repeats
  - reference entries with no in-text citation, and same-author year-letter gaps
  - local-currency prefixes (A$, $A) outside the reference list (rule R)
Edits that need judgement (renumbering, citation changes, deleting entries) go through
track_edit_ops.py with an ops.json, as tracked changes by the owner.
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile, zipfile, collections
from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
W14 = 'http://schemas.microsoft.com/office/word/2010/wordml'
W15 = 'http://schemas.microsoft.com/office/word/2012/wordml'
q = lambda t, ns=W: '{%s}%s' % (ns, t)
PARSER = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
HERE = os.path.dirname(os.path.abspath(__file__))


def parse(p):
    return etree.parse(p, PARSER)


def save(t, p):
    t.write(p, xml_declaration=True, encoding='UTF-8', standalone=True)


def para_text(p, accepted=True):
    out = []
    for el in p.iter(q('t'), q('delText')):
        in_del = any(a.tag == q('del') for a in el.iterancestors())
        if el.tag == q('t') and not (accepted and in_del):
            out.append(el.text or '')
    return ''.join(out)


def strip_markers(doc_path, marker):
    t = parse(doc_path); r = t.getroot(); removed = []
    for p in r.iter(q('p')):
        dts = list(p.iter(q('delText'))); i = 0
        while i < len(dts):
            d = dts[i]
            if d.text and '[' + marker in d.text:
                k = d.text.index('[' + marker); pre = d.text[:k]; rest = d.text[k:]
                chain = [d]; j = i
                while ']' not in rest and j + 1 < len(dts):
                    j += 1; rest = dts[j].text or ''; chain.append(dts[j])
                post = rest[rest.index(']') + 1:] if ']' in rest else ''
                removed.append(''.join(x.text or '' for x in chain)[:120])
                for n, x in enumerate(chain):
                    txt = (pre if n == 0 else '') + (post if n == len(chain) - 1 else '')
                    if txt:
                        x.text = txt
                    else:
                        run = x.getparent(); par = run.getparent(); par.remove(run)
                        if par.tag == q('del') and len(par) == 0:
                            par.getparent().remove(par)
                i = j + 1
            else:
                i += 1
    save(t, doc_path)
    return removed


def dedupe_people(d):
    p = os.path.join(d, 'word', 'people.xml')
    if not os.path.exists(p):
        return
    t = parse(p); r = t.getroot(); seen = set()
    for e in list(r):
        a = e.get(q('author', W15))
        if a in seen:
            r.remove(e)
        seen.add(a)
    save(t, p)


def report(doc_path, marker, bad_authors):
    r = parse(doc_path).getroot()
    paras = [(p.get(q('paraId', W14)), para_text(p)) for p in r.iter(q('p'))]
    lines = []
    ref_i = next((i for i, (_, t) in enumerate(paras) if re.fullmatch(r'\s*(References|Reference list)\s*', t)), len(paras))
    body = paras[:ref_i]; refs = [x for x in paras[ref_i + 1:] if x[1].strip()]
    # names
    pat = re.compile('|'.join(re.escape(x) for x in [marker] + bad_authors), re.I)
    hits = [(pid, t[:100]) for pid, t in paras if pat.search(t)]
    lines.append(f'## Visible text naming {marker}/{",".join(bad_authors)}: {len(hits)}')
    lines += [f'- {pid}: {t}' for pid, t in hits]
    # numbering
    for kind in ('Figure', 'Table'):
        nums = [(pid, int(m.group(1))) for pid, t in body for m in [re.match(kind + r'\s+\d+\.(\d+)\b', t.strip())] if m]
        seq = [n for _, n in nums]
        ok = seq == list(range(1, len(seq) + 1))
        lines.append(f'## {kind} captions: {seq} ' + ('OK' if ok else 'NEEDS RENUMBER'))
        bad = [t for _, t in body if re.match(kind + r'\s+\d+\b(?!\.\d)', t.strip())]
        lines += [f'- odd caption: {t[:80]}' for t in bad]
    # references
    btxt = '\n'.join(t for _, t in body)
    groups = collections.defaultdict(list); uncited = []
    for pid, t in refs:
        m = re.match(r'(.+?)\s(\d{4}|n\.d\.)([a-z]?)[,\s]', t)
        if not m:
            continue
        a, y, l = m.groups(); first = re.split(r',| & | \(', a)[0].strip()
        if not re.search(re.escape(first) + r'[^)\n]{0,160}?' + re.escape(y + l) + r'(?![0-9a-z])', btxt):
            uncited.append((pid, t[:90]))
        else:
            groups[(a, y)].append(l)
    lines.append(f'## References: {len(refs)} entries, {len(uncited)} with no in-text match (check before deleting)')
    lines += [f'- {pid}: {t}' for pid, t in uncited]
    gaps = [(k, sorted(v)) for k, v in groups.items() if any(v) and sorted(v) != [chr(97 + i) for i in range(len(v))] if len(v) > 1 or v != ['']]
    lines.append(f'## Year-letter gaps among cited entries: {len(gaps)}')
    lines += [f'- {k[0]} {k[1]}: {v}' for k, v in gaps]
    cur = [(pid, m.group(0)) for pid, t in body for m in re.finditer(r'(?<![A-Za-z])A\$[\d.,]+\w*|\$A(?=[\d ])', t)]
    lines.append(f'## Local-currency prefixes outside references (rule R): {len(cur)}')
    lines += [f'- {pid}: {s}' for pid, s in cur[:40]]
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('doc'); ap.add_argument('out')
    ap.add_argument('--owner', required=True); ap.add_argument('--aliases', default='')
    ap.add_argument('--remove-authors', default='Claude'); ap.add_argument('--remove-ids', default='')
    ap.add_argument('--marker', default='CLAUDE'); ap.add_argument('--report')
    ap.add_argument('--date', default='2026-01-01T00:00:00Z')
    a = ap.parse_args()
    tmp = tempfile.mkdtemp()
    with zipfile.ZipFile(a.doc) as z:
        z.extractall(tmp)
    bad = [x.strip() for x in a.remove_authors.split(',') if x.strip()]
    ops = [{'op': 'rename', 'from': al.strip(), 'to': a.owner} for al in a.aliases.split(',') if al.strip()]
    cpath = os.path.join(tmp, 'word', 'comments.xml'); ids = []
    if os.path.exists(cpath):
        for c in parse(cpath).getroot().findall(q('comment')):
            if c.get(q('author')) in bad:
                ids.append(c.get(q('id')))
    ids += [x.strip() for x in a.remove_ids.split(',') if x.strip()]
    ops += [{'op': 'remove_comment', 'id': i} for i in ids]
    opf = os.path.join(tmp, '_ops.json'); json.dump(ops, open(opf, 'w'))
    subprocess.run([sys.executable, os.path.join(HERE, 'track_edit_ops.py'), tmp, opf, a.owner, a.date], check=True, stdout=subprocess.DEVNULL)
    os.remove(opf)
    removed = strip_markers(os.path.join(tmp, 'word', 'document.xml'), a.marker)
    dedupe_people(tmp)
    if os.path.exists(a.out):
        os.remove(a.out)
    with zipfile.ZipFile(a.out, 'w', zipfile.ZIP_DEFLATED) as z:
        ct = os.path.join(tmp, '[Content_Types].xml')
        z.write(ct, '[Content_Types].xml')
        for root, _, files in os.walk(tmp):
            for f in files:
                full = os.path.join(root, f); rel = os.path.relpath(full, tmp)
                if rel != '[Content_Types].xml':
                    z.write(full, rel)
    rep = [f'# Final pass: {os.path.basename(a.doc)}',
           f'- authors renamed to {a.owner}: {a.aliases or "none"}',
           f'- comments removed: {len(ids)}',
           f'- deleted [{a.marker}] notes stripped: {len(removed)}',
           report(os.path.join(tmp, 'word', 'document.xml'), a.marker, bad)]
    txt = '\n'.join(rep)
    if a.report:
        open(a.report, 'w').write(txt)
    print(txt)
    shutil.rmtree(tmp)


if __name__ == '__main__':
    main()
