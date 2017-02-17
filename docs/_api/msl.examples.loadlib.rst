.. _mod32bit:

msl.examples.loadlib package
============================

.. automodule:: msl.examples.loadlib

Modules that end in **32** contain a class that is a subclass of
:class:`~msl.loadlib.server32.Server32`. This subclass is a wrapper around
a 32-bit library and is hosted on a 32-bit server.

Modules that end in **64** contain a class that is a subclass of
:class:`~msl.loadlib.client64.Client64`. This subclass sends a request to
the corresponding :class:`~msl.loadlib.server32.Server32` subclass to
communicate with the 32-bit library.

.. toctree::

   dummy32 <msl.examples.loadlib.dummy32>
   dummy64 <msl.examples.loadlib.dummy64>
   cpp32 <msl.examples.loadlib.cpp32>
   cpp64 <msl.examples.loadlib.cpp64>
   kernel32 <msl.examples.loadlib.kernel32>
   kernel64 <msl.examples.loadlib.kernel64>
   dotnet32 <msl.examples.loadlib.dotnet32>
   dotnet64 <msl.examples.loadlib.dotnet64>
   fortran32 <msl.examples.loadlib.fortran32>
   fortran64 <msl.examples.loadlib.fortran64>
