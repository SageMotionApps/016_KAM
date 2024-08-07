import os
import sys

from sage.base_app import BaseApp
import sklearn

if __name__ == "__main__":
    from gait_phase import GaitPhase
    from knee_moments import MomentPrediction
    from const import WAIT_PREDICTION, PREDICTION_DONE, R_FOOT
else:
    from .gait_phase import GaitPhase
    from .knee_moments import MomentPrediction
    from .const import WAIT_PREDICTION, PREDICTION_DONE, R_FOOT

class Core(BaseApp):
    ###########################################################
    # INITIALIZE APP
    ###########################################################
    def __init__(self, my_sage):
        BaseApp.__init__(self, my_sage, __file__)
        self.gait_phase = GaitPhase()
        self.height_meter = self.config["height"]
        self.weight_kg = self.config["weight"]
        self.moment_prediction = MomentPrediction(
            self.height_meter, self.weight_kg
        )
        self.time_now = 0

    #############################################################
    # UPON STARTING THE APP
    # If you have anything that needs to happen before the app starts
    # collecting data, you can uncomment the following lines
    # and add the code in there. This function will be called before the
    # run_in_loop() function below.
    #############################################################
    # def on_start_event(self, start_time):
    #     print("In On Start Event: {start_time}")

    ###########################################################
    # RUN APP IN LOOP
    ###########################################################
    def run_in_loop(self):
        data = self.my_sage.get_next_data()
        self.gait_phase.update_gaitphase(data[R_FOOT])
        data_to_send = self.moment_prediction.update_stream(data, self.gait_phase)
        for data, kam, _, stance_flag in data_to_send:
            self.time_now += 0.01
            my_data = {
                "time": [self.time_now],
                "KAM": [kam],
                "Stance_Flag": [stance_flag],
            }
            self.my_sage.send_stream_data(data, my_data)
            self.my_sage.save_data(data, my_data)
        return True

    #############################################################
    # UPON STOPPING THE APP
    # If you have anything that needs to happen after the app stops,
    # you can uncomment the following lines and add the code in there.
    # This function will be called after the data file is saved and
    # can be read back in for reporting purposes if needed.
    #############################################################
    # def on_stop_event(self, stop_time):
    #     print(f"In On Stop Event: {stop_time}")


if __name__ == "__main__":
    # This is only for testing. make sure you do the pairing first in web api
    from sage.sage import Sage

    app = Core(Sage())
    app.test_run()
