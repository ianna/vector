# Copyright (c) 2019-2021, Jonas Eschle, Jim Pivarski, Eduardo Rodrigues, and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/vector for details.

import numpy

from vector.compute.planar import rho2
from vector.methods import AzimuthalRhoPhi, AzimuthalXY, _aztype, _from_signature


def xy(lib, x, y):
    return lib.sqrt(rho2.xy(lib, x, y))


def rhophi(lib, rho, phi):
    return rho


dispatch_map = {
    (AzimuthalXY,): (xy, float),
    (AzimuthalRhoPhi,): (rhophi, float),
}


def dispatch(v):
    function, *returns = _from_signature(__name__, dispatch_map, (_aztype(v),))
    with numpy.errstate(all="ignore"):
        return v._wrap_result(function(v.lib, *v.azimuthal.elements), returns)
