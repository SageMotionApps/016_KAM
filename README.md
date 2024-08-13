# 016 Knee Adduction Moment (KAM)
Estimation of Knee Adduction Moment (KAM) from wearable IMUs during walking. 

### Nodes Required: 7 
 - Sensing (7): 
   - left foot (top of the foot, with switch pointing towards body)
   - right foot (top of the foot, with switch pointing towards body)
   - left shank (Midway between Femur Lateral Epicondyle and Fibula Apex of Lateral Malleolus)
   - right shank (Midway between Femur Lateral Epicondyle and Fibula Apex of Lateral Malleolus)
   - left thigh ( Midway between Femur Greater Trochanter and Femur Lateral Epicondyle)
   - right thigh ( Midway between Femur Greater Trochanter and Femur Lateral Epicondyle)
   - pelvis (Midway between Left and Right Anterior Superior Iliac Spine)
 - Feedback (0)


## Algorithm & Calibration
### Calibration Process:
No initial static calibration is performed to compensate for misalignment with the segment, so the user should be standing upright when starting the trial.

## ML Model Statistics 
Our KAM app has two modes, real-time and offline. Due to limited computational resources, the sage system cannot run the full-size model in real-time. Thus, the real-time model has a reduced size and lower performance. 

- Real-time model with size reduction: RMSE = 0.9 (%Body weight * Body height), r = 0.79
- Offline full-size model: RMSE= 0.6 (%Body weight * Body height), r = 0.87,

RMSE is the root mean square error, and r is the correlation coefficient.

### Citation Information
> [!IMPORTANT]  
> Please cite this paper [IMU and Smartphone Camera Fusion for Knee Adduction and Knee Flexion Moment Estimation During Walking](https://ieeexplore.ieee.org/abstract/document/9826418)

For convenience, here is the BibTeX Citation:
> ```
> @ARTICLE{9826418,
>   author={Tan, Tian and Wang, Dianxin and Shull, Peter B. and Halilaj, Eni},
>   journal={IEEE Transactions on Industrial Informatics}, 
>   title={IMU and Smartphone Camera Fusion for Knee Adduction and Knee Flexion Moment Estimation During Walking}, 
>   year={2023},
>   volume={19},
>   number={2},
>   pages={1445-1455},
>   keywords={Knee;Cameras;Foot;Estimation;Feature extraction;Sensors;Legged locomotion;Deep learning;joint kinetics;osteoarthritis (OA);portable sensing},
>   doi={10.1109/TII.2022.3189648}}
> ```

## Description of Data in Downloaded File
### Calculated Fields
- time (sec): time since trial start
- weight_kg: the users weight in kilograms as entered on the app configuration panel
- height_meter: the users height in meters as entered on the app configuration panel
- KAM: right knee aduction moment
- Stance Flag: 
  - 0 for swing phase or not walking
  - 1 for stance phase
### Sensor Raw Data Values 
Please Note: Each of the columns listed below will be repeated for each sensor
- SensorIndex: index of raw sensor data
- AccelX/Y/Z (m/s^2): raw acceleration data
- GyroX/Y/Z (deg/s): raw gyroscope data
- MagX/Y/Z (μT): raw magnetometer data
- Quat1/2/3/4: quaternion data (Scaler first order)
- Sampletime: timestamp of the sensor value
- Package: package number of the sensor value

# Development and App Processing Loop
The best place to start with developing an or modifying an app, is the [SageMotion Documentation](http://docs.sagemotion.com/index.html) page.
