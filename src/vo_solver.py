from vo_utils import *


class VOsolver:
    def __init__(self, camera_calib : np.ndarray, preferred : int) -> None:
        self.camera_calib           = camera_calib.copy()
        self.detector               = cv2.ORB_create(3500)
        self.frame0, self.frame1    = None, None
        self.points0, self.points1  = None, None
        self.kpoints0,self.kpoints1 = None, None
        self.tracker                = self.__tracker
        self.R, self.t              = None, None
        self.FEATLIMIT              = 2000  
        self.origin                 = np.array([0, 0, 0, 1])
        self.preferred              = preferred

        FLANN_INDEX_LSH             = 6
        index_params                = {
                                        "algorithm"         : FLANN_INDEX_LSH, 
                                        "table_number"      : 6, 
                                        "key_size"          : 12, 
                                        "multi_probe_level" : 1
                                      }
        search_params               = {"checks" : 50}
        self.flann                  = cv2.FlannBasedMatcher(indexParams = index_params, searchParams = search_params)
    
    def setup(self, frame0, frame1, initial_pose):
        self.frame0 = frame0
        self.frame1 = frame1

        self.kpoints0 = self.detector.detectAndCompute(frame0, None)
        self.kpoints1 = self.detector.detectAndCompute(frame1, None)

        self.points0, self.points1 = self.tracker(frame0, frame1, self.kpoints0, self.kpoints1)

        E_mat, E_mask = self.__compute_essential_matrix()
                                         
        good, self.R, self.t, P_mask, self.triangulated = self.__recover_pose(E_mat, E_mask)
        P_mask = P_mask.flatten()
        self.points0 = self.points1
        self.frame0  = self.frame1
        self.cur_pose = initial_pose
        self.cur_pose = self.get_pose()

    def run_frame(self, frame, scale = None):

        self.frame1 = frame
        self.kpoints1 = self.detector.detectAndCompute(self.frame1, None)
        self.points0, self.points1 = self.tracker(self.frame0, self.frame1, self.kpoints0, self.kpoints1)

        E_mat, E_mask = self.__compute_essential_matrix()

        good, fR, ft, P_mask, triangulated = self.__recover_pose(E_mat, E_mask)
        P_mask = P_mask.flatten()
        if scale is None:
            scale = self.__compute_ratio(triangulated)
        self.triangulated = triangulated
        if self.preferred == -1 or abs(ft[self.preferred][0]) == max(abs(ft[:, 0])) and scale > 0.1:
            self.t = scale * ft
            self.R = fR

        self.cur_pose = self.get_pose()
        self.kpoints0 = self.kpoints1
        self.frame0  = self.frame1

        if len(self.points1) < self.FEATLIMIT:
            self.kpoints0 = self.detector.detectAndCompute(self.frame0, None)

    def get_pose(self):
        T = self.__get_T()
        return np.matmul(self.cur_pose, T)
    def __get_T(self):
        T = np.eye(4, dtype=np.float64)
        T[:3, :3] = self.R
        T[:3, 3]  = self.t.flatten()
        return T
    def __compute_ratio(self, triangulated0):
        
        triangulated1 = self.__get_T() @ triangulated0
        T0 = triangulated0[:3, :] / triangulated1[3, :]
        T1 = triangulated1[:3, :] / triangulated1[3, :]  
        
        r = np.mean(np.linalg.norm(T0.T[:-1] - T0.T[1:], axis=-1) /
                    np.linalg.norm(T1.T[:-1] - T1.T[1:], axis=-1))
        return r
        
    def __compute_essential_matrix(self):
        return cv2.findEssentialMat(self.points1, self.points0, 
                                    cameraMatrix = self.camera_calib, 
                                    method = cv2.RANSAC, prob = 0.9999, threshold = 1.0)

    def __recover_pose(self, E_mat, E_mask):
        return cv2.recoverPose( E_mat, self.points1, self.points0, 
                                cameraMatrix = self.camera_calib, 
                                distanceThresh = 500.0, mask = E_mask )

    def __tracker(self, frame0, frame1, points0, points1):

        # lk_params = dict(winSize  = (15, 15), maxLevel = 3, criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01))


        # p0 = np.array([p.pt for p in points0[0]], dtype = np.float32)
        # p1, status, err = cv2.calcOpticalFlowPyrLK(frame0, frame1, p0, None, **lk_params)
        # status  = status.reshape(status.shape[0])
        # p0 = p0[status == 1]
        # p1 = p1[status == 1]

        keypoints0, descriptors0 = points0
        keypoints1, descriptors1 = points1

        matches = self.flann.knnMatch(descriptors0, descriptors1, k = 2)
        good = []
        for m,n in matches:
            if m.distance < 0.5 * n.distance:
                good.append(m)

        p0 = np.array([ keypoints0[m.queryIdx].pt for m in good ])
        p1 = np.array([ keypoints1[m.trainIdx].pt for m in good ])

        return p0, p1

    