import csv
from pathlib import Path
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, classification_report

def evaluate(ground_truth: list[str], predictions: list[str]) -> dict:
    if not ground_truth or len(ground_truth) != len(predictions): raise ValueError('Provide equally sized nonempty labeled lists')
    labels = sorted(set(ground_truth) | set(predictions))
    precision, recall, macro_f1, _ = precision_recall_fscore_support(ground_truth, predictions, average='macro', zero_division=0)
    return {'accuracy': accuracy_score(ground_truth, predictions), 'macro_f1': macro_f1,
        'weighted_f1': precision_recall_fscore_support(ground_truth, predictions, average='weighted', zero_division=0)[2],
        'precision_macro': precision, 'recall_macro': recall, 'labels': labels,
        'confusion_matrix': confusion_matrix(ground_truth, predictions, labels=labels).tolist(),
        'classification_report': classification_report(ground_truth, predictions, zero_division=0, output_dict=True)}

def export_predictions(path: str, ground_truth: list[str], predictions: list[str], model: str):
    if len(ground_truth) != len(predictions): raise ValueError('Label lengths differ')
    with Path(path).open('w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['ground_truth', 'prediction', 'model'])
        writer.writerows((truth, pred, model) for truth, pred in zip(ground_truth, predictions))
