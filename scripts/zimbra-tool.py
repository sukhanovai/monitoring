#!/usr/bin/env python3
"""Zimbra 8.8 mailbox exports over SSH. Python 3.8+, standard library only."""
import argparse
import base64
import concurrent.futures
import contextlib
import datetime as dt
import getpass
import hashlib
import json
import os
import re
import secrets
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath

# Configure here, or override with environment variables in cron.
HOST = os.environ.get('ZB_HOST', 'zbackup@backup.example.invalid')
ROOT = os.environ.get('ZB_ROOT', '/rpool/mail')
KEY = os.environ.get('ZB_KEY', '/opt/zimbra/.ssh/zimbra_backup_ed25519')
EXPECTED_SOURCE = os.environ.get('ZB_SOURCE', 'rpool')
JOBS = int(os.environ.get('ZB_JOBS', '4'))
KEEP = int(os.environ.get('ZB_KEEP', '3'))  # Completed backups, not calendar days.
RESERVE = int(os.environ.get('ZB_RESERVE_GIB', '20')) * 1024**3
TIMEOUT = int(os.environ.get('ZB_TIMEOUT', '21600'))  # Per mailbox, seconds.
TRIES = int(os.environ.get('ZB_TRIES', '3'))
STATE = Path(os.environ.get('ZB_STATE', '/opt/zimbra/data/zimbra-tool'))
SPOOL = Path(os.environ.get('ZB_SPOOL', '/opt/zimbra/data/zimbra-tool-spool'))
MAIL_TO = os.environ.get('ZB_REPORT_TO', '')
BIN = '/opt/zimbra/bin/'
SAFE_SETTINGS = {
    'cn', 'givenName', 'sn', 'displayName', 'initials', 'description',
    'title', 'company', 'department', 'telephoneNumber', 'mobile',
    'homePhone', 'street', 'l', 'st', 'postalCode', 'co',
    'zimbraMailQuota', 'zimbraMailForwardingAddress',
    'zimbraPrefMailForwardingAddress', 'zimbraPrefMailLocalDeliveryDisabled',
    'zimbraPrefLocale', 'zimbraPrefTimeZoneId', 'zimbraPrefFromDisplay',
    'zimbraPrefReplyToEnabled', 'zimbraPrefReplyToAddress',
    'zimbraPrefReplyToDisplay', 'zimbraPrefMailSignature',
    'zimbraPrefMailSignatureEnabled', 'zimbraPrefMailSignatureStyle',
    'zimbraPrefOutOfOfficeReply', 'zimbraPrefOutOfOfficeReplyEnabled',
    'zimbraPrefOutOfOfficeFromDate', 'zimbraPrefOutOfOfficeUntilDate',
    'zimbraPrefMailDisplay', 'zimbraPrefMailItemsPerPage',
    'zimbraPrefMailDefaultCharset', 'zimbraPrefComposeFormat',
    'zimbraPrefSaveToSent', 'zimbraPrefGroupMailBy',
}

