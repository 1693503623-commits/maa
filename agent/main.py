import os
import sys
from maa.agent.agent_server import AgentServer
from maa.toolkit import Toolkit

# 必须在这里 import 你的自定义动作文件，触发装饰器注册
import agent_table

def main():
    # 日志写到项目根目录的 debug/（而非子进程的工作目录 assets/）
    Toolkit.init_option(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    if len(sys.argv) < 2:
        sys.exit(1)
        
    socket_id = sys.argv[-1]

    AgentServer.start_up(socket_id)
    AgentServer.join() # 关键：阻塞主线程，保持父子进程连接
    AgentServer.shut_down()

if __name__ == "__main__":
    main()