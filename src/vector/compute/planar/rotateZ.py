# Copyright (c) 2019-2021, Jonas Eschle, Jim Pivarski, Eduardo Rodrigues, and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/vector for details.

import numpy

from vector.methods import AzimuthalRhoPhi, AzimuthalXY, _aztype, _from_signature


def rectify(lib, phi):
    return (phi + lib.pi) % (2 * lib.pi) - lib.pi


def xy(lib, angle, x, y):
    s = lib.sin(angle)
    c = lib.cos(angle)
    return c * x - s * y, s * x + c * y


def rhophi(lib, angle, rho, phi):
    return rho, rectify(lib, phi + angle)


dispatch_map = {
    (AzimuthalXY,): (xy, AzimuthalXY),
    (AzimuthalRhoPhi,): (rhophi, AzimuthalRhoPhi),
}


def dispatch(angle, v):
    function, *returns = _from_signature(__name__, dispatch_map, (_aztype(v),))
    with numpy.errstate(all="ignore"):
        return v._wrap_result(function(v.lib, angle, *v.azimuthal.elements), returns)
