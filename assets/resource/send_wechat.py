import pyautogui
import pyperclip
import time
import sys

def send_msg(contact_name):
    # 1. 第一时间把手机传过来的代付链接存到变量里保护起来
    time.sleep(1) # 给跨设备剪贴板同步留1秒缓冲
    pay_link = pyperclip.paste()
    
    # 2. 唤醒微信窗口
    pyautogui.hotkey('ctrl', 'alt', 'w')
    time.sleep(1)
    
    # 3. 搜索联系人
    pyautogui.hotkey('ctrl', 'f')
    time.sleep(0.5)
    
    # 复制传进来的联系人名字，并粘贴搜索
    pyperclip.copy(contact_name)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1)
    pyautogui.press('enter') 
    time.sleep(1)
    
    # 4. 关键点：把刚才存起来的代付链接重新放回剪贴板！
    pyperclip.copy(pay_link)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.5)
    pyautogui.press('enter')
    
    print(f"已成功将代付链接发送给 {contact_name}！")

if __name__ == '__main__':
    # 接收从 MAA 传进来的名字参数，如果没有传，就默认发给 Kanbara
    name = sys.argv[1] if len(sys.argv) > 1 else "Kanbara"
    send_msg(name)