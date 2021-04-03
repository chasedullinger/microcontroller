try:
    import usocket as socket
except:
    import socket

import machine
import ntptime, utime
from machine import RTC, Pin


response_template = """HTTP/1.0 200 OK

%s
"""


seconds = ntptime.time()
rtc = RTC()
rtc.datetime(utime.localtime(seconds))

adc = machine.ADC(0)

led = Pin(9, Pin.OUT)

switch_pin = Pin(10, Pin.IN)

def time():
    body = """<html>
 <body>
 <h1>Time</h1>
 <p>%s</p>
 </body>
 </html>
    """ % str(rtc.datetime())

    return response_template % body


def dummy():
    body = "This is a dummy endpoint"

    return response_template % body


def light_on():
    led(1)

    body = "The light is on! :-)"

    return response_template % body


def light_off():
    led(0)

    body = "The light is off! :-("

    return response_template % body


def switch():
    state = switch_pin.value()
    body = "Switch state is {}".format(state)

    return response_template % body


def light():
     body = "Light value: {}".format(adc.read())
     return response_template % body


handlers = {
    'time': time,
    'dummy': dummy,
    'light_on': light_on,
    'light_off': light_off,
    'switch': switch,
    'light': light,
}


def main():
    s = socket.socket()
    ai = socket.getaddrinfo("0.0.0.0", 8080)
    addr = ai[0][-1]

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    s.bind(addr)
    s.listen(5)
    print("Listening, connect your browser to http://<this_host>:8080/")

    while True:
        res = s.accept()
        client_s = res[0]
        client_addr = res[1]
        req = client_s.recv(4096)
        print("Request:")
        print(req)

        # The first line of a request looks like "GET /arbitrary/path/ HTTP/1.1".
        # This grabs that first line and whittles it down to just "/arbitrary/path/"
        if req.decode():
            path = req.decode().split("\r\n")[0].split(" ")[1]
        else:
            continue

        # Given the path, identify the correct handler to use
        try:
            handler = handlers[path.strip('/').split('/')[0]]
        except KeyError:
            handler = dummy

        response = handler()

        # A handler returns an entire response in the form of a multi-line string.
        # This breaks up the response into single strings, byte-encodes them, and
        # joins them back together with b"\r\n". Then it sends that to the client.
        client_s.send(b"\r\n".join([line.encode() for line in response.split("\n")]))

        client_s.close()
        print()


main()
