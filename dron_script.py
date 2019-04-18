from pyparrot.Minidrone import Mambo
from pyparrot.DroneVisionGUI import DroneVisionGUI
import cv2
from pyzbar import pyzbar


# you will need to change this to the address of YOUR mambo
mamboAddr = "e0:14:d0:63:3d:d0"

# make my mambo object
# remember to set True/False for the wifi depending on if you are using the wifi or the BLE to connect
mambo = Mambo(mamboAddr, use_wifi=True)
print("trying to connect to mambo now")
success = mambo.connect(num_retries=3)
print("connected: %s" % success)

def demo_mambo_user_vision_function(mamboVision, args):
    """
    Demo the user code to run with the run button for a mambo

    :param args:
    :return:
    """
    mambo = args[0]
    print("taking off!")
    mambo.safe_takeoff(5)

    if (mambo.sensors.flying_state != "emergency"):
        print("flying state is %s" % mambo.sensors.flying_state)
        print("Flying direct: going up")
        mambo.fly_direct(roll=0, pitch=0, yaw=0, vertical_movement=15, duration=2)

        print("flip left")
        print("flying state is %s" % mambo.sensors.flying_state)
        success = mambo.flip(direction="left")
        print("mambo flip result %s" % success)
        mambo.smart_sleep(5)


if (success):
    # get the state information
    print("sleeping")
    mambo.smart_sleep(1)
    mambo.ask_for_state_update()
    mambo.smart_sleep(1)

    print("Preparing to open vision")
    mamboVision = DroneVisionGUI(mambo, is_bebop=False, buffer_size=200,
                                 user_code_to_run=demo_mambo_user_vision_function, user_args=(mambo, ))
    mamboVision._start_video_buffering()
    image_kote = mamboVision.get_latest_valid_picture()
    print(image_kote)
    cv2.imshow("Image", image_kote)
    mamboVision.open_video()






print("disconnecting")
mambo.disconnect()











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
