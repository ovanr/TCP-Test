# TCP-Test

A Black-box testing technique to test the base Linux TCP impementation

# Setup
This section will go over how to setup and run the testing environment, and how to create tests of your own. In order to start with the setup, please clone the repository.

## 0. Requirements and installation
1.  You will need a linux kernel. The currently tested kernel versions are 5.04 and 5.10, but it is expected that it will work with any kernel version.
1. In order to run this project, you need at least python version 3.8. The project has been tested with python versions 3.8 and 3.9.
1. Additionally, you must have pip installed.
1. Finally, you have to navigate to the github folder using the terminal and run the following command:
```
pip install -r requirements.txt
```
## 1. Where to find and store existing testcases
In order to find existing testcases, you must first checkout the auto_testing_develop branch. You can do that by the following git command:
```
git checkout auto_testing_develop
```
Afterwards you can find the testcases under the folder tcpTester/testCases. Each test case is represented by a python file, following the textX.py format, where X is the number of the test case.
## 2. How to write a testcase
The previous chapter mentions the directory where tests are made, as well as the naming convention. To create a new testcase we must create a new python file following the naming convention. For the purposes of this tutorial, let's say we make test15.py.
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
An example of using test commands from testCase 12:
```python
    def prepare_queues_setup_test(self):
        self.queue_test_setup_ts = [
            # SYNC(id=1, wait_response=False)
            # WAIT(sec=2)
            TestCommand(
                self.test_id,
                CommandType['CONNECT'],
                ConnectParameters(destination=SUT_IP, src_port=PORT_TS, dst_port=PORT_SUT)
            )
        ]
        self.queue_test_setup_sut = [
            TestCommand(
                self.test_id,
                CommandType['LISTEN'],
                ListenParameters(interface=SUT_IP, src_port=PORT_SUT)
            )
            # SYNC(id=1, wait_response=False)
        ]

    def prepare_queues_test(self):
        self.queue_test_ts = [
            TestCommand(
                self.test_id,
                CommandType['SENDRECEIVE'],
                SendReceiveParameters(
                    SendParameters(acknowledgement_number=4294967196, flags="A"),
                    ReceiveParameters(flags="A")
                )
            )
        ]
        self.queue_test_sut = []
```

## 3. How to run the defined testcases
