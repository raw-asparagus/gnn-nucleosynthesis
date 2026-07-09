"""Schema tests for the reaction-disposition document (Step 4, Task 1)."""

import pytest

from gnn_nucleo.crosscheck import diff_inventories, validate_disposition


def _mesa_rec(key, source="reaclib_forward", **kw):
    rec = {
        "mesa_handle": f"r_{key}",
        "key": key,
        "pair_key": key,
        "source": source,
        "is_weak": source.startswith("weak"),
        "q_mev": 1.0,
        "qneu_mev": 0.0,
    }
    rec.update(kw)
    return rec


def _pyna_rec(key, *, tabular=False, weak=False, inverse=False, label="ths8"):
    return {
        "fname": f"f_{key}",
        "key": key,
        "pair_key": key,
        "q_mev": 1.0,
        "is_weak": weak,
        "is_tabular": tabular,
        "derived_from_inverse": inverse,
        "source_label": label,
    }


class TestDiff:
    def test_partition_is_exact(self):
        mesa = [_mesa_rec("a"), _mesa_rec("b"), _mesa_rec("m_only")]
        pyna = [_pyna_rec("a"), _pyna_rec("b"), _pyna_rec("p_only")]
        doc = diff_inventories(mesa, pyna, "toy")
        assert doc["tallies"] == {
            "MATCHED_CLEAN": 2,
            "MATCHED_DIFF_PROVENANCE": 0,
            "MESA_ONLY": 1,
            "PYNA_ONLY": 1,
        }
        validate_disposition(doc)  # must not raise

    def test_construction_mismatch_flags_provenance(self):
        mesa = [_mesa_rec("a", source="reaclib_reverse")]
        pyna = [_pyna_rec("a", inverse=False)]
        doc = diff_inventories(mesa, pyna, "toy")
        assert doc["tallies"]["MATCHED_DIFF_PROVENANCE"] == 1
        assert "construction" in doc["entries"][0]["notes"][0]

    def test_weak_table_mismatch_flags_provenance(self):
        mesa = [
            _mesa_rec("w", source="weaklib", weak_table_source="LMP"),
        ]
        pyna = [_pyna_rec("w", tabular=True, weak=True, label="suzuki")]
        doc = diff_inventories(mesa, pyna, "toy")
        assert doc["tallies"]["MATCHED_DIFF_PROVENANCE"] == 1
        assert any("weak table" in n for n in doc["entries"][0]["notes"])

    def test_weak_table_match_is_clean(self):
        mesa = [
            _mesa_rec("w", source="weaklib", weak_table_source="LMP"),
        ]
        pyna = [_pyna_rec("w", tabular=True, weak=True, label="langanke")]
        doc = diff_inventories(mesa, pyna, "toy")
        assert doc["tallies"]["MATCHED_CLEAN"] == 1


class TestValidator:
    def test_rejects_bad_disposition(self):
        doc = diff_inventories([_mesa_rec("a")], [_pyna_rec("a")], "toy")
        doc["entries"][0]["disposition"] = "MAYBE"
        with pytest.raises(ValueError):
            validate_disposition(doc)

    def test_rejects_tally_mismatch(self):
        doc = diff_inventories([_mesa_rec("a")], [_pyna_rec("a")], "toy")
        doc["tallies"]["MESA_ONLY"] = 5
        with pytest.raises(ValueError):
            validate_disposition(doc)

    def test_rejects_duplicate_keys(self):
        doc = diff_inventories([_mesa_rec("a")], [_pyna_rec("a")], "toy")
        doc["entries"].append(dict(doc["entries"][0]))
        doc["tallies"]["MATCHED_CLEAN"] = 2
        with pytest.raises(ValueError):
            validate_disposition(doc)
