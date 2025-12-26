import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (IncludeLaunchDescription, DeclareLaunchArgument, RegisterEventHandler,
                          LogInfo, EmitEvent)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, LifecycleNode
from launch.event_handlers import OnProcessStart
from launch_ros.event_handlers import OnStateTransition
from launch.events import matches_action
import launch_ros.events
import launch_ros.events.lifecycle
import lifecycle_msgs.msg

def generate_launch_description():
    koder_bringup_pkg = get_package_share_directory('koder_bringup')

    # --- Declare arguments ---
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    slam_params_file = LaunchConfiguration('slam_params_file')

    declare_use_sim_time_argument = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation/Gazebo clock')

    declare_slam_params_file_cmd = DeclareLaunchArgument(
        'slam_params_file',
        default_value=os.path.join(koder_bringup_pkg,
                                   'config', 'slam_params.yaml'),
        description='Full path to the ROS2 parameters file for slam_toolbox node')

    # --- Nodes and Launch Includes ---

    # 1. Include the new, correct base robot bringup launch file
    robot_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(koder_bringup_pkg, 'launch', 'bringup.launch.py')
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )

    # 2. Laser scan filter node (NEW - Added to fix inconsistent scan sizes)
    laser_filter_node = Node(
        package='laser_filters',
        executable='scan_to_scan_filter_chain',
        name='laser_filter',
        output='screen',
        parameters=[
            os.path.join(koder_bringup_pkg, 'config', 'scan_filter.yaml'),
            {'use_sim_time': use_sim_time}
        ],
        remappings=[
            ('scan', 'scan_raw'),           # Input: raw scans from LD08
            ('scan_filtered', 'scan')       # Output: filtered scans to SLAM
        ]
    )

    # 3. Start SLAM Toolbox node as a LifecycleNode
    start_async_slam_toolbox_node = LifecycleNode(
        parameters=[
          slam_params_file,
          {'use_sim_time': use_sim_time}
        ],
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        namespace='',
        output='screen',
    )

    # --- Event Handlers for Lifecycle Management ---
    configure_slam_event = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=start_async_slam_toolbox_node,
            on_start=[
                LogInfo(msg='Bringup launched, configuring slam_toolbox...'),
                EmitEvent(
                    event=launch_ros.events.lifecycle.ChangeState(
                        lifecycle_node_matcher=matches_action(start_async_slam_toolbox_node),
                        transition_id=lifecycle_msgs.msg.Transition.TRANSITION_CONFIGURE,
                    )
                )
            ]
        )
    )

    activate_slam_event = RegisterEventHandler(
        event_handler=OnStateTransition(
            target_lifecycle_node=start_async_slam_toolbox_node,
            start_state='configuring',
            goal_state='inactive',
            entities=[
                LogInfo(msg='slam_toolbox configured, activating...'),
                EmitEvent(
                    event=launch_ros.events.lifecycle.ChangeState(
                        lifecycle_node_matcher=matches_action(start_async_slam_toolbox_node),
                        transition_id=lifecycle_msgs.msg.Transition.TRANSITION_ACTIVATE,
                    )
                )
            ]
        )
    )

    # --- Create Launch Description ---
    ld = LaunchDescription()

    ld.add_action(declare_use_sim_time_argument)
    ld.add_action(declare_slam_params_file_cmd)

    ld.add_action(robot_bringup_launch)
    ld.add_action(laser_filter_node)  # NEW: Add laser filter
    ld.add_action(start_async_slam_toolbox_node)

    ld.add_action(configure_slam_event)
    ld.add_action(activate_slam_event)

    return ld