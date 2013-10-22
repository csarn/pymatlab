import os
import os.path
import platform

from pymatlab.matlab import MatlabSession

def session_factory(options='',output_buffer_size=8096):
    system = platform.system()
    path = None
    if (system == 'Linux') or (system == 'Darwin'):
        # find the MATLAB-root path:
        locations = os.environ.get("PATH").split(os.pathsep)
        for location in locations:
            candidate = os.path.join(location, 'matlab')
            if os.path.isfile(candidate):
                path = candidate
                break
        executable = os.path.realpath(path)
        basedir = os.path.dirname(os.path.dirname(executable))
        exec_and_options = " ".join([executable,options])
        session = MatlabSession(basedir,exec_and_options,output_buffer_size)
    elif system =='Windows':
        locations = os.environ.get("PATH").split(os.pathsep)
        for location in locations:
            candidate = os.path.join(location, 'matlab.exe')
            if os.path.isfile(candidate):
                path = candidate
                break
        executable = os.path.realpath(path)
        basedir = os.path.dirname(os.path.dirname(executable))
        session = MatlabSession(path=basedir,bufsize=output_buffer_size)

    else:
        raise NotSupportedException(
                'Not supported on the {platform}-platform'.format(
                        platform=system))
    return session

def remote_session_factory(hostname,remote_path):
    system = platform.system()
    path = None
    if (system == 'Linux') or (system == 'Darwin'):
        locations = os.environ.get("PATH").split(os.pathsep)
        for location in locations:
            candidate = os.path.join(location, 'matlab')
            if os.path.isfile(candidate):
                path = candidate
                break
        executable = os.path.realpath(path)
        basedir = os.path.dirname(os.path.dirname(executable))
        session = MatlabSession(
            basedir,
            "ssh {host} '/bin/csh -c {full_path}'".format(
                    host=hostname,
                    full_path=remote_path)
            )
    else:
        raise NotSupportedException(
                'Not supported on the {platform}-platform'.format(
                        platform=system))
    return session

