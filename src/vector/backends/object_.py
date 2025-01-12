# Copyright (c) 2019-2021, Jonas Eschle, Jim Pivarski, Eduardo Rodrigues, and Henry Schreiner.
#
# Distributed under the 3-clause BSD license, see accompanying file LICENSE
# or https://github.com/scikit-hep/vector for details.

import typing

import numpy

from vector.methods import (
    Azimuthal,
    AzimuthalRhoPhi,
    AzimuthalXY,
    Coordinates,
    Longitudinal,
    LongitudinalEta,
    LongitudinalTheta,
    LongitudinalZ,
    Lorentz,
    LorentzMomentum,
    Planar,
    PlanarMomentum,
    Spatial,
    SpatialMomentum,
    TemporalT,
    TemporalTau,
    Vector,
    Vector2D,
    Vector3D,
    Vector4D,
    _aztype,
    _coordinate_class_to_names,
    _handler,
    _ltype,
    _repr_generic_to_momentum,
    _ttype,
)


class CoordinatesObject:
    pass


class AzimuthalObject(CoordinatesObject):
    pass


class LongitudinalObject(CoordinatesObject):
    pass


class TemporalObject(CoordinatesObject):
    pass


def _replace_data(obj, result):
    if not isinstance(result, VectorObject):
        raise TypeError(f"can only assign a single vector to {type(obj).__name__}")

    if isinstance(obj.azimuthal, AzimuthalObjectXY):
        obj.azimuthal = AzimuthalObjectXY(result.x, result.y)
    elif isinstance(obj.azimuthal, AzimuthalObjectRhoPhi):
        obj.azimuthal = AzimuthalObjectRhoPhi(result.rho, result.phi)
    else:
        raise AssertionError(type(obj))

    if hasattr(obj, "longitudinal"):
        if isinstance(obj.longitudinal, LongitudinalObjectZ):
            obj.longitudinal = LongitudinalObjectZ(result.z)
        elif isinstance(obj.longitudinal, LongitudinalObjectTheta):
            obj.longitudinal = LongitudinalObjectTheta(result.theta)
        elif isinstance(obj.longitudinal, LongitudinalObjectEta):
            obj.longitudinal = LongitudinalObjectEta(result.eta)
        else:
            raise AssertionError(type(obj))

    if hasattr(obj, "temporal"):
        if isinstance(obj.temporal, TemporalObjectT):
            obj.temporal = TemporalObjectT(result.t)
        elif isinstance(obj.temporal, TemporalObjectTau):
            obj.temporal = TemporalObjectTau(result.tau)
        else:
            raise AssertionError(type(obj))

    return obj


