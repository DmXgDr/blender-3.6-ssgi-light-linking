"""Remove an equal-length local path prefix from non-executable PE .rdata only."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

def sections(data):
    if data[:2] != b'MZ':
        raise ValueError('Not a PE executable')
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    assert data[pe:pe+4] == b'PE\0\0'
    count = struct.unpack_from('<H', data, pe+6)[0]
    optional_size = struct.unpack_from('<H', data, pe+20)[0]
    result = []
    for i in range(count):
        pos = pe+24+optional_size+40*i
        name = data[pos:pos+8].split(b'\0')[0].decode('ascii')
        size, offset = struct.unpack_from('<II', data, pos+16)
        flags = struct.unpack_from('<I', data, pos+36)[0]
        result.append((name, offset, offset+size, flags))
    return result

def sanitize(path, old, new):
    assert len(old) == len(new) and len(old) > 3
    assert old[1:3] in (':/', ':\\') and new[1:3] in (':/', ':\\')
    data = path.read_bytes()
    output = bytearray(data)
    ranges = sections(data)
    changed = 0
    for separator, encoding in [(s,e) for s in ['\\','/'] for e in ['ascii','utf-16-le']]:
        before = old.replace('\\', separator).replace('/', separator).encode(encoding)
        after = new.replace('\\', separator).replace('/', separator).encode(encoding)
        offset = 0
        while True:
            offset = data.find(before, offset)
            if offset < 0:break
            section = next(s for s in ranges if s[1] <= offset and offset+len(before) <= s[2])
            assert section[0] == '.rdata' and not section[3] & 0x20000000
            suffix=separator.encode(encoding)
            assert data[offset+len(before):offset+len(before)+len(suffix)] == suffix
            output[offset:offset+len(before)] = after
            changed += 1
            offset += len(before)
    assert changed
    code = {}
    for name, start, end, flags in ranges:
        if name != '.rdata':assert output[start:end] == data[start:end]
        if flags & 0x20000000:
            code[name] = hashlib.sha256(output[start:end]).hexdigest()
    assert len(output) == len(data)
    path.write_bytes(output)
    return {'replacement_count':changed,'executable_sections_unchanged':True,
            'executable_section_sha256':code,'file_size_unchanged':True,
            'before_sha256':hashlib.sha256(data).hexdigest(),
            'after_sha256':hashlib.sha256(output).hexdigest()}

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary',type=Path)
    parser.add_argument('--from-prefix',required=True)
    parser.add_argument('--to-prefix',required=True)
    parser.add_argument('--report',required=True,type=Path)
    args=parser.parse_args()
    report=sanitize(args.binary,args.from_prefix,args.to_prefix)
    args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report))
