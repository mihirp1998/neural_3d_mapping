import numpy as np
from scipy.spatial import ConvexHull
# some funcs from https://github.com/charlesq34/frustum-pointnets/blob/master/train/box_util.py

def polygon_clip(subjectPolygon, clipPolygon):
   """ Clip a polygon with another polygon.

   Ref: https://rosettacode.org/wiki/Sutherland-Hodgman_polygon_clipping#Python

   Args:
     subjectPolygon: a list of (x,y) 2d points, any polygon.
     clipPolygon: a list of (x,y) 2d points, has to be *convex*
   Note:
     **points have to be counter-clockwise ordered**

   Return:
     a list of (x,y) vertex point for the intersection polygon.
   """
   def inside(p):
      return(cp2[0]-cp1[0])*(p[1]-cp1[1]) > (cp2[1]-cp1[1])*(p[0]-cp1[0])
 
   def computeIntersection():
      dc = [ cp1[0] - cp2[0], cp1[1] - cp2[1] ]
      dp = [ s[0] - e[0], s[1] - e[1] ]
      n1 = cp1[0] * cp2[1] - cp1[1] * cp2[0]
      n2 = s[0] * e[1] - s[1] * e[0] 
      n3 = 1.0 / (dc[0] * dp[1] - dc[1] * dp[0])
      return [(n1*dp[0] - n2*dc[0]) * n3, (n1*dp[1] - n2*dc[1]) * n3]
 
   outputList = subjectPolygon
   cp1 = clipPolygon[-1]
 
   for clipVertex in clipPolygon:
      cp2 = clipVertex
      inputList = outputList
      outputList = []
      s = inputList[-1]
 
      for subjectVertex in inputList:
         e = subjectVertex
         if inside(e):
            if not inside(s):
               outputList.append(computeIntersection())
            outputList.append(e)
         elif inside(s):
            outputList.append(computeIntersection())
         s = e
      cp1 = cp2
      if len(outputList) == 0:
          return None
   return(outputList)

def box3d_vol(corners):
    ''' corners: (8,3) no assumption on axis direction '''
    a = np.sqrt(np.sum((corners[0,:] - corners[1,:])**2))
    b = np.sqrt(np.sum((corners[1,:] - corners[2,:])**2))
    c = np.sqrt(np.sum((corners[0,:] - corners[4,:])**2))
    return a*b*c

def poly_area(x,y):
    """ Ref: http://stackoverflow.com/questions/24467972/calculate-area-of-polygon-given-x-y-coordinates """
    return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))

def convex_hull_intersection(p1, p2):
    """ Compute area of two convex hull's intersection area.
        p1,p2 are a list of (x,y) tuples of hull vertices.
        return a list of (x,y) for the intersection and its volume
    """
    inter_p = polygon_clip(p1,p2)
    if inter_p is not None and not np.isnan(inter_p).any(): 
       hull_inter = ConvexHull(inter_p)
       return inter_p, hull_inter.volume
    else:
       return None, 0.0
    
def box3d_iou(corners1, corners2):
    ''' Compute 3D bounding box IoU.

    Input:
        corners1: numpy array (8,3), assume up direction is negative Y
        corners2: numpy array (8,3), assume up direction is negative Y
    Output:
        iou: 3D bounding box IoU
        iou_2d: bird's eye view 2D bounding box IoU

    todo (rqi): add more description on corner points' orders.
    '''
    rect1 = [(corners1[i,0], corners1[i,2]) for i in list(range(3,-1,-1))]
    rect2 = [(corners2[i,0], corners2[i,2]) for i in list(range(3,-1,-1))]

    def get_iou_2d(rect1, rect2):
       # this func only works properly when the points are in counter-clockwise order
       area1 = poly_area(np.array(rect1)[:,0], np.array(rect1)[:,1])
       area2 = poly_area(np.array(rect2)[:,0], np.array(rect2)[:,1])
       # print('rect1', rect1)
       # print('rect2', rect2)
       # print('area1', area1)
       # print('area2', area2)
       # if np.isnan(rect1).any() or np.isnan(rect2).any() or np.isclose(area1, 0) or np.isclose(area2, 0):
       #    iou_2d = 0.00
       #    inter_area = 0.00001
       # else:
       inter, inter_area = convex_hull_intersection(rect1, rect2)
       iou_2d = inter_area/(area1+area2-inter_area)
       return iou_2d, inter_area

    # it's hard to guarantee the corners are counter-clockwise,
    # so let's just compute both ways and take the winner
    iou_2d_a, inter_area_a = get_iou_2d(rect1, rect2)
    iou_2d_b, inter_area_b = get_iou_2d(rect1[::-1], rect2[::-1])
    # the wrong way will return near zero for iou_2d
    if iou_2d_a > iou_2d_b:
       iou_2d = iou_2d_a
       inter_area = inter_area_a
    else:
       iou_2d = iou_2d_b
       inter_area = inter_area_b
    ymax = min(corners1[0,1], corners2[0,1])
    ymin = max(corners1[4,1], corners2[4,1])
    inter_vol = inter_area * max(0.0, ymax-ymin)
    vol1 = box3d_vol(corners1)
    vol2 = box3d_vol(corners2)
    iou = inter_vol / (vol1 + vol2 - inter_vol)
    return iou, iou_2d


