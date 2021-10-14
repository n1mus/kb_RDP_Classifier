from pytest import raises

from kb_RDP_Classifier.util.debug import dprint
from kb_RDP_Classifier.util.misc import get_numbered_duplicate
from kb_RDP_Classifier.util.cli import run_check, NonZeroReturnException


####################################################################################################
####################################################################################################
def test_run_check():
    with raises(NonZeroReturnException, match='`127`'):
        run_check('set -o pipefail && tmp |& tee tmp')

    with raises(NonZeroReturnException, match='`127`'):
        run_check('set -o pipefail && echo hi |& tmp')

    run_check('set -o pipefail && echo hi |& tee tmp')  # run correctly


####################################################################################################
####################################################################################################
def test_get_numbered_duplicate():
    # test numbering system
    q = 'the_attr'
    names = ['null']
    assert get_numbered_duplicate(names, q) == 'the_attr'
    names = ['the_attr']
    assert get_numbered_duplicate(names, q) == 'the_attr (1)'
    names = ['the_attr', 'the_attr (1)', 'the_attr (2)']
    assert get_numbered_duplicate(names, q) == 'the_attr (3)', get_numbered_duplicate(names, q)
    names = ['the_attr (1)', 'the_attr (2)']
    assert get_numbered_duplicate(names, q) == 'the_attr'
    names = ['the_attr', 'the_attr (1)', 'the_attr (5)']
    assert get_numbered_duplicate(names, q) == 'the_attr (2)'
    names = ['the_attr (0)', 'the_attr (1)', 'the_attr (2)']
    assert get_numbered_duplicate(names, q) == 'the_attr'
    names = ['the_attr (-1)', 'the_attr (1)', 'the_attr (2)']
    assert get_numbered_duplicate(names, q) == 'the_attr'

    # test internal regexing
    q = 'the[0-9]_attr'
    names = [q]
    assert get_numbered_duplicate(names, q) == q + ' (1)'
