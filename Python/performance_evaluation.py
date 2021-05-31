import sys, math

def get_true_positives(y_true, y_bin):
    return len([yb for yt, yb in zip(y_true, y_bin) if yt and yb])

def calc_recall(y_true, y_bin):
    truePositives = get_true_positives(y_true, y_bin)
    allPositives = len([yt for yt in y_true if yt])

    return truePositives / (allPositives + sys.float_info.epsilon)

def calc_precision(y_true, y_bin):
    truePositives = get_true_positives(y_true, y_bin)
    pred_positives = len([yb for yb in y_bin if yb])

    return truePositives / (pred_positives + sys.float_info.epsilon)

def calc_f1(y_true, y_pred, threshold = 0.5):
    y_bin = [val > threshold for val in y_pred]
    
    recall = calc_recall(y_true, y_bin)
    precision = calc_precision(y_true, y_bin)
    f1 = 2*((precision * recall) / (precision + recall + sys.float_info.epsilon))

    return [recall, precision, f1]

def calc_MCC(y_true, y_pred, threshold):
    y_bin = [val > threshold for val in y_pred]

    tp = tn = fp = fn = 0

    for yt, yb in zip(y_true, y_bin):
        tp += yt and yb
        fn += yt and not yb
        fp += not yt and yb
        tn += not yt and not yb

    return (tp * tn - fp * fn) / (math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)) + sys.float_info.epsilon)