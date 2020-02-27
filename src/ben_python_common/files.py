# BenPythonCommon,
# 2015 Ben Fisher, released under the GPLv3 license.

import sys
import os as _os
import shutil as _shutil
from .common_util import *

rename = _os.rename
delete = _os.unlink
exists = _os.path.exists
join = _os.path.join
split = _os.path.split
splitext = _os.path.splitext
isdir = _os.path.isdir
isfile = _os.path.isfile
getsize = _os.path.getsize
rmdir = _os.rmdir
chdir = _os.chdir
sep = _os.path.sep
linesep = _os.linesep
abspath = _os.path.abspath
rmtree = _shutil.rmtree

# simple wrappers
def getparent(s):
    return _os.path.split(s)[0]
    
def getname(s):
    return _os.path.split(s)[1]
    
def modtime(s):
    return _os.stat(s).st_mtime
    
def createdtime(s):
    return _os.stat(s).st_ctime
    
def getext(s):
    a, b = splitext(s)
    if len(b) > 0 and b[0] == '.':
        return b[1:].lower()
    else:
        return b.lower()
    
def deletesure(s):
    if exists(s):
        delete(s)
    assert not exists(s)
    
def makedirs(s):
    try:
        _os.makedirs(s)
    except OSError:
        if isdir(s):
            return
        else:
            raise

def ensure_empty_directory(d):
    if isfile(d):
        raise IOError('file exists at this location ' + d)
    
    if isdir(d):
        # delete all existing files in the directory
        for s in _os.listdir(d):
            if _os.path.isdir(join(d, s)):
                _shutil.rmtree(join(d, s))
            else:
                _os.unlink(join(d, s))
        
        assertTrue(isemptydir(d))
    else:
        _os.makedirs(d)

def copy(srcfile, destfile, overwrite, traceToStdout=False):
    if not isfile(srcfile):
        raise IOError('source path does not exist or is not a file')

    if traceToStdout:
        trace('copy()', srcfile, destfile)

    if srcfile == destfile:
        pass
    elif sys.platform.startswith('win'):
        from ctypes import windll, c_wchar_p, c_int, GetLastError
        failIfExists = c_int(0) if overwrite else c_int(1)
        res = windll.kernel32.CopyFileW(c_wchar_p(srcfile), c_wchar_p(destfile), failIfExists)
        if not res:
            err = GetLastError()
            raise IOError('CopyFileW failed (maybe dest already exists?) err=%d' % err +
                getPrintable(srcfile + '->' + destfile))
    else:
        if overwrite:
            _shutil.copy(srcfile, destfile)
        else:
            copyFilePosixWithoutOverwrite(srcfile, destfile)

    assertTrue(exists(destfile))
        
def move(srcfile, destfile, overwrite, warn_between_drives=False,
    traceToStdout=False, allowDirs=False):
    if not exists(srcfile):
        raise IOError('source path does not exist')
    if not allowDirs and not isfile(srcfile):
        raise IOError('source path does not exist or is not a file')

    if traceToStdout:
        trace('move()', srcfile, destfile)

    if srcfile == destfile:
        pass
    elif sys.platform.startswith('win'):
        from ctypes import windll, c_wchar_p, c_int, GetLastError
        ERROR_NOT_SAME_DEVICE = 17
        flags = 0
        flags |= 1 if overwrite else 0
        flags |= 0 if warn_between_drives else 2
        res = windll.kernel32.MoveFileExW(c_wchar_p(srcfile), c_wchar_p(destfile), c_int(flags))
        if not res:
            err = GetLastError()
            if err == ERROR_NOT_SAME_DEVICE and warn_between_drives:
                rinput('Note: moving file from one drive to another. ' +
                    '%s %s Press Enter to continue.\r\n'%(srcfile, destfile))
                return move(srcfile, destfile, overwrite, warn_between_drives=False)
                
            raise IOError('MoveFileExW failed (maybe dest already exists?) err=%d' % err +
                getPrintable(srcfile + '->' + destfile))
        
    elif sys.platform.startswith('linux') and overwrite:
        _os.rename(srcfile, destfile)
    else:
        copy(srcfile, destfile, overwrite)
        _os.unlink(srcfile)
    
    assertTrue(exists(destfile))
    
def copyFilePosixWithoutOverwrite(srcfile, destfile):
    # fails if destination already exist. O_EXCL prevents other files from writing to location.
    # raises OSError on failure.
    flags = _os.O_CREAT | _os.O_EXCL | _os.O_WRONLY
    file_handle = _os.open(destfile, flags)
    with _os.fdopen(file_handle, 'wb') as fdest:
        with open(srcfile, 'rb') as fsrc:
            while True:
                buffer = fsrc.read(64 * 1024)
                if not buffer:
                    break
                fdest.write(buffer)

