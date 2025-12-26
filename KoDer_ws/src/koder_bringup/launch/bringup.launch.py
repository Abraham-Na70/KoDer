import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration

def generate_launch_description():

    koder_description_pkg = get_package_share_directory('koder_description')
    koder_bringup_pkg = get_package_share_directory('koder_bringup')
    # use_sim_time = LaunchConfiguration('use_sim_time', default='false')

    micro_ros_agent_node = Node(
        package='micro_ros_agent',
        executable='micro_ros_agent',
        name='micro_ros_agent',
        output='screen',
        arguments=['serial', '--dev', '/dev/ttyAMA0', '-b', '921600']
    )

    # MODIFIED: Launch LD08 driver directly with remapping to scan_raw
    lidar_node = Node(
        package='ld08_driver',
        executable='ld08_driver',
        name='ld08_driver',
        output='screen',
        parameters=[
            {'frame_id': 'base_scan'},
            {'use_sim_time': False}
        ]
    )

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': open(os.path.join(koder_description_pkg, 'urdf', 'koder.urdf')).read(),
            'use_sim_time': False,
            'publish_frequency': 30.0,  # ← ADD THIS! Publish at 30 Hz
        }]
    )

    robot_localization_node = Node(
       package='robot_localization',
       executable='ekf_node',
       name='ekf_filter_node',
       output='screen',
       parameters=[os.path.join(koder_bringup_pkg, 'config', 'ekf.yaml'),
                   {'use_sim_time': False}]
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
        
        # All nodes launch together
        micro_ros_agent_node,
        lidar_node,
        robot_state_publisher_node,
        robot_localization_node
    ])