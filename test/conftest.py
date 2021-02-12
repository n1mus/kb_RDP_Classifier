import pytest

from kb_RDP_Classifier.util.debug import dprint
from kb_RDP_Classifier.impl import app_file


@pytest.fixture(autouse=True) # TODO selectively disable
def cache_clear():
    yield
    dprint('teardown: cache_clear fixture', run=None)
    app_file._get_fixRank.cache_clear()

