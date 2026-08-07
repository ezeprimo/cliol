"""Unit tests for constants derived from py_iol and the choice normalizer."""

from cliol.constants import (
    COUNTRIES,
    CPD_SEGMENTS,
    CPD_STATES,
    MARKETS,
    OPERATION_STATES,
    SETTLEMENT_TERMS,
    normalize_choice,
)


def _pyiol_values(cls):
    """Extract string constant values from a py_iol class, excluding dunders and docstrings."""
    return sorted(
        v
        for k, v in vars(cls).items()
        if isinstance(v, str) and not k.startswith("__") and " " not in v
    )


def test_markets_derived_from_pyiol_constants():
    from pyIol import Markets

    expected = _pyiol_values(Markets)
    assert sorted(set(MARKETS)) == expected
    assert "bCBA" in MARKETS
    assert "nYSE" in MARKETS


def test_settlement_terms_derived():
    from pyIol import SettlementTerms

    expected = _pyiol_values(SettlementTerms)
    assert sorted(set(SETTLEMENT_TERMS)) == expected
    assert SETTLEMENT_TERMS == ["t0", "t1", "t2", "t3"]


def test_countries_derived():
    from pyIol import Countries

    expected = _pyiol_values(Countries)
    assert sorted(set(COUNTRIES)) == expected


def test_cpd_states_and_segments_derived():
    from pyIol import CPDSegments, CPDStates

    assert sorted(set(CPD_STATES)) == _pyiol_values(CPDStates)
    assert sorted(set(CPD_SEGMENTS)) == _pyiol_values(CPDSegments)
    assert "vigentes" in CPD_STATES
    assert "avalados" in CPD_SEGMENTS


def test_operation_states_derived():
    from pyIol import OperationStates

    assert sorted(set(OPERATION_STATES)) == _pyiol_values(OperationStates)
    assert "pendientes" in OPERATION_STATES


def test_normalize_choice_case_insensitive():
    assert normalize_choice("nyse", MARKETS) == "nYSE"
    assert normalize_choice("T2", SETTLEMENT_TERMS) == "t2"
    assert normalize_choice("BCBA", MARKETS) == "bCBA"


def test_normalize_choice_returns_none_for_unknown():
    assert normalize_choice("INVALIDO", MARKETS) is None
    assert normalize_choice("t5", SETTLEMENT_TERMS) is None
    assert normalize_choice("", MARKETS) is None