# Sent to the destination on each call. No installed receiver or daemon required.
REMOTE = r'''
import base64, datetime, fcntl, hashlib, json, os, pathlib, shutil
import subprocess, sys, tarfile, tempfile
a = json.loads(base64.b64decode(sys.argv[1]))
root = pathlib.Path(a['root'])
assert root.is_absolute() and str(root) not in ('/', '/rpool'), 'Unsafe backup root'
assert not root.is_symlink(), 'Backup root is a symlink'
probe = root
while not probe.exists():
    probe = probe.parent
mount = subprocess.check_output(['findmnt', '-J', '-T', str(probe),
                                '-o', 'SOURCE,FSTYPE'], text=True)
fs = json.loads(mount)['filesystems'][0]
assert fs['source'] == a['source'] and fs['fstype'] == 'zfs', 'Wrong destination filesystem'
root.mkdir(mode=0o700, parents=True, exist_ok=True)
os.umask(0o077)

def path(rel):
    p = pathlib.PurePosixPath(rel)
    assert not p.is_absolute() and '..' not in p.parts and p.parts, 'Unsafe relative path'
    target = root.joinpath(*p.parts)
    assert all(not q.is_symlink() for q in [target, *target.parents] if q != root.parent), 'Symlink in path'
    assert root.resolve() in target.resolve().parents, 'Path escapes root'
    return target

def out(value):
    print(json.dumps(value, ensure_ascii=False), flush=True)

def atomic(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.writing-', dir=str(p.parent))
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)
        d = os.open(str(p.parent), os.O_DIRECTORY)
        try:
            os.fsync(d)
        finally:
            os.close(d)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def check(p, archive=False):
    digest = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            digest.update(chunk)
    if archive:
        import gzip
        with gzip.open(str(p), 'rb') as f:
            with tarfile.open(fileobj=f, mode='r|') as t:
                for member in t:
                    if member.isfile():
                        data = t.extractfile(member)
                        for _ in iter(lambda: data.read(1024*1024), b''):
                            pass
            # Consume gzip trailer after tar's end-of-archive blocks.
            for _ in iter(lambda: f.read(1024*1024), b''):
                pass
    return {'sha256': digest.hexdigest(), 'size': p.stat().st_size}

def entries():
    result = []
    for p in sorted(root.iterdir(), reverse=True):
        if p.is_symlink() or not p.is_dir():
            continue
        if not (__import__('re').fullmatch(r'\d{8}T\d{6}-[a-f0-9]{8}', p.name)
                or __import__('re').fullmatch(r'\d{2}\.\d{2}\.\d{4}', p.name)):
            continue
        status = 'legacy' if (p/'users.txt').is_file() else 'incomplete'
        date = p.stat().st_mtime
        if (p/'manifest.json').is_file():
            m = json.loads((p/'manifest.json').read_text())
            status = m.get('status', 'incomplete')
            date = m['started']
        result.append({'id': p.name, 'status': status, 'started': date,
                       'protected': (p/'.protected').exists()})
    return sorted(result, key=lambda x: x['started'], reverse=True)

op = a['op']
if op == 'lease':
    f = (root/'.zimbra-tool.lock').open('a+')
    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    out({'locked': True})
    sys.stdin.buffer.read()
elif op == 'check':
    out({'free': shutil.disk_usage(root).free, 'source': fs['source'], 'root': str(root)})
elif op == 'list':
    out(entries())
elif op == 'read':
    sys.stdout.buffer.write(path(a['path']).read_bytes())
elif op == 'put':
    atomic(path(a['path']), sys.stdin.buffer.read())
    out(True)
elif op == 'receive':
    p = path(a['path'])
    p.parent.mkdir(parents=True, exist_ok=True)
    assert not p.exists(), 'Pending file already exists'
    digest = hashlib.sha256()
    count = 0
    with p.open('xb') as f:
        for chunk in iter(lambda: sys.stdin.buffer.read(1024*1024), b''):
            assert shutil.disk_usage(root).free - len(chunk) >= a['reserve'], 'Free space reserve reached'
            f.write(chunk)
            digest.update(chunk)
            count += len(chunk)
        f.flush()
        os.fsync(f.fileno())
    out({'sha256': digest.hexdigest(), 'size': count})
elif op == 'commit':
    p = path(a['pending'])
    info = check(p, True)
    assert info == a['expected'], 'Archive checksum/size mismatch'
    target = path(a['path'])
    assert not target.exists(), 'Archive already exists'
    atomic(path(a['path']+'.receipt.json'), json.dumps(info).encode())
    os.replace(str(p), str(target))
    d = os.open(str(target.parent), os.O_DIRECTORY)
    try:
        os.fsync(d)
    finally:
        os.close(d)
    out(info)
elif op == 'existing':
    p = path(a['path'])
    receipt = path(a['path']+'.receipt.json')
    if not p.exists():
        out(None)
    else:
        assert receipt.is_file(), 'Unrecorded archive without receipt; inspect manually'
        info = json.loads(receipt.read_text())
        assert check(p, True) == info, 'Recovered archive damaged'
        out(info)
elif op == 'download':
    with path(a['path']).open('rb') as f:
        shutil.copyfileobj(f, sys.stdout.buffer, 1024*1024)
elif op == 'verify':
    out(check(path(a['path']), a.get('archive', False)))
elif op == 'remove-pending':
    p = path(a['path'])
    assert p.name.endswith('.part'), 'Only pending files can be removed'
    p.unlink(missing_ok=True)
    out(True)
elif op == 'protect':
    p = path(a['id']+'/.protected')
    if a['value']:
        atomic(p, b'protected\n')
    else:
        p.unlink(missing_ok=True)
    out(True)
elif op == 'delete':
    entry = next(e for e in entries() if e['id'] == a['id'])
    assert not entry['protected'], 'Backup is protected'
    shutil.rmtree(path(entry['id']))
    out(True)
elif op == 'prune':
    keep = a['keep']
    assert keep >= 1
    complete = [e for e in entries() if e['status'] == 'complete'
                and json.loads(path(e['id']+'/manifest.json').read_text()).get('kind') == 'full']
    victims = [e['id'] for e in complete[keep:] if not e['protected']]
    if a.get('apply'):
        for name in victims:
            shutil.rmtree(path(name))
    out(victims)
else:
    raise ValueError('Unknown receiver command')
'''


