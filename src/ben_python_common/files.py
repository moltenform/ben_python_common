# BenPythonCommon,
# 2015 Ben Fisher, released under the GPLv3 license.

import sys
import os as _os
import shutil as _shutil_hide
from common_util import *

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
makedir = _os.mkdir
makedirs = _os.makedirs
sep = _os.path.sep
linesep = _os.linesep
abspath = _shutil_hide.abspath
rmtree = _shutil_hide.rmtree

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
    if files.exists(s):
        files.delete(s)
    assert not files.exists(s)
   
def copy(srcfile, destfile, overwrite):
    if not exists(srcfile):
        raise IOError('source path does not exist')
        
    if srcfile == destfile:
        pass
    elif sys.platform == 'win32':
        from ctypes import windll, c_wchar_p, c_int
        failIfExists = c_int(0) if overwrite else c_int(1)
        res = windll.kernel32.CopyFileW(c_wchar_p(srcfile), c_wchar_p(destfile), failIfExists)
        if not res:
            raise IOError('CopyFileW failed (maybe dest already exists?)')
    else:
        if overwrite:
            _shutil_hide.copy(srcfile, destfile)
        else:
            copyFilePosixWithoutOverwrite(srcfile, destfile)

    assertTrue(exists(destfile))
        
def move(srcfile, destfile, overwrite):
    if not exists(srcfile):
        raise IOError('source path does not exist')
        
    if srcfile == destfile:
        pass
    elif sys.platform == 'win32':
        from ctypes import windll, c_wchar_p, c_int
        replaceExisting = c_int(1) if overwrite else c_int(0)
        res = windll.kernel32.MoveFileExW(c_wchar_p(srcfile), c_wchar_p(destfile), replaceExisting)
        if not res:
            raise IOError('MoveFileExW failed (maybe dest already exists?)')
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
    
# unicodetype can be utf-8, utf-8-sig, etc.
def readall(s, mode='r', unicodetype=None):
    if unicodetype:
        import codecs
        f = codecs.open(s, mode, unicodetype)
    else:
        f = open(s, mode)
    txt = f.read()
    f.close()
    return txt

# unicodetype can be utf-8, utf-8-sig, etc.
def writeall(s, txt, mode='w', unicodetype=None):
    if unicodetype:
        import codecs
        f = codecs.open(s, mode, unicodetype)
    else:
        f = open(s, mode)
    f.write(txt)
    f.close()

# use this to make the caller pass argument names,
# allowing foo(param=False) but preventing foo(False)
_enforceExplicitlyNamedParameters = object()

def _checkNamedParameters(obj):
    if obj is not _enforceExplicitlyNamedParameters:
        raise ValueError('please name parameters for this function or method')

# allowedexts in the form ['png', 'gif']
def listchildrenUnsorted(dir, _ind=_enforceExplicitlyNamedParameters, filenamesOnly=False, allowedexts=None):
    _checkNamedParameters(_ind)
    for filename in _os.listdir(dir):
        if not allowedexts or getext(filename) in allowedexts:
            yield filename if filenamesOnly else (dir + _os.path.sep + filename, filename)
    
if sys.platform == 'win32':
    listchildren = listchildrenUnsorted
else:
    def listchildren(*args, **kwargs):
        return sorted(listchildrenUnsorted(*args, **kwargs))
    
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
            for filename in (filenames if sys.platform == 'win32' else sorted(filenames)):
                if not allowedexts or getext(filename) in allowedexts:
                    yield filename if filenamesOnly else (dirpath + _os.path.sep + filename, filename)
        
        if includeDirs:
            yield getname(dirpath) if filenamesOnly else (dirpath, getname(dirpath))
    
def recursedirs(root, _ind=_enforceExplicitlyNamedParameters, filenamesOnly=False, fnFilterDirs=None, topdown=True):
    _checkNamedParameters(_ind)
    return recursefiles(root, filenamesOnly=filenamesOnly, fnFilterDirs=fnFilterDirs, includeFiles=False, includeDirs=True, topdown=topdown)
    
def isemptydir(dir):
    return len(_os.listdir(dir)) == 0
    
# processes
def openDirectoryInExplorer(dir):
    assert isdir(dir), 'not a dir? ' + dir
    assert '^' not in dir and '"' not in dir, 'dir cannot contain ^ or "'
    runWithoutWaitUnicode([u'cmd', u'/c', u'start', u'explorer.exe', dir])

def openUrl(s):
    assert s.startswith('http:') or s.startswith('https:')
    assert '^' not in s and '"' not in s, 'url cannot contain ^ or "'
    import webbrowser
    webbrowser.open(s, new=2)

# returns tuple (returncode, stdout, stderr)
def run(listArgs, _ind=_enforceExplicitlyNamedParameters, shell=False, createNoWindow=True,
        throwOnFailure=RuntimeError, stripText=True, captureoutput=True, silenceoutput=False):
    import subprocess
    _checkNamedParameters(_ind)
    kwargs = {}
    
    if sys.platform == 'win32' and createNoWindow:
        kwargs['creationflags'] = 0x08000000
    
    if not captureoutput:
        retcode = subprocess.call(listArgs, shell=shell, **kwargs)
        if silenceoutput:
            stdout = open(_os.devnull, 'wb')
            stderr = open(_os.devnull, 'wb')
        else:
            stdout = None
            stderr = None
    else:
        sp = subprocess.Popen(listArgs, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
        comm = sp.communicate()
        stdout = comm[0]
        stderr = comm[1]
        retcode = sp.returncode
        if stripText:
            stdout = stdout.rstrip()
            stderr = stderr.rstrip()
        
    if throwOnFailure and retcode != 0:
        if throwOnFailure is True:
            throwOnFailure = RuntimeError
        exceptionText = 'retcode is not 0 for process ' + str(listArgs) + '\nstdout was ' + str(stdout) + '\nstderr was ' + str(stderr)
        raise throwOnFailure(getPrintable(exceptionText))
    
    return retcode, stdout, stderr
    
def runWithoutWaitUnicode(listArgs):
    # in Windows, non-ascii characters cause subprocess.Popen to fail.
    # https://bugs.python.org/issue1759845
    import subprocess
    if sys.platform != 'win32' or all(isinstance(arg, str) for arg in listArgs):
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