def getModTimeNs(path):
    return _os.stat(path).st_mtime_ns

def getCTimeNs(path):
    return _os.stat(path).st_ctime_ns

def getATimeNs(path):
    return _os.stat(path).st_atime_ns

def setModTimeNs(path, mtime):
    atime = getATimeNs(path)
    _os.utime(path, ns=(atime, mtime))

def setATimeNs(path, atime):
    mtime = getModTimeNs(path)
    _os.utime(path, ns=(atime, mtime))

def getFileLastModifiedTime(filepath):
    return _os.path.getmtime(filepath)

def setFileLastModifiedTime(filepath, lmt):
    curtimes = _os.stat(filepath)
    newtimes = (curtimes.st_atime, lmt)
    with open(filepath, 'ab'):
        _os.utime(filepath, newtimes)

# unicodetype can be utf-8, utf-8-sig, etc.
def readall(s, mode='r', unicodetype=None, encoding=None):
    if encoding:
        # python 3-style
        getF = lambda: open(s, mode, encoding=encoding)
    elif unicodetype:
        # python 2-style
        import codecs
        getF = lambda: codecs.open(s, mode, encoding=unicodetype)
    else:
        getF = lambda: open(s, mode)

    with getF() as f:
        txt = f.read()

    return txt

# unicodetype can be utf-8, utf-8-sig, etc.
def writeall(s, txt, mode='w', unicodetype=None, encoding=None):
    if encoding:
        # python 3-style
        getF = lambda: open(s, mode, encoding=encoding)
    elif unicodetype:
        # python 2-style
        import codecs
        getF = lambda: codecs.open(s, mode, encoding=unicodetype)
    else:
        getF = lambda: open(s, mode)

    with getF() as f:
        f.write(txt)

def writeallunlessalreadythere(path, txt, mode='w', encoding='utf-8'):
    ret = False
    if mode == 'wb':
        current = readall(path, 'rb') if exists(path) else False
        if current != txt:
            writeall(path, txt, 'wb')
            ret = True
    elif mode == 'w':
        assertTrue(isPy3OrNewer)
        current = readall(path, 'r', encoding=encoding) if \
            exists(path) else False
        if current != txt:
            writeall(path, txt, 'w', encoding=encoding)
            ret = True
    else:
        raise ValueError('please use a mode of "w" or "wb"')
    return ret


_enforceExplicitlyNamedParameters = object()
# use this to make the caller pass argument names,
# allowing foo(param=False) but preventing foo(False)

def _checkNamedParameters(obj):
    if obj is not _enforceExplicitlyNamedParameters:
        raise ValueError('please name parameters for this function or method')

# allowedexts in the form ['png', 'gif']
def listchildrenUnsorted(dir, _ind=_enforceExplicitlyNamedParameters, filenamesOnly=False, allowedexts=None):
    _checkNamedParameters(_ind)
    for filename in _os.listdir(dir):
        if not allowedexts or getext(filename) in allowedexts:
            yield filename if filenamesOnly else (dir + _os.path.sep + filename, filename)


if sys.platform.startswith('win'):
    listchildren = listchildrenUnsorted
else:
    def listchildren(*args, **kwargs):
        return sorted(listchildrenUnsorted(*args, **kwargs))

def listdirs(dir, _ind=_enforceExplicitlyNamedParameters, filenamesOnly=False, allowedexts=None):
    _checkNamedParameters(_ind)
    for full, name in listchildren(dir, allowedexts=allowedexts):
        if _os.path.isdir(full):
            yield name if filenamesOnly else (full, name)

def listfiles(dir, _ind=_enforceExplicitlyNamedParameters, filenamesOnly=False, allowedexts=None):
    _checkNamedParameters(_ind)
    for full, name in listchildren(dir, allowedexts=allowedexts):
        if not _os.path.isdir(full):
            yield name if filenamesOnly else (full, name)

def recursefiles(root, _ind=_enforceExplicitlyNamedParameters, filenamesOnly=False, allowedexts=None,
        fnFilterDirs=None, includeFiles=True, includeDirs=False, topdown=True):
    _checkNamedParameters(_ind)
    assert isdir(root)
    
    for (dirpath, dirnames, filenames) in _os.walk(root, topdown=topdown):
        if fnFilterDirs:
            newdirs = [dir for dir in dirnames if fnFilterDirs(join(dirpath, dir))]
            dirnames[:] = newdirs
        
        if includeFiles:
            for filename in (filenames if sys.platform.startswith('win') else sorted(filenames)):
                if not allowedexts or getext(filename) in allowedexts:
                    yield filename if filenamesOnly else (dirpath + _os.path.sep + filename, filename)
        
        if includeDirs:
            yield getname(dirpath) if filenamesOnly else (dirpath, getname(dirpath))
    
