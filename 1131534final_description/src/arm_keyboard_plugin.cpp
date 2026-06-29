#include <gazebo/gazebo.hh>
#include <gazebo/physics/physics.hh>
#include <ros/ros.h>
#include <std_msgs/Float64.h>

namespace gazebo {
class ArmKeyboardPlugin : public ModelPlugin {
public:
  void Load(physics::ModelPtr _model, sdf::ElementPtr _sdf) override {
    model = _model;
    
    // 獲取三個關節的指標
    body = model->GetJoint(_sdf->Get<std::string>("body_arm"));
    arm = model->GetJoint(_sdf->Get<std::string>("arms"));
    backet = model->GetJoint(_sdf->Get<std::string>("backet_arm"));

    // 設定三個關節的 PID 控制器參數
    controller = model->GetJointController();
    controller->SetPositionPID(body->GetScopedName(), common::PID(50000, 10, 1000));
    controller->SetPositionPID(arm->GetScopedName(), common::PID(20000, 5, 500));
    controller->SetPositionPID(backet->GetScopedName(), common::PID(30000, 5, 600));

    // 紀錄目前的初始位置作為目標值
    bodyTarget = body->Position(0);
    armTarget = arm->Position(0);
    backetTarget = backet->Position(0);

    // 初始化目標位置
    controller->SetPositionTarget(body->GetScopedName(), bodyTarget);
    controller->SetPositionTarget(arm->GetScopedName(), armTarget);
    controller->SetPositionTarget(backet->GetScopedName(), backetTarget);

    // 初始化 ROS 節點
    if (!ros::isInitialized()) {
      int argc = 0;
      char **argv = NULL;
      ros::init(argc, argv, "gazebo_arm_plugin_node", ros::init_options::NoSigintHandler);
    }
    rosNode.reset(new ros::NodeHandle("gazebo_client"));
    
    // 讓三個關節各自訂閱獨立的增量 Topic，絕對跟 cmd_vel 分開！
    bodySub = rosNode->subscribe("/arm_joint/body_delta", 10, &ArmKeyboardPlugin::OnBodyCmd, this);
    armSub = rosNode->subscribe("/arm_joint/arm_delta", 10, &ArmKeyboardPlugin::OnArmCmd, this);
    backetSub = rosNode->subscribe("/arm_joint/backet_delta", 10, &ArmKeyboardPlugin::OnBacketCmd, this);

    updateConnection = event::Events::ConnectWorldUpdateBegin(
        std::bind(&ArmKeyboardPlugin::OnUpdate, this));
  }

  // 獨立控制下臂
  void OnBodyCmd(const std_msgs::Float64::ConstPtr& msg) {
    bodyTarget += msg->data;
    controller->SetPositionTarget(body->GetScopedName(), bodyTarget);
  }

  // 獨立控制上臂
  void OnArmCmd(const std_msgs::Float64::ConstPtr& msg) {
    armTarget += msg->data;
    controller->SetPositionTarget(arm->GetScopedName(), armTarget);
  }

  // 獨立控制籃子
  void OnBacketCmd(const std_msgs::Float64::ConstPtr& msg) {
    backetTarget += msg->data;
    controller->SetPositionTarget(backet->GetScopedName(), backetTarget);
  }

  void OnUpdate() {
    ros::spinOnce(); 
    controller->Update();   
  }

private:
  physics::ModelPtr model;
  physics::JointPtr body, arm, backet; 
  physics::JointControllerPtr controller;
  double bodyTarget{}, armTarget{}, backetTarget{}; 
  
  std::unique_ptr<ros::NodeHandle> rosNode;
  ros::Subscriber bodySub, armSub, backetSub;
  event::ConnectionPtr updateConnection;
};

GZ_REGISTER_MODEL_PLUGIN(ArmKeyboardPlugin)
}