class VectorObject:
    def __eq__(self, other):
        return numpy.equal(self, other)

    def __ne__(self, other):
        return numpy.not_equal(self, other)

    def __abs__(self):
        return numpy.absolute(self)

    def __add__(self, other):
        return numpy.add(self, other)

    def __radd__(self, other):
        return numpy.add(other, self)

    def __iadd__(self, other):
        return _replace_data(self, numpy.add(self, other))

    def __sub__(self, other):
        return numpy.subtract(self, other)

    def __rsub__(self, other):
        return numpy.subtract(other, self)

    def __isub__(self, other):
        return _replace_data(self, numpy.subtract(self, other))

    def __mul__(self, other):
        return numpy.multiply(self, other)

    def __rmul__(self, other):
        return numpy.multiply(other, self)

    def __imul__(self, other):
        return _replace_data(self, numpy.multiply(self, other))

    def __neg__(self):
        return numpy.negative(self)

    def __pos__(self):
        return numpy.positive(self)

    def __truediv__(self, other):
        return numpy.true_divide(self, other)

    def __rtruediv__(self, other):
        return numpy.true_divide(other, self)

    def __itruediv__(self, other):
        return _replace_data(self, numpy.true_divide(self, other))

    def __pow__(self, other):
        return numpy.power(self, other)

    def __matmul__(self, other):
        return numpy.matmul(self, other)

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        if not isinstance(_handler(inputs), VectorObject):
            # Let the array-of-vectors object handle it.
            return NotImplemented

        if isinstance(self, Vector2D):
            from vector.compute.planar import add, dot, equal, not_equal
            from vector.compute.planar import rho as absolute
            from vector.compute.planar import rho2 as absolute2
            from vector.compute.planar import scale, subtract
        elif isinstance(self, Vector3D):
            from vector.compute.spatial import add, dot, equal
            from vector.compute.spatial import mag as absolute
            from vector.compute.spatial import mag2 as absolute2
            from vector.compute.spatial import not_equal, scale, subtract
        elif isinstance(self, Vector4D):
            from vector.compute.lorentz import (
                add,
                dot,
                equal,
                not_equal,
                scale,
                subtract,
            )
            from vector.compute.lorentz import tau as absolute
            from vector.compute.lorentz import tau2 as absolute2

        outputs = kwargs.get("out", ())
        if any(not isinstance(x, VectorObject) for x in outputs):
            raise TypeError(
                "ufunc operating on VectorObjects can only fill another VectorObject "
                "with 'out' keyword"
            )

        if ufunc is numpy.absolute and len(inputs) == 1:
            result = absolute.dispatch(inputs[0])
            for output in outputs:
                _replace_data(output, result)
            return result

        elif ufunc is numpy.add and len(inputs) == 2:
            result = add.dispatch(inputs[0], inputs[1])
            for output in outputs:
                _replace_data(output, result)
            return result

        elif ufunc is numpy.subtract and len(inputs) == 2:
            result = subtract.dispatch(inputs[0], inputs[1])
            for output in outputs:
                _replace_data(output, result)
            return result

        elif (
            ufunc is numpy.multiply
            and not isinstance(inputs[0], (Vector, Coordinates))
            and len(inputs) == 2
        ):
            result = scale.dispatch(inputs[0], inputs[1])
            for output in outputs:
                _replace_data(output, result)
            return result

        elif (
            ufunc is numpy.multiply
            and not isinstance(inputs[1], (Vector, Coordinates))
            and len(inputs) == 2
        ):
            result = scale.dispatch(inputs[1], inputs[0])
            for output in outputs:
                _replace_data(output, result)
            return result

        elif ufunc is numpy.negative and len(inputs) == 1:
            result = scale.dispatch(-1, inputs[0])
            for output in outputs:
                _replace_data(output, result)
            return result

        elif ufunc is numpy.positive and len(inputs) == 1:
            result = inputs[0]
            for output in outputs:
                _replace_data(output, result)
            return result

        elif (
            ufunc is numpy.true_divide
            and not isinstance(inputs[1], (Vector, Coordinates))
            and len(inputs) == 2
        ):
            result = scale.dispatch(1 / inputs[1], inputs[0])
            for output in outputs:
                _replace_data(output, result)
            return result

        elif (
            ufunc is numpy.power
            and not isinstance(inputs[1], (Vector, Coordinates))
            and len(inputs) == 2
        ):
            result = absolute.dispatch(inputs[0]) ** inputs[1]
            for output in outputs:
                _replace_data(output, result)
            return result

        elif ufunc is numpy.square and len(inputs) == 1:
            result = absolute2.dispatch(inputs[0])
            for output in outputs:
                _replace_data(output, result)
            return result

        elif ufunc is numpy.sqrt and len(inputs) == 1:
            result = numpy.sqrt(absolute.dispatch(inputs[0]))
            for output in outputs:
                _replace_data(output, result)
            return result

        elif ufunc is numpy.cbrt and len(inputs) == 1:
            result = numpy.cbrt(absolute.dispatch(inputs[0]))
            for output in outputs:
                _replace_data(output, result)
            return result

        elif ufunc is numpy.matmul and len(inputs) == 2:
            result = dot.dispatch(inputs[0], inputs[1])
            for output in outputs:
                _replace_data(output, result)
            return result

        elif ufunc is numpy.equal and len(inputs) == 2:
            result = equal.dispatch(inputs[0], inputs[1])
            for output in outputs:
                _replace_data(output, result)
            return result

        elif ufunc is numpy.not_equal and len(inputs) == 2:
            result = not_equal.dispatch(inputs[0], inputs[1])
            for output in outputs:
                _replace_data(output, result)
            return result

        else:
            return NotImplemented


class AzimuthalObjectXY(typing.NamedTuple):
    x: float
    y: float

    @property
    def elements(self):
        return (self.x, self.y)


