"""Tracked edits as OWNER on a docx unpacked dir.
ops json list: {"op":"rename","from":..,"to":..} | {"op":"replace","para":pid,"old":..,"new":..,"occ":"first|last|N"}
 | {"op":"delete_para","para":pid} | {"op":"remove_comment","id":"208"}
 | {"op":"reject","para":pid,"text":..,"kind":"ins|del|both","all":false}  undo OWNER's own pending change(s) whose
   text contains `text` (ins removed, del restored), leaving no trace; use to roll back unasked edits
usage: track_edit_ops.py unpacked_dir ops.json owner date
Rules: text inside OWNER's pending w:ins is edited in place (as Word does); other text gets w:del
(nested inside a reviewer's w:ins if needed, splitting that ins so the new w:ins sits after it)."""
import sys,json,copy,re,os
from lxml import etree
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
W14='http://schemas.microsoft.com/office/word/2010/wordml'
W15='http://schemas.microsoft.com/office/word/2012/wordml'
def q(t,ns=W): return '{%s}%s'%(ns,t)
D,OPS,OWNER,DATE=sys.argv[1],json.load(open(sys.argv[2])),sys.argv[3],sys.argv[4]
P=lambda f: os.path.join(D,'word',f)
parser=etree.XMLParser(remove_blank_text=False, resolve_entities=False, no_network=True, load_dtd=False)
doc=etree.parse(P('document.xml'),parser); root=doc.getroot()
NID=[900000]
def nid(): NID[0]+=1; return str(NID[0])
def mk(tag):
  e=etree.Element(q(tag)); e.set(q('id'),nid()); e.set(q('author'),OWNER); e.set(q('date'),DATE); return e
def para(pid):
  r=root.xpath('//w:p[@w14:paraId=$p]',namespaces={'w':W,'w14':W14},p=pid)
  assert len(r)==1,(pid,len(r)); return r[0]
CONTENT={q('t'),q('delText'),q('tab'),q('br'),q('drawing'),q('fldChar'),q('instrText'),q('commentReference'),q('footnoteReference'),q('endnoteReference'),q('sym'),q('noBreakHyphen'),q('lastRenderedPageBreak')}
def normalize(p):
  for r in list(p.iter(q('r'))):
    kids=[c for c in r if c.tag!=q('rPr')]
    if len(kids)<=1: continue
    rpr=r.find(q('rPr')); par=r.getparent(); i=par.index(r)
    for k,c in enumerate(kids):
      nr=etree.Element(q('r'))
      for a,v in r.attrib.items(): nr.set(a,v)
      if rpr is not None: nr.append(copy.deepcopy(rpr))
      nr.append(c); par.insert(i+k,nr)
    par.remove(r)
def anc(el,tag):
  e=el.getparent()
  while e is not None and e.tag!=q('p'):
    if e.tag==q(tag): return e
    e=e.getparent()
  return None
def visible(p):
  segs=[]
  for t in p.iter(q('t')):
    if anc(t,'del') is not None or anc(t,'moveFrom') is not None: continue
    segs.append(t)
  return segs
def split_run(r,t,a,b):
  """split run r (single t) so that chars [a,b) are in their own run; return mid run"""
  s=t.text or ''
  par=r.getparent(); i=par.index(r)
  parts=[(s[:a],'pre'),(s[a:b],'mid'),(s[b:],'post')]
  out={}
  k=0
  for txt,nm in parts:
    if not txt: continue
    nr=copy.deepcopy(r); nt=nr.find(q('t')); nt.text=txt
    nt.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
    par.insert(i+k,nr); k+=1; out[nm]=nr
  par.remove(r); return out['mid']
def owner_ins(el):
  a=anc(el,'ins'); return a is not None and a.get(q('author'))==OWNER, a
def new_run_like(r,text):
  nr=etree.Element(q('r')); rpr=r.find(q('rPr'))
  if rpr is not None:
    rp=copy.deepcopy(rpr)
    for x in rp.findall(q('rPrChange'))+rp.findall(q('highlight')): rp.remove(x)
    nr.append(rp)
  t=etree.SubElement(nr,q('t')); t.text=text; t.set('{http://www.w3.org/XML/1998/namespace}space','preserve'); return nr
