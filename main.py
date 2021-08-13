# encoding : utf-8
'''
串口助手
'''

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from uart import Ui_Form
import serial
import serial.tools.list_ports
from collections import deque


class Uart_Demo(QWidget,Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self._Load_QSS()
        self.timer_send = QTimer(self)   #定时发送数据定时器
        self.timer_recv = QTimer(self)   #定时接收数据定时器
        self.slot_connect()
        self.serial = serial.Serial()
        self.port_check()
        self.data_num_recv = 0  #接收到的字节数
        self.data_num_send = 0  #发送的字节数
        self.update_DataShow()
        self.uart_state = False #当前串口是否打开
        self.txt_send_last_num = 0   #txt_send上一次字符数目
        self.queue_max_num = 20 #画图队列的最大数
        self.queue = deque([0.0 for _ in range(self.queue_max_num)])




    def _Load_QSS(self):
        '''
        加载QSS文件
        :return:
        '''
        try:
            with open('QSS/flatwhite.qss','r') as f:
                qss = f.read()
                self.setStyleSheet(qss)
        except:
            print('Open QSS File Error')

        self.txt_recv.setFont(QFont("Consolas", 16))
        self.txt_recv.setStyleSheet("color:#CCCCFF")
        self.txt_send.setFont(QFont("Consolas", 16))
        self.txt_send.setStyleSheet("color:#99CCFF")
        self.btn_send.setFont(QFont("Consolas", 12))

    def slot_connect(self):
        '''
        信号和槽函数连接
        :return:
        '''
        self.btn_open_uart.clicked.connect(self.slot_port_open)
        self.timer_recv.timeout.connect(self.slot_data_recv)
        self.timer_send.timeout.connect(self.slot_data_send)
        self.cb_timed_send.stateChanged.connect(self.slot_data_send_timer)
        self.btn_send.clicked.connect(self.slot_data_send)
        self.txt_send.textChanged.connect(self.slot_txt_send_setspace)

    def port_check(self):
        '''
        串口端口检测
        :return:
        '''
        self.com_dict = {}
        port_list = list(serial.tools.list_ports.comports())
        self.cbb_uart_port.clear()
        if port_list:
            for port in port_list:
                self.com_dict[port[0]] = port[1]
                self.cbb_uart_port.addItem(port[0])
        else:
            self.cbb_uart_port.addItem('无串口')

    def update_DataShow(self):
        '''
        更新一些数据显示
        :return:
        '''
        self.lb_recv_num.setText('接收:{}'.format(self.data_num_recv))
        self.lb_send_num.setText('发送:{}'.format(self.data_num_send))

    def slot_port_open(self):
        '''
        槽函数，打开串口
        :return:
        '''
        print('func slot_port_open')
        if not self.uart_state:
            map_bytesize = {
                '5':serial.FIVEBITS,
                '6':serial.SIXBITS,
                '7':serial.SEVENBITS,
                '8':serial.EIGHTBITS,
            }
            map_stopbits = {
                'One':serial.STOPBITS_ONE,
                'Two':serial.STOPBITS_TWO,
                'OnePointF':serial.STOPBITS_ONE_POINT_FIVE,
            }
            map_parity = {
                'Even':serial.PARITY_EVEN,
                'Mark':serial.PARITY_MARK,
                'None':serial.PARITY_NONE,
                'Odd':serial.PARITY_ODD,
            }
            port = self.cbb_uart_port.currentText()
            baud = self.cbb_uart_baud.currentText()
            byte_size = self.cbb_data_bit.currentText()
            byte_size = map_bytesize[byte_size]
            stop_size = self.cbb_stop_bit.currentText()
            stop_size = map_stopbits[stop_size]
            check_size = self.cbb_check_bit.currentText()
            check_size = map_parity[check_size]

            self.serial.port = port
            self.serial.baudrate = baud
            self.serial.bytesize = byte_size
            self.serial.stopbits = stop_size
            self.serial.parity = check_size

            try:
                self.serial.open()
                print('open uart port')
            except:
                QMessageBox.critical(self,'Port Error','此串口不能被打开!!')
                return None

            self.btn_open_uart.setText('关闭串口')
            self.uart_state = True
            #打开串口接收定时器，周期为2ms
            self.timer_recv.start(2)

        else:
            self.btn_open_uart.setText('打开串口')
            self.uart_state = False
            self.timer_recv.stop()
            self.timer_send.stop()
            try:
                self.serial.close()
                print('close uart port')
            except Exception as e:
                print(e)
            self.data_num_recv = 0  # 接收到的字节数
            self.data_num_send = 0  # 发送的字节数
            self.update_DataShow()




    def slot_data_send(self):
        '''
        槽函数，发送数据
        :return:
        '''
        print('slot_data_send')
        if self.serial.isOpen():
            input_s = self.txt_send.toPlainText()
            if input_s :   # 非空字符串
                if self.cb_hex_send.isChecked():
                    # hex发送
                    input_s = input_s.strip()
                    send_list = input_s.split(' ')
                    try:
                        for i in range(len(send_list)):
                            send_list[i] = int(send_list[i], 16)
                        input_s = bytes(send_list)
                    except:
                        QMessageBox.critical(self, 'wrong data', '请输入十六进制数据，以空格分开!')
                        self.timer_send.stop()
                        self.cb_hex_send.setChecked(False)
                        return None
                else:
                    # ascii发送
                    input_s = (input_s).encode('utf-8')
                num = self.serial.write(input_s)
                data = input_s
                data_str = data.decode('utf-8',errors='ignore')
                show_content = ''
                # hex格式显示
                if self.cb_hex_display.checkState():
                    for i in range(len(data)):
                        show_content += '{:02X}'.format(data[i]) + ' '
                else:
                    show_content = data_str
                self.show_on_Txt_recv(show_content,'>> ','#99CCFF')
                self.data_num_send += num
                self.update_DataShow()
        else:
            QMessageBox.critical(self, 'Wrong', '未连接串口!!!')
            self.timer_send.stop()
            self.cb_hex_send.setChecked(False)
            return None


    def slot_data_recv(self):
        '''
        槽函数，接收数据
        :return:
        '''
        try:
            num = self.serial.inWaiting()
        except Exception as e:
            print(e)
            return None
        if num>0:
            data = self.serial.read(num)
            data_str = data.decode('utf-8')
            show_content = ''
            #hex格式显示
            if self.cb_hex_display.checkState():
                for i in range(len(data)):
                    show_content += '{:02X}'.format(data[i]) + ' '
            else:
                show_content = data_str
            self.show_on_Txt_recv(show_content,'<< ','#CCCCFF')
            self.data_num_recv += num
            self.update_DataShow()
            # 检验数据是否需要绘制
            data_list = data_str.split(':')
            if len(data_list)==2:
                try:
                    data_num = float(data_list[1])
                except:
                    return None
                self.queue.popleft()
                self.queue.append(data_num)
                self.widget_draw.mpl.start_static_plot(
                    range(self.queue_max_num),
                    self.queue,
                    '时间戳',
                    '数据值',
                    data_list[0]
                )


        else:
            pass

    def slot_data_send_timer(self):
        '''
        槽函数,设置是否定时发送数据
        :return:
        '''
        print('func data_send_timer')
        if self.cb_timed_send.isChecked():
            self.timer_send.start(int(self.dsb_time.value()*1000))
            self.txt_send.setEnabled(False)
        else:
            self.timer_send.stop()
            self.txt_send.setEnabled(True)


    def show_on_Txt_recv(self,content:str,prefix = '',color='#CCCCFF'):
        '''
        在txt_recv控件上显示内容
        :param content: 显示内容
        :param prefix: 内容前缀
        :param color: 字体颜色
        :return:
        '''
        if content.endswith('\n'):
            show_content = prefix + content
        else:
            show_content = prefix + content + '\n'
        show_content = show_content.replace('<=','&le;')
        show_content = show_content.replace('>=','&ge;')
        show_content = show_content.replace('<','&lt;')
        show_content = show_content.replace('>','&gt;')
        self.txt_recv.insertHtml(
            '<font color=' + color + ' style="white-space: pre-line;">' + show_content + '</font>'
        )

        # 获取到text光标
        textCursor = self.txt_recv.textCursor()
        # 滚动到底部
        textCursor.movePosition(textCursor.End)
        # 设置光标到text中去
        self.txt_recv.setTextCursor(textCursor)

    def slot_txt_send_setspace(self):
        '''
        槽函数，设置自动空格
        :return:
        '''
        if self.cb_hex_send.isChecked():
            text = self.txt_send.toPlainText()
            num = len(text.replace(' ',''))
            if num > self.txt_send_last_num and not text.endswith(' '):    #改变为新增内容
                if num % 2 == 0:
                    self.txt_send.insertPlainText(' ')
            self.txt_send_last_num = num
        else:
            pass








if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = Uart_Demo()
    win.show()
    sys.exit(app.exec_())