AzimuthalObjectXY.__bases__ = (AzimuthalObject, AzimuthalXY, tuple)


class AzimuthalObjectRhoPhi(typing.NamedTuple):
    rho: float
    phi: float

    @property
    def elements(self):
        return (self.rho, self.phi)


AzimuthalObjectRhoPhi.__bases__ = (AzimuthalObject, AzimuthalRhoPhi, tuple)


class LongitudinalObjectZ(typing.NamedTuple):
    z: float

    @property
    def elements(self):
        return (self.z,)


LongitudinalObjectZ.__bases__ = (LongitudinalObject, LongitudinalZ, tuple)


class LongitudinalObjectTheta(typing.NamedTuple):
    theta: float

    @property
    def elements(self):
        return (self.theta,)


LongitudinalObjectTheta.__bases__ = (LongitudinalObject, LongitudinalTheta, tuple)


class LongitudinalObjectEta(typing.NamedTuple):
    eta: float

    @property
    def elements(self):
        return (self.eta,)


LongitudinalObjectEta.__bases__ = (LongitudinalObject, LongitudinalEta, tuple)


class TemporalObjectT(typing.NamedTuple):
    t: float

    @property
    def elements(self):
        return (self.t,)


TemporalObjectT.__bases__ = (TemporalObject, TemporalT, tuple)


class TemporalObjectTau(typing.NamedTuple):
    tau: float

    @property
    def elements(self):
        return (self.tau,)


TemporalObjectTau.__bases__ = (TemporalObject, TemporalTau, tuple)


class VectorObject2D(VectorObject, Planar, Vector2D):
    __slots__ = ("azimuthal",)

    lib = numpy

    @classmethod
    def from_xy(cls, x, y):
        return cls(AzimuthalObjectXY(x, y))

    @classmethod
    def from_rhophi(cls, rho, phi):
        return cls(AzimuthalObjectRhoPhi(rho, phi))

    def __init__(self, azimuthal):
        self.azimuthal = azimuthal

    def __repr__(self):
        aznames = _coordinate_class_to_names[_aztype(self)]
        out = []
        for x in aznames:
            out.append(f"{x}={getattr(self.azimuthal, x)}")
        return "vector.obj(" + ", ".join(out) + ")"

    def _wrap_result(self, result, returns):
        if isinstance(self, type):
            cls = self
        else:
            cls = type(self)

        if returns == [float] or returns == [bool]:
            return result

        elif returns == [AzimuthalXY]:
            return cls(AzimuthalObjectXY(*result))

        elif returns == [AzimuthalRhoPhi]:
            return cls(AzimuthalObjectRhoPhi(*result))

        else:
            raise AssertionError(repr(returns))

    @property
    def x(self):
        return super().x

    @x.setter
    def x(self, x):
        self.azimuthal = AzimuthalObjectXY(x, self.y)

    @property
    def y(self):
        return super().y

    @y.setter
    def y(self, y):
        self.azimuthal = AzimuthalObjectXY(self.x, y)

    @property
    def rho(self):
        return super().rho

    @rho.setter
    def rho(self, rho):
        self.azimuthal = AzimuthalObjectRhoPhi(rho, self.phi)

    @property
    def phi(self):
        return super().phi

    @phi.setter
    def phi(self, phi):
        self.azimuthal = AzimuthalObjectRhoPhi(self.rho, phi)


class MomentumObject2D(PlanarMomentum, VectorObject2D):
    def __repr__(self):
        aznames = _coordinate_class_to_names[_aztype(self)]
        out = []
        for x in aznames:
            y = _repr_generic_to_momentum.get(x, x)
            out.append(f"{y}={getattr(self.azimuthal, x)}")
        return "vector.obj(" + ", ".join(out) + ")"

    @property
    def px(self):
        return super().px

    @px.setter
    def px(self, px):
        self.azimuthal = AzimuthalObjectXY(px, self.py)

    @property
    def py(self):
        return super().py

    @py.setter
    def py(self, py):
        self.azimuthal = AzimuthalObjectXY(self.px, py)

    @property
    def pt(self):
        return super().pt

    @pt.setter
    def pt(self, pt):
        self.azimuthal = AzimuthalObjectRhoPhi(pt, self.phi)


