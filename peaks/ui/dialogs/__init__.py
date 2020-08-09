from .detrend import (
    PolynomialBaselineDialog, 
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
Factory.register('SingleFileLoadDialog', cls=SingleFileLoadDialog)
Factory.register('GaussModelDialog', cls=GaussModelDialog)
Factory.register('RescaleDialog', cls=RescaleDialog)
Factory.register('ToAbsorbanceDialog', cls=ToAbsorbanceDialog)
Factory.register('ToTransmittanceDialog', cls=ToTransmittanceDialog)