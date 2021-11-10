# TCP-Test

A Black-box testing technique to test the base Linux TCP impementation

# Setup
This section will go over how to setup and run the testing environment, and how to create tests of your own. In order to start with the setup, please clone the repository.

## 1. Requirements and installation
1.  You will need a linux kernel. The currently tested kernel versions are 5.04 and 5.10, but it is expected that it will work with any kernel version.
1. In order to run this project, you need at least python version 3.8. The project has been tested with python versions 3.8 and 3.9.
1. Additionally, you must have pip installed.
1. Finally, you have to navigate to the github folder using the terminal and run the following command:
```
pip install -r requirements.txt
```

## 2. How to write a testcase
You can find the existing testcases under the folder **tcpTester/testCases**. Each test case is represented by a python file, following the textX.py format, where X is the number of the test case. To create a new testcase we must create a new python file following the naming convention. For the purposes of this tutorial, let's say we make test15.py.
### Structuring the file
First we will have to import relevant classes and tools for making a testcase. These imports are the same for any testcase.
```python
from tcpTester.testCommand import (
    CommandType,
    ConnectParameters,
    ListenParameters,
    SendReceiveParameters,
    SendParameters,
    ReceiveParameters,
    TestCommand,
)
from tcpTester.config import TEST_SERVER_IP
from tcpTester.baseTestCase import BaseTestCase
```
Afterwards, it will be necessary to define the ports for the Test Server (TS) and the  System Under Test (SUT). 
* Our convention is to use port 6000 + testNumber-1 for the TS port, and 5000 + testNumber-1 for the SUT port. 
So, given that we made test15.py, and our testNumber is 15, we would get the following:
```python
PORT_TS = 6014
PORT_SUT = 5014
```
Then, we must create a class which defines our testcase. This class must be unique compared to the classes in the other test files under testCases. We use the naming convention Test{testNumber to string}. So in our case, TestFifteen.
* The class must inherit the BaseTestCase class.
* The class must define two properties, namely
    * Test name: describes what the test is about in a few words.
    * Test number: the textNumber we talked about earlier, so 15.
Thus, we end up with:
```python
class TestFifteen(BaseTestCase):
    @property
    def test_name(self) -> str:
        return "Testing testcase creation"

    @property
    def test_id(self) -> int:
        return 15
```
Further, we have two functions that need to be defined in our TestFifteen class.
* prepare_queues_setup_test which takes self as parameter. This is used to get the SUT into the state we are testing. It can be left empty.
    * The body of this function consits of two queues
    * The self.queue_test_setup_ts queue which contains TestCommands and is responsible for the actions the TS must perform to reach a valid state for testing.
    * The self.queue_test_setup_sut queue which contains TestCommands and is responsible for the actions the SUT must perform to reach a valid state for testing.
* prepare_queues_test which also takes self as parameter. This defines the sequence of actions that the TS and SUT shall execute.
    * The body of this function also consits of two similar queus, which both contain TestCommand objects
    * The self.queue_test_ts queue
    * The self.queue_test_sut queue
An example below:
```python
    def prepare_queues_setup_test(self):
        self.queue_test_setup_ts = []
        self.queue_test_setup_sut = []

    def prepare_queues_test(self):
        self.queue_test_ts = []
        self.queue_test_sut = []
```
We fill up these queues with TestCommands. The TestCommands can be found under **tcpTester/testCommand.py**. A test command is like a mini-test, storing information such as timestamp, input, expected output, and the testID which ran it.
An example of using test commands from testCase 11:
```python
    def prepare_queues_setup_test(self):
        self.queue_test_setup_ts = [
            Command(
                CommandType['SYNC'],
                SyncParameters(
                    sync_id=1,
                    wait_for_result=False
                )
            ),
            TestCommand(
                self.test_id,
                CommandType['CONNECT'],
                ConnectParameters(
                    destination=self.sut_ip,
                    src_port=PORT_TS,
                    dst_port=PORT_SUT
                )
            ),
            Command(
                CommandType['SYNC'],
                SyncParameters(
                    sync_id=2,
                    wait_for_result=True
                )
            )
        ]
        self.queue_test_setup_sut = [
            TestCommand(
                self.test_id,
                CommandType['LISTEN'],
                ListenParameters(
                    interface=self.sut_ip,
                    src_port=PORT_SUT
                )
            ),
            Command(
                CommandType['SYNC'],
                SyncParameters(
                    sync_id=1,
                    wait_for_result=False
                )
            ),
            Command(
                CommandType['SYNC'],
                SyncParameters(
                    sync_id=2,
                    wait_for_result=True
                )
            )
        ]

    def prepare_queues_test(self):
        for _ in range(0, 3):
            self.queue_test_ts = [
                TestCommand(
                    self.test_id,
                    CommandType['RECEIVE'],
                    ReceiveParameters(flags="A", payload=PAYLOAD)
                ),
                TestCommand(
                    self.test_id,
                    CommandType['SEND'],
                    SendParameters(flags="A")
                ),
                Command(
                    CommandType['SYNC'],
                    SyncParameters(
                        sync_id=1,
                        wait_for_result=False
                    )
                ),
                Command(
                    CommandType['SYNC'],
                    SyncParameters(
                        sync_id=2,
                        wait_for_result=True
                    )
                )
            ]
            self.queue_test_sut = [
                Command(
                    CommandType['SYNC'],
                    SyncParameters(
                        sync_id=1,
                        wait_for_result=False
                    )
                ),
                TestCommand(
                    self.test_id,
                    CommandType['SEND'],
                    SendParameters(payload=PAYLOAD)
                ),
                Command(
                    CommandType['SYNC'],
                    SyncParameters(
                        sync_id=2,
                        wait_for_result=True
                    )
                )
            ]
```

## 3. How to run the defined testcases
### Configuring ini files
First you would have to configure the **sut.ini**, **test_server.ini** and the **test_runner.ini** files. These ini files contain the prots, the ips, as well as the way logging is done.
For example, these are the defaults for
* Test runner
```
[logging]
console=ERROR
file_logging=True

[test_runner]
port=8765

[sut]
ip=192.168.92.38

[test_server]
ip=192.168.92.81
```
* Test server
```
[logging]
console=ERROR
file_logging=False

[test_runner]
ip=192.168.92.38
port=8765

[test_server]
iface=en0
```
* SUT
```
[logging]
console=ERROR
file_logging=False

[test_runner]
ip=192.168.92.38
port=8765
```

As can be seen here, by default only test runner does file logging. Additionally, test runner defines an ip and a port number, which is then referenced by both the SUT and the TestServer.

### Running the tests
We have three applications which we will run in python, in the following order:
1. testRunnerMain.py
    * **If you run testRunner on a Linux machine, make sure you execute the following command first**
    ```
    sudo iptables -I OUTPUT -p tcp --tcp-flags RST RST -j DROP
    ```
    * To run testRunnerMain.py, execute the following command, pasing test_runner.ini as argument.
    ```
    python3 testRunnerMain.py test_runner.ini
    ```
1. testServerMain.py
    * To run testServerMain.py, execute the following command, pasing test_server.ini as argument.
    ```
    python3 testServerMain.py test_server.ini
    ```
1. sutMain.py
    * To run sutMain.py, execute the following command, pasing sut.ini as argument.
    ```
    python3 sutMain.py sut.ini
    ```
    
The **testRunner** screen shall output the results of the tests. Additionally, logs are created in the root project directory. As we saw int he ini files, testRunner has file logging enabled by default.

Happy testing!