class VectorObject3D(VectorObject, Spatial, Vector3D):
    __slots__ = ("azimuthal", "longitudinal")

    lib = numpy
    ProjectionClass2D = VectorObject2D

    @classmethod
    def from_xyz(cls, x, y, z):
        return cls(AzimuthalObjectXY(x, y), LongitudinalObjectZ(z))

    @classmethod
    def from_xytheta(cls, x, y, theta):
        return cls(AzimuthalObjectXY(x, y), LongitudinalObjectTheta(theta))

    @classmethod
    def from_xyeta(cls, x, y, eta):
        return cls(AzimuthalObjectXY(x, y), LongitudinalObjectEta(eta))

    @classmethod
    def from_rhophiz(cls, rho, phi, z):
        return cls(AzimuthalObjectRhoPhi(rho, phi), LongitudinalObjectZ(z))

    @classmethod
    def from_rhophitheta(cls, rho, phi, theta):
        return cls(AzimuthalObjectRhoPhi(rho, phi), LongitudinalObjectTheta(theta))

    @classmethod
    def from_rhophieta(cls, rho, phi, eta):
        return cls(AzimuthalObjectRhoPhi(rho, phi), LongitudinalObjectEta(eta))

    def __init__(self, azimuthal, longitudinal):
        self.azimuthal = azimuthal
        self.longitudinal = longitudinal

    def __repr__(self):
        aznames = _coordinate_class_to_names[_aztype(self)]
        lnames = _coordinate_class_to_names[_ltype(self)]
        out = []
        for x in aznames:
            out.append(f"{x}={getattr(self.azimuthal, x)}")
        for x in lnames:
            out.append(f"{x}={getattr(self.longitudinal, x)}")
        return "vector.obj(" + ", ".join(out) + ")"

    def _wrap_result(self, result, returns):
        if isinstance(self, type):
            cls = self
        else:
            cls = type(self)

        if returns == [float] or returns == [bool]:
            return result

        elif returns == [AzimuthalXY]:
            return cls(AzimuthalObjectXY(*result), self.longitudinal)

        elif returns == [AzimuthalRhoPhi]:
            return cls(AzimuthalObjectRhoPhi(*result), self.longitudinal)

        elif (
            (len(returns) == 2 or (len(returns) == 3 and returns[2] is None))
            and isinstance(returns[0], type)
            and issubclass(returns[0], Azimuthal)
            and isinstance(returns[1], type)
            and issubclass(returns[1], Longitudinal)
        ):
            if returns[0] is AzimuthalXY:
                azimuthal = AzimuthalObjectXY(result[0], result[1])
            elif returns[0] is AzimuthalRhoPhi:
                azimuthal = AzimuthalObjectRhoPhi(result[0], result[1])
            else:
                raise AssertionError(repr(returns[0]))
            if returns[1] is LongitudinalZ:
                longitudinal = LongitudinalObjectZ(result[2])
            elif returns[1] is LongitudinalTheta:
                longitudinal = LongitudinalObjectTheta(result[2])
            elif returns[1] is LongitudinalEta:
                longitudinal = LongitudinalObjectEta(result[2])
            else:
                raise AssertionError(repr(returns[1]))
            return cls(azimuthal, longitudinal)

        else:
            raise AssertionError(repr(returns))

    @property
    def x(self):
        return super().x

    @x.setter
    def x(self, x):
        self.azimuthal = AzimuthalObjectXY(x, self.y)

    @property
    def y(self):
        return super().y

    @y.setter
    def y(self, y):
        self.azimuthal = AzimuthalObjectXY(self.x, y)

    @property
    def rho(self):
        return super().rho

    @rho.setter
    def rho(self, rho):
        self.azimuthal = AzimuthalObjectRhoPhi(rho, self.phi)

    @property
    def phi(self):
        return super().phi

    @phi.setter
    def phi(self, phi):
        self.azimuthal = AzimuthalObjectRhoPhi(self.rho, phi)

    @property
    def z(self):
        return super().z

    @z.setter
    def z(self, z):
        self.longitudinal = LongitudinalObjectZ(z)

    @property
    def theta(self):
        return super().theta

    @theta.setter
    def theta(self, theta):
        self.longitudinal = LongitudinalObjectTheta(theta)

    @property
    def eta(self):
        return super().eta

    @eta.setter
    def eta(self, eta):
        self.longitudinal = LongitudinalObjectEta(eta)