def cleanup(p):
  for tag in ('ins','del'):
    for e in list(p.iter(q(tag))):
      if len([x for x in e.iter(q('t'),q('delText'))])==0 and len(list(e.iter(q('drawing'))))==0 and e.getparent().tag!=q('rPr') and e.getparent().tag!=q('trPr'):
        if e.getparent() is not None and len(e)==0 or all(c.tag==q('r') and len([k for k in c if k.tag!=q('rPr')])==0 for c in e):
          e.getparent().remove(e)
def replace(op):
  p=para(op['para']); normalize(p)
  segs=visible(p); full=''.join(t.text or '' for t in segs)
  old=op['old']; occ=op.get('occ','first')
  idxs=[m.start() for m in re.finditer(re.escape(old),full)]
  if not idxs and op.get('optional'):
    print('skip (not in editable text, e.g. equation)',op['para'],old); return
  assert idxs,('not found',op['para'],old,full[:200])
  if occ=='first':
    assert len(idxs)==1 or op.get('allow_multi'),('ambiguous',op['para'],old,len(idxs))
    s=idxs[0]
  elif occ=='last': s=idxs[-1]
  else: s=idxs[int(occ)]
  s+=op.get('offset',0); e=s+op.get('span',len(old)-op.get('offset',0))
  pos=0; mids=[]
  for t in segs:
    L=len(t.text or ''); a,b=max(s,pos),min(e,pos+L)
    if a<b: mids.append((t,a-pos,b-pos))
    pos+=L
  anchor=None  # (kind, element)
  for n,(t,a,b) in enumerate(mids):
    r=t.getparent(); m=split_run(r,t,a,b)
    own,ins=owner_ins(m)
    if n==0: first=(m,own,ins)
    if own:
      if n==0:
        if op['new']:
          m.addprevious(new_run_like(m,op['new']))
        anchor='done'
      m.getparent().remove(m)
    else:
      mt=m.find(q('t')); mt.tag=q('delText')
      d=mk('del'); m.addprevious(d); d.append(m)
      if n==0: first=(d,own,ins)
  if anchor!='done' and op['new']:
    el,own,ins=first
    nr=new_run_like(el if el.tag==q('r') else el.find(q('r')),op['new'])
    ni=mk('ins'); ni.append(nr)
    par=el.getparent()
    if par.tag==q('ins'):  # inside reviewer insertion: split it
      after=list(el.itersiblings())
      if after:
        clone=etree.Element(q('ins'))
        for k,v in par.attrib.items(): clone.set(k,v)
        clone.set(q('id'),nid())
        for x in after: clone.append(x)
        par.addnext(clone)
      # put new ins after reviewer ins, but must sit right after the del: del is last child of par now
      par.addnext(ni)
    else:
      el.addnext(ni)
  if not mids: raise Exception('no mids')
  cleanup(p)
def delete_para(op):
  p=para(op['para']); normalize(p)
  ppr=p.find(q('pPr'))
  mark_ins=ppr is not None and ppr.find(q('rPr')) is not None and ppr.find(q('rPr')).find(q('ins')) is not None and ppr.find(q('rPr')).find(q('ins')).get(q('author'))==OWNER
  for r in list(p.iter(q('r'))):
    if r.getparent() is None or anc(r,'del') is not None: continue
    if r.getparent().tag==q('rPr'): continue
    own,ins=owner_ins(r)
    if own: r.getparent().remove(r); continue
    for t in r.findall(q('t')): t.tag=q('delText')
    for t in r.findall(q('instrText')): t.tag=q('delInstrText')
    d=mk('del'); r.addprevious(d); d.append(r)
  cleanup(p)
  if mark_ins and not list(p.iter(q('delText'))) and not [x for x in p.iter(q('ins')) if x.getparent().tag!=q('rPr')]:
    # whole paragraph was owner's pending insertion: drop it, keep any bookmarks/comment anchors out
    p.getparent().remove(p); return
  if ppr is None: ppr=etree.SubElement(p,q('pPr')); p.insert(0,ppr)
  rpr=ppr.find(q('rPr'))
  if rpr is None: rpr=etree.SubElement(ppr,q('rPr'))
  if rpr.find(q('del')) is None: rpr.append(mk('del'))
