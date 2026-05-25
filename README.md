# Open Manipulator SARA 6-DOF

## 사전 설정

```bash
// 포트 권한 설정
sudo chmod 666 /dev/ttyUSB0
sudo chmod 666 /dev/ttyUSB1

// 빌드 (conda 환경 비활성화 필요)
cd ~/colcon_ws
colcon build --packages-select open_manipulator_sara_description open_manipulator_sara_bringup open_manipulator_sara_moveit_config

// 환경 소싱
source ~/colcon_ws/install/setup.bash
```

## 단일 로봇 실행

```bash
// 매니퓰레이터 구동 명령
source ~/colcon_ws/install/setup.bash
ros2 launch open_manipulator_sara_bringup hardware.launch.py port_name:=/dev/ttyUSB0 start_rviz:=true

// 매니퓰레이터 MoveIt2 실행 커맨드 (별도 터미널)
ros2 launch open_manipulator_sara_moveit_config moveit_core.launch.py use_sim:=false
```

## 듀얼 로봇 실행 (Leader-Follower 모방학습)

```bash
// 매니퓰레이터 동시 실행 (Leader-Follower)
source ~/colcon_ws/install/setup.bash
ros2 launch open_manipulator_sara_bringup dual_robot.launch.py follower_port:=/dev/ttyUSB0 leader_port:=/dev/ttyUSB1

// 매니퓰레이터 Leader 토크 off 명령 (별도 터미널)
ros2 service call /leader/dynamixel_hardware_interface/set_dxl_torque std_srvs/srv/SetBool "{data: false}"

// 매니퓰레이터 Leader 토크 on 명령
ros2 service call /leader/dynamixel_hardware_interface/set_dxl_torque std_srvs/srv/SetBool "{data: true}"
```

## Fake Hardware 실행 (하드웨어 없이 테스트)

```bash
// Fake 하드웨어로 실행
ros2 launch open_manipulator_sara_bringup fake.launch.py
```

## 디버깅 커맨드

```bash
// Joint States 확인
ros2 topic echo /joint_states --once

// Leader Joint States 확인
ros2 topic echo /leader/joint_states --once

// 토픽 목록 확인
ros2 topic list | grep joint_states

// 컨트롤러 상태 확인
ros2 control list_controllers

// 특정 위치로 이동 (init pose)
ros2 action send_goal /arm_controller/follow_joint_trajectory control_msgs/action/FollowJointTrajectory "{
  trajectory: {
    joint_names: [joint1, joint2, joint3, joint4, joint5, joint6],
    points: [{positions: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], time_from_start: {sec: 3}}]
  }
}"
```


// 포트 권한 설정
sudo chmod 666 /dev/ttyUSB0
sudo chmod 666 /dev/ttyUSB1

// 매니퓰레이터 구동 명령
source ~/colcon_ws/install/setup.bash 
ros2 launch open_manipulator_sara_bringup hardware.launch.py port_name:=/dev/ttyUSB0 start_rviz:=true 

// 매니퓰레이터 MoveIt2 실행 커맨드
ros2 launch open_manipulator_sara_moveit_config moveit_core.launch.py use_sim:=false

// 매니퓰레이터 동시 실행(Leader-Following)
ros2 launch open_manipulator_sara_bringup dual_robot.launch.py follower_port:=/dev/ttyUSB0 leader_port:=/dev/ttyUSB1

// 매니퓰레이터 Lear 토크 off 명령
ros2 service call /leader/dynamixel_hardware_interface/set_dxl_torque std_srvs/srv/SetBool "{data: false}"