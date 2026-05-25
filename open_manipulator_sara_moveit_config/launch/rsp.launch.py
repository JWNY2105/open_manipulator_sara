#!/usr/bin/env python3

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import xacro


def generate_launch_description():

    ld = LaunchDescription()
    publish_frequency = LaunchConfiguration('publish_frequency')
    ld.add_action(DeclareLaunchArgument('publish_frequency', default_value='15.0'))

    # Robot description
    robot_description_config = xacro.process_file(
        os.path.join(
            get_package_share_directory('open_manipulator_sara_description'),
            'urdf',
            'open_manipulator_sara_robot.urdf.xacro',
        )
    )
    robot_description = {'robot_description': robot_description_config.toxml()}

    rsp_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        respawn=True,
        output='screen',
        parameters=[{'publish_frequency': publish_frequency}, robot_description]
    )

    ld.add_action(rsp_node)

    return ld
