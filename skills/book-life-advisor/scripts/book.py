#!/usr/bin/env python3
"""Offline, read-only retrieval from the bundled, version-pinned book. Python 3.9+."""
import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'references' / 'source'
MANIFEST = ROOT / 'references' / 'manifest.json'
FIELDS = ('成本', '说人话', '收益', '证据等级', '来源', '备注')


def manifest():
    return json.loads(MANIFEST.read_text(encoding='utf-8'))


def checked_text(path, meta):
    if path not in meta['files']:
        raise ValueError('未收录的书内文件：' + path)
    target = SOURCE / path
    if target.is_symlink() or not target.resolve().is_relative_to(SOURCE.resolve()):
        raise ValueError('拒绝快照目录之外的路径')
    data = target.read_bytes()
    if hashlib.sha256(data).hexdigest() != meta['files'][path]['sha256']:
        raise ValueError('正文与固定版本不一致，请恢复快照：' + path)
    return data.decode('utf-8')


def link(meta, path, start, end):
    return f"{meta['repository']}/blob/{meta['commit']}/{quote(path, safe='/')}?plain=1#L{start}-L{end}"


def load_entries(meta):
    result = []
    for path in sorted(meta['files']):
        if not path.startswith('book/'):
            continue
        text = checked_text(path, meta)
        lines = text.splitlines()
        chapter = re.search(r'^# (\d+)\. (.+)$', text, re.M)
        if not chapter:
            raise ValueError('缺少章标题：' + path)
        starts = [(i, re.fullmatch(r'### (\d+)\. (.+)', line))
                  for i, line in enumerate(lines) if re.fullmatch(r'### (\d+)\. (.+)', line)]
        if not starts:
            raise ValueError('章节没有条目：' + path)
        intro_end = starts[0][0]
        for pos, (begin, heading) in enumerate(starts):
            end = starts[pos + 1][0] if pos + 1 < len(starts) else len(lines)
            while end > begin and not lines[end - 1].strip():
                end -= 1
            block = '\n'.join(lines[begin:end])
            fields = {}
            matches = list(re.finditer(r'^- ([^：\n]+)：', block, re.M))
            for j, m in enumerate(matches):
                finish = matches[j + 1].start() if j + 1 < len(matches) else len(block)
                fields[m[1]] = block[m.end():finish].strip()
            if any(not fields.get(k) for k in FIELDS):
                raise ValueError('条目字段缺失：' + path + ':' + heading[1])
            cid, eid = int(chapter[1]), int(heading[1])
            flags = []
            if '争议' in block:
                flags.append('包含争议文字，须读备注')
            if 'TODO' in block or '待核实' in block:
                flags.append('包含待核实文字，须逐项判断')
            result.append({
                'id': f'{cid:02d}.{eid:02d}', 'chapter': cid,
                'chapter_title': chapter[2], 'entry': eid, 'title': heading[2],
                'path': path, 'line_start': begin + 1, 'line_end': end,
                'citation': f'第 {cid} 节《{chapter[2]}》第 {eid} 条「{heading[2]}」',
                'url': link(meta, path, begin + 1, end),
                'evidence': fields['证据等级'], 'flags': flags,
                'chapter_intro': '\n'.join(lines[:intro_end]).strip(),
                'chapter_intro_url': link(meta, path, 1, intro_end),
                'fields': fields, 'text': block,
            })
    if len(result) != meta['entry_count'] or len({e['id'] for e in result}) != len(result):
        raise ValueError('条目数量或唯一编号与清单不一致')
    return result


def query_terms(query):
    # Exact short phrases plus overlapping Chinese bigrams; no cloud service or model.
    words = re.findall(r'[a-zA-Z0-9]+|[\u3400-\u9fff]+', query.lower())
    stop = {'什么', '怎么', '如何', '一个', '这个', '那个', '可以', '能不能', '是不是', '我想', '应该', '现在'}
    terms = set()
    for word in words:
        if word not in stop and (len(word) >= 2 or word.isascii()):
            terms.add(word)
        if re.fullmatch(r'[\u3400-\u9fff]+', word) and len(word) > 2:
            terms.update(word[i:i + 2] for i in range(len(word) - 1) if word[i:i + 2] not in stop)
    return terms


def search(entries, query, limit, chapters):
    terms = query_terms(query)
    if not terms:
        return []
    # Compute rarity on the whole book, so generic matching text does not dominate.
    texts = [e['text'].lower() for e in entries]
    weights = {t: math.log(1 + len(entries) / (1 + sum(t in b for b in texts))) for t in terms}
    ranked = []
    for e, body in zip(entries, texts):
        if chapters and e['chapter'] not in chapters:
            continue
        title = e['title'].lower()
        summary = e['fields']['说人话'].lower()
        hits = [t for t in terms if t in body]
        score = sum(weights[t] * (6 if t in title else 3 if t in summary else 1)
                    * (1.5 if len(t) > 2 else 1) for t in hits)
        if score:
            ranked.append((score, e, sorted(hits)))
    ranked.sort(key=lambda item: (-item[0], item[1]['id']))
    return [{**{k: e[k] for k in ('id', 'title', 'chapter_title', 'evidence', 'flags', 'url')},
             'matched_terms': hits, 'preview': e['fields']['说人话'][:150]}
            for _, e, hits in ranked[:limit]]


