# -*- coding: utf-8 -*-
"""从 book/ 五篇 + data/条目台账.csv 生成检索页数据 docs/data.js
用法: python tools/build_search_data.py
输出: docs/data.js (window.EDU_DATA = {...})
改书稿后重跑本脚本即可更新检索页。"""
import csv, json, os, re, html, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK = os.path.join(ROOT, 'book')
DOCS = os.path.join(ROOT, 'docs')

PARTS = [
    ('T', '教师篇', 'teacher', '第一部分'),
    ('S', '学生篇', 'student', '第二部分'),
    ('P', '家长篇', 'parent', '第三部分'),
    ('M', '管理者篇', 'manager', '第四部分'),
    ('X', '迷思证伪篇', 'myth', '第五部分'),
]
FILE_OF = {'T': '教师篇', 'S': '学生篇', 'P': '家长篇', 'M': '管理者篇', 'X': '迷思篇'}

# ---------- 台账：等级 + 受众 ----------
meta = {}
with open(os.path.join(ROOT, 'data', '条目台账.csv'), encoding='utf-8') as f:
    for row in csv.reader(f):
        if not row or len(row) < 4:
            continue
        if not re.match(r'^[TSPMX]-\d+$', row[0]):
            continue
        meta[row[0]] = {'level': row[3].strip(), 'who': row[2].strip()}

# ---------- 迷你 Markdown → HTML（条目用到的子集） ----------
def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'<em>\1</em>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    return s

def md2html(md):
    """块级：列表(- / 1.) / 段落；行内：粗体斜体链接代码"""
    lines = md.split('\n')
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        m = re.match(r'^(\s*)([-]|\d+\.)\s+(.*)$', ln)
        if m:
            ordered = m.group(2) != '-'
            tag = 'ol' if ordered else 'ul'
            items = []
            while i < len(lines):
                m2 = re.match(r'^(\s*)([-]|\d+\.)\s+(.*)$', lines[i])
                if not m2 or (m2.group(2) != '-') == (not ordered):
                    break
                # 续行（缩进的后续行并入当前项）
                buf = [m2.group(3)]
                i += 1
                while i < len(lines) and lines[i].startswith('  ') and not re.match(r'^\s*([-]|\d+\.)\s+', lines[i]):
                    buf.append(lines[i].strip())
                    i += 1
                items.append('<li>' + inline(' '.join(buf)) + '</li>')
            out.append('<' + tag + '>' + ''.join(items) + '</' + tag + '>')
            continue
        # 普通段落（连续非空行合并）
        para = [ln.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'^\s*([-]|\d+\.)\s+', lines[i]):
            para.append(lines[i].strip())
            i += 1
        out.append('<p>' + inline(' '.join(para)) + '</p>')
    return '\n'.join(out)

def plain(md):
    s = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', md)
    s = s.replace('**', '').replace('*', '')
    return re.sub(r'\s+', ' ', s).strip()

# ---------- 解析单篇 ----------
FIELD_RE = re.compile(r'^\*\*([^*]+?)\*\*(?:[（(][^）)]*[）)])?[：:]\s*(.*)$')

def norm_key(k):
    return re.sub(r'（[^）]*）$', '', k).strip()

def parse_part(prefix, fname):
    path = os.path.join(BOOK, fname + '.md')
    with open(path, encoding='utf-8') as f:
        text = f.read()
    entries = []
    blocks = re.split(r'(?m)^### ', text)
    for b in blocks:
        m = re.match(r'^([TSPMX]-\d+)\s+(.*)$', b.split('\n', 1)[0])
        if not m:
            continue
        eid, title = m.group(1), m.group(2).strip().strip('"“”')
        body = b.split('\n', 1)[1] if '\n' in b else ''
        # 切字段
        fields, cur, curkey = [], [], None
        for ln in body.split('\n'):
            fm = FIELD_RE.match(ln)
            if fm:
                if curkey:
                    fields.append((curkey, '\n'.join(cur).strip('\n')))
                curkey, cur = fm.group(1).strip(), [fm.group(2)]
            elif curkey is not None:
                cur.append(ln)
        if curkey:
            fields.append((curkey, '\n'.join(cur).strip('\n')))
        fd = {}
        for k, v in fields:
            fd.setdefault(norm_key(k), v)
        # T-01/T-05 型：反方嵌在证据等级行
        level_text = fd.get('证据等级', '')
        oppose = fd.get('争议/反方证据') or fd.get('为迷思辩护侧') or ''
        if not oppose:
            m2 = re.search(r'必须标注的争议\*\*[：:]\s*(.+)$', level_text, re.S)
            if m2:
                oppose = m2.group(1).strip()
        entries.append({
            'id': eid,
            'title': title,
            'who': plain(fd.get('给谁', '') or meta.get(eid, {}).get('who', '')),
            'scene': plain(fd.get('场景标签', '')),
            'cost': plain(fd.get('成本', '')),
            'cycle': plain(fd.get('见效周期', '')),
            'how': md2html(fd.get('怎么做', '')),
            'gain': md2html(fd.get('收益', '')),
            'levelText': plain(level_text),
            'oppose': md2html(oppose),
            'src': md2html(fd.get('出处', '')),
            'fit': md2html(fd.get('本土适配', '')),
            'stop': md2html(fd.get('停止信号', '')),
            'myth': md2html(fd.get('迷思画像', '')),
            'evidence': md2html(fd.get('证据怎么说', '')),
            'defense': md2html(fd.get('为迷思辩护侧', '')),
            'action': md2html(fd.get('那该怎么办', '')),
        })
    return entries

