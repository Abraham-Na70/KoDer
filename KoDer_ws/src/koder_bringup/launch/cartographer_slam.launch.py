import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    koder_bringup_pkg = get_package_share_directory('koder_bringup')
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')

    declare_use_sim_time_argument = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation/Gazebo clock')


    # Include base robot bringup
    robot_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(koder_bringup_pkg, 'launch', 'bringup.launch.py')
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )

    # Cartographer node
    cartographer_node = Node(
        package='cartographer_ros',
        executable='cartographer_node',
        name='cartographer_node',
        output='screen',
        parameters=[
            {'use_sim_time': False}
        ],
        arguments=[
            '-configuration_directory', os.path.join(koder_bringup_pkg, 'config'),
            '-configuration_basename', 'cartographer.lua'
        ],
        remappings=[
            ('scan', '/scan'),
            ('odom', '/odometry/filtered'),
            ('imu', '/imu/data')  # ← RE-ADDED! We're using IMU now
        ]
    )

    # Occupancy grid node
    occupancy_grid_node = Node(
        package='cartographer_ros',
        executable='cartographer_occupancy_grid_node',
        name='cartographer_occupancy_grid_node',
        output='screen',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'resolution': 0.05}
        ]
    )

    return LaunchDescription([
        declare_use_sim_time_argument,
        robot_bringup_launch,        # ← SECOND (starts sensors)
        cartographer_node,           # ← THIRD (uses IMU data)
        occupancy_grid_node,         # ← FOURTH (creates map)
    ])