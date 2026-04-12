This file contains the prime directives for this project that must be kept in mind on every iteration.

The purpose of this application is to capture a photo using a Canon camera connected via USB to a Raspberry pi. We then will do several things with this image:
1. Save the raw image to disk - call it "original-xxxxx.jpg"
2. Apply a watermark - call it "originalW-xxxxx.jpg"
3. Apply a filter to the watermarked version - call it "1976edition-xxxxx.jpg"
4. Put the image in a vertical side-by-side with the "Steve.jpg" image, inside of a 2868 x 1320 px frame that will be uploaded called "Frame.jpg". Save this as "social-xxxxx.jpg"

The process of capturing the image, and then performing the above operations should happen through a kiosk-style webpage. At idle, we should see a real-time feed from the camera on the webpage with a button to "Take photo".
After the photo is taken, the versions listed in steps 2-4 should be displayed side-by-side on the webpage.
There should be an option to re-take the photo, send it or cancel. 
If the user selects the option to send it, we should present a web form asking for a name and an email address. We then should write an email with these three images attached to send to the user.
This should direct us back to the idle screen, ready to take another photo.

The most important aspect of this application that is running on the raspberry pi is that the webpage is compatible and able to be natively rendered on Safari 4.1.3 in Mac OS 10.4.
