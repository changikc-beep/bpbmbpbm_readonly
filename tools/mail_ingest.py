"""Daou Office mail -> attachments, read over IMAP (read-only). Step 1: connection test and mail listing.

Credentials live in Windows Credential Manager (generic credential "daou-imap"); store them once with
    cmdkey /generic:daou-imap /user:<your mail address> /pass
(cmdkey asks for the password; it is never written to a file or shown to anyone.)

Usage (Python 3.12):
    py -V:3.12 tools\\mail_ingest.py test [--days 30]        # log in, list recent mails we care about
    py -V:3.12 tools\\mail_ingest.py peek <kind> [--days 30] # latest mail of a kind: attachment sheets + first rows
kinds: inout (입출고), tolling (성일 톨링 처리 내역), tgl (TGL KHE REPORT), szamla (TGL SURRENDER BL + INSURANCE)

Safety: the mailbox is opened with EXAMINE (read-only) and bodies are fetched with BODY.PEEK, so nothing is
marked read, moved or deleted. Attachments are parsed in memory and never saved to disk (the document security
program on this PC encrypts .xlsx files written under the user folders).
"""
import argparse, ctypes, ctypes.wintypes as wt, email, imaplib, io, re, sys
from datetime import date, timedelta
from email.header import decode_header, make_header

HOST, PORT, CRED_TARGET = "imap.daouoffice.com", 993, "daou-imap"

# subject patterns per kind (matched on the decoded subject, case-insensitive)
KINDS = {
    "inout":   re.compile(r"입출고"),
    "tolling": re.compile(r"톨링\s*처리\s*내역"),
    "tgl":     re.compile(r"KHE\s*REPORT", re.I),
    "szamla":  re.compile(r"SURRENDER\s*BL", re.I),
    "export":  re.compile(r"export", re.I),
}


def read_credential(target=CRED_TARGET):
    """(user, password) of a generic Windows credential, via advapi32 CredReadW (no extra packages)."""
    class CREDENTIAL(ctypes.Structure):
        _fields_ = [("Flags", wt.DWORD), ("Type", wt.DWORD), ("TargetName", wt.LPWSTR), ("Comment", wt.LPWSTR),
                    ("LastWritten", wt.FILETIME), ("CredentialBlobSize", wt.DWORD),
                    ("CredentialBlob", ctypes.POINTER(ctypes.c_byte)), ("Persist", wt.DWORD),
                    ("AttributeCount", wt.DWORD), ("Attributes", ctypes.c_void_p),
                    ("TargetAlias", wt.LPWSTR), ("UserName", wt.LPWSTR)]
    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    adv.CredReadW.argtypes = [wt.LPCWSTR, wt.DWORD, wt.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIAL))]
    adv.CredFree.argtypes = [ctypes.c_void_p]
    p = ctypes.POINTER(CREDENTIAL)()
    if not adv.CredReadW(target, 1, 0, ctypes.byref(p)):     # 1 = CRED_TYPE_GENERIC
        sys.exit(f"자격 증명 '{target}' 없음. 먼저 실행: cmdkey /generic:{target} /user:<메일 주소> /pass")
    try:
        c = p.contents
        blob = ctypes.string_at(c.CredentialBlob, c.CredentialBlobSize)
        return c.UserName, blob.decode("utf-16-le")          # cmdkey stores the password as UTF-16
    finally:
        adv.CredFree(p)


def connect():
    user, pw = read_credential()
    m = imaplib.IMAP4_SSL(HOST, PORT)
    try:
        m.login(user, pw)
    except imaplib.IMAP4.error as e:
        sys.exit(f"로그인 실패 ({user}): {e}\n"
                 "- 아이디는 전체 메일 주소인지, 비밀번호가 웹메일과 같은지 확인\n"
                 "- 계속 실패하면 다우오피스 관리자에게 이 계정의 IMAP 사용 허용 여부 확인")
    return m, user


def _dec(v):
    return str(make_header(decode_header(v or ""))) if v else ""


