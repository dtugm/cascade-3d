import numpy as np

def add_vote(vote_label_pool, point_idx, pred_label, weight):
    B = pred_label.shape[0]
    N = pred_label.shape[1]
    for b in range(B):
        for n in range(N):
            if weight[b, n] != 0 and not np.isinf(weight[b, n]):
                if int(pred_label[b, n]) < vote_label_pool.shape[1]:
                    vote_label_pool[int(point_idx[b, n]), int(pred_label[b, n])] += 1
                else:
                    print(f"Warning: Predicted label {int(pred_label[b, n])} is out of bounds for the current class range.")
    return vote_label_pool