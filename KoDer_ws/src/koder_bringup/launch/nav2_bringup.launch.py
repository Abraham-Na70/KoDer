import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_koder_bringup = get_package_share_directory('koder_bringup')
    
    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    map_yaml_file = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')
    autostart = LaunchConfiguration('autostart')
    
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock')
    
    declare_map_yaml_cmd = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(pkg_koder_bringup, 'maps', 'map.yaml'),
        description='Full path to map yaml file')
    
    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(pkg_koder_bringup, 'config', 'koder_nav2.yaml'),
        description='Full path to Nav2 parameters file')
    
    declare_autostart_cmd = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Automatically startup the nav2 stack')
    
    # Map server
    start_map_server_cmd = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[
            {'use_sim_time': False},
            {'yaml_filename': map_yaml_file}
        ]
    )
    
    start_map_lifecycle_manager_cmd = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_map',
        output='screen',
        parameters=[
            {'use_sim_time': False},
            {'autostart': autostart},
            {'node_names': ['map_server']}
        ]
    )
    
    # AMCL (handles map→odom transform)
    start_amcl_cmd = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[params_file, {'use_sim_time': False}]
    )
    
    # Controller
    start_controller_cmd = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[params_file, {'use_sim_time': False}]
    )
    
    # Planner
    start_planner_cmd = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=[params_file, {'use_sim_time': False}]
    )
    
    # Behavior
    start_behavior_cmd = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        output='screen',
        parameters=[params_file, {'use_sim_time': False}]
    )
    
    # BT Navigator
    start_bt_navigator_cmd = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=[params_file, {'use_sim_time': False}]
    )
    
    # Velocity Smoother
    start_velocity_smoother_cmd = Node(
        package='nav2_velocity_smoother',
        executable='velocity_smoother',
        name='velocity_smoother',
        output='screen',
        parameters=[params_file, {'use_sim_time': False}]
    )
    
    # Lifecycle manager for navigation stack
    start_lifecycle_manager_cmd = TimerAction(
        period=3.0,  # Wait 3 seconds for map server
        actions=[
            Node(
                package='nav2_lifecycle_manager',
                executable='lifecycle_manager',
                name='lifecycle_manager_navigation',
                output='screen',
                parameters=[
                    {'use_sim_time': False},
                    {'autostart': autostart},
                    {'bond_timeout': 4.0},
                    {'node_names': [
                        'amcl',
                        'controller_server',
                        'planner_server',
                        'behavior_server',
                        'bt_navigator',
                        'velocity_smoother'
                    ]}
                ]
            )
        ]
    )
    
    return LaunchDescription([
        declare_use_sim_time_cmd,
        declare_map_yaml_cmd,
        declare_params_file_cmd,
        declare_autostart_cmd,
        
        # Launch nodes
        start_map_server_cmd,
        start_map_lifecycle_manager_cmd,
        start_amcl_cmd,
        start_controller_cmd,
        start_planner_cmd,
        start_behavior_cmd,
        start_bt_navigator_cmd,
        start_velocity_smoother_cmd,
        
        # Start lifecycle manager after delay
        start_lifecycle_manager_cmd
    ])