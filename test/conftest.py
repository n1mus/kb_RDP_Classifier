import pytest

from kb_RDP_Classifier.util.debug import dprint
from kb_RDP_Classifier.impl.globals import Var, reset_Var
from kb_RDP_Classifier.impl import app_file


@pytest.fixture(autouse=True) # TODO selectively disable
def tear_down():
    yield
    reset_Var()
    app_file._get_fixRank.cache_clear()