class MomentumObject3D(SpatialMomentum, VectorObject3D):
    ProjectionClass2D = MomentumObject2D

    def __repr__(self):
        aznames = _coordinate_class_to_names[_aztype(self)]
        lnames = _coordinate_class_to_names[_ltype(self)]
        out = []
        for x in aznames:
            y = _repr_generic_to_momentum.get(x, x)
            out.append(f"{y}={getattr(self.azimuthal, x)}")
        for x in lnames:
            y = _repr_generic_to_momentum.get(x, x)
            out.append(f"{y}={getattr(self.longitudinal, x)}")
        return "vector.obj(" + ", ".join(out) + ")"

    @property
    def px(self):
        return super().px

    @px.setter
    def px(self, px):
        self.azimuthal = AzimuthalObjectXY(px, self.py)

    @property
    def py(self):
        return super().py

    @py.setter
    def py(self, py):
        self.azimuthal = AzimuthalObjectXY(self.px, py)

    @property
    def pt(self):
        return super().pt

    @pt.setter
    def pt(self, pt):
        self.azimuthal = AzimuthalObjectRhoPhi(pt, self.phi)

    @property
    def pz(self):
        return super().pz

    @pz.setter
    def pz(self, pz):
        self.longitudinal = LongitudinalObjectZ(pz)


