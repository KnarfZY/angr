import nose
import angr
from simuvex.s_type import SimTypePointer, SimTypeFunction, SimTypeChar, SimTypeInt, parse_defns
from angr.surveyors.caller import Callable
from angr.errors import AngrCallableMultistateError

import logging
l = logging.getLogger("angr_tests")

import os
location = str(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../binaries/tests'))

addresses_fauxware = {
    'armel': 0x8524,
    'armhf': 0x104c9,   # addr+1 to force thumb
    'i386': 0x8048524,
    'mips': 0x400710,
    'mipsel': 0x4006d0,
    'ppc': 0x1000054c,
    'ppc64': 0x10000698,
    'x86_64': 0x400664
}

addresses_manysum = {
    'armel': 0x1041c,
    'armhf': 0x103bd,
    'i386': 0x80483d8,
    'mips': 0x400704,
    'mipsel': 0x400704,
    'ppc': 0x10000418,
    'ppc64': 0x10000500,
    'x86_64': 0x4004ca
}

def run_fauxware(arch):
    addr = addresses_fauxware[arch]
    p = angr.Project(location + '/' + arch + '/fauxware')
    charstar = SimTypePointer(SimTypeChar())
    prototype = SimTypeFunction((charstar, charstar), SimTypeInt(False))
    cc = p.factory.cc(func_ty=prototype)
    authenticate = p.factory.callable(addr, toc=0x10018E80 if arch == 'ppc64' else None, concrete_only=True, cc=cc)
    nose.tools.assert_equal(authenticate("asdf", "SOSNEAKY")._model_concrete.value, 1)
    nose.tools.assert_raises(AngrCallableMultistateError, authenticate, "asdf", "NOSNEAKY")

def run_manysum(arch):
    addr = addresses_manysum[arch]
    p = angr.Project(location + '/' + arch + '/manysum')
    inttype = SimTypeInt()
    prototype = SimTypeFunction([inttype]*11, inttype)
    cc = p.factory.cc(func_ty=prototype)
    sumlots = Callable(p, addr, cc=cc)
    result = sumlots(1,2,3,4,5,6,7,8,9,10,11)
    nose.tools.assert_false(result.symbolic)
    nose.tools.assert_equal(result._model_concrete.value, sum(xrange(12)))

type_cache = None

def run_manyfloatsum(arch):
    global type_cache
    if type_cache is None:
        type_cache = parse_defns(open('/home/angr/angr/binaries/tests_src/manyfloatsum.c').read())

    p = angr.Project(location + '/' + arch + '/manyfloatsum')
    for function in ('sum_floats', 'sum_combo', 'sum_segregated', 'sum_doubles', 'sum_combo_doubles', 'sum_segregated_doubles'):
        cc = p.factory.cc(func_ty=type_cache[function])
        args = list(range(len(cc.func_ty.args)))
        answer = float(sum(args))
        addr = p.loader.main_bin.get_symbol(function).rebased_addr
        my_callable = p.factory.callable(addr, cc=cc)
        result = my_callable(*args)
        nose.tools.assert_false(result.symbolic)
        result_concrete = result.args[0]
        nose.tools.assert_equal(answer, result_concrete)


def test_fauxware():
    for arch in addresses_fauxware:
        yield run_fauxware, arch

def test_manysum():
    for arch in addresses_manysum:
        yield run_manysum, arch

def test_manyfloatsum():
    for arch in ('i386', 'x86_64'):
        yield run_manyfloatsum, arch

if __name__ == "__main__":
    print 'testing manyfloatsum'
    for func, march in test_manyfloatsum():
        print '* testing ' + march
        func(march)
    print 'testing fauxware'
    for func, march in test_fauxware():
        print '* testing ' + march
        func(march)
    print 'testing manysum'
    for func, march in test_manysum():
        print '* testing ' + march
        func(march)