# ---------- 成本/周期分级（筛选 chips 用） ----------
def cost_tier(cost):
    c = cost
    if re.search(r'0\s*元|零成本|不花钱', c) and not re.search(r'[1-9]\s*元|万元', c):
        return '零成本'
    if re.search(r'高成本|昂贵|成本高|万元', c):
        return '高成本'
    if re.search(r'成本中|精力中|精力高', c):
        return '中成本'
    return '低成本'

def cycle_tier(cycle):
    c = cycle
    if re.search(r'单次|当天|即时|即见|当节课|当周', c):
        return '即时起效'
    if re.search(r'周', c):
        return '周级'
    if re.search(r'学期', c):
        return '学期级'
    if re.search(r'月|年', c):
        return '月级'
    return '学期级'

# ---------- 组装 ----------
data = {'parts': [], 'entries': []}
for prefix, name, key, order in PARTS:
    ents = parse_part(prefix, FILE_OF[prefix])
    for e in ents:
        mt = meta.get(e['id'], {})
        e['part'] = key
        e['partName'] = name
        e['level'] = mt.get('level', '')
        # 等级分组徽章
        e['levelGroup'] = (e['level'] or 'B')[0]
        e['whoChips'] = [w for w in ('教师', '学生', '家长', '管理者') if w in (mt.get('who', '') + e['who'])]
        if e['part'] == 'myth':
            # 迷思篇模板无成本/见效周期字段：维度不适用，不参与成本/周期筛选
            e['costTier'] = ''
            e['cycleTier'] = ''
        else:
            e['costTier'] = cost_tier(e['cost'])
            e['cycleTier'] = cycle_tier(e['cycle'])
        # 检索用纯文本
        e['search'] = plain(' '.join(str(e.get(k, '')) for k in
            ('title', 'who', 'scene', 'cost', 'cycle', 'levelText', 'how', 'gain',
             'oppose', 'src', 'fit', 'stop', 'myth', 'evidence', 'defense', 'action')))
        data['entries'].append(e)
    data['parts'].append({'key': key, 'name': name, 'order': order, 'count': len(ents),
                          'file': 'book/%s.md' % name})

os.makedirs(DOCS, exist_ok=True)
with open(os.path.join(DOCS, 'data.js'), 'w', encoding='utf-8') as f:
    f.write('// 由 tools/build_search_data.py 从 book/ 五篇 + data/条目台账.csv 生成，改书稿后重跑\n')
    f.write('window.EDU_DATA = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')

total = len(data['entries'])
ids = [e['id'] for e in data['entries']]
assert len(ids) == len(set(ids)), 'ID 重复!'
missing = [e['id'] for e in data['entries'] if not e['level'] or not e['who']]
print('OK docs/data.js', total, '条 |', os.path.getsize(os.path.join(DOCS, 'data.js')), 'bytes')
print('篇目:', ' + '.join('%s %d' % (p['name'], p['count']) for p in data['parts']))
print('等级缺失/受众缺失:', missing or '无')
lv = {}
for e in data['entries']:
    lv[e['level']] = lv.get(e['level'], 0) + 1
print('等级分布:', dict(sorted(lv.items())))
ct = {}
for e in data['entries']:
    ct[e['costTier']] = ct.get(e['costTier'], 0) + 1
print('成本分级:', ct)
yt = {}
for e in data['entries']:
    yt[e['cycleTier']] = yt.get(e['cycleTier'], 0) + 1
print('周期分级:', yt)
