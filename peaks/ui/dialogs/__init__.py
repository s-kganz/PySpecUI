from .detrend import (
    PolynomialBaselineDialog,
    BoxcarSmoothDialog,
    TriangleSmoothDialog,
    GaussianSmoothDialog,
    SavgolSmoothDialog,
    RollingBallDialog
)

from .io import (
    SingleFileLoadDialog
)

from .model import (
    GaussModelDialog
)

from .transform import (
    RescaleDialog,
    ToAbsorbanceDialog,
    ToTransmittanceDialog
)

from kivy.factory import Factory

Factory.register('PolynomialBaselineDialog', cls=PolynomialBaselineDialog)
Factory.register('BoxcarSmoothDialog', cls=BoxcarSmoothDialog)
Factory.register('TriangleSmoothDialog', cls=TriangleSmoothDialog)
Factory.register('GaussianSmoothDialog', cls=GaussianSmoothDialog)
Factory.register('SingleFileLoadDialog', cls=SingleFileLoadDialog)
Factory.register('GaussModelDialog', cls=GaussModelDialog)
Factory.register('RescaleDialog', cls=RescaleDialog)
Factory.register('ToAbsorbanceDialog', cls=ToAbsorbanceDialog)
Factory.register('ToTransmittanceDialog', cls=ToTransmittanceDialog)
Factory.register('SavgolSmoothDialog', cls=SavgolSmoothDialog)
Factory.register('RollingBallDialog', cls=RollingBallDialog)