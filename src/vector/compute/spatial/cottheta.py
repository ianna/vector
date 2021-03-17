# Copyright (c) 2019-2021, Jonas Eschle, Jim Pivarski, Eduardo Rodrigues, and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/vector for details.

import numpy

from vector.compute.planar import rho
from vector.compute.spatial import theta
from vector.methods import (
    AzimuthalRhoPhi,
    AzimuthalXY,
    LongitudinalEta,
    LongitudinalTheta,
    LongitudinalZ,
    _aztype,
    _from_signature,
    _ltype,
)


def xy_z(lib, x, y, z):
    return lib.nan_to_num(z / rho.xy(lib, x, y), lib.inf)


def xy_theta(lib, x, y, theta):
    return 1 / lib.tan(theta)


def xy_eta(lib, x, y, eta):
    return 1 / lib.tan(theta.xy_eta(lib, x, y, eta))


def rhophi_z(lib, rho, phi, z):
    return lib.nan_to_num(z / rho, lib.inf)


def rhophi_theta(lib, rho, phi, theta):
    return 1 / lib.tan(theta)


def rhophi_eta(lib, rho, phi, eta):
    return 1 / lib.tan(theta.rhophi_eta(lib, rho, phi, eta))


dispatch_map = {
    (AzimuthalXY, LongitudinalZ): (xy_z, float),
    (AzimuthalXY, LongitudinalTheta): (xy_theta, float),
    (AzimuthalXY, LongitudinalEta): (xy_eta, float),
    (AzimuthalRhoPhi, LongitudinalZ): (rhophi_z, float),
    (AzimuthalRhoPhi, LongitudinalTheta): (rhophi_theta, float),
    (AzimuthalRhoPhi, LongitudinalEta): (rhophi_eta, float),
}


def dispatch(v):
    function, *returns = _from_signature(
        __name__,
        dispatch_map,
        (
            _aztype(v),
            _ltype(v),
        ),
    )
    with numpy.errstate(all="ignore"):
        return v._wrap_result(
            function(v.lib, *v.azimuthal.elements, *v.longitudinal.elements), returns
        )