class VectorObject4D(VectorObject, Lorentz, Vector4D):
    __slots__ = ("azimuthal", "longitudinal", "temporal")

    lib = numpy
    ProjectionClass2D = VectorObject2D
    ProjectionClass3D = VectorObject3D

    @classmethod
    def from_xyzt(cls, x, y, z, t):
        return cls(AzimuthalObjectXY(x, y), LongitudinalObjectZ(z), TemporalObjectT(t))

    @classmethod
    def from_xyztau(cls, x, y, z, tau):
        return cls(
            AzimuthalObjectXY(x, y), LongitudinalObjectZ(z), TemporalObjectTau(tau)
        )

    @classmethod
    def from_xythetat(cls, x, y, theta, t):
        return cls(
            AzimuthalObjectXY(x, y), LongitudinalObjectTheta(theta), TemporalObjectT(t)
        )

    @classmethod
    def from_xythetatau(cls, x, y, theta, tau):
        return cls(
            AzimuthalObjectXY(x, y),
            LongitudinalObjectTheta(theta),
            TemporalObjectTau(tau),
        )

    @classmethod
    def from_xyetat(cls, x, y, eta, t):
        return cls(
            AzimuthalObjectXY(x, y), LongitudinalObjectEta(eta), TemporalObjectT(t)
        )

    @classmethod
    def from_xyetatau(cls, x, y, eta, tau):
        return cls(
            AzimuthalObjectXY(x, y), LongitudinalObjectEta(eta), TemporalObjectTau(tau)
        )

    @classmethod
    def from_rhophizt(cls, rho, phi, z, t):
        return cls(
            AzimuthalObjectRhoPhi(rho, phi), LongitudinalObjectZ(z), TemporalObjectT(t)
        )

    @classmethod
    def from_rhophiztau(cls, rho, phi, z, tau):
        return cls(
            AzimuthalObjectRhoPhi(rho, phi),
            LongitudinalObjectZ(z),
            TemporalObjectTau(tau),
        )

    @classmethod
    def from_rhophithetat(cls, rho, phi, theta, t):
        return cls(
            AzimuthalObjectRhoPhi(rho, phi),
            LongitudinalObjectTheta(theta),
            TemporalObjectT(t),
        )

    @classmethod
    def from_rhophithetatau(cls, rho, phi, theta, tau):
        return cls(
            AzimuthalObjectRhoPhi(rho, phi),
            LongitudinalObjectTheta(theta),
            TemporalObjectTau(tau),
        )

    @classmethod
    def from_rhophietat(cls, rho, phi, eta, t):
        return cls(
            AzimuthalObjectRhoPhi(rho, phi),
            LongitudinalObjectEta(eta),
            TemporalObjectT(t),
        )

    @classmethod
    def from_rhophietatau(cls, rho, phi, eta, tau):
        return cls(
            AzimuthalObjectRhoPhi(rho, phi),
            LongitudinalObjectEta(eta),
            TemporalObjectTau(tau),
        )

    def __init__(self, azimuthal, longitudinal, temporal):
        self.azimuthal = azimuthal
        self.longitudinal = longitudinal
        self.temporal = temporal

    def __repr__(self):
        aznames = _coordinate_class_to_names[_aztype(self)]
        lnames = _coordinate_class_to_names[_ltype(self)]
        tnames = _coordinate_class_to_names[_ttype(self)]
        out = []
        for x in aznames:
            out.append(f"{x}={getattr(self.azimuthal, x)}")
        for x in lnames:
            out.append(f"{x}={getattr(self.longitudinal, x)}")
        for x in tnames:
            out.append(f"{x}={getattr(self.temporal, x)}")
        return "vector.obj(" + ", ".join(out) + ")"

    def _wrap_result(self, result, returns):
        if isinstance(self, type):
            cls = self
        else:
            cls = type(self)

        if returns == [float] or returns == [bool]:
            return result

        elif returns == [AzimuthalXY]:
            return cls(AzimuthalObjectXY(*result), self.longitudinal, self.temporal)

        elif returns == [AzimuthalRhoPhi]:
            return cls(AzimuthalObjectRhoPhi(*result), self.longitudinal, self.temporal)

        elif (
            len(returns) == 2
            and isinstance(returns[0], type)
            and issubclass(returns[0], Azimuthal)
            and isinstance(returns[1], type)
            and issubclass(returns[1], Longitudinal)
        ):
            if returns[0] is AzimuthalXY:
                azimuthal = AzimuthalObjectXY(result[0], result[1])
            elif returns[0] is AzimuthalRhoPhi:
                azimuthal = AzimuthalObjectRhoPhi(result[0], result[1])
            else:
                raise AssertionError(repr(returns[0]))
            if returns[1] is LongitudinalZ:
                longitudinal = LongitudinalObjectZ(result[2])
            elif returns[1] is LongitudinalTheta:
                longitudinal = LongitudinalObjectTheta(result[2])
            elif returns[1] is LongitudinalEta:
                longitudinal = LongitudinalObjectEta(result[2])
            else:
                raise AssertionError(repr(returns[1]))
            return cls(azimuthal, longitudinal, self.temporal)

        elif (
            len(returns) == 3
            and isinstance(returns[0], type)
            and issubclass(returns[0], Azimuthal)
            and isinstance(returns[1], type)
            and issubclass(returns[1], Longitudinal)
        ):
            if returns[0] is AzimuthalXY:
                azimuthal = AzimuthalObjectXY(result[0], result[1])
            elif returns[0] is AzimuthalRhoPhi:
                azimuthal = AzimuthalObjectRhoPhi(result[0], result[1])
            else:
                raise AssertionError(repr(returns[0]))
            if returns[1] is LongitudinalZ:
                longitudinal = LongitudinalObjectZ(result[2])
            elif returns[1] is LongitudinalTheta:
                longitudinal = LongitudinalObjectTheta(result[2])
            elif returns[1] is LongitudinalEta:
                longitudinal = LongitudinalObjectEta(result[2])
            else:
                raise AssertionError(repr(returns[1]))
            is_4d = True
            if returns[2] is TemporalT:
                temporal = TemporalObjectT(result[3])
            elif returns[2] is TemporalTau:
                temporal = TemporalObjectTau(result[3])
            elif returns[2] is None:
                is_4d = False
            else:
                raise AssertionError(repr(returns[2]))
            if is_4d:
                return cls(azimuthal, longitudinal, temporal)
            else:
                return self.ProjectionClass3D(azimuthal, longitudinal)

        else:
            raise AssertionError(repr(returns))

    @property
    def x(self):
        return super().x

    @x.setter
    def x(self, x):
        self.azimuthal = AzimuthalObjectXY(x, self.y)

    @property
    def y(self):
        return super().y

    @y.setter
    def y(self, y):
        self.azimuthal = AzimuthalObjectXY(self.x, y)

    @property
    def rho(self):
        return super().rho

    @rho.setter
    def rho(self, rho):
        self.azimuthal = AzimuthalObjectRhoPhi(rho, self.phi)

    @property
    def phi(self):
        return super().phi

    @phi.setter
    def phi(self, phi):
        self.azimuthal = AzimuthalObjectRhoPhi(self.rho, phi)

    @property
    def z(self):
        return super().z

    @z.setter
    def z(self, z):
        self.longitudinal = LongitudinalObjectZ(z)

    @property
    def theta(self):
        return super().theta

    @theta.setter
    def theta(self, theta):
        self.longitudinal = LongitudinalObjectTheta(theta)

    @property
    def eta(self):
        return super().eta

    @eta.setter
    def eta(self, eta):
        self.longitudinal = LongitudinalObjectEta(eta)

    @property
    def t(self):
        return super().t

    @t.setter
    def t(self, t):
        self.temporal = TemporalObjectT(t)

    @property
    def tau(self):
        return super().tau

    @tau.setter
    def tau(self, tau):
        self.temporal = TemporalObjectTau(tau)