def recursedirs(root, _ind=_enforceExplicitlyNamedParameters, filenamesOnly=False, fnFilterDirs=None, topdown=True):
    _checkNamedParameters(_ind)
    return recursefiles(root, filenamesOnly=filenamesOnly, fnFilterDirs=fnFilterDirs, includeFiles=False, includeDirs=True, topdown=topdown)

class FileInfoEntryWrapper(object):
    def __init__(self, obj):
        self.obj = obj
        self.path = obj.path
        
    def is_dir(self, *args):
        return self.obj.is_dir(*args)
        
    def is_file(self, *args):
        return self.obj.is_file(*args)
        
    def short(self):
        return _os.path.split(self.path)[1]
        
    def size(self):
        return self.obj.stat().st_size
        
    def mtime(self):
        return self.obj.stat().st_mtime
    
    def metadatachangetime(self):
        assertTrue(not sys.platform.startswith('win'))
        return self.obj.stat().st_ctime
    
    def createtime(self):
        assertTrue(sys.platform.startswith('win'))
        return self.obj.stat().st_ctime

def recursefileinfo(root, recurse=True, followSymlinks=False, filesOnly=True):
    assertTrue(isPy3OrNewer)
    
    # scandir's resources are released in destructor,
    # do not create circular references holding it
    for entry in _os.scandir(root):
        if entry.is_dir(follow_symlinks=followSymlinks):
            if not filesOnly:
                yield FileInfoEntryWrapper(entry)
            if recurse:
                for subentry in recursefileinfo(entry.path, recurse=recurse,
                        followSymlinks=followSymlinks, filesOnly=filesOnly):
                    yield subentry
        
        if entry.is_file():
            yield FileInfoEntryWrapper(entry)

def listfileinfo(root, followSymlinks=False, filesOnly=True):
    return recursefileinfo(root, recurse=False,
        followSymlinks=followSymlinks, filesOnly=filesOnly)

def isemptydir(dir):
    return len(_os.listdir(dir)) == 0
    
def fileContentsEqual(f1, f2):
    import filecmp
    return filecmp.cmp(f1, f2, shallow=False)

# processes
def openDirectoryInExplorer(dir):
    assert isdir(dir), 'not a dir? ' + dir
    if sys.platform.startswith('win'):
        assert '^' not in dir and '"' not in dir, 'dir cannot contain ^ or "'
        runWithoutWaitUnicode([u'cmd', u'/c', u'start', u'explorer.exe', dir])
    else:
        for candidate in ['xdg-open', 'nautilus']:
            path = findBinaryOnPath(candidate)
            if path:
                args = [path, dir]
                run(args, shell=False, createNoWindow=False, throwOnFailure=False, captureoutput=False, wait=False)
                return
        raise RuntimeError('unable to open directory.')

def openUrl(s):
    import webbrowser
    if s.startswith('http://'):
        prefix = 'http://'
    elif s.startswith('https://'):
        prefix = 'https://'
    else:
        assertTrue(False, 'url did not start with http')
    
    s = s[len(prefix):]
    s = s.replace('%', '%25')
    s = s.replace('&', '%26')
    s = s.replace('|', '%7C')
    s = s.replace('\\', '%5C')
    s = s.replace('^', '%5E')
    s = s.replace('"', '%22')
    s = s.replace("'", '%27')
    s = s.replace('>', '%3E')
    s = s.replace('<', '%3C')
    s = s.replace(' ', '%20')
    s = prefix + s
    webbrowser.open(s, new=2)


exeExt = {'.action': 1, '.apk': 1, '.app': 1, '.bat': 1, '.bin': 1, '.cmd': 1, '.com': 1,
    '.command': 1, '.cpl': 1, '.csh': 1, '.exe': 1, '.gadget': 1, '.inf1': 1, '.ins': 1, '.inx': 1,
    '.ipa': 1, '.isu': 1, '.job': 1, '.jse': 1, '.ksh': 1, '.lnk': 1, '.msc': 1, '.msi': 1,
    '.msp': 1, '.mst': 1, '.osx': 1, '.out': 1, '.paf': 1, '.pif': 1, '.prg': 1, '.ps1': 1,
    '.reg': 1, '.rgs': 1, '.run': 1, '.scr': 1, '.sct': 1, '.shb': 1, '.shs': 1, '.u3p': 1,
    '.vb': 1, '.vbe': 1, '.vbs': 1, '.vbscript': 1, '.workflow': 1, '.ws': 1, '.wsf': 1, '.wsh': 1}

