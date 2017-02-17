"""
Contains the base class for loading a 32-bit shared library in 32-bit Python.

The :class:`~.server32.Server32` class is used in combination with the
:class:`~.client64.Client64` class to communicate with a 32-bit shared library
from 64-bit Python.
"""
import os
import sys
import traceback
import threading
import subprocess
try:
    import cPickle as pickle
except ImportError:
    import pickle

from msl.loadlib import LoadLibrary
from msl.loadlib import IS_PYTHON2, IS_PYTHON3
from msl.loadlib.freeze_server32 import SERVER_FILENAME

if IS_PYTHON2:
    from BaseHTTPServer import HTTPServer
    from BaseHTTPServer import BaseHTTPRequestHandler
elif IS_PYTHON3:
    from http.server import HTTPServer
    from http.server import BaseHTTPRequestHandler
else:
    raise NotImplementedError('Python major version is not 2 or 3')


class Server32(HTTPServer):
    """
    Loads a 32-bit shared library which is then hosted on a 32-bit server.

    All modules that are to be run on the 32-bit server must contain a class
    that is inherited from this class and the module can import **any** of
    the `standard`_ python modules **except** for :py:mod:`distutils`,
    :py:mod:`ensurepip`, :py:mod:`tkinter` and :py:mod:`turtle`.

    All modules that are run on the 32-bit server must be able to run on the Python
    interpreter that the server is running on. To get the version information of the
    Python interpreter run

        >>> from msl.loadlib import Server32  # doctest: +SKIP
        >>> Server32.version()  # doctest: +SKIP

    The returned value will be something similar to::

    'Python 3.5.2 |Continuum Analytics, Inc.| (default, Jul  5 2016, 11:45:57) [MSC v.1900 32 bit (Intel)]'

    Args:
        path (str): The full path to the 32-bit library *or* only the
            filename if the library file is located in the current working directory.

        libtype (str): The library type to use for the calling convention.
            Must be either **cdll**, **windll**, **oledll** or **net**.

            * **cdll** for a C/C++ __cdecl library or a FORTRAN library
            * **oledll** or **windll** for a __stdcall library (Windows only), or
            * **net** for a .NET Framework library.

        host (str): The IP address of the server.

        port (int): The port to open on the server.

        quiet (bool): Whether to hide :py:data:`sys.stdout` messages from
            the server.

    Raises:
        IOError: If the shared library cannot be loaded.
        TypeError: If the value of ``libtype`` is not supported.

    .. _standard: https://docs.python.org/3.5/py-modindex.html
    """
    def __init__(self, path, libtype, host, port, quiet):
        HTTPServer.__init__(self, (host, int(port)), RequestHandler)
        self.quiet = quiet
        self._library = LoadLibrary(path, libtype)

    @property
    def path(self):
        """
        Returns:
            :py:class:`str`: The absolute path to the shared library file.
        """
        return self._library.path

    @property
    def lib(self):
        """
        Returns the reference to the 32-bit, loaded-library object.

        For example:

        * if ``libtype`` = **cdll** then a :class:`ctypes.CDLL` object
        * if ``libtype`` = **windll** then a :class:`ctypes.WinDLL` object
        * if ``libtype`` = **oledll** then a :class:`ctypes.OleDLL` object
        * if ``libtype`` = **net** then the imported .NET module

        .. attention::
           For **cdll**, **windll** and **oledll** a :py:mod:`ctypes` class is returned.
           However, for a .NET library it is the imported module that is returned
           (not a class from the library).
        """
        return self._library.lib

    @property
    def net(self):
        """
        Returns the reference to the `.NET RuntimeAssembly <NET_>`_ object -- *only if
        the shared library is a .NET library, otherwise returns* :py:data:`None`.

        .. tip::
           The `JetBrains dotPeek <https://www.jetbrains.com/decompiler/>`_ program can be used
           to reliably decompile any .NET assembly into the equivalent C# source code.

        .. _NET: https://msdn.microsoft.com/en-us/library/system.reflection.assembly(v=vs.110).aspx
        """
        return self._library.net

    @staticmethod
    def version():
        """
        Gets the version of the Python interpreter running on the 32-bit server.

        .. note::
            This method takes about 1 second to finish because the server executable
            needs to start in order to determine the Python version.

        Returns:
            :py:class:`str`: The result of executing ``'Python' + sys.version`` on the
            32-bit server.
        """
        exe = os.path.join(os.path.dirname(__file__), SERVER_FILENAME)
        pipe = subprocess.Popen([exe, '--version'], stdout=subprocess.PIPE)
        return pipe.communicate()[0].decode().strip()

    @staticmethod
    def interactive_console():
        """
        Start an interactive console with the Python interpreter on the 32-bit server.

        *Currently only tested on Windows.*
        """
        exe = os.path.join(os.path.dirname(__file__), SERVER_FILENAME)
        os.system('start ' + ' '.join((exe, '--interactive')))


class RequestHandler(BaseHTTPRequestHandler):
    """
    Handles the request that was sent to the 32-bit server.
    """

    def do_GET(self):
        """
        Handle a GET request.
        """
        request = self.path[1:]
        if request == 'SHUTDOWN_SERVER':
            threading.Thread(target=self.server.shutdown).start()
            return

        try:
            method, pickle_protocol, pickle_temp_file = request.split(':', 2)
            if method == 'LIB32_PATH':
                response = self.server.path
            else:
                with open(pickle_temp_file, 'rb') as f:
                    args = pickle.load(f)
                    kwargs = pickle.load(f)
                response = getattr(self.server, method)(*args, **kwargs)

            with open(pickle_temp_file, 'wb') as f:
                pickle.dump(response, f, protocol=int(pickle_protocol))

            self.send_response(200)
            self.end_headers()

        except Exception:
            self.send_response(501)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()

            exc_type, exc_value, exc_traceback = sys.exc_info()
            tb_list = traceback.extract_tb(exc_traceback)
            tb = tb_list[min(len(tb_list)-1, 1)]  # get the Server32 subclass exception

            msg = '\n  File "{}", line {}, in {}'.format(tb[0], tb[1], tb[2])
            if tb[3]:
                msg += '\n    {}'.format(tb[3])
            msg += '\n{}: {}'.format(exc_type.__name__, exc_value)

            self.wfile.write(msg.encode())

    def log_message(self, fmt, *args):
        """
        Overrides: :py:meth:`~http.server.BaseHTTPRequestHandler.log_message`

        Ignore all log messages from being displayed in :py:data:`sys.stdout`.
        """
        pass