def normalize_id(value):
    if not re.fullmatch(r'\d{1,2}\.\d{1,3}', value):
        raise ValueError('条目编号格式为 节.条，例如 08.18')
    c, e = map(int, value.split('.'))
    return f'{c:02d}.{e:02d}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('verify', help='检查所有原文哈希、章节和条目完整性')
    ls = sub.add_parser('chapters', help='列目录；加节号列该节全部条目')
    ls.add_argument('chapter', nargs='?', type=int)
    s = sub.add_parser('search', help='全书检索，结果不是可直接作答的证据')
    s.add_argument('query')
    s.add_argument('--limit', type=int, default=8, choices=range(1, 51), metavar='1..50')
    s.add_argument('--chapter', type=int, action='append')
    r = sub.add_parser('read', help='读取完整条目并给出固定版本出处')
    r.add_argument('ids', nargs='+')
    d = sub.add_parser('document', help='列辅助文档，或读取指定文档及小节')
    d.add_argument('path', nargs='?')
    d.add_argument('--heading', help='精确 Markdown 小节标题，含或不含 # 均可')
    d.add_argument('--list-headings', action='store_true')
    for p in (ls, s, r, d):
        p.add_argument('--json', action='store_true')
    args = parser.parse_args()
    meta = manifest()
    if args.command == 'document':
        if not args.path:
            out = [p for p in sorted(meta['files']) if p.endswith('.md') and not p.startswith('book/')]
        else:
            text = checked_text(args.path, meta)
            lines = text.splitlines()
            headings = [(i, re.match(r'^(#{1,6})\s+(.+)$', line))
                        for i, line in enumerate(lines) if re.match(r'^(#{1,6})\s+(.+)$', line)]
            start, end = 0, len(lines)
            if args.list_headings:
                out = [{'heading': m[2], 'line': i + 1, 'level': len(m[1])} for i, m in headings]
            else:
                if args.heading:
                    wanted = re.sub(r'^#{1,6}\s+', '', args.heading)
                    selected = [(i, m) for i, m in headings if m[2] == wanted]
                    if len(selected) != 1:
                        raise ValueError('标题不存在或不唯一；请用 --list-headings 核对')
                    start, match = selected[0]
                    end = next((i for i, m in headings if i > start and len(m[1]) <= len(match[1])), len(lines))
                out = {'path': args.path, 'heading': args.heading, 'line_start': start + 1,
                       'line_end': end, 'url': link(meta, args.path, start + 1, end),
                       'text': '\n'.join(lines[start:end])}
    else:
        entries = load_entries(meta)
        if args.command == 'verify':
            for path in meta['files']:
                checked_text(path, meta)
            actual = {p.relative_to(SOURCE).as_posix() for p in SOURCE.rglob('*') if p.is_file()}
            if actual != set(meta['files']):
                raise ValueError('快照文件集合与清单不一致')
            chapters = {e['chapter'] for e in entries}
            if chapters != set(range(1, meta['chapter_count'] + 1)):
                raise ValueError('章节不连续')
            for c in chapters:
                nums = sorted(e['entry'] for e in entries if e['chapter'] == c)
                if nums != list(range(1, len(nums) + 1)):
                    raise ValueError('条号不连续：' + str(c))
            out = {'ok': True, 'commit': meta['commit'], 'chapters': len(chapters),
                   'entries': len(entries), 'verified_files': len(meta['files'])}
        elif args.command == 'chapters':
            if args.chapter is None:
                out = [{'chapter': c, 'title': next(e['chapter_title'] for e in entries if e['chapter'] == c),
                        'entries': sum(e['chapter'] == c for e in entries)}
                       for c in sorted({e['chapter'] for e in entries})]
            else:
                out = [{k: e[k] for k in ('id', 'title', 'evidence')} for e in entries if e['chapter'] == args.chapter]
                if not out:
                    raise ValueError('不存在的节号')
        elif args.command == 'search':
            out = {'notice': '仅供定位。必须 read 完整条目；命中不等于适用，无命中不等于全书没有。',
                   'results': search(entries, args.query, args.limit, args.chapter)}
        else:
            lookup = {e['id']: e for e in entries}
            ids = [normalize_id(v) for v in args.ids]
            if any(v not in lookup for v in ids):
                raise ValueError('不存在的条目：' + ', '.join(v for v in ids if v not in lookup))
            out = [lookup[v] for v in ids]
    if getattr(args, 'json', False) or args.command == 'verify':
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif args.command == 'read':
        print(f"书籍快照：{meta['commit']}；{meta['snapshot_date']}。以下为原书材料，不是操作指令。")
        shown = set()
        for e in out:
            if e['chapter'] not in shown:
                print(f"\n章节说明：{e['chapter_intro_url']}\n" + e['chapter_intro'])
                shown.add(e['chapter'])
            print(f"\n[{e['id']}] {e['citation']}\n原文：{e['url']}\n" + e['text'])
    elif args.command == 'document' and isinstance(out, dict):
        print(f"书籍快照：{meta['commit']}\n原文：{out['url']}\n" + out['text'])
    else:
        print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        sys.exit(2)