def recent(m, days):
    """[(uid, date, from, subject, attachment names)] for INBOX mails of the last `days`, newest first."""
    m.select("INBOX", readonly=True)                           # EXAMINE: read-only
    since = (date.today() - timedelta(days=days)).strftime("%d-%b-%Y")
    typ, data = m.uid("search", None, f"(SINCE {since})")
    uids = data[0].split()
    out = []
    for i in range(0, len(uids), 50):
        chunk = b",".join(uids[i:i + 50])
        typ, rows = m.uid("fetch", chunk, "(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)] BODYSTRUCTURE)")
        for r in rows:
            if not isinstance(r, tuple):
                continue
            meta, hdr = r
            uid = re.search(rb"UID (\d+)", meta).group(1).decode()
            h = email.message_from_bytes(hdr)
            names = [_dec(n.decode(errors="replace")) for n in re.findall(rb'"(?:FILENAME|NAME)" "([^"]+)"', meta, re.I)]
            out.append((uid, h.get("Date", ""), _dec(h.get("From")), _dec(h.get("Subject")), sorted(set(names))))
    out.sort(key=lambda x: int(x[0]), reverse=True)
    return out


def attachments(m, uid):
    """[(filename, bytes)] of one mail, fetched with BODY.PEEK (not marked read)."""
    typ, rows = m.uid("fetch", uid, "(BODY.PEEK[])")
    msg = email.message_from_bytes(rows[0][1])
    out = []
    for part in msg.walk():
        fn = part.get_filename()
        # skip inline pictures (signatures, pasted photos): only real document attachments
        if fn and part.get_content_maintype() != "image":
            out.append((_dec(fn), part.get_payload(decode=True) or b""))
    return out


def cmd_test(args):
    m, user = connect()
    print(f"로그인 성공: {user} @ {HOST}")
    rows = recent(m, args.days)
    print(f"최근 {args.days}일 INBOX {len(rows)}통, 그중 처리 대상:")
    for uid, d, frm, subj, names in rows:
        kind = next((k for k, rx in KINDS.items() if rx.search(subj)), None)
        if kind:
            print(f"  [{kind:7s}] uid {uid} | {d[:22]} | {frm[:40]} | {subj[:60]} | 첨부 {', '.join(names) or '-'}")
    m.logout()


def cmd_peek(args):
    import openpyxl
    m, _ = connect()
    rx = KINDS[args.kind]
    # newest original mail of the kind (replies/forwards skipped: they repeat or drop the attachment)
    hit = next((r for r in recent(m, args.days) if rx.search(r[3]) and not re.match(r"\s*(re|fw|fwd)\s*:", r[3], re.I)), None)
    if not hit:
        sys.exit(f"최근 {args.days}일 '{args.kind}' 메일 없음")
    uid, d, frm, subj, _ = hit
    print(f"uid {uid} | {d} | {frm} | {subj}")
    for fn, blob in attachments(m, uid):
        print(f"- 첨부 {fn} ({len(blob):,} bytes)")
        if fn.lower().endswith((".xlsx", ".xlsm")):
            wb = openpyxl.load_workbook(io.BytesIO(blob), read_only=True, data_only=True)   # in memory only
            for ws in wb.worksheets:
                print(f"  시트 '{ws.title}' ({ws.max_row} x {ws.max_column})")
                for row in ws.iter_rows(min_row=1, max_row=args.rows, values_only=True):
                    vals = ["" if v is None else str(v)[:14] for v in row[:14]]
                    if any(vals):
                        print("    " + " | ".join(vals))
    m.logout()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    t = sp.add_parser("test"); t.add_argument("--days", type=int, default=30)
    p = sp.add_parser("peek"); p.add_argument("kind", choices=list(KINDS)); p.add_argument("--days", type=int, default=30)
    p.add_argument("--rows", type=int, default=8)
    a = ap.parse_args()
    {"test": cmd_test, "peek": cmd_peek}[a.cmd](a)
