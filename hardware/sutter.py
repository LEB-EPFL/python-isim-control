import time, serial
from pymm_eventserver.event_thread import EventListener


class Lambda_10_B:
    def __init__(self, read_on_init=True, event_thread: EventListener = None):
        print("Initializing Sutter filter wheel...")
        try:
            self.serial = serial.Serial('COM9', 128000)
        except serial.SerialException:
            raise UserWarning(
                "Could not open the serial port to the Sutter Lambda 10-B." +
                " Is it on? Is it plugged in? Plug it in! Turn it on!")
        self.serial.write(b'\xee')
        if read_on_init:
            self.read(2)
            self.init_finished = True
            print ("Done initializing filter wheel.")
        else:
            self.init_finished = False
        self.wheel_position = 0
        
        if event_thread is not None:
            self.event_thread = event_thread
            self.event_thread.configuration_settings_event.connect(self.signal_move)
        
        return None

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def signal_move(self, device, prop, value):
        """Receive an event from the event_bus and perform the requested move"""
        print(device, prop, value)
        if all([device == "561_AOTF", prop == "Channel"]):
            if value == "toggle":
                self.toggle()
            else:
                self.move(int(value)-1)

    def move(self, filter_slot=0, speed=1):
        if filter_slot == self.wheel_position:
            print ("Filter wheel is already at position", self.wheel_position)
            return None
        assert filter_slot in range(10)
        assert speed in range(8)
        if not self.init_finished:
            self.read(2)
            self.init_finished = True
            print("Done initializing filter wheel.")
        print("Moving filter wheel to position", filter_slot)
        self.serial.write(chr(filter_slot + 16*speed).encode('utf-8'))
        self.read(2)
        self.wheel_position = filter_slot
        return None

    def toggle(self):
        "Toggle inbetween 488 and 561"
        if self.wheel_position == 1:
            self.move(2)
        elif self.wheel_position == 2:
            self.move(1)
        else:
            self.move(1)

    def read(self, num_bytes):
        for i in range(100):
            num_waiting = self.serial.inWaiting()
            if num_waiting == num_bytes:
                break
            time.sleep(0.01)
        else:
            raise UserWarning(
                "The serial port to the Sutter Lambda 10-B" +
                " is on, but it isn't responding as expected.")
        return self.serial.read(num_bytes)

    def close(self):
        self.move()
        self.serial.close()


if __name__ == '__main__':
    with Lambda_10_B() as wheel:
        wheel.move(0)
        wheel.move(1)
