from vo_utils import *


# Whiteboard to plot the predicted and ground truth poses
class VOvisualizer:
    def __init__(self, total : int = 1000):
        self.whiteboard     = np.full((600, 600, 3), 255, dtype=np.uint8)                          

        self.font           = cv2.FONT_HERSHEY_PLAIN                                            # Font to write the text on the whiteboard
        self.text           = "{} : x = {:0.2f}m y = {:0.2f}m z = {:0.2f}m"                     # Text to write the pose on the whiteboard

        self.p_text_pos     = (20, 40)                                                          # Position of the predicted pose text on the whiteboard
        self.gt_text_pos    = (20, 60)                                                          # Position of the ground truth pose text on the whiteboard
        self.time_text_pos  = (20, 20)                                                          # Position of the time text on the whiteboard

        self.txt_color      = (0, 0, 0)                                                         # Color of the text on the whiteboard
        self.p_color        = (0, 0, 255)                                                       # Color of the predicted pose point on the whiteboard
        self.gt_color       = (0, 255, 0)                                                       # Color of the ground truth pose point on the whiteboard
        self.point_radius   = 1                                                                 # Radius (pixels) of the predicted and ground truth pose points on the whiteboard

        self.text_size      = 1                                                                 # Size (pixels) of the predicted pose text on the whiteboard
        self.pose_scale     = 0.5                                                               # Size (pixels / m) of the predicted pose point on the whiteboard

        self.origin         = (300, 450)                                                        # Origin of the whiteboard
        self.total_imgs     = total                                                             # Total number of images plotted
        cv2.rectangle(self.whiteboard, 
                     (self.origin[0] - 5, self.origin[1] + 5), (self.origin[0] + 5, self.origin[1] - 5),  
                      (0, 0, 0), 2)                                                             # Draw the origin on the whiteboard

    def plot_frame(self, frame: np.ndarray, img_id: int, p_pose: np.ndarray, gt_pose: np.ndarray, features : np.ndarray, frate : int = -1) -> None:
        """
        Plots the predicted and ground truth poses on the whiteboard.

        Parameters
        ----------
        frame : np.ndarray
            Frame to plot the poses on.
        img_id : int
            ID of the frame.
        p_pose : np.ndarray
            Predicted pose (x, y, z) to plot.
        gt_pose : np.ndarray
            Ground truth pose (x, y, z) to plot.
        frate : int
            Estimated frame rate

        """
        self.__draw_pose(p_pose, 'pred')
        self.__draw_pose(gt_pose, 'gt')
        self.__show(frame, img_id, features, frate)
        
    
    def __show(self, frame: np.ndarray, img_id: int, features: np.ndarray, frate: int) -> None:

        if frame is not None:
            frame = cv2.resize(frame, (600, 600))
            if features is not None:
                for feature in features:
                    cv2.circle(frame, (int(feature[1]), int(feature[0])), 2, (0, 0, 255), -1)
            cv2.imshow('Frame', frame)

        cv2.putText(self.whiteboard, 'Framerate {}, Frame {} / {}'.format(int(frate), img_id, self.total_imgs), 
                    self.time_text_pos, self.font, self.text_size, self.txt_color, 1, cv2.LINE_AA)
        cv2.imshow('Whiteboard', self.whiteboard)
        self.__reset_whiteboard_txt()
        key = cv2.waitKey(1)
        if key == ord('q'):
            cv2.destroyAllWindows()
            sys.exit()
        
    def __reset_whiteboard_txt(self) -> None:
        self.whiteboard[0:80] = 255

    def __draw_pose(self, pose: np.ndarray, pose_type: str, put_text = True) -> None:

        if pose_type == 'pred':
            text_pos = self.p_text_pos
            color = self.p_color
        elif pose_type == 'gt':
            text_pos = self.gt_text_pos
            color = self.gt_color
        else:
            raise ValueError('Invalid pose type')
        
        text = self.text.format(pose_type, pose[0], pose[1], pose[2])
        color = self.__depth_adjust(pose[1], color)
        invcolor = (255 - color[0], 255 - color[1], 255 - color[2])
        cv2.circle(self.whiteboard, self.__pose_to_pixel(pose), self.point_radius, color, -1)
        cv2.putText(self.whiteboard, text, text_pos, self.font, self.text_size, self.txt_color, 1, cv2.LINE_AA)

    def __pose_to_pixel(self, pose: np.ndarray) -> tuple:
        """
        Converts a pose (x, y, z) to a pixel (x, y) on the whiteboard.

        Parameters
        ----------
        pose : np.ndarray
            Pose (x, y, z) to convert.
        
        Returns
        -------
        tuple
            Pixel (x, y) on the whiteboard.

        """
        x = int(self.origin[0] + pose[0] * self.pose_scale)
        y = int(self.origin[1] - pose[2] * self.pose_scale)
        return (x, y)
    
    def __depth_adjust(self, y : float,  color : tuple) -> tuple:
        """
        Adjusts the colour of the pose point color based on its depth.

        Parameters
        ----------
        pixel : np.ndarray
            Pixel to adjust the colour of.
        
        Returns
        -------
        np.ndarray
            Pixel with adjusted colour.

        """
        color = np.array(color)
        h     = 255/(1 + np.exp(-y/30))                                 # Sigmoid. 
        H     = np.array([[i] for i in range(256)], dtype=np.uint8)
        Hout  = cv2.applyColorMap(H, cv2.COLORMAP_BONE)
        color = Hout[int(h)][0] * color / 255
        return (int(color[0]), int(color[1]), int(color[2]))