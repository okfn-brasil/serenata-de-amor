from jarbas.chamber_of_deputies.models import (
    Reimbursement as ChamberOfDeputiesReimbursement,
    ReimbursementSummary,
)

from jarbas.federal_senate.models import (
    Reimbursement as FederalSenateReimbursement,
)
from jarbas.dashboard.admin.chamber_of_deputies import (
    ChamberOfDeputiesReimbursementModelAdmin,
    ReimbursementSummaryModelAdmin
)
from jarbas.dashboard.admin.federal_senate import (
    FederalSenateReimbursementModelAdmin,
)
from jarbas.public_admin.sites import public_admin

public_admin.register(
    ChamberOfDeputiesReimbursement,
    ChamberOfDeputiesReimbursementModelAdmin
)
public_admin.register(
    FederalSenateReimbursement,
    FederalSenateReimbursementModelAdmin
)
public_admin.register(ReimbursementSummary, ReimbursementSummaryModelAdmin)