class MomentumObject4D(LorentzMomentum, VectorObject4D):
    ProjectionClass2D = MomentumObject2D
    ProjectionClass3D = MomentumObject3D

    def __repr__(self):
        aznames = _coordinate_class_to_names[_aztype(self)]
        lnames = _coordinate_class_to_names[_ltype(self)]
        tnames = _coordinate_class_to_names[_ttype(self)]
        out = []
        for x in aznames:
            y = _repr_generic_to_momentum.get(x, x)
            out.append(f"{y}={getattr(self.azimuthal, x)}")
        for x in lnames:
            y = _repr_generic_to_momentum.get(x, x)
            out.append(f"{y}={getattr(self.longitudinal, x)}")
        for x in tnames:
            y = _repr_generic_to_momentum.get(x, x)
            out.append(f"{y}={getattr(self.temporal, x)}")
        return "vector.obj(" + ", ".join(out) + ")"

    @property
    def px(self):
        return super().px

    @px.setter
    def px(self, px):
        self.azimuthal = AzimuthalObjectXY(px, self.py)

    @property
    def py(self):
        return super().py

    @py.setter
    def py(self, py):
        self.azimuthal = AzimuthalObjectXY(self.px, py)

    @property
    def pt(self):
        return super().pt

    @pt.setter
    def pt(self, pt):
        self.azimuthal = AzimuthalObjectRhoPhi(pt, self.phi)

    @property
    def pz(self):
        return super().pz

    @pz.setter
    def pz(self, pz):
        self.longitudinal = LongitudinalObjectZ(pz)

    @property
    def E(self):
        return super().E

    @E.setter
    def E(self, E):
        self.temporal = TemporalObjectT(E)

    @property
    def e(self):
        return super().e

    @e.setter
    def e(self, e):
        self.temporal = TemporalObjectT(e)

    @property
    def energy(self):
        return super().energy

    @energy.setter
    def energy(self, energy):
        self.temporal = TemporalObjectT(energy)

    @property
    def M(self):
        return super().M

    @M.setter
    def M(self, M):
        self.temporal = TemporalObjectTau(M)

    @property
    def m(self):
        return super().m

    @m.setter
    def m(self, m):
        self.temporal = TemporalObjectTau(m)

    @property
    def mass(self):
        return super().mass

    @mass.setter
    def mass(self, mass):
        self.temporal = TemporalObjectTau(mass)


