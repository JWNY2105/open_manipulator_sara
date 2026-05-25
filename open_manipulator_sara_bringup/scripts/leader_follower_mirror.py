#!/usr/bin/env python3
#
# Leader-Follower Mirror Node
#
# Subscribes to leader's joint states and publishes trajectory commands
# to the follower's arm controller for real-time mirroring.

import rclpy
from rclpy.node import Node
from control_msgs.action import GripperCommand
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

from rclpy.action import ActionClient


class LeaderFollowerMirror(Node):
    def __init__(self):
        super().__init__('leader_follower_mirror')

        self.declare_parameter('leader_joint_states_topic', '/leader/joint_states')
        self.declare_parameter('follower_trajectory_topic', '/arm_controller/joint_trajectory')
        self.declare_parameter('follower_gripper_topic', '/gripper_controller/gripper_cmd')
        self.declare_parameter('gripper_joint_name', 'gripper_left_joint')
        self.declare_parameter('joint_names', [
            'joint1', 'joint2', 'joint3',
            'joint4', 'joint5', 'joint6',
        ])
        self.declare_parameter('publish_rate', 50.0)

        leader_topic = self.get_parameter('leader_joint_states_topic').value
        follower_topic = self.get_parameter('follower_trajectory_topic').value
        gripper_topic = self.get_parameter('follower_gripper_topic').value
        self.gripper_joint_name = self.get_parameter('gripper_joint_name').value
        self.joint_names = self.get_parameter('joint_names').value

        self.subscription = self.create_subscription(
            JointState,
            leader_topic,
            self.joint_state_callback,
            10
        )

        self.publisher = self.create_publisher(
            JointTrajectory,
            follower_topic,
            10
        )

        self.gripper_client = ActionClient(
            self, GripperCommand, gripper_topic)

        self.latest_positions = None
        self.latest_gripper_position = None
        self.last_sent_gripper = None
        publish_rate = self.get_parameter('publish_rate').value
        self.timer = self.create_timer(1.0 / publish_rate, self.publish_trajectory)

        self.get_logger().info(
            f'Mirror node started: {leader_topic} -> {follower_topic} + {gripper_topic}'
        )

    def joint_state_callback(self, msg):
        positions = {}
        for i, name in enumerate(msg.name):
            if i < len(msg.position):
                positions[name] = msg.position[i]

        ordered_positions = []
        for joint_name in self.joint_names:
            if joint_name in positions:
                ordered_positions.append(positions[joint_name])
            else:
                return

        self.latest_positions = ordered_positions

        if self.gripper_joint_name in positions:
            self.latest_gripper_position = positions[self.gripper_joint_name]

    def publish_trajectory(self):
        if self.latest_positions is None:
            return

        trajectory = JointTrajectory()
        trajectory.joint_names = list(self.joint_names)

        point = JointTrajectoryPoint()
        point.positions = list(self.latest_positions)
        point.time_from_start = Duration(sec=0, nanosec=20000000)  # 20ms

        trajectory.points.append(point)
        self.publisher.publish(trajectory)

        # Gripper mirroring
        if self.latest_gripper_position is not None:
            if (self.last_sent_gripper is None or
                    abs(self.latest_gripper_position - self.last_sent_gripper) > 0.001):
                self.last_sent_gripper = self.latest_gripper_position
                if self.gripper_client.server_is_ready():
                    goal = GripperCommand.Goal()
                    goal.command.position = self.latest_gripper_position
                    goal.command.max_effort = 1.0
                    self.gripper_client.send_goal_async(goal)


def main(args=None):
    rclpy.init(args=args)
    node = LeaderFollowerMirror()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
