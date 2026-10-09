import csv
import pytest
from backend.evaluation.metrics import evaluate,export_predictions

def test_metrics_and_export(tmp_path):
    # Hand-authored unit fixture verifies arithmetic only; not a benchmark.
    result=evaluate(['ang','neu','sad'],['ang','neu','neu'])
    assert result['accuracy']==pytest.approx(2/3)
    assert len(result['confusion_matrix'])==3
    path=tmp_path/'labels.csv'
    export_predictions(str(path),['ang','sad'],['ang','neu'],'test-fixture')
    with path.open() as file: rows=list(csv.DictReader(file))
    assert rows[1]=={'ground_truth':'sad','prediction':'neu','model':'test-fixture'}
    with pytest.raises(ValueError):evaluate([],[])
