<<<<<<< HEAD
import unittest
import sys

sys.path.append("../config.py")
import config as config


class UnitTests(unittest.TestCase):
    def test_default_config(self):
        self.failUnless(config.serial_port == '/dev/ttyUSB0')
        self.failUnless(config.serial_baud == 115200)
        self.failUnless(config.serial_timeout == 0.1)
        self.failUnless(config.position_poll_interval == 250)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
=======

>>>>>>> d166e2c81cd178728562f93efb52e60df56a9230