def reject(op):
  p=para(op['para']); kind=op.get('kind','both'); hits=0
  for tag in ('ins','del'):
    if kind not in (tag,'both'): continue
    for e in list(p.iter(q(tag))):
      if e.getparent() is None or e.getparent().tag in (q('rPr'),q('trPr')) or e.get(q('author'))!=OWNER: continue
      txt=''.join(x.text or '' for x in e.iter(q('t'),q('delText')))
      if op['text'] not in txt: continue
      if hits and not op.get('all'): raise Exception(('ambiguous reject',op['para'],op['text']))
      hits+=1
      if tag=='ins': e.getparent().remove(e)
      else:
        for x in e.iter(q('delText')): x.tag=q('t')
        for x in e.iter(q('delInstrText')): x.tag=q('instrText')
        par=e.getparent(); i=par.index(e)
        for k,c in enumerate(list(e)): par.insert(i+k,c)
        par.remove(e)
  assert hits or op.get('optional'),('reject: no owner change with text',op['para'],op['text'])
  cleanup(p)
def rename(op):
  for f in os.listdir(os.path.join(D,'word')):
    if not f.endswith('.xml'): continue
    fp=P(f); s=open(fp,encoding='utf-8').read()
    s2=s.replace(f'w:author="{op["from"]}"',f'w:author="{op["to"]}"').replace(f'w15:author="{op["from"]}"',f'w15:author="{op["to"]}"')
    if f=='people.xml':
      s2=s2.replace(f'w15:author="{op["to"]}"',f'w15:author="{op["to"]}"')
    if s2!=s:
      open(fp,'w',encoding='utf-8').write(s2)
  global doc,root
  doc=etree.parse(P('document.xml'),parser); root=doc.getroot()
def remove_comment(op):
  cid=op['id']
  for tag in ('commentRangeStart','commentRangeEnd'):
    for e in root.iter(q(tag)):
      if e.get(q('id'))==cid: e.getparent().remove(e)
  for e in list(root.iter(q('commentReference'))):
    if e.get(q('id'))==cid:
      r=e.getparent(); r.getparent().remove(r)
  cx=etree.parse(P('comments.xml'),parser); cr=cx.getroot()
  for c in cr.findall(q('comment')):
    if c.get(q('id'))==cid:
      pids=[x.get(q('paraId',W14)) for x in c.findall(q('p'))]
      cr.remove(c)
  cx.write(P('comments.xml'),xml_declaration=True,encoding='UTF-8',standalone=True)
  if os.path.exists(P('commentsExtended.xml')):
    ex=etree.parse(P('commentsExtended.xml'),parser)
    for e in list(ex.getroot()):
      if e.get(q('paraId',W15)) in pids: ex.getroot().remove(e)
    ex.write(P('commentsExtended.xml'),xml_declaration=True,encoding='UTF-8',standalone=True)
  W16CID='http://schemas.microsoft.com/office/word/2016/wordml/cid'
  dur=[]
  if os.path.exists(P('commentsIds.xml')):
    ix=etree.parse(P('commentsIds.xml'),parser)
    for e in list(ix.getroot()):
      if e.get(q('paraId',W16CID)) in pids: dur.append(e.get(q('durableId',W16CID))); ix.getroot().remove(e)
    ix.write(P('commentsIds.xml'),xml_declaration=True,encoding='UTF-8',standalone=True)
  if os.path.exists(P('commentsExtensible.xml')):
    W16CEX='http://schemas.microsoft.com/office/word/2018/wordml/cex'
    xx=etree.parse(P('commentsExtensible.xml'),parser)
    for e in list(xx.getroot()):
      if e.get(q('durableId',W16CEX)) in dur: xx.getroot().remove(e)
    xx.write(P('commentsExtensible.xml'),xml_declaration=True,encoding='UTF-8',standalone=True)
for op in OPS:
  if op['op']=='rename': rename(op)
for op in OPS:
  o=op['op']
  try:
    if o=='replace': replace(op)
    elif o=='delete_para': delete_para(op)
    elif o=='remove_comment': remove_comment(op)
    elif o=='reject': reject(op)
  except Exception as ex:
    print('FAIL',op,ex); sys.exit(1)
  else:
    if o!='rename': print('ok',o,op.get('para',op.get('id')),(op.get('old') or op.get('text') or '')[:40])
doc.write(P('document.xml'),xml_declaration=True,encoding='UTF-8',standalone=True)
