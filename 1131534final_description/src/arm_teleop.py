#!/usr/bin/env python3
import rospy
from std_msgs.msg import Float64
from geometry_msgs.msg import Twist
import sys, select, termios, tty

msg = """
======================================================
         1131534 全車一體化鍵盤控制節點 (超直覺版)
======================================================
【底盤輪胎控制】
       ⬆️ (前進)
  ⬅️ (左轉) ⬇️ (後退) ➡️ (右轉) 
                              
   按任意其他鍵 : 煞車停下 
========================================
【控制身體關節 】

  a : 身體關節順時針/向前轉(+)      q : 身體關節逆時針/向後轉(-)

  b : 手臂關節向前轉(+)      w : 手臂關節向後轉(-)
  
  c : 籃子關節向上轉(+)      e : 籃子關節向下轉(-)

  CTRL-C : 離開程式

========================================
"""

# 設定控制參數
ARM_STEP = 0.05    # 手臂每次移動的角度
SPEED_LIN = 0.3    # 車子前進後退速度
SPEED_ANG = 0.6    # 車子原地旋轉速度

def getKey():
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
        if key == '\x1b':
            key += sys.stdin.read(2)
    else:
        key = ''
    termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, settings)
    return key

if __name__=="__main__":
    settings = termios.tcgetattr(sys.stdin.fileno())
    
    rospy.init_node('total_teleop_keyboard')

    # 機械臂的 Publisher
    pub_body = rospy.Publisher('/arm_joint/body_delta', Float64, queue_size=10)
    pub_arm = rospy.Publisher('/arm_joint/arm_delta', Float64, queue_size=10)
    pub_backet = rospy.Publisher('/arm_joint/backet_delta', Float64, queue_size=10)
    
    # 底盤輪胎的 Publisher
    pub_cmd_vel = rospy.Publisher('/cmd_vel', Twist, queue_size=10)

    try:
        print(msg)
        while not rospy.is_shutdown():
            key = getKey()
            
            body_d = 0.0
            arm_d = 0.0
            backet_d = 0.0
            twist = Twist()
            
            # ====== 右手：根據你的測試結果重新對應方向鍵 ======
            if key == '\x1b[C':   # ➡️ 鍵：根據你的測試改成「前進」
                twist.linear.x = SPEED_LIN
            elif key == '\x1b[D': # ⬅️ 鍵：根據你的測試改成「後退」
                twist.linear.x = -SPEED_LIN
                
            elif key == '\x1b[A': # ⬆️ 鍵：改成「左轉」
                twist.angular.z = -SPEED_ANG
            elif key == '\x1b[B': # ⬇️ 鍵：改成「右轉」
                twist.angular.z = SPEED_ANG
                
            # ====== 左手：機械臂控制 ======
            elif key == 'a':
                body_d = ARM_STEP
            elif key == 'q':
                body_d = -ARM_STEP
                
            elif key == 'b':
                arm_d = ARM_STEP
            elif key == 'w':
                arm_d = -ARM_STEP
                
            elif key == 'c':
                backet_d = ARM_STEP
            elif key == 'e':
                backet_d = -ARM_STEP

            elif key == '\x03': # CTRL-C
                break

            # 發送手臂訊號
            if body_d != 0.0: pub_body.publish(body_d)
            if arm_d != 0.0: pub_arm.publish(arm_d)
            if backet_d != 0.0: pub_backet.publish(backet_d)
            
            # 發送車子速度訊號
            pub_cmd_vel.publish(twist)

    except Exception as e:
        print(e)

    finally:
        twist = Twist()
        pub_cmd_vel.publish(twist)
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, settings)