def boxlist_2d_iou(boxlist1, boxlist2):
   '''
      Input:
      [boxlist1, boxlist2]: N x 4 each, or B x N x 4
      Ordering: ymin, xmin, ymax, xmax

      Output:
      [IoUs]: N x 1 or B x N x 1
   '''
   assert len(boxlist1.shape) == len(boxlist2.shape)
   batched = None
   if len(boxlist1.shape) == 3:
      batched = True
      B1, N1, D1 = boxlist1.shape 
      B2, N2, D2 = boxlist2.shape
      assert B1 == B2 and N1 == N2 and D1 == D2 and D1 == 4
      boxlist1_ = boxlist1.reshape((B1*N1, D1))
      boxlist2_ = boxlist2.reshape((B2*N2, D2))
   else:
      batched = False
      boxlist1_, boxlist2_ = boxlist1, boxlist2

   # Now we can assume boxlists are M x 4
   ymin1, xmin1, ymax1, xmax1 = np.split(boxlist1_, 4, axis=1)
   ymin2, xmin2, ymax2, xmax2 = np.split(boxlist2_, 4, axis=1)

   # Find the intersection first
   xmin = np.maximum(xmin1, xmin2)
   xmax = np.minimum(xmax1, xmax2)
   ymin = np.maximum(ymin1, ymin2)
   ymax = np.minimum(ymax1, ymax2)

   widths = xmax - xmin
   heights = ymax - ymin
   # Handle case where there is NO overlap
   widths[widths < 0] = 0
   heights[heights < 0] = 0
   # intersection area
   inter_area = widths * heights

   # Now comes the union
   areas1 = (xmax1 - xmin1) * (ymax1 - ymin1)
   areas2 = (xmax2 - xmin2) * (ymax2 - ymin2)
   union_area = areas1 + areas2 - inter_area

   # Finally, get the IoUs
   IoUs = inter_area / union_area
   # Take back to the original shapes
   if batched:
      IoUs = IoUs.reshape((B1,N1,1))
   return IoUs

if __name__ == '__main__':
   b1, b2 = np.array([[0,0,2,2]]), np.array([[0,3,2,5]]) # next to each other 0.0
   b1, b2 = np.array([[0,0,2,2]]), np.array([[3,0,5,2]]) # below each other 0.0
   b1, b2 = np.array([[0,0,2,2]]), np.array([[0,2,2,5]]) # next to each other 0.0
   b1, b2 = np.array([[0,0,2,2]]), np.array([[2,0,5,2]]) # below each other 0.0
   b1, b2 = np.array([[0,0,2,2]]), np.array([[1,1,3,3]]) # 0.14285714285714285
   b1, b2 = np.array([[0,0,4,4]]), np.array([[1,1,3,3]]) # contained 0.25
   b1, b2 = np.array([[0,0,4,4]]), np.array([[0,0,4,4]]) # identical 1.0
   b1, b2 = np.array([[0,0,2,2]]), np.array([[0,1,2,3]]) # side overlaps 0.33
   b1, b2 = np.array([[0,0,2,2]]), np.array([[1,0,3,2]]) # side overlaps 0.33
   print(boxlist_2d_iou(b1, b2))

   b1 = np.array([[0,0,2,2], [0,0,2,2], [0,0,2,2], [0,0,2,2], [0,0,2,2], [0,0,4,4], [0,0,4,4], [0,0,2,2], [0,0,2,2]])
   b2 = np.array([[0,3,2,5], [3,0,5,2], [0,2,2,5], [2,0,5,2], [1,1,3,3], [1,1,3,3], [0,0,4,4], [0,1,2,3], [1,0,3,2]])
   print(boxlist_2d_iou(b1, b2))

   b1 = np.array([[0,0,2,2], [0,0,2,2], [0,0,2,2], [0,0,2,2], [0,0,2,2], [0,0,4,4], [0,0,4,4], [0,0,2,2], [0,0,2,2]]).reshape((3,3,4))
   b2 = np.array([[0,3,2,5], [3,0,5,2], [0,2,2,5], [2,0,5,2], [1,1,3,3], [1,1,3,3], [0,0,4,4], [0,1,2,3], [1,0,3,2]]).reshape((3,3,4))

   b1 = np.array([[0,0,2,2], [0,0,2,2], [0,0,2,2], [0,0,2,2], [0,0,4,4], [0,0,4,4], [0,0,2,2], [0,0,2,2]]).reshape((2,4,4))
   b2 = np.array([[3,0,5,2], [0,2,2,5], [2,0,5,2], [1,1,3,3], [1,1,3,3], [0,0,4,4], [0,1,2,3], [1,0,3,2]]).reshape((2,4,4))

   b1 = np.array([[0,0,2,2], [0,0,2,2], [0,0,2,2], [0,0,2,2], [0,0,4,4], [0,0,4,4], [0,0,2,2], [0,0,2,2]]).reshape((4,2,4))
   b2 = np.array([[3,0,5,2], [0,2,2,5], [2,0,5,2], [1,1,3,3], [1,1,3,3], [0,0,4,4], [0,1,2,3], [1,0,3,2]]).reshape((4,2,4))
   print(boxlist_2d_iou(b1, b2))
