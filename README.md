# TCP Testing using Torxakis

## Running

**Note that the `testServerMain.py` and the `sutMain.py` must run on different machines**

1. Install python dependencies: `pip install --user -r requirements.txt`

2. Edit `test_server.ini` and specify the interface (iface) of where the test server should listen to (wifi or ethernet), specify the IP of the host that will be running the SUT and the port for communicating with Torxakis (in the Torxakis model this would be the port for channels InSutNet and OutSutNet)

3. Edit `sut.ini` and specify the Torxakis port (in Torxakis model this would be the port for channels InSutUser and OutSutUser). Additionally specify the IP address of the host that will be running the test server

4. Update the torxakis model with the IP and ports of the Sut and Test Server (model is in `torxakisTcpTester/Tcp.txs`)

5. Start the sut: `python3 sutMain.py sut.ini`

6. Start the test server: `python3 testServerMain.py test_server.ini`

7. Start torxakis: `cd torxakisTcpTester; torxakis Tcp.txs`

8. Run Torxakis command: `tester Tcp Sut`

9. Run Torxakis command: `test 100`