def _gather_coordinates(planar_class, spatial_class, lorentz_class, coordinates):
    azimuthal = None
    if "x" in coordinates and "y" in coordinates:
        if "rho" in coordinates or "phi" in coordinates:
            raise TypeError("specify x= and y= or rho= and phi=, but not both")
        azimuthal = AzimuthalObjectXY(coordinates.pop("x"), coordinates.pop("y"))
    elif "rho" in coordinates and "phi" in coordinates:
        if "x" in coordinates or "y" in coordinates:
            raise TypeError("specify x= and y= or rho= and phi=, but not both")
        azimuthal = AzimuthalObjectRhoPhi(
            coordinates.pop("rho"), coordinates.pop("phi")
        )

    longitudinal = None
    if "z" in coordinates:
        if "theta" in coordinates or "eta" in coordinates:
            raise TypeError("specify z= or theta= or eta=, but not more than one")
        longitudinal = LongitudinalObjectZ(coordinates.pop("z"))
    elif "theta" in coordinates:
        if "z" in coordinates or "eta" in coordinates:
            raise TypeError("specify z= or theta= or eta=, but not more than one")
        longitudinal = LongitudinalObjectTheta(coordinates.pop("theta"))
    elif "eta" in coordinates:
        if "z" in coordinates or "theta" in coordinates:
            raise TypeError("specify z= or theta= or eta=, but not more than one")
        longitudinal = LongitudinalObjectEta(coordinates.pop("eta"))

    temporal = None
    if "t" in coordinates:
        if "tau" in coordinates:
            raise TypeError("specify t= or tau=, but not more than one")
        temporal = TemporalObjectT(coordinates.pop("t"))
    elif "tau" in coordinates:
        if "t" in coordinates:
            raise TypeError("specify t= or tau=, but not more than one")
        temporal = TemporalObjectTau(coordinates.pop("tau"))

    if len(coordinates) == 0:
        if azimuthal is not None and longitudinal is None and temporal is None:
            return planar_class(azimuthal)
        if azimuthal is not None and longitudinal is not None and temporal is None:
            return spatial_class(azimuthal, longitudinal)
        if azimuthal is not None and longitudinal is not None and temporal is not None:
            return lorentz_class(azimuthal, longitudinal, temporal)

    raise TypeError(
        "unrecognized combination of coordinates, allowed combinations are:\n\n"
        "    (2D) x= y=\n"
        "    (2D) rho= phi=\n"
        "    (3D) x= y= z=\n"
        "    (3D) x= y= theta=\n"
        "    (3D) x= y= eta=\n"
        "    (3D) rho= phi= z=\n"
        "    (3D) rho= phi= theta=\n"
        "    (3D) rho= phi= eta=\n"
        "    (4D) x= y= z= t=\n"
        "    (4D) x= y= z= tau=\n"
        "    (4D) x= y= theta= t=\n"
        "    (4D) x= y= theta= tau=\n"
        "    (4D) x= y= eta= t=\n"
        "    (4D) x= y= eta= tau=\n"
        "    (4D) rho= phi= z= t=\n"
        "    (4D) rho= phi= z= tau=\n"
        "    (4D) rho= phi= theta= t=\n"
        "    (4D) rho= phi= theta= tau=\n"
        "    (4D) rho= phi= eta= t=\n"
        "    (4D) rho= phi= eta= tau="
    )


def obj(**coordinates):
    "obj docs"
    is_momentum = False
    generic_coordinates = {}
    if "px" in coordinates:
        is_momentum = True
        generic_coordinates["x"] = coordinates.pop("px")
    if "py" in coordinates:
        is_momentum = True
        generic_coordinates["y"] = coordinates.pop("py")
    if "pt" in coordinates:
        is_momentum = True
        generic_coordinates["rho"] = coordinates.pop("pt")
    if "pz" in coordinates:
        is_momentum = True
        generic_coordinates["z"] = coordinates.pop("pz")
    if "E" in coordinates:
        is_momentum = True
        generic_coordinates["t"] = coordinates.pop("E")
    if "e" in coordinates and "t" not in generic_coordinates:
        is_momentum = True
        generic_coordinates["t"] = coordinates.pop("e")
    if "energy" in coordinates and "t" not in generic_coordinates:
        is_momentum = True
        generic_coordinates["t"] = coordinates.pop("energy")
    if "M" in coordinates:
        is_momentum = True
        generic_coordinates["tau"] = coordinates.pop("M")
    if "m" in coordinates and "tau" not in generic_coordinates:
        is_momentum = True
        generic_coordinates["tau"] = coordinates.pop("m")
    if "mass" in coordinates and "tau" not in generic_coordinates:
        is_momentum = True
        generic_coordinates["tau"] = coordinates.pop("mass")
    for x in list(coordinates):
        if x not in generic_coordinates:
            generic_coordinates[x] = coordinates.pop(x)
    if len(coordinates) != 0:
        raise TypeError(
            "duplicate coordinates (through momentum-aliases): "
            + ", ".join(repr(x) for x in coordinates)
        )
    if is_momentum:
        return _gather_coordinates(
            MomentumObject2D, MomentumObject3D, MomentumObject4D, generic_coordinates
        )
    else:
        return _gather_coordinates(
            VectorObject2D, VectorObject3D, VectorObject4D, generic_coordinates
        )
