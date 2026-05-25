#!/usr/bin/env python3
#
# Dual robot launch for imitation learning (leader-follower)
#
# Follower: root namespace, /dev/ttyACM0, motor IDs 11-17
# Leader:   /leader/ namespace, /dev/ttyACM2, motor IDs 11-17 (separate bus)
#           Leader runs with torque off for human backdrive

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import RegisterEventHandler
from launch.actions import TimerAction
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command
from launch.substitutions import FindExecutable
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    follower_port = LaunchConfiguration('follower_port')
    leader_port = LaunchConfiguration('leader_port')

    declared_arguments = [
        DeclareLaunchArgument(
            'follower_port',
            default_value='/dev/ttyACM0',
            description='Serial port for the follower robot'),
        DeclareLaunchArgument(
            'leader_port',
            default_value='/dev/ttyACM2',
            description='Serial port for the leader robot'),
    ]

    # --- Follower URDF ---
    follower_urdf = Command(
        [
            PathJoinSubstitution([FindExecutable(name='xacro')]),
            ' ',
            PathJoinSubstitution(
                [
                    FindPackageShare('open_manipulator_sara_description'),
                    'urdf',
                    'open_manipulator_sara_robot.urdf.xacro'
                ]
            ),
            ' use_sim:=false use_fake_hardware:=false port_name:=',
            follower_port,
            ' role:=follower',
        ]
    )

    follower_controller_config = PathJoinSubstitution(
        [
            FindPackageShare('open_manipulator_sara_bringup'),
            'config',
            'hardware_controller_manager.yaml',
        ]
    )

    # --- Leader URDF ---
    leader_urdf = Command(
        [
            PathJoinSubstitution([FindExecutable(name='xacro')]),
            ' ',
            PathJoinSubstitution(
                [
                    FindPackageShare('open_manipulator_sara_description'),
                    'urdf',
                    'open_manipulator_sara_robot.urdf.xacro'
                ]
            ),
            ' use_sim:=false use_fake_hardware:=false port_name:=',
            leader_port,
            ' role:=leader',
        ]
    )

    leader_controller_params = {
        'update_rate': 100,
        'joint_state_broadcaster': {
            'type': 'joint_state_broadcaster/JointStateBroadcaster',
        },
    }

    # ==================== FOLLOWER (root namespace) ====================
    follower_robot_description = ParameterValue(follower_urdf, value_type=str)

    follower_control_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[
            {'robot_description': follower_robot_description},
            follower_controller_config
        ],
        output='both',
    )

    follower_robot_state_pub = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': follower_robot_description}],
        output='screen'
    )

    follower_jsb_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        output='screen',
    )

    follower_arm_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['arm_controller'],
        output='screen',
    )

    follower_gripper_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['gripper_controller'],
        output='screen',
    )

    delay_follower_arm = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=follower_jsb_spawner,
            on_exit=[follower_arm_controller_spawner],
        )
    )

    delay_follower_gripper = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=follower_jsb_spawner,
            on_exit=[follower_gripper_controller_spawner],
        )
    )

    # ==================== LEADER (/leader namespace) ====================
    leader_robot_description = ParameterValue(leader_urdf, value_type=str)

    leader_control_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        namespace='leader',
        parameters=[
            {'robot_description': leader_robot_description},
            leader_controller_params
        ],
        output='both',
    )

    leader_robot_state_pub = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        namespace='leader',
        parameters=[
            {'robot_description': leader_robot_description},
            {'frame_prefix': 'leader_'},
        ],
        output='screen',
    )

    leader_jsb_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager', '/leader/controller_manager'
        ],
        output='screen',
    )

    # Start leader after follower arm controller is ready
    delay_leader_start = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=follower_arm_controller_spawner,
            on_exit=[leader_control_node, leader_robot_state_pub],
        )
    )

    # Start leader joint state broadcaster after leader is up
    delay_leader_jsb = TimerAction(
        period=5.0,
        actions=[leader_jsb_spawner],
    )

    # ==================== MIRROR NODE ====================
    mirror_node = Node(
        package='open_manipulator_sara_bringup',
        executable='leader_follower_mirror',
        output='screen',
        parameters=[{
            'leader_joint_states_topic': '/leader/joint_states',
            'follower_trajectory_topic': '/arm_controller/joint_trajectory',
            'joint_names': [
                'joint1', 'joint2', 'joint3',
                'joint4', 'joint5', 'joint6',
            ],
        }],
    )

    delay_mirror = TimerAction(
        period=8.0,
        actions=[mirror_node],
    )

    nodes = [
        # Follower
        follower_control_node,
        follower_robot_state_pub,
        follower_jsb_spawner,
        delay_follower_arm,
        delay_follower_gripper,
        # Leader (delayed)
        delay_leader_start,
        delay_leader_jsb,
        # Mirror (delayed)
        delay_mirror,
    ]

    return LaunchDescription(declared_arguments + nodes)
