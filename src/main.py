from vo_utils import *
from vo_visualizer import VOvisualizer
from vo_solver import VOsolver
from PIL import Image


def run_KITTI_visual_odometry(sequences_path : str, seq_name : str, seq_idx : int, 
                              gt : np.ndarray, camera_calib : np.ndarray, 
                              time_stamps : np.ndarray, 
                              preffered : int, 
                              use_scale: bool, plot_frames: bool) -> None:
    """
    Runs the visual odometry algorithm on the given sequences, and compare it to the ground truth poses.
    
    Parameters
    ----------
    sequences_path : str
        Path to the folder containing the sequences.
    poses_path : str
        Path to the file containing the ground truth poses.
    time_stamps : list
        List of time stamps of the frames
    camera_calib : np.array
        Camera calibration matrix

    """
    

    os.chdir(os.path.expanduser("~"))
    
    

    try:
        images_path = os.path.join("./" + sequences_path[1:], seq_name, 'image_0/')
        images_list = sorted(os.listdir(images_path))

        vo_v = VOvisualizer(len(images_list))
        vo_s = VOsolver(camera_calib, preffered)

        frame_count = 0
        start_time = time.time()
        start_frame = 0

        frame0 = cv2.imread(images_path + images_list[start_frame])
        frame1 = cv2.imread(images_path + images_list[start_frame+1])

        vo_s.setup(frame0, frame1, gt[start_frame])
        n_frames = len(images_list)
        prev_gt = gt[1].dot(vo_s.origin)
        for i in range(start_frame + 2, n_frames):

            frame = cv2.imread(images_path + images_list[i])
            gt_pose = gt[i]

            gt_world = gt_pose.dot(vo_s.origin)
            scale = np.linalg.norm(gt_world - prev_gt) if use_scale else None
            prev_gt = gt_world
            vo_s.run_frame(frame, scale if use_scale else None)

            pred_pose = vo_s.get_pose().dot(vo_s.origin)


            frame_count += 1
            frate = frame_count / (time.time() - start_time)
            yield frate, i, pred_pose, gt_world, scale
            # print(frame_count, frate)
            if plot_frames:
                vo_v.plot_frame(frame, i, pred_pose, gt_world, None, frate)
    except:
        os.chdir(os.path.realpath(__file__).split("src")[0] + '/src')
    os.chdir(os.path.realpath(__file__).split("src")[0] + '/src')