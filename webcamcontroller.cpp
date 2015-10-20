#include "webcamcontroller.hpp"

using namespace cv;
using namespace std;

WebcamController::WebcamController()
{
    this->cap = VideoCapture (0);
    this->paused = false;
}

bool WebcamController::getPaused (void) const
{
    return this->paused;
}

void WebcamController::setPaused (bool paused)
{
    Mat frame;
    Mat edges;

    if (paused == true)
        frame = this->getFrame ();

    this->paused = paused;
}

Mat WebcamController::getFrame (void)
{
    Mat ret;

    if (this->paused == true)
        return this->savedFrame;
    else
        this->cap.read (ret);
        this->savedFrame = ret;
        return ret;
}