def run(argv, **kwargs):
    result = subprocess.run(argv, capture_output=True, timeout=TIMEOUT, **kwargs)
    if result.returncode:
        error = result.stderr.decode('utf-8', 'replace').strip()
        raise RuntimeError(f'{Path(argv[0]).name} failed ({result.returncode}): {error}')
    return result.stdout.decode('utf-8', 'strict')


def prov(*args):
    return run([BIN+'zmprov', *args])


def attributes(text):
    """Parse zmprov output, retaining repeated attributes and multiline Sieve."""
    result = {}
    key = None
    for line in text.splitlines():
        if line.startswith('#') and key is None:
            continue
        match = re.match(r'^([A-Za-z][A-Za-z0-9]*): ?(.*)$', line)
        if match:
            key = match[1]
            result.setdefault(key, []).append(match[2])
        elif key:
            result[key][-1] += '\n'+line
    return result


def account_name(value):
    if not re.fullmatch(r'[^\s/@\\\x00-\x1f]+@[^\s/@\\\x00-\x1f]+', value):
        raise ValueError('Invalid account: '+value)
    if value.startswith('-') or '..' in value:
        raise ValueError('Unsafe account name')
    return value


class Store:
    def __init__(self):
        self.lease = None

    def command(self, op, **args):
        args.update(op=op, root=ROOT, source=EXPECTED_SOURCE)
        payload = base64.b64encode(json.dumps(args).encode()).decode()
        command = f'python3 -c {shlex.quote(REMOTE)} {shlex.quote(payload)}'
        return ['ssh', '-T', '-i', KEY, '-o', 'BatchMode=yes', '-o', 'IdentitiesOnly=yes',
                '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=15',
                '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=3',
                '-o', 'Compression=no', HOST, command]

    def request(self, op, data=None, raw=False, **args):
        self.alive()
        value = run(self.command(op, **args), input=data)
        return value if raw else json.loads(value)

    def alive(self):
        if self.lease and self.lease.poll() is not None:
            raise RuntimeError('Storage lock connection lost. Operation stopped.')

    def __enter__(self):
        self.lease = subprocess.Popen(self.command('lease'), stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if self.lease.stdout.readline().strip() != b'{"locked": true}':
            self.lease.stdin.close()
            error = self.lease.stderr.read()
            self.lease.wait(timeout=30)
            raise RuntimeError('Cannot lock storage: '+error.decode('utf-8', 'replace'))
        return self

    def __exit__(self, *exc):
        self.lease.stdin.close()
        try:
            self.lease.wait(timeout=20)
        except subprocess.TimeoutExpired:
            self.lease.kill()
            self.lease.wait()

    def put_json(self, path, value):
        return self.request('put', path=path,
                            data=json.dumps(value, ensure_ascii=False, indent=2).encode())

    def export(self, account, destination):
        pending = destination+'.'+secrets.token_hex(6)+'.part'
        start = time.monotonic()
        with tempfile.TemporaryFile() as errors:
            exporter = subprocess.Popen([BIN+'zmmailbox', '-z', '-m', account,
                                         '-t', '0', 'getRestURL', '/?fmt=tgz'],
                                        stdout=subprocess.PIPE, stderr=errors)
            receiver = subprocess.Popen(self.command('receive', path=pending, reserve=RESERVE),
                                        stdin=exporter.stdout, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
            exporter.stdout.close()
            try:
                reply, error = receiver.communicate(timeout=TIMEOUT)
                export_code = exporter.wait(timeout=30)
                self.alive()
                if receiver.returncode or export_code:
                    errors.seek(0)
                    raise RuntimeError('Export {} / SSH {}: {} {}'.format(
                        export_code, receiver.returncode, errors.read().decode('utf-8', 'replace'),
                        error.decode('utf-8', 'replace')))
                expected = json.loads(reply)
                if expected['size'] == 0:
                    raise RuntimeError('Empty export')
                info = self.request('commit', pending=pending, path=destination, expected=expected)
                info['seconds'] = round(time.monotonic()-start, 2)
                return info
            finally:
                for process in (exporter, receiver):
                    if process.poll() is None:
                        process.kill()
                    process.wait()
                try:
                    self.request('remove-pending', path=pending)
                except Exception:
                    pass


def confirm(text):
    answer = input(text + "\nConfirm [yes/NO]: ").strip().casefold()
    if answer not in ("yes", "y", "\u0434\u0430"):
        raise RuntimeError("Operation cancelled")



def choose(prompt, values):
    if not values:
        raise RuntimeError('Список пуст')
    print(prompt)
    for index, value in enumerate(values, 1):
        print(f'  {index}. {value}')
    number = input('Номер (Enter — отмена): ').strip()
    if not number.isdigit() or not 1 <= int(number) <= len(values):
        raise RuntimeError('Операция отменена')
    return values[int(number)-1]


def send_report(subject, body):
    if not MAIL_TO:
        return
    from email.message import EmailMessage
    msg = EmailMessage()
    msg['To'] = MAIL_TO
    msg['Subject'] = subject
    msg.set_content(body)
    try:
        subprocess.run(['/opt/zimbra/common/sbin/sendmail', '-t'],
                       input=msg.as_bytes(), check=True, timeout=30)
    except Exception as error:
        print('Ошибка отправки отчёта: '+str(error), file=sys.stderr)


def build_backup_report(manifest, deleted):
    ident = manifest['id']
    kind = manifest['kind']
    backup_path = str(PurePosixPath(ROOT) / ident)
    files = manifest['files']
    total_bytes = sum(file['size'] for file in files.values())
    size = f'{total_bytes / 1024**3:.2f} GiB' if total_bytes >= 1024**3 else f'{total_bytes} B'
    started = dt.datetime.fromtimestamp(manifest['started']).astimezone()
    finished = dt.datetime.fromtimestamp(manifest['finished']).astimezone()
    duration = dt.timedelta(seconds=round(manifest['finished'] - manifest['started']))
    mailbox_count = sum(name.startswith('mailboxes/') for name in files)
    mode = {
        'full': 'Полная копия',
        'partial': 'Выбранные аккаунты',
    }[kind]
    if manifest['settings_only']:
        mode = 'Только настройки'

    subject = f'Zimbra backup OK {kind} {ident} {size} {backup_path}'
    body = '\n'.join([
        'Резервное копирование Zimbra завершено успешно.',
        f'Сервер: {manifest["host"]}',
        f'Тип копии: {mode}',
        f'ID: {ident}',
        f'Хранилище: {HOST.rsplit("@", 1)[-1]}:{backup_path}',
        f'Начало: {started.isoformat(sep=" ", timespec="seconds")}',
        f'Окончание: {finished.isoformat(sep=" ", timespec="seconds")}',
        f'Длительность: {duration}',
        f'Аккаунтов: {len(manifest["accounts"])}',
        f'Архивов почты: {mailbox_count}',
        f'Файлов: {len(files)}',
        f'Размер файлов: {total_bytes} байт',
        'Удалены старые копии: ' + (', '.join(deleted) if deleted else 'нет'),
    ])
    return subject, body


def backup(store, accounts=None, settings_only=False, resume=None):
    accounts_requested = bool(accounts)
    if resume:
        manifest = json.loads(store.request('read', path=resume+'/manifest.json', raw=True))
        if manifest['status'] == 'complete':
            raise RuntimeError('Копия уже завершена')
        if manifest['host'] != os.uname().nodename:
            raise RuntimeError('Копия создана другим сервером')
        ident = resume
        accounts = manifest['accounts']
        settings_only = manifest['settings_only']
    else:
        accounts = accounts or prov('-l', 'gaa').splitlines()
        accounts = [account_name(a.strip()) for a in accounts if a.strip()]
        if not accounts:
            raise RuntimeError('Нет аккаунтов для резервного копирования')
        ident = dt.datetime.now().strftime('%Y%m%dT%H%M%S-')+secrets.token_hex(4)
        manifest = dict(version=1, id=ident, host=os.uname().nodename,
                        started=time.time(), status='incomplete', accounts=accounts,
                        settings_only=settings_only, files={}, errors={},
                        kind='partial' if accounts_requested or settings_only else 'full')
        store.put_json(ident+'/manifest.json', manifest)
    print('BACKUP '+ident, flush=True)
    info = store.request('check')
    if info['free'] <= RESERVE:
        raise RuntimeError(f'Свободное место ниже резерва {RESERVE//1024**3} GiB')

    def save(name, value):
        content = json.dumps(value, ensure_ascii=False, indent=2).encode()
        relative = name
        store.request('put', path=ident+'/'+relative, data=content)
        manifest['files'][relative] = {'size': len(content), 'sha256': hashlib.sha256(content).hexdigest()}

    # Each resume preserves the metadata already captured for this run.
    if 'metadata.json' not in manifest['files']:
        domains = prov('gad').splitlines()
        groups = prov('gadl').splitlines()
        metadata = {'domains': domains, 'admins': prov('gaaa').splitlines(), 'groups': {}}
        for group in groups:
            metadata['groups'][group] = attributes(prov('gdl', group))
        save('metadata.json', metadata)
    for account in accounts:
        name = 'accounts/'+account+'.json'
        if name not in manifest['files']:
            save(name, attributes(prov('-l', 'ga', account)))
            store.put_json(ident+'/manifest.json', manifest)
    failures = {}

    def worker(account):
        relative = 'mailboxes/'+account+'.tgz'
        if relative in manifest['files']:
            expected = manifest['files'][relative]
            actual = store.request('verify', path=ident+'/'+relative)
            if all(actual[k] == expected[k] for k in ('size', 'sha256')):
                print('SKIP '+account, flush=True)
                return relative, expected
            raise RuntimeError('Изменён готовый архив '+account)
        for attempt in range(1, TRIES+1):
            try:
                existing = store.request('existing', path=ident+'/'+relative)
                if existing:
                    print('RECOVERED '+account, flush=True)
                    return relative, existing
                print(f'EXPORT {account} ({attempt}/{TRIES})', flush=True)
                result = store.export(account, ident+'/'+relative)
                print('DONE {} {:.1f} GiB / {} s'.format(account, result['size']/1024**3,
                                                       result['seconds']), flush=True)
                return relative, result
            except Exception:
                if attempt == TRIES:
                    raise
                time.sleep(5)

    if not settings_only:
        with concurrent.futures.ThreadPoolExecutor(max_workers=JOBS) as pool:
            tasks = {pool.submit(worker, account): account for account in accounts}
            for future in concurrent.futures.as_completed(tasks):
                account = tasks[future]
                try:
                    name, result = future.result()
                    manifest['files'][name] = result
                except Exception as error:
                    failures[account] = str(error)
                    print(f'ERROR {account}: {error}', file=sys.stderr, flush=True)
                manifest['errors'] = failures
                store.put_json(ident+'/manifest.json', manifest)
    manifest['errors'] = failures
    manifest['status'] = 'failed' if failures else 'complete'
    manifest['finished'] = time.time()
    store.put_json(ident+'/manifest.json', manifest)
    if failures:
        raise RuntimeError('Не завершена копия {}. Ошибки: {}. Продолжить: resume {}'.format(
            ident, ', '.join(failures), ident))
    deleted = store.request('prune', keep=KEEP, apply=True) if manifest['kind'] == 'full' else []
    print(f'Готово: {ident}. Удалены старые копии: {deleted}')
    send_report(*build_backup_report(manifest, deleted))
    return ident


class Snapshot:
    def __init__(self, store, ident):
        self.store, self.ident = store, ident
        self.entry = next(e for e in store.request('list') if e['id'] == ident)
        self.legacy = self.entry['status'] == 'legacy'
        self.manifest = None if self.legacy else json.loads(self.read('manifest.json', check=False))
        if self.legacy:
            self.accounts = self.read('users.txt').split()
        else:
            self.accounts = self.manifest['accounts']
        if self.entry['status'] not in ('complete', 'legacy'):
            confirm(f'Копия {ident} незавершена. Доступны только сохранённые компоненты.')

    def read(self, rel, check=True):
        text = self.store.request('read', path=self.ident+'/'+rel, raw=True)
        if check and self.manifest:
            expected = self.manifest['files'][rel]
            if hashlib.sha256(text.encode()).hexdigest() != expected['sha256']:
                raise RuntimeError('Несовпадение контрольной суммы '+rel)
        return text

    def attrs(self, account):
        if not self.legacy:
            return json.loads(self.read('accounts/'+account+'.json'))
        attrs = attributes(self.read('users_settings/'+account+'.txt'))
        attrs['zimbraMailSieveScript'] = [self.read('filters/'+account)]
        try:
            attrs['zimbraMailAlias'] = self.read('aliases/'+account+'.txt').split()
        except RuntimeError:
            attrs['zimbraMailAlias'] = []
        return attrs

    def metadata(self):
        if not self.legacy:
            return json.loads(self.read('metadata.json'))
        groups = {}
        for group in self.read('distribution_lists.txt').split():
            members = [line.strip() for line in self.read('distributions_lists/'+group+'.txt').splitlines()
                       if '@' in line and not line.startswith('#')]
            groups[group] = {'zimbraMailForwardingAddress': members}
        return {'domains': self.read('domains.txt').split(), 'groups': groups}

    @contextlib.contextmanager
    def archive(self, account):
        rel = 'mailboxes/'+account+'.tgz'
        expected = self.store.request('verify', path=self.ident+'/'+rel, archive=True)
        if self.manifest:
            recorded = self.manifest['files'][rel]
            if any(recorded[k] != expected[k] for k in ('size', 'sha256')):
                raise RuntimeError('Повреждён архив '+account)
        SPOOL.mkdir(parents=True, exist_ok=True, mode=0o700)
        if shutil.disk_usage(SPOOL).free < expected['size']+RESERVE:
            raise RuntimeError('Недостаточно места во временном каталоге '+str(SPOOL))
        with tempfile.TemporaryDirectory(prefix='restore-', dir=str(SPOOL)) as tmp:
            p = Path(tmp)/'mailbox.tgz'
            with p.open('wb') as output:
                result = subprocess.run(self.store.command('download', path=self.ident+'/'+rel),
                                        stdout=output, stderr=subprocess.PIPE, timeout=TIMEOUT)
            if result.returncode:
                raise RuntimeError('Ошибка скачивания: '+result.stderr.decode('utf-8', 'replace'))
            digest = hashlib.sha256()
            with p.open('rb') as source:
                for block in iter(lambda: source.read(1024*1024), b''):
                    digest.update(block)
            if p.stat().st_size != expected['size'] or digest.hexdigest() != expected['sha256']:
                raise RuntimeError('Повреждение при скачивании')
            yield str(p)


def ensure_account(account):
    account_name(account)
    result = subprocess.run([BIN+'zmprov', 'ga', account, 'zimbraId'],
                            capture_output=True, timeout=60)
    if result.returncode == 0:
        return
    if b'NO_SUCH_ACCOUNT' not in result.stderr:
        raise RuntimeError(result.stderr.decode('utf-8', 'replace'))
    confirm('Создать аккаунт '+account+'?')
    password = getpass.getpass('Пароль нового аккаунта (Enter — случайный): ')
    if not password:
        password = secrets.token_urlsafe(24)
        print('Пароль нового аккаунта: '+password)
    prov('ca', account, password)


def apply_account(destination, attrs, parts, same_account):
    ensure_account(destination)
    if 'settings' in parts:
        print('Переносятся имя, контакты, квота, переадресация и выбранные предпочтения.')
        argv = []
        for key in sorted(SAFE_SETTINGS.intersection(attrs)):
            values = attrs[key]
            argv.extend([key, values[0]])
        if argv:
            prov('ma', destination, *argv)
        for key in sorted(SAFE_SETTINGS.intersection(attrs)):
            for value in attrs[key][1:]:
                prov('ma', destination, '+'+key, value)
    if 'filters' in parts:
        prov('ma', destination, 'zimbraMailSieveScript',
             attrs.get('zimbraMailSieveScript', [''])[0])
    if 'aliases' in parts:
        current = attributes(prov('ga', destination, 'zimbraMailAlias')).get('zimbraMailAlias', [])
        for alias in attrs.get('zimbraMailAlias', []):
            if alias in current:
                continue
            prov('aaa', destination, alias)
    if same_account and 'settings' in parts and attrs.get('userPassword'):
        if input('Восстановить сохранённый хеш пароля? [да/НЕТ]: ').lower() == 'да':
            prov('ma', destination, 'userPassword', attrs['userPassword'][0])


def select_snapshot(store):
    entries = store.request('list')
    labels = ['{} [{}]{}'.format(e['id'], e['status'], ' protected' if e['protected'] else '')
              for e in entries]
    return entries[labels.index(choose('Резервная копия', labels))]['id']


def restore_account(snapshot, source, destination=None, parts=None):
    destination = account_name(destination or source)
    parts = parts or choose_parts()
    if source != destination and 'aliases' in parts:
        raise RuntimeError('Для переноса алиасов на другой аккаунт сначала измените их владельца вручную')
    attrs = snapshot.attrs(source)
    confirm('Восстановление {} / {} -> {}. Компоненты: {}'.format(
        snapshot.ident, source, destination, ', '.join(parts)))
    # Download/validate before mutating the target when data is included.
    with contextlib.ExitStack() as stack:
        archive = stack.enter_context(snapshot.archive(source)) if 'data' in parts else None
        apply_account(destination, attrs, parts, source == destination)
        if archive:
            run([BIN+'zmmailbox', '-z', '-m', destination, '-t', '0',
                 'postRestURL', '/?fmt=tgz&resolve=skip', archive])


def choose_parts():
    label = choose('Компоненты', ['Всё', 'Данные', 'Настройки', 'Алиасы', 'Фильтры', 'Настройки и фильтры'])
    return {'Всё': ['settings', 'aliases', 'filters', 'data'], 'Данные': ['data'],
            'Настройки': ['settings'], 'Алиасы': ['aliases'], 'Фильтры': ['filters'],
            'Настройки и фильтры': ['settings', 'filters']}[label]


def restore_domains(metadata):
    for domain in metadata['domains']:
        result = subprocess.run([BIN+'zmprov', 'gd', domain], capture_output=True,
                                timeout=60)
        if result.returncode:
            if b'NO_SUCH_DOMAIN' not in result.stderr:
                raise RuntimeError(result.stderr.decode('utf-8', 'replace'))
            prov('cd', domain, 'zimbraAuthMech', 'zimbra')
        print('DOMAIN '+domain)


def restore_groups(metadata, names):
    for group in names:
        result = subprocess.run([BIN+'zmprov', 'gdl', group], capture_output=True,
                                timeout=60)
        if result.returncode:
            if b'NO_SUCH_DISTRIBUTION_LIST' not in result.stderr:
                raise RuntimeError(result.stderr.decode('utf-8', 'replace'))
            prov('cdl', group)
        existing = attributes(prov('gdl', group)).get('zimbraMailForwardingAddress', [])
        for member in metadata['groups'][group].get('zimbraMailForwardingAddress', []):
            if member not in existing:
                prov('adlm', group, member)
        print('GROUP '+group)


def menu(store):
    while True:
        action = choose('Zimbra Tool', ['Бэкап', 'Восстановить ящик', 'Восстановить все аккаунты',
                                       'Домены', 'Рассылки', 'Копировать действующий ящик',
                                       'Проверить копию', 'Защитить копию от очистки',
                                       'Очистить старые копии', 'Удалить выбранную копию', 'Выход'])
        if action == 'Выход':
            return
        if action == 'Бэкап':
            backup(store)
            continue
        if action == 'Копировать действующий ящик':
            source = account_name(input('Исходный адрес: ').strip())
            destination = account_name(input('Целевой адрес: ').strip())
            if source == destination:
                raise RuntimeError('Источник совпадает с назначением')
            parts = choose_parts()
            if 'aliases' in parts:
                parts.remove('aliases')
                print('Алиасы принадлежат исходному аккаунту. Копируются остальные компоненты.')
            confirm('Копирование {} -> {}: {}'.format(source, destination, ', '.join(parts)))
            ident = backup(store, [source], settings_only='data' not in parts)
            snapshot = Snapshot(store, ident)
            restore_account(snapshot, source, destination, parts)
            continue
        if action == 'Очистить старые копии':
            victims = store.request('prune', keep=KEEP, apply=False)
            print('К удалению: '+str(victims))
            confirm('Удалить перечисленные копии?')
            store.request('prune', keep=KEEP, apply=True)
            continue
        ident = select_snapshot(store)
        if action == 'Удалить выбранную копию':
            confirm('Удалить целиком резервную копию '+ident+'?')
            store.request('delete', id=ident)
            continue
        if action == 'Защитить копию от очистки':
            value = input('Защитить? [ДА/нет]: ').strip().lower() != 'нет'
            store.request('protect', id=ident, value=value)
            continue
        snapshot = Snapshot(store, ident)
        if action == 'Восстановить ящик':
            source = choose('Аккаунт', snapshot.accounts)
            target = input('Адрес назначения (Enter — исходный): ').strip() or source
            restore_account(snapshot, source, target)
        elif action == 'Восстановить все аккаунты':
            confirm('Восстановить все аккаунты из '+ident+'?')
            restore_domains(snapshot.metadata())
            parts = ['settings', 'filters', 'aliases']
            if not snapshot.manifest or not snapshot.manifest['settings_only']:
                parts.append('data')
            for account in snapshot.accounts:
                restore_account(snapshot, account, parts=parts)
            restore_groups(snapshot.metadata(), snapshot.metadata()['groups'])
        elif action == 'Домены':
            confirm('Создать отсутствующие домены из '+ident+'?')
            restore_domains(snapshot.metadata())
        elif action == 'Рассылки':
            metadata = snapshot.metadata()
            names = list(metadata['groups'])
            selection = choose('Группы', ['Все']+names)
            confirm('Восстановить участников групп? '+selection)
            restore_groups(metadata, names if selection == 'Все' else [selection])
        elif action == 'Проверить копию':
            if snapshot.manifest:
                for name, expected in snapshot.manifest['files'].items():
                    actual = store.request('verify', path=ident+'/'+name, archive=name.endswith('.tgz'))
                    if any(actual[k] != expected[k] for k in ('size', 'sha256')):
                        raise RuntimeError('Повреждён '+name)
                    print('OK '+name)
            else:
                for account in snapshot.accounts:
                    store.request('verify', path=ident+'/mailboxes/'+account+'.tgz', archive=True)
                    print('Архив читается: '+account+' (исторической контрольной суммы нет)')


def purge(confirmed=False):
    if not confirmed:
        confirm('Очистить Dumpster ВСЕХ аккаунтов? Восстановление удалённых элементов из Dumpster станет недоступно.')
    failures = []
    for account in prov('-l', 'gaa').splitlines():
        try:
            run([BIN+'zmmailbox', '-z', '-m', account_name(account), '-A', 'emptyDumpster'])
            print('PURGED '+account)
        except Exception as error:
            failures.append(account)
            print(str(error), file=sys.stderr)
    if failures:
        raise RuntimeError('Dumpster failures: '+', '.join(failures))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', nargs='?', default='menu',
                        choices=['menu', 'check', 'list', 'backup', 'scheduled', 'resume', 'prune', 'purge'])
    parser.add_argument('backup_id', nargs='?')
    parser.add_argument('--account', action='append', help='Repeat for selected accounts')
    parser.add_argument('--settings-only', action='store_true')
    parser.add_argument('--yes-purge', action='store_true', help='Allow scheduled Dumpster cleanup')
    parser.add_argument('--new', action='store_true', help='Start another full backup today')
    args = parser.parse_args()
    if JOBS < 1 or KEEP < 1 or TRIES < 1 or RESERVE < 0 or TIMEOUT < 1:
        parser.error('Invalid numeric configuration')
    if getpass.getuser() != 'zimbra':
        raise RuntimeError('Запускайте от zimbra: su - zimbra -c "python3 /opt/zimbra/zimbra-tool.py ..."')
    import fcntl
    os.umask(0o077)
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (STATE/'local.lock').open('a+') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            if args.command == 'scheduled':
                print('Другая операция ещё выполняется. Следующая проверка по расписанию.')
                return
            raise
        if args.command == 'purge':
            purge(args.yes_purge)
            return
        with Store() as store:
            if args.command in ('backup', 'scheduled', 'resume'):
                if args.command == 'resume' and not args.backup_id:
                    parser.error('resume requires backup_id')
                resume_id = args.backup_id if args.command == 'resume' else None
                if args.command == 'scheduled':
                    now = dt.datetime.now()
                    due = now.replace(hour=18, minute=0, second=0, microsecond=0)
                    if now < due:
                        due -= dt.timedelta(days=1)
                    for entry in store.request('list'):
                        if entry['status'] == 'legacy' or entry['started'] < due.timestamp():
                            continue
                        old = json.loads(store.request('read', path=entry['id']+'/manifest.json', raw=True))
                        if old.get('kind') != 'full':
                            continue
                        if entry['status'] == 'complete':
                            print('Плановая копия уже готова: '+entry['id'])
                            return
                        resume_id = entry['id']
                        break
                if args.command == 'backup' and not args.account and not args.settings_only and not args.new:
                    today = dt.datetime.now().strftime('%Y%m%d')
                    for entry in store.request('list'):
                        if not entry['id'].startswith(today) or entry['status'] == 'legacy':
                            continue
                        old = json.loads(store.request('read', path=entry['id']+'/manifest.json', raw=True))
                        if old.get('kind') != 'full':
                            continue
                        if entry['status'] == 'complete':
                            print('Сегодняшняя полная копия уже готова: '+entry['id'])
                            return
                        resume_id = entry['id']
                        break
                backup(store, args.account, args.settings_only,
                       resume_id)
            elif args.command in ('check', 'list'):
                print(json.dumps(store.request(args.command), ensure_ascii=False, indent=2))
            elif args.command == 'prune':
                print('К удалению: '+str(store.request('prune', keep=KEEP, apply=False)))
                confirm('Применить очистку?')
                store.request('prune', keep=KEEP, apply=True)
            else:
                menu(store)


if __name__ == '__main__':
    try:
        main()
    except (Exception, KeyboardInterrupt) as error:
        message = f'{type(error).__name__}: {error}'
        print(message, file=sys.stderr)
        if len(sys.argv) > 1 and sys.argv[1] in ('backup', 'scheduled', 'resume'):
            send_report('Zimbra backup FAILED', '\n'.join([
                'Ошибка при выполнении резервного копирования Zimbra.',
                f'Сервер: {os.uname().nodename}',
                f'Команда: {sys.argv[1]}',
                f'Время: {dt.datetime.now().astimezone().isoformat(sep=" ", timespec="seconds")}',
                f'Причина: {message}',
            ]))
        sys.exit(1)