warnExt = {'.0xe': 1, '.73k': 1, '.89k': 1, '.a6p': 1, '.ac': 1, '.acc': 1, '.acr': 1, '.actm': 1,
    '.ahk': 1, '.air': 1, '.app': 1, '.arscript': 1, '.as': 1, '.asb': 1, '.awk': 1, '.azw2': 1,
    '.beam': 1, '.btm': 1, '.cel': 1, '.celx': 1, '.chm': 1, '.cof': 1, '.crt': 1, '.dek': 1,
    '.dld': 1, '.dmc': 1, '.docm': 1, '.dotm': 1, '.dxl': 1, '.ear': 1, '.ebm': 1, '.ebs': 1,
    '.ebs2': 1, '.ecf': 1, '.eham': 1, '.elf': 1, '.es': 1, '.ex4': 1, '.exopc': 1, '.ezs': 1,
    '.fas': 1, '.fky': 1, '.fpi': 1, '.frs': 1, '.fxp': 1, '.gs': 1, '.ham': 1, '.hms': 1,
    '.hpf': 1, '.hta': 1, '.iim': 1, '.ipf': 1, '.isp': 1, '.jar': 1, '.js': 1, '.jsx': 1,
    '.kix': 1, '.lo': 1, '.ls': 1, '.mam': 1, '.mcr': 1, '.mel': 1, '.mpx': 1, '.mrc': 1,
    '.ms': 1, '.ms': 1, '.mxe': 1, '.nexe': 1, '.obs': 1, '.ore': 1, '.otm': 1, '.pex': 1,
    '.plx': 1, '.potm': 1, '.ppam': 1, '.ppsm': 1, '.pptm': 1, '.prc': 1, '.pvd': 1, '.pwc': 1,
    '.pyc': 1, '.pyo': 1, '.qpx': 1, '.rbx': 1, '.rox': 1, '.rpj': 1, '.s2a': 1, '.sbs': 1,
    '.sca': 1, '.scar': 1, '.scb': 1, '.script': 1, '.smm': 1, '.spr': 1, '.tcp': 1, '.thm': 1,
    '.tlb': 1, '.tms': 1, '.udf': 1, '.upx': 1, '.url': 1, '.vlx': 1, '.vpm': 1, '.wcm': 1,
    '.widget': 1, '.wiz': 1, '.wpk': 1, '.wpm': 1, '.xap': 1, '.xbap': 1, '.xlam': 1, '.xlm': 1,
    '.xlsm': 1, '.xltm': 1, '.xqt': 1, '.xys': 1, '.zl9': 1}

def extensionPossiblyExecutable(s):
    '''Returns 'exe' if it looks executable,
    Returns 'warn' if it is a document type that can include embedded scripts,
    Returns False otherwise'''
    _, ext = _os.path.splitext(s)
    ext = ext.lower()
    if ext in exeExt:
        return 'exe'
    elif ext in warnExt:
        return 'warn'
    else:
        return False

def findBinaryOnPath(binaryName):
    def is_exe(fpath):
        return _os.path.isfile(fpath) and _os.access(fpath, _os.X_OK)

    if _os.sep in binaryName:
        return binaryName if is_exe(binaryName) else None

    if sys.platform.startswith('win') and not binaryName.lower().endswith('.exe'):
        binaryName += '.exe'

    for path in _os.environ["PATH"].split(_os.pathsep):
        path = path.strip('"')
        exe_file = _os.path.join(path, binaryName)
        if is_exe(exe_file):
            return exe_file

    return None

def hasherFromString(s):
    import hashlib
    if s == 'sha1':
        return hashlib.sha1()
    elif s == 'sha224':
        return hashlib.sha224()
    elif s == 'sha256':
        return hashlib.sha256()
    elif s == 'sha384':
        return hashlib.sha384()
    elif s == 'sha512':
        return hashlib.sha512()
    elif s == 'blake2b':
        return hashlib.blake2b()
    elif s == 'blake2s':
        return hashlib.blake2s()
    elif s == 'md5':
        return hashlib.md5()
    elif s == 'sha3_224':
        return hashlib.sha3_224()
    elif s == 'sha3_256':
        return hashlib.sha3_256()
    elif s == 'sha3_384':
        return hashlib.sha3_384()
    elif s == 'sha3_512':
        return hashlib.sha3_512()
    elif s == 'shake_128':
        return hashlib.shake_128()
    elif s == 'shake_256':
        return hashlib.shake_256()
    else:
        return None

