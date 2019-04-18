from pyparrot.Minidrone import Mambo
import cv2
from pyzbar import pyzbar

image = cv2.imread('kote.png',0)
barcodes = pyzbar.decode(image)

for barcode in barcodes:
	# extract the bounding box location of the barcode and draw the
	# bounding box surrounding the barcode on the image
	(x, y, w, h) = barcode.rect
	cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)

	# the barcode data is a bytes object so if we want to draw it on
	# our output image we need to convert it to a string first
	barcodeData = barcode.data.decode("utf-8")
	barcodeType = barcode.type

	# draw the barcode data and barcode type on the image
	text = "{} ({})".format(barcodeData, barcodeType)
	cv2.putText(image, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
		0.5, (0, 0, 255), 2)

	# print the barcode type and data to the terminal
	print("[INFO] Found {} barcode: {}".format(barcodeType, barcodeData))

# show the output image
cv2.imshow("Image", image)
cv2.waitKey(0)

'''

# If you are using BLE: you will need to change this to the address of YOUR mambo
# if you are using Wifi, this can be ignored
mamboAddr = "e0:14:d0:63:3d:d0"

# make my mambo object
# remember to set True/False for the wifi depending on if you are using the wifi or the BLE to connect
mambo = Mambo(mamboAddr, use_wifi=True)

print("trying to connect")
success = mambo.connect(num_retries=3)
print("connected: %s" % success)

if (success):image = cv2.imread(args["image"])

# find the barcodes in the image and decode each of the barcodes
barcodes = pyzbar.decode(image)
    # get the state information
    print("sleeping")
    mambo.smart_sleep(2)
    mambo.ask_for_state_update()
    mambo.smart_sleep(2)

    print("taking off!")
    mambo.safe_takeoff(5)

    if (mambo.sensors.flying_state != "emergency"):
        print("flying state is %s" % mambo.sensors.flying_state)
        print("Flying direct: going up")
        mambo.fly_direct(roll=0, pitch=0, yaw=0, vertical_movement=20, duration=1)

        print("flip left")
        print("flying state is %s" % mambo.sensors.flying_state)
        success = mambo.flip(direction="left")
        print("mambo flip result %s" % success)
        mambo.smart_sleep(5)

        print("flip right")
        print("flying state is %s" % mambo.sensors.flying_state)
        success = mambo.flip(direction="right")
        print("mambo flip result %s" % success)
        mambo.smart_sleep(5)

        print("flip front")
        print("flying state is %s" % mambo.sensors.flying_state)
        success = mambo.flip(direction="front")
        print("mambo flip result %s" % success)
        mambo.smart_sleep(5)

        print("flip back")
        print("flying state is %s" % mambo.sensors.flying_state)
        success = mambo.flip(direction="back")
        print("mambo flip result %s" % success)
        mambo.smart_sleep(5)

        print("landing")
        print("flying state is %s" % mambo.sensors.flying_state)
        mambo.safe_land(5)
        mambo.smart_sleep(5)

    print("disconnect")
mambo.disconnect()
'''
