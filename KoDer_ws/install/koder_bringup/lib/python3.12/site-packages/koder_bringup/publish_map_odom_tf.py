#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped, TransformStamped
from tf2_ros import TransformBroadcaster
import math
import tf_transformations

class MapOdomTFPublisher(Node):
    def __init__(self):
        super().__init__('map_odom_tf_publisher')
        
        self.tf_broadcaster = TransformBroadcaster(self)
        
        # Subscribe to AMCL's pose estimate
        self.subscription = self.create_subscription(
            PoseWithCovarianceStamped,
            '/amcl_pose',
            self.amcl_pose_callback,
            10
        )
        
        # Subscribe to odometry to get odom→base_footprint
        self.odom_subscription = self.create_subscription(
            PoseWithCovarianceStamped,  # or Odometry if needed
            '/odometry/filtered',  # EKF output
            self.odom_callback,
            10
        )
        
        # Timer to publish TF at 20 Hz
        self.timer = self.create_timer(0.05, self.publish_tf)
        
        # Store latest poses
        self.latest_amcl_pose = None  # map → base_footprint (from AMCL)
        self.latest_odom_pose = None  # odom → base_footprint (from EKF)
        
        self.get_logger().info('Map->Odom TF publisher started')
    
    def amcl_pose_callback(self, msg):
        """Store AMCL's estimate of robot pose in map frame"""
        self.latest_amcl_pose = msg.pose.pose
    
    def odom_callback(self, msg):
        """Store odometry estimate of robot pose in odom frame"""
        self.latest_odom_pose = msg.pose.pose
    
    def publish_tf(self):
        """
        Publish map→odom transform
        
        Relationship: map → odom → base_footprint
        
        AMCL gives us: map → base_footprint (latest_amcl_pose)
        EKF gives us:  odom → base_footprint (latest_odom_pose)
        
        We need to compute: map → odom
        
        Transform algebra:
        map_T_base = map_T_odom * odom_T_base
        Therefore:
        map_T_odom = map_T_base * inv(odom_T_base)
        """
        
        if self.latest_amcl_pose is None or self.latest_odom_pose is None:
            # No poses yet, publish identity (but this should resolve quickly)
            t = TransformStamped()
            t.header.stamp = self.get_clock().now().to_msg()
            t.header.frame_id = 'map'
            t.child_frame_id = 'odom'
            t.transform.translation.x = 0.0
            t.transform.translation.y = 0.0
            t.transform.translation.z = 0.0
            t.transform.rotation.w = 1.0
            t.transform.rotation.x = 0.0
            t.transform.rotation.y = 0.0
            t.transform.rotation.z = 0.0
            self.tf_broadcaster.sendTransform(t)
            return
        
        # ✅ COMPUTE CORRECT TRANSFORM!
        
        # Get AMCL pose (map → base_footprint)
        map_x = self.latest_amcl_pose.position.x
        map_y = self.latest_amcl_pose.position.y
        map_quat = self.latest_amcl_pose.orientation
        
        # Get odom pose (odom → base_footprint)
        odom_x = self.latest_odom_pose.position.x
        odom_y = self.latest_odom_pose.position.y
        odom_quat = self.latest_odom_pose.orientation
        
        # Convert quaternions to yaw angles
        map_yaw = self.quat_to_yaw(map_quat)
        odom_yaw = self.quat_to_yaw(odom_quat)
        
        # Compute map → odom transform
        # map_T_odom = map_T_base * inv(odom_T_base)
        
        # Inverse of odom pose
        cos_odom = math.cos(odom_yaw)
        sin_odom = math.sin(odom_yaw)
        inv_odom_x = -(odom_x * cos_odom + odom_y * sin_odom)
        inv_odom_y = -(-odom_x * sin_odom + odom_y * cos_odom)
        inv_odom_yaw = -odom_yaw
        
        # Compose transforms
        result_x = map_x + inv_odom_x * math.cos(map_yaw) - inv_odom_y * math.sin(map_yaw)
        result_y = map_y + inv_odom_x * math.sin(map_yaw) + inv_odom_y * math.cos(map_yaw)
        result_yaw = map_yaw + inv_odom_yaw
        
        # Publish transform
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'map'
        t.child_frame_id = 'odom'
        t.transform.translation.x = result_x
        t.transform.translation.y = result_y
        t.transform.translation.z = 0.0
        
        # Convert yaw back to quaternion
        result_quat = self.yaw_to_quat(result_yaw)
        t.transform.rotation = result_quat
        
        self.tf_broadcaster.sendTransform(t)
    
    def quat_to_yaw(self, quat):
        """Convert quaternion to yaw angle"""
        # Using tf_transformations
        euler = tf_transformations.euler_from_quaternion([
            quat.x, quat.y, quat.z, quat.w
        ])
        return euler[2]  # yaw
    
    def yaw_to_quat(self, yaw):
        """Convert yaw angle to quaternion"""
        from geometry_msgs.msg import Quaternion
        quat_list = tf_transformations.quaternion_from_euler(0, 0, yaw)
        quat = Quaternion()
        quat.x = quat_list[0]
        quat.y = quat_list[1]
        quat.z = quat_list[2]
        quat.w = quat_list[3]
        return quat

def main(args=None):
    rclpy.init(args=args)
    node = MapOdomTFPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()