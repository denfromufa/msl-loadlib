import os
import pytest

from msl import loadlib
from msl.examples.loadlib import Cpp64, Fortran64, Dummy64

eps = 1e-10

c = Cpp64()
f = Fortran64()
d = Dummy64(True)


def teardown_module(module):
    c.shutdown_server()
    f.shutdown_server()
    d.shutdown_server()


def test_unique_ports():
    for item in [f, d]:
        assert c.port != item.port
    for item in [c, d]:
        assert f.port != item.port
    for item in [c, f]:
        assert d.port != item.port


def test_lib_name():
    def get_name(path):
        return os.path.basename(path).split('.')[0]

    assert 'cpp_lib32' == get_name(c.lib32_path)
    assert 'fortran_lib32' == get_name(f.lib32_path)


def test_load_failure_in_64bit_python():
    if loadlib.IS_PYTHON_64BIT:
        with pytest.raises(IOError):
            loadlib.LoadLibrary(os.path.join('.', 'examples', 'cpp_lib32'))
        with pytest.raises(IOError):
            loadlib.LoadLibrary(os.path.join('.', 'examples', 'fortran_lib32'))


def test_load_failure_in_32bit_python():
    if not loadlib.IS_PYTHON_64BIT:
        with pytest.raises(IOError):
            loadlib.LoadLibrary(os.path.join('.', 'examples', 'cpp_lib64'))
        with pytest.raises(IOError):
            loadlib.LoadLibrary(os.path.join('.', 'examples', 'fortran_lib64'))


def test_server_version():
    assert 'Python' in loadlib.Server32.version()


def test_cpp():
    assert 3 == c.add(1, 2)
    assert -1002 == c.add(-1000, -2)
    assert abs(10.0 - c.subtract(20.0, 10.0)) < eps
    assert abs(-10.0 - c.subtract(90.0, 100.0)) < eps
    assert abs(0.0 - c.add_or_subtract(0.1234, -0.1234, True)) < eps
    assert abs(100.0 - c.add_or_subtract(123.456, 23.456, False)) < eps

    a = 3.1415926
    values = [float(x) for x in range(100)]
    c_values = c.scalar_multiply(a, values)
    for i in range(len(values)):
        assert abs(a*values[i] - c_values[i]) < eps

    assert '0987654321' == c.reverse_string_v1('1234567890')
    assert '[abc x|z j 1 *&' == c.reverse_string_v2('&* 1 j z|x cba[')


def test_fortran():
    assert -127 == f.sum_8bit(-2**7, 1)
    assert 32766 == f.sum_16bit(2**15 - 1, -1)
    assert 123456789 == f.sum_32bit(123456788, 1)
    assert -9223372036854775807 == f.sum_64bit(-2**63, 1)
    assert abs(-52487.570494 - f.multiply_float32(40.874, -1284.131)) < 1e-3
    assert abs(2.31e300 - f.multiply_float64(1.1e100, 2.1e200)) < eps
    assert f.is_positive(1e-100)
    assert not f.is_positive(-1e-100)
    assert 3000 == f.add_or_subtract(1000, 2000, True)
    assert -1000 == f.add_or_subtract(1000, 2000, False)
    assert 1 == int(f.factorial(0))
    assert 1 == int(f.factorial(1))
    assert 120 == int(f.factorial(5))
    assert abs(2.73861278752583 - f.standard_deviation([float(val) for val in range(1,10)])) < eps
    assert abs(0.171650807137 - f.besselJ0(8.0)) < eps
    assert '!dlrow olleh' == f.reverse_string('hello world!')

    a = [float(val) for val in range(1, 1000)]
    b = [3.0*val for val in range(1, 1000)]
    f_values = f.add_1D_arrays(a, b)
    for i in range(len(a)):
        assert abs(a[i] + b[i] - f_values[i]) < eps

    f_mat = f.matrix_multiply([[1., 2., 3.], [4., 5., 6.]], [[1., 2.], [3., 4.], [5., 6.]])
    assert abs(22.0 - f_mat[0][0]) < eps
    assert abs(28.0 - f_mat[0][1]) < eps
    assert abs(49.0 - f_mat[1][0]) < eps
    assert abs(64.0 - f_mat[1][1]) < eps


def test_dummy():

    args, kwargs = d.send_data(True)
    assert args[0]
    assert {} == kwargs

    args, kwargs = d.send_data(x=1.0)
    assert args == ()
    assert kwargs == {'x': 1.0}

    x = [val for val in range(100)]
    y = range(9999)
    my_dict = {'x': x, 'y': y, 'text': 'abcd 1234 wxyz'}
    args, kwargs = d.send_data(111, 2.3, complex(-1.2, 2.30), (1, 2), x=x, y=y, my_dict=my_dict)
    assert args[0] == 111
    assert args[1] == 2.3
    assert args[2] == complex(-1.2, 2.30)
    assert args[3] == (1, 2)
    assert kwargs['x'] == x
    assert kwargs['y'] == y
    assert kwargs['my_dict'] == my_dict