def computeHash(path, hasher='sha1', buffersize=0x40000):
    if hasher == 'crc32':
        import zlib
        crc = zlib.crc32(bytes(), 0)
        with open(path, 'rb') as f:
            while True:
                # update the hash with the contents of the file
                buffer = f.read(buffersize)
                if not buffer:
                    break
                crc = zlib.crc32(buffer, crc)
        crc = crc & 0xffffffff
        return '%08x' % crc
    else:
        checkFromString = hasherFromString(hasher)
        hasher = checkFromString if checkFromString else hasher
        with open(path, 'rb') as f:
            while True:
                # update the hash with the contents of the file
                buffer = f.read(buffersize)
                if not buffer:
                    break
                hasher.update(buffer)
        return hasher.hexdigest()

def windowsUrlFileGet(path):
    assertEq('.url', _os.path.splitext(path)[1].lower())
    s = readall(path, mode='r', encoding='latin1')
    lines = s.split('\n')
    for line in lines:
        if line.startswith('URL='):
            return line[len('URL='):]
    raise RuntimeError('no url seen in ' + path)

def windowsUrlFileWrite(path, url):
    assertTrue(len(url) > 0)
    assertTrue(not files.exists(path), 'file already exists at', path)
    try:
        url.encode('ascii')
    except e:
        if isinstance(e, UnicodeEncodeError):
            raise RuntimeError('can\'t support a non-ascii url' + url + ' ' + path)
        else:
            raise
    f = open(path, 'w', encoding='ascii')
    f.write('[InternetShortcut]\n')
    f.write('URL=%s\n' % url)
    f.close()

# returns tuple (returncode, stdout, stderr)
def run(listArgs, _ind=_enforceExplicitlyNamedParameters, shell=False, createNoWindow=True,
        throwOnFailure=RuntimeError, stripText=True, captureoutput=True, silenceoutput=False,
        wait=True):
    import subprocess
    _checkNamedParameters(_ind)
    kwargs = {}
    
    if sys.platform.startswith('win') and createNoWindow:
        kwargs['creationflags'] = 0x08000000
    
    if captureoutput and not wait:
        raise ValueError('captureoutput implies wait')
    
    if throwOnFailure and not wait:
        raise ValueError('throwing on failure implies wait')
    
    retcode = -1
    stdout = None
    stderr = None
    
    if captureoutput:
        sp = subprocess.Popen(listArgs, shell=shell,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
        
        comm = sp.communicate()
        stdout = comm[0]
        stderr = comm[1]
        retcode = sp.returncode
        if stripText:
            stdout = stdout.rstrip()
            stderr = stderr.rstrip()

    else:
        if silenceoutput:
            stdoutArg = open(_os.devnull, 'wb')
            stderrArg = open(_os.devnull, 'wb')
        else:
            stdoutArg = None
            stderrArg = None
        
        if wait:
            retcode = subprocess.call(listArgs, stdout=stdoutArg, stderr=stderrArg, shell=shell, **kwargs)
        else:
            subprocess.Popen(listArgs, stdout=stdoutArg, stderr=stderrArg, shell=shell, **kwargs)
        
    if throwOnFailure and retcode != 0:
        if throwOnFailure is True:
            throwOnFailure = RuntimeError

        exceptionText = 'retcode is not 0 for process ' + \
            str(listArgs) + '\nretcode was ' + str(retcode) + \
            '\nstdout was ' + str(stdout) + \
            '\nstderr was ' + str(stderr)
        raise throwOnFailure(getPrintable(exceptionText))
    
    return retcode, stdout, stderr
    
def runWithoutWaitUnicode(listArgs):
    # in Windows in Python2, non-ascii characters cause subprocess.Popen to fail.
    # https://bugs.python.org/issue1759845
    
    import subprocess
    if isPy3OrNewer or not sys.platform.startswith('win') or all(isinstance(arg, str) for arg in listArgs):
        # no workaround needed in Python3
        p = subprocess.Popen(listArgs, shell=False)
        return p.pid
    else:
        import winprocess
        import types
        if isinstance(listArgs, types.StringTypes):
            combinedArgs = listArgs
        else:
            combinedArgs = subprocess.list2cmdline(listArgs)
            
        combinedArgs = unicode(combinedArgs)
        executable = None
        close_fds = False
        creationflags = 0
        env = None
        cwd = None
        startupinfo = winprocess.STARTUPINFO()
        handle, ht, pid, tid = winprocess.CreateProcess(executable, combinedArgs,
            None, None,
            int(not close_fds),
            creationflags,
            env,
            cwd,
            startupinfo)
        ht.Close()
        handle.Close()
        return pid
