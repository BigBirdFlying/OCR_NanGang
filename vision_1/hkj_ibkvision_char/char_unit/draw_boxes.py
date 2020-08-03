import cv2
import numpy as np

def nms(boxes, scores, thresh):
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]

    order = scores.argsort()[::-1]
    areas = (x2 - x1 + 1) * (y2 - y1 + 1)

    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)

        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1 + 1)
        h = np.maximum(0.0, yy2 - yy1 + 1)
        inter = w * h

        ovr = inter / (areas[i] + areas[order[1:]] - inter)

        inds = np.where(ovr < thresh)[0]
        order = order[inds + 1]

    return keep

def draw_boxes(image, boxes, scores, labels, colors, classes):
    for b, l, s in zip(boxes, labels, scores):
        class_id = int(l)
        class_name = classes[class_id]
    
        xmin, ymin, xmax, ymax = list(map(int, b))
        score = '{:.4f}'.format(s)
        color = colors[class_id]
        # label = '-'.join([class_name, score])
        label = class_name
    
        ret, baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)#0.5
        cv2.rectangle(image, (xmin, ymin), (xmax, ymax), color, 1)#2
        #cv2.rectangle(image, (xmin, ymax - ret[1] - baseline), (xmin + ret[0], ymax), color, -1)
        cv2.rectangle(image, (xmin, ymax), (xmin + ret[0], ymax + ret[1] + baseline), color, -1)
        #cv2.putText(image, label, (xmin, ymax - baseline), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)#0.5
        cv2.putText(image, label, (xmin, ymax + ret[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)#0